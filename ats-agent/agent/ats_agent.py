import os, httpx, json, re, logging
from dotenv import load_dotenv
from typing import List, Optional
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor  # fix 1
load_dotenv()

MCP_JD_PARSER      = "http://localhost:8001/call"
MCP_KW_EXTRACTOR   = "http://localhost:8002/call"
MCP_ATS_SCORE      = "http://localhost:8003/call"

@tool
def parse_job_description(job_text: str = "", job_url: str = "") -> dict:
    """Parse a job description from raw text or a URL. Returns the cleaned text."""
    r = httpx.post(MCP_JD_PARSER, json={"job_text": job_text, "job_url": job_url}, timeout=15)
    return r.json()

@tool
def extract_keywords(text: str) -> dict:
    """Extract important skills, keywords, and entities from job or resume text."""
    r = httpx.post(MCP_KW_EXTRACTOR, json={"jd_text": text}, timeout=15)
    logging.info(f"extract_keywords status={r.status_code}, body={r.text[:500]}")

    if r.status_code != 200:
        logging.error(f"Keyword API error {r.status_code}: {r.text[:500]}")
        return {"error": f"keyword_api_{r.status_code}", "raw": r.text[:200]}

    try:
        return r.json()
    except ValueError:
        logging.error(f"Non-JSON response from keyword API: {r.text[:500]}")
        return {"error": "keyword_api_non_json", "raw": r.text[:200]}

@tool
def compute_ats_score(
    resume_text: str,
    required_skills: List[str],
    preferred_skills: List[str],
    keywords: List[str],
    certifications: List[str],
    experience_years: Optional[int] = None,
) -> dict:
    """Compute the ATS score for a resume against extracted job requirements."""
    r = httpx.post(MCP_ATS_SCORE, json={
        "resume_text": resume_text,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "keywords": keywords,
        "certifications": certifications,
        "experience_years": experience_years,
    }, timeout=30)
    return r.json()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",  # fix 2: 8b → 70b for reliable tool chaining
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    temperature=0,
    max_tokens=2048,                  # fix 3: 512 → 2048 for full JSON report
)

tools = [parse_job_description, extract_keywords, compute_ats_score]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert ATS analyzer. Follow these steps exactly:

STEP 1: Call parse_job_description with the job text or URL.
STEP 2: Call extract_keywords with the raw_text from step 1.
STEP 3: Call compute_ats_score using:
  - resume_text = the resume provided
  - required_skills = required_skills list from step 2
  - preferred_skills = preferred_skills list from step 2
  - keywords = keywords list from step 2
  - certifications = certifications list from step 2
  - experience_years = experience_years from step 2

STEP 4: Return a JSON report with:
  - ats_score
  - verdict (PASS if >= 75, else NEEDS IMPROVEMENT)
  - breakdown (per dimension scores)
  - matched (what was found)
  - missing (critical gaps)
  - top_suggestions (3 specific actionable fixes)

Never skip a step. Always pass the actual extracted lists to the scorer."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=6,
    return_intermediate_steps=True,
)

def run_ats_analysis(job_input: str, resume_text: str) -> dict:
    user_message = f"""Analyze this resume against the job description.

JOB DESCRIPTION (text or URL):
{job_input}

RESUME TEXT:
{resume_text[:5000]}

Run all tools and return the complete ATS analysis report as JSON."""

    result = agent_executor.invoke({"input": user_message})

    output = result.get("output", "")
    try:
        output = re.sub(r"^```(?:json)?\s*\n?", "", output.strip())
        output = re.sub(r"\n?```\s*$", "", output.strip())
        return json.loads(output)
    except Exception:
        return {"raw_output": output, "parse_error": True}