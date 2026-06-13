from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import re, math, os
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
    text: str

def split_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 20]

def burstiness_score(sentences: List[str]) -> float:
    """Human writing has high variance in sentence length. AI writing is uniform."""
    if len(sentences) < 2:
        return 0.0
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std = math.sqrt(variance)
    # Normalize: low burstiness = more AI-like
    burstiness = std / mean if mean > 0 else 0
    return round(burstiness, 3)

def score_sentence_ai_probability(sentence: str, all_sentences: List[str]) -> float:
    """
    Heuristic AI probability per sentence based on:
    - sentence length uniformity vs neighbors
    - presence of AI-typical phrases
    - low lexical diversity
    """
    ai_phrases = [
        "it is important to", "in conclusion", "furthermore", "moreover",
        "it should be noted", "in order to", "a wide range of", "plays a crucial role",
        "it is worth noting", "this allows for", "by leveraging", "utilize",
        "in today's", "needless to say", "as previously mentioned",
        "i hope this", "certainly", "absolutely", "of course",
    ]
    text_lower = sentence.lower()
    phrase_hits = sum(1 for p in ai_phrases if p in text_lower)

    # Word repetition penalty
    words = re.findall(r'\b\w+\b', text_lower)
    unique_ratio = len(set(words)) / len(words) if words else 1.0

    # Length uniformity vs neighbors
    lengths = [len(s.split()) for s in all_sentences]
    mean_len = sum(lengths) / len(lengths) if lengths else 1
    this_len = len(sentence.split())
    len_diff = abs(this_len - mean_len) / mean_len if mean_len > 0 else 0

    # Combine signals → 0.0 to 1.0
    score = 0.0
    score += min(phrase_hits * 0.25, 0.5)   # phrase hits: up to 0.5
    score += max(0, (0.7 - unique_ratio))    # low diversity: up to 0.3
    score -= min(len_diff * 0.2, 0.2)        # high length variance reduces score
    return round(max(0.0, min(1.0, score)), 2)

@app.post("/call")
def analyze_ai_content(req: CallRequest):
    sentences = split_sentences(req.text)
    if not sentences:
        return {"error": "No sentences found", "ai_score": 0}

    burst = burstiness_score(sentences)

    sentence_scores = []
    for s in sentences:
        prob = score_sentence_ai_probability(s, sentences)
        sentence_scores.append({
            "sentence": s,
            "ai_probability": prob,
            "flagged": prob >= 0.35,
        })

    flagged = [s for s in sentence_scores if s["flagged"]]
    overall_ai_score = round(
        sum(s["ai_probability"] for s in sentence_scores) / len(sentence_scores) * 100, 1
    )

    # Burstiness penalty: low burstiness → push score up
    if burst < 0.3:
        overall_ai_score = min(100, overall_ai_score + 15)

    return {
        "ai_score": overall_ai_score,
        "burstiness": burst,
        "verdict": "LIKELY AI" if overall_ai_score >= 40 else "LIKELY HUMAN",
        "total_sentences": len(sentences),
        "flagged_count": len(flagged),
        "flagged_sentences": flagged,
        "sentence_analysis": sentence_scores,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)