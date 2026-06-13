from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import os, json, re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()
app = FastAPI()

llm = ChatOpenAI(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0.5,
    max_tokens=2048,
)

class CallRequest(BaseModel):
    job_title: str
    core_topics: List[str]
    required_skills: List[str]
    behavioral_themes: List[str]
    seniority: Optional[str] = "junior"
    resume_summary: Optional[str] = ""

@app.post("/call")
def generate_questions(req: CallRequest):
    resp = llm.invoke([
        SystemMessage(content="""You are a senior technical interviewer.
Generate interview questions and return ONLY a raw JSON object:
{
  "technical": [
    {
      "question": "string",
      "topic": "string",
      "difficulty": "easy|medium|hard",
      "ideal_answer": "2-3 sentence ideal answer",
      "follow_up": "one follow-up question"
    }
  ],
  "behavioral": [
    {
      "question": "string",
      "theme": "string",
      "star_hint": "how to structure the answer using STAR",
      "ideal_answer": "example ideal answer outline"
    }
  ],
  "questions_to_ask_interviewer": [
    "string"
  ]
}
Generate 6 technical and 4 behavioral questions.
Return ONLY the JSON. No markdown. Start with { end with }."""),
        HumanMessage(content=f"""
Role: {req.job_title} ({req.seniority})
Core Topics: {', '.join(req.core_topics)}
Required Skills: {', '.join(req.required_skills)}
Behavioral Themes: {', '.join(req.behavioral_themes)}
Candidate Background: {req.resume_summary[:400] if req.resume_summary else 'Not provided'}

Generate realistic interview questions for this role.""")
    ])

    raw = (getattr(resp, "content", None) or str(resp)).strip()
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)
    if not raw.startswith("{"):
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        raw = match.group(0) if match else raw

    try:
        return json.loads(raw)
    except Exception as e:
        return {"raw": raw, "parse_error": True, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)