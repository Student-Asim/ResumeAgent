import os, httpx, json, re
from dotenv import load_dotenv
from typing import List
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

load_dotenv()

MCP_AI_DETECTOR = "http://localhost:8004/call"
MCP_HUMANISER   = "http://localhost:8005/call"

llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0,
    max_tokens=2048,
)

@tool
def analyze_ai_content(text: str) -> dict:
    """Analyze resume text for AI-generated content. Returns ai_score, flagged sentences, burstiness."""
    r = httpx.post(MCP_AI_DETECTOR, json={"text": text}, timeout=30)
    return r.json()

@tool
def humanise_text(flagged_sentences: List[str], context: str = "") -> dict:
    """Rewrite AI-flagged sentences to sound human. Pass the flagged sentences and optional context."""
    r = httpx.post(MCP_HUMANISER, json={
        "flagged_sentences": flagged_sentences,
        "context": context,
    }, timeout=30)
    return r.json()

tools = [analyze_ai_content, humanise_text]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an AI content detection specialist for resumes.

Follow these steps exactly:

STEP 1: Call analyze_ai_content with the full resume text.
  - Note the ai_score, verdict, flagged_sentences list, and burstiness.

STEP 2: If flagged_count > 0, call humanise_text with:
  - flagged_sentences = list of sentence strings from the flagged_sentences field
  - context = first 300 chars of the resume

STEP 3: Return a final JSON report:
{{
  "ai_score": <number 0-100>,
  "verdict": "LIKELY AI" or "LIKELY HUMAN",
  "burstiness": <number>,
  "flagged_count": <number>,
  "risk_level": "HIGH" if ai_score >= 60 else "MEDIUM" if ai_score >= 35 else "LOW",
  "flagged_sentences": [list of flagged sentence strings],
  "rewrites": [list of {{"original": "...", "rewritten": "..."}}],
  "top_tips": [3 specific tips to make this resume sound more human]
}}

If flagged_count is 0, skip step 2 and return empty rewrites.
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

def run_ai_detection(resume_text: str) -> dict:
    result = agent_executor.invoke({
        "input": f"""Analyze this resume for AI-generated content and provide humanisation rewrites.

RESUME TEXT:
{resume_text[:6000]}"""
    })

    output = result.get("output", "")
    try:
        output = re.sub(r"^```(?:json)?\s*\n?", "", output.strip())
        output = re.sub(r"\n?```\s*$", "", output.strip())
        return json.loads(output)
    except Exception:
        return {"raw_output": output, "parse_error": True}
    