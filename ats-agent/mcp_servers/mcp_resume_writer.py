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
    temperature=0.4,
    max_tokens=2048,
)

class CallRequest(BaseModel):
    bullets: List[str]
    missing_keywords: Optional[List[str]] = []
    job_title: Optional[str] = ""

@app.post("/call")
def rewrite_bullets(req: CallRequest):
    if not req.bullets:
        return {"error": "No bullets provided", "rewritten": []}

    bullets_block = "\n".join(f"{i+1}. {b}" for i, b in enumerate(req.bullets))
    keywords_hint = ", ".join(req.missing_keywords) if req.missing_keywords else "none"

    resp = llm.invoke([
        SystemMessage(content="""You are an expert resume writer specializing in ATS optimization.
Rewrite each bullet point following these rules:
- Use STAR format where possible (Situation/Task → Action → Result)
- Start every bullet with a strong action verb (Built, Led, Reduced, Increased, Designed)
- Add metrics and numbers where they can be inferred or estimated
- Naturally include missing keywords if they fit the context
- Keep each bullet under 20 words
- Remove filler: "responsible for", "helped with", "worked on"
- Replace passive voice with active voice
- Return ONLY a JSON array of rewritten bullet strings
- Same count as input. Start with [ end with ]"""),
        HumanMessage(content=f"""Rewrite these {len(req.bullets)} resume bullets.
Target role: {req.job_title or 'Software Engineer'}
Missing keywords to naturally include: {keywords_hint}

Bullets:
{bullets_block}

Return a JSON array with exactly {len(req.bullets)} improved bullet strings.""")
    ])

    raw = (getattr(resp, "content", None) or str(resp)).strip()
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)

    if not raw.startswith("["):
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        raw = match.group(0) if match else raw

    try:
        rewritten = json.loads(raw)
        if not isinstance(rewritten, list):
            raise ValueError
    except Exception:
        rewritten = req.bullets  # fallback to originals

    return {
        "rewritten": [
            {"original": orig, "improved": impr}
            for orig, impr in zip(req.bullets, rewritten)
        ],
        "count": len(rewritten),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)