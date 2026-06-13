from fastapi import FastAPI
from pydantic import BaseModel
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
    temperature=0,
    max_tokens=1024,
)

class CallRequest(BaseModel):
    jd_text: str

@app.post("/call")
def analyze_jd(req: CallRequest):
    resp = llm.invoke([
        SystemMessage(content="""You are an expert interview coach.
Analyze the job description and return ONLY a raw JSON object with these keys:
{
  "job_title": "string",
  "seniority": "junior|mid|senior",
  "company_culture": ["list of culture signals"],
  "core_topics": ["main technical topics the interview will cover"],
  "required_skills": ["must-know skills"],
  "behavioral_themes": ["teamwork", "ownership", etc],
  "red_flags_to_avoid": ["things candidates typically get wrong for this role"],
  "talking_points": ["3-5 things the candidate should emphasize about themselves"]
}
Return ONLY the JSON. No markdown. Start with { end with }."""),
        HumanMessage(content=f"Job Description:\n{req.jd_text[:5000]}")
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
    uvicorn.run(app, host="0.0.0.0", port=8008)