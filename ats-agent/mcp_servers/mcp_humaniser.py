from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import os, re, json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()
app = FastAPI()

llm = ChatOpenAI(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    temperature=0.7,    # higher temp = more varied rewrites
    max_tokens=2048,
)

class CallRequest(BaseModel):
    flagged_sentences: List[str]
    context: str = ""   # optional: pass resume section for better rewrites

@app.post("/call")
def humanise_text(req: CallRequest):
    if not req.flagged_sentences:
        return {"rewrites": [], "message": "No flagged sentences to rewrite"}

    sentences_block = "\n".join(
        f"{i+1}. {s}" for i, s in enumerate(req.flagged_sentences)
    )

    resp = llm.invoke([
        SystemMessage(content="""You are an expert resume editor who makes AI-written text sound natural and human.
Rules for rewriting:
- Vary sentence length dramatically (mix short punchy sentences with longer ones)
- Use first person naturally (I built, I led, I reduced)
- Replace vague words: utilize→use, leverage→use, facilitate→help, demonstrate→show
- Add specific numbers or outcomes where possible
- Remove filler phrases: "it is important to", "in order to", "plays a crucial role"
- Keep the same meaning and facts — only change the style
- Return ONLY a JSON array of rewritten strings, one per input sentence
- Same count as input. No explanations. Start with [ and end with ]"""),
        HumanMessage(content=f"""Rewrite these {len(req.flagged_sentences)} sentences to sound human-written:

{sentences_block}

Context (resume section):
{req.context[:500] if req.context else 'Not provided'}

Return a JSON array with exactly {len(req.flagged_sentences)} rewritten strings.""")
    ])

    raw = (getattr(resp, "content", None) or str(resp)).strip()
    raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
    raw = re.sub(r"\n?```\s*$", "", raw)

    try:
        rewrites = json.loads(raw)
        if not isinstance(rewrites, list):
            raise ValueError("Not a list")
    except Exception:
        # Fallback: return originals with error note
        rewrites = req.flagged_sentences

    return {
        "rewrites": [
            {"original": orig, "rewritten": rewr}
            for orig, rewr in zip(req.flagged_sentences, rewrites)
        ],
        "count": len(rewrites),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)