import os, httpx, json, re, uuid
from dotenv import load_dotenv
from typing import List, Optional
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()

MCP_JD_ANALYZER   = "http://localhost:8008/call"
MCP_QUESTION_GEN  = "http://localhost:8009/call"

# In-memory session store: session_id → cheatsheet data
SESSION_STORE: dict = {}

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0,
    max_tokens=4096,
)

@tool
def analyze_job_description(jd_text: str) -> dict:
    """Analyze a job description to extract topics, seniority, culture signals, and talking points."""
    r = httpx.post(MCP_JD_ANALYZER, json={"jd_text": jd_text}, timeout=30)
    return r.json()

@tool
def generate_interview_questions(
    job_title: str,
    core_topics: List[str],
    required_skills: List[str],
    behavioral_themes: List[str],
    seniority: str = "junior",
    resume_summary: str = "",
) -> dict:
    """Generate technical and behavioral interview questions with ideal answers."""
    r = httpx.post(MCP_QUESTION_GEN, json={
        "job_title": job_title,
        "core_topics": core_topics,
        "required_skills": required_skills,
        "behavioral_themes": behavioral_themes,
        "seniority": seniority,
        "resume_summary": resume_summary,
    }, timeout=30)
    return r.json()

tools = [analyze_job_description, generate_interview_questions]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert interview coach. Build a complete interview cheatsheet.

STEP 1: Call analyze_job_description with the full JD text.
  Save: job_title, seniority, core_topics, required_skills,
        behavioral_themes, red_flags_to_avoid, talking_points, company_culture.

STEP 2: Call generate_interview_questions with values from step 1.
  Pass resume_summary from the candidate resume if provided.

STEP 3: Return final JSON:
{{
  "job_title": "string",
  "seniority": "string",
  "company_culture": ["..."],
  "talking_points": ["3-5 things to emphasize"],
  "red_flags_to_avoid": ["..."],
  "technical_questions": [
    {{
      "question": "string",
      "topic": "string",
      "difficulty": "easy|medium|hard",
      "ideal_answer": "string",
      "follow_up": "string"
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "string",
      "theme": "string",
      "star_hint": "string",
      "ideal_answer": "string"
    }}
  ],
  "questions_to_ask_interviewer": ["string"],
  "cheatsheet_latex": "<full overleaf .tex cheatsheet>",
  "overleaf_url": "https://www.overleaf.com/latex/templates/jakes-resume/syzfjbzwjncs"
}}

For cheatsheet_latex generate a complete compilable LaTeX document using article class
that lists all questions with ideal answers, talking points, and red flags.
Return ONLY the JSON. No markdown."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    return_intermediate_steps=True,
)

def run_interview_coach(
    jd_text: str,
    resume_text: str = "",
) -> tuple[dict, str]:
    """Returns (result_dict, session_id)"""
    result = agent_executor.invoke({
        "input": f"""Build a complete interview cheatsheet for this job.

JOB DESCRIPTION:
{jd_text[:4000]}

CANDIDATE RESUME SUMMARY:
{resume_text[:1500] if resume_text else 'Not provided'}

Call both tools and return the complete cheatsheet JSON."""
    })

    output = result.get("output", "")
    try:
        output = re.sub(r"^```(?:json)?\s*\n?", "", output.strip())
        output = re.sub(r"\n?```\s*$", "", output.strip())
        data = json.loads(output)
    except Exception:
        data = {"raw_output": output, "parse_error": True}

    # Store session for practice UI
    session_id = str(uuid.uuid4())[:8]
    SESSION_STORE[session_id] = data

    return data, session_id