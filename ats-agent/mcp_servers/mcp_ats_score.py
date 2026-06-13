from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
from typing import List
import re

app = FastAPI()

# Loads once on startup (~80MB, fast after first run)
model = SentenceTransformer("all-MiniLM-L6-v2")

class CallRequest(BaseModel):
    resume_text: str
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    keywords: List[str] = []
    certifications: List[str] = []
    experience_years: int | None = None

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", text.lower())

@app.post("/call")
def compute_ats_score(req: CallRequest):
    resume_lower = normalize(req.resume_text)

    # ── Exact match scoring ──
    def exact_match_score(terms: List[str]) -> tuple[float, list, list]:
        if not terms:
            return 0.0, [], []
        matched, missing = [], []
        for term in terms:
            if normalize(term) in resume_lower:
                matched.append(term)
            else:
                missing.append(term)
        score = len(matched) / len(terms)
        return score, matched, missing

    req_score,  req_matched,  req_missing  = exact_match_score(req.required_skills)
    pref_score, pref_matched, _            = exact_match_score(req.preferred_skills)
    kw_score,   kw_matched,   kw_missing   = exact_match_score(req.keywords)
    cert_score, cert_matched, cert_missing = exact_match_score(req.certifications)

    # ── Semantic similarity ──
    all_jd_terms = req.required_skills + req.preferred_skills + req.keywords
    semantic_score = 0.0
    if all_jd_terms:
        jd_embedding     = model.encode(" ".join(all_jd_terms), convert_to_tensor=True)
        resume_embedding = model.encode(req.resume_text[:3000], convert_to_tensor=True)
        semantic_score   = float(util.cos_sim(jd_embedding, resume_embedding)[0][0])

    # ── Dynamic weighted score (skip dimensions with no data) ──
    dimension_scores = {
        "required": (req_score,    0.40, bool(req.required_skills)),
        "keywords":  (kw_score,    0.25, bool(req.keywords)),
        "semantic":  (semantic_score, 0.20, bool(all_jd_terms)),
        "preferred": (pref_score,  0.10, bool(req.preferred_skills)),
        "certs":     (cert_score,  0.05, bool(req.certifications)),
    }

    total_weight  = sum(w for _, w, active in dimension_scores.values() if active)
    weighted_sum  = sum(s * w for s, w, active in dimension_scores.values() if active)
    final         = (weighted_sum / total_weight * 100) if total_weight > 0 else 0.0

    # ── Penalty: missing required skills tanks the score ──
    if req.required_skills:
        missing_ratio = len(req_missing) / len(req.required_skills)
        penalty       = missing_ratio * 15          # up to -15 points
        final         = max(0.0, final - penalty)

    return {
        "ats_score": round(final, 1),
        "breakdown": {
            "required_skills":    round(req_score      * 100, 1),
            "preferred_skills":   round(pref_score     * 100, 1),
            "keywords":           round(kw_score       * 100, 1),
            "certifications":     round(cert_score     * 100, 1),
            "semantic_similarity": round(semantic_score * 100, 1),
        },
        "matched": {
            "required":      req_matched,
            "preferred":     pref_matched,
            "keywords":      kw_matched,
            "certifications": cert_matched,
        },
        "missing": {
            "required":      req_missing,
            "keywords":      kw_missing,
            "certifications": cert_missing,
        },
        "verdict":        "PASS" if final >= 75 else "NEEDS IMPROVEMENT",
        "active_dimensions": [k for k, (_, _, active) in dimension_scores.items() if active],
        "total_weight_used":  round(total_weight, 2),
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)