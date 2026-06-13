from fastapi import FastAPI
from pydantic import BaseModel
import os, json, re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

app = FastAPI()
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatOpenAI(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
    temperature=0,
    max_tokens=512,
)

class CallRequest(BaseModel):
    jd_text: str

@app.post("/call")
def extract_keywords(req: CallRequest):
    prompt = f"""Extract structured requirements from this job description.

Return a JSON object with exactly these keys:
- required_skills: list of must-have technical skills (short strings)
- preferred_skills: list of nice-to-have skills
- job_titles: list of acceptable job titles/roles
- certifications: list of required/preferred certs (empty list if none)
- experience_years: minimum years required as integer, or null
- education: required education level as string, or null
- keywords: list of important domain keywords for ATS matching

Job Description:
{req.jd_text[:6000]}"""

    resp = llm.invoke([
        SystemMessage(content=(
            "You are a JSON extraction API. "
            "Output ONLY raw valid JSON. "
            "Never use markdown. Never use code fences. Never add explanation. "
            "Your entire response must start with { and end with }."
        )),
        HumanMessage(content=prompt)
    ])

    raw = (getattr(resp, "content", None) or str(resp)).strip()

    # Strip fences defensively (multiline-aware)
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)
    raw = raw.strip()

    # If model still wrapped it, find the JSON object manually
    if not raw.startswith("{"):
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group(0)

    try:
        result = json.loads(raw)
    except Exception as e:
        result = {"raw": raw, "parse_error": True, "error": str(e)}

    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)