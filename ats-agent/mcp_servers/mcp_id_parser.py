from fastapi import FastAPI
from pydantic import BaseModel
import httpx, re

app = FastAPI()

class CallRequest(BaseModel):
    job_text: str = ""
    job_url: str = ""

@app.post("/call")
async def parse_jd(req: CallRequest):
    text = req.job_text

    if not text and req.job_url:
        async with httpx.AsyncClient() as client:
            r = await client.get(req.job_url, timeout=10)
            # strip HTML tags simply
            text = re.sub(r"<[^>]+>", " ", r.text)
            text = re.sub(r"\s+", " ", text).strip()[:8000]

    if not text:
        return {"error": "No job description provided"}

    return {
        "raw_text": text,
        "char_count": len(text),
        "status": "parsed"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)