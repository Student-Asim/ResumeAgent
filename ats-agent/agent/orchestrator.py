import asyncio
import uuid
from typing import Optional

from agent.ats_agent import run_ats_analysis
from agent.ai_detection_agent import run_ai_detection
from agent.resume_enhancer_agent import run_resume_enhancer
from agent.interview_coach_agent import run_interview_coach, SESSION_STORE


def _compute_overall_verdict(ats: dict, ai: dict) -> str:
    ats_score = ats.get("ats_score", 0) if not ats.get("parse_error") else 0
    ai_score  = ai.get("ai_score", 0)  if not ai.get("parse_error")  else 0

    if ats_score >= 75 and ai_score < 40:
        return "STRONG — resume is ATS-ready and looks human-written"
    elif ats_score >= 75 and ai_score >= 40:
        return "MODERATE — good ATS score but AI content detected, humanise before applying"
    elif ats_score < 75 and ai_score < 40:
        return "MODERATE — human-written but needs keyword optimisation for ATS"
    else:
        return "NEEDS WORK — low ATS score and AI content detected, use the suggestions below"


def _build_priority_actions(ats: dict, ai: dict, enhancer: dict) -> list:
    actions = []

    # ATS gaps
    missing_required = ats.get("missing", {}).get("required", [])
    if missing_required:
        actions.append(
            f"Add these missing required skills to your resume: {', '.join(missing_required[:3])}"
        )

    missing_keywords = ats.get("missing", {}).get("keywords", [])
    if missing_keywords:
        actions.append(
            f"Weave these keywords into your bullets: {', '.join(missing_keywords[:3])}"
        )

    # AI detection
    ai_score = ai.get("ai_score", 0) if not ai.get("parse_error") else 0
    if ai_score >= 40:
        flagged = ai.get("flagged_count", 0)
        actions.append(
            f"Humanise {flagged} flagged sentences — use the rewritten versions in your resume"
        )

    # Preferred skills
    missing_preferred = ats.get("missing", {}).get("preferred", [])
    if missing_preferred:
        actions.append(
            f"Consider adding preferred skills: {', '.join(missing_preferred[:2])}"
        )

    # Enhancer
    if enhancer and not enhancer.get("parse_error"):
        actions.append(
            "Download the enhanced LaTeX resume and paste into Overleaf to get a polished PDF"
        )

    return actions[:5]  # top 5 only


async def _run_ats(job_input: str, resume_text: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_ats_analysis, job_input, resume_text)


async def _run_ai(resume_text: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_ai_detection, resume_text)


async def _run_enhancer(resume_text: str, missing_keywords: list, job_title: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, run_resume_enhancer, resume_text, missing_keywords, job_title
    )


async def _run_coach(jd_text: str, resume_text: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, run_interview_coach, jd_text, resume_text)


async def run_full_analysis(
    job_input: str,
    resume_text: str,
    job_title: Optional[str] = "",
) -> dict:
    """
    Run all 4 agents in parallel and merge results.
    Returns a single comprehensive report.
    """

    # ── Stage 1: Run ATS first (we need missing keywords for the enhancer) ──
    ats_result = await _run_ats(job_input, resume_text)

    # Extract missing keywords from ATS result to guide enhancer
    missing_keywords = (
        ats_result.get("missing", {}).get("required", []) +
        ats_result.get("missing", {}).get("keywords", [])
    )
    extracted_job_title = job_title or ats_result.get("job_title", "")

    # ── Stage 2: Run remaining 3 agents in parallel ──
    ai_result, enhancer_result, (coach_result, session_id) = await asyncio.gather(
        _run_ai(resume_text),
        _run_enhancer(resume_text, missing_keywords, extracted_job_title),
        _run_coach(job_input, resume_text),
    )

    # ── Stage 3: Merge everything ──
    overall_verdict  = _compute_overall_verdict(ats_result, ai_result)
    priority_actions = _build_priority_actions(ats_result, ai_result, enhancer_result)
    practice_url     = f"http://localhost:8000/practice?session={session_id}"

    return {
        "overall_verdict":  overall_verdict,
        "priority_actions": priority_actions,

        "ats": {
            "score":    ats_result.get("ats_score"),
            "verdict":  ats_result.get("verdict"),
            "breakdown": ats_result.get("breakdown", {}),
            "matched":  ats_result.get("matched", {}),
            "missing":  ats_result.get("missing", {}),
            "top_suggestions": ats_result.get("top_suggestions", []),
        },

        "ai_detection": {
            "score":              ai_result.get("ai_score"),
            "verdict":            ai_result.get("verdict"),
            "risk_level":         ai_result.get("risk_level"),
            "flagged_count":      ai_result.get("flagged_count"),
            "burstiness":         ai_result.get("burstiness"),
            "flagged_sentences":  ai_result.get("flagged_sentences", []),
            "rewrites":           ai_result.get("rewrites", []),
            "top_tips":           ai_result.get("top_tips", []),
        },

        "resume_enhancer": {
            "enhanced_bullets": enhancer_result.get("enhanced_bullets", []),
            "latex":            enhancer_result.get("latex", ""),
            "filename":         enhancer_result.get("filename", "resume_enhanced.tex"),
            "instructions":     enhancer_result.get("instructions", ""),
            "overleaf_url":     "https://www.overleaf.com/latex/templates/jakes-resume/syzfjbzwjncs",
        },

        "interview_coach": {
            "job_title":                    coach_result.get("job_title"),
            "seniority":                    coach_result.get("seniority"),
            "company_culture":              coach_result.get("company_culture", []),
            "talking_points":               coach_result.get("talking_points", []),
            "red_flags_to_avoid":           coach_result.get("red_flags_to_avoid", []),
            "technical_questions":          coach_result.get("technical_questions", []),
            "behavioral_questions":         coach_result.get("behavioral_questions", []),
            "questions_to_ask_interviewer": coach_result.get("questions_to_ask_interviewer", []),
            "cheatsheet_latex":             coach_result.get("cheatsheet_latex", ""),
        },

        "practice_url":  practice_url,
        "session_id":    session_id,
    }