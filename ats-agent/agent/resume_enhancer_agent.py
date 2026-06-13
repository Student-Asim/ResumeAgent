import os, httpx, json, re
from dotenv import load_dotenv
from typing import List, Optional, Dict
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()

MCP_RESUME_WRITER  = "http://localhost:8006/call"
MCP_LATEX_GENERATOR = "http://localhost:8007/call"

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0,
    max_tokens=4096,
)

@tool
def rewrite_bullets(
    bullets: List[str],
    missing_keywords: Optional[List[str]] = None,
    job_title: Optional[str] = "",
) -> dict:
    """Rewrite resume bullet points in STAR format with strong action verbs and metrics."""
    r = httpx.post(MCP_RESUME_WRITER, json={
        "bullets": bullets,
        "missing_keywords": missing_keywords or [],
        "job_title": job_title or "",
    }, timeout=30)
    return r.json()

@tool
def generate_latex_resume(
    name: str,
    email: str,
    phone: str,
    location: str,
    summary: str,
    skills: Dict[str, List[str]],
    experience: List[dict],
    projects: List[dict],
    education: List[dict],
    linkedin: Optional[str] = "",
    github: Optional[str] = "",
    certifications: Optional[List[str]] = None,
) -> dict:
    """Generate a complete Overleaf-ready LaTeX resume from structured resume data."""
    r = httpx.post(MCP_LATEX_GENERATOR, json={
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin": linkedin or "",
        "github": github or "",
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "education": education,
        "certifications": certifications or [],
    }, timeout=30)
    return r.json()

tools = [rewrite_bullets, generate_latex_resume]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert resume enhancer. You parse resumes, improve bullets, and generate LaTeX.

Follow these steps exactly:

STEP 1: Extract all bullet points from the experience and projects sections of the resume.
  Call rewrite_bullets with:
  - bullets = all extracted bullet points as a list of strings
  - missing_keywords = the missing keywords provided (if any)
  - job_title = the target job title (if provided)

STEP 2: Call generate_latex_resume with the complete structured resume data.
  Use the REWRITTEN bullets from step 1 (improved field) for experience and projects.
  Extract from the original resume:
  - name, email, phone, location, linkedin, github
  - summary (first paragraph or objective)
  - skills as a dict: {{"Languages & Tools": [...], "AI/ML": [...], "Frameworks": [...]}}
  - experience: list of {{"title": "...", "company": "...", "date": "...", "bullets": [...]}}
  - projects: list of {{"name": "...", "tech": "...", "bullets": [...]}}
  - education: list of {{"degree": "...", "institution": "...", "date": "...", "gpa": "..."}}
  - certifications: list of strings

STEP 3: Return final JSON:
{{
  "enhanced_bullets": [list of {{"original": "...", "improved": "..."}}],
  "latex": "<full .tex file content>",
  "filename": "resume_enhanced.tex",
  "instructions": "Paste into overleaf.com → New Project → Blank Project → replace main.tex → Compile"
}}

Return ONLY the JSON. No markdown wrapping."""),
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

def run_resume_enhancer(
    resume_text: str,
    missing_keywords: Optional[List[str]] = None,
    job_title: Optional[str] = "",
) -> dict:
    result = agent_executor.invoke({
        "input": f"""Enhance this resume and generate an Overleaf LaTeX file.

TARGET JOB TITLE: {job_title or 'Not specified'}
MISSING KEYWORDS TO ADD: {', '.join(missing_keywords or []) or 'None'}

RESUME TEXT:
{resume_text[:6000]}

Call both tools in order and return the final JSON with enhanced_bullets and latex fields."""
    })

    output = result.get("output", "")
    try:
        output = re.sub(r"^```(?:json)?\s*\n?", "", output.strip())
        output = re.sub(r"\n?```\s*$", "", output.strip())
        return json.loads(output)
    except Exception:
        return {"raw_output": output, "parse_error": True}