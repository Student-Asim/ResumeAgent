from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from agent.resume_enhancer_agent import run_resume_enhancer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from agent.interview_coach_agent import run_interview_coach, SESSION_STORE
from agent.orchestrator import run_full_analysis
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.pdf_parser import extract_text_from_pdf
from agent.ats_agent import run_ats_analysis
from agent.ai_detection_agent import run_ai_detection

app = FastAPI(title="ATS Scorer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Serve static files (practice UI)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(""),
    job_url: str = Form(""),
):
    pdf_bytes = await resume.read()
    resume_text = extract_text_from_pdf(pdf_bytes)

    if not resume_text:
        return {"error": "Could not extract text from PDF"}

    job_input = job_url if job_url else job_description
    if not job_input:
        return {"error": "Provide either job_description or job_url"}

    result = run_ats_analysis(job_input, resume_text)
    return {"status": "success", "result": result}


@app.post("/detect-ai")
async def detect_ai(
    resume: UploadFile = File(...),
):
    pdf_bytes = await resume.read()
    resume_text = extract_text_from_pdf(pdf_bytes)

    if not resume_text:
        return {"error": "Could not extract text from PDF"}

    result = run_ai_detection(resume_text)
    return {"status": "success", "result": result}


@app.post("/enhance-resume")
async def enhance_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(""),
    missing_keywords: str = Form(""),   # comma-separated
    job_title: str = Form(""),
):
    pdf_bytes = await resume.read()
    resume_text = extract_text_from_pdf(pdf_bytes)

    if not resume_text:
        return {"error": "Could not extract text from PDF"}

    kw_list = [k.strip() for k in missing_keywords.split(",") if k.strip()]

    result = run_resume_enhancer(
        resume_text=resume_text,
        missing_keywords=kw_list,
        job_title=job_title,
    )
    return {"status": "success", "result": result}




@app.post("/interview-prep")
async def interview_prep(
    resume: UploadFile = File(None),
    job_description: str = Form(""),
    job_url: str = Form(""),
):
    resume_text = ""
    if resume:
        pdf_bytes = await resume.read()
        resume_text = extract_text_from_pdf(pdf_bytes)

    job_input = job_url if job_url else job_description
    if not job_input:
        return {"error": "Provide job_description or job_url"}

    result, session_id = run_interview_coach(
        jd_text=job_input,
        resume_text=resume_text,
    )

    practice_url = f"http://localhost:8000/practice?session={session_id}"

    return {
        "status": "success",
        "practice_url": practice_url,
        "session_id": session_id,
        "result": result,
    }

@app.get("/practice")
async def practice_page():
    with open("static/practice.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/practice-data")
async def practice_data(session: str):
    if session not in SESSION_STORE:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Session not found")
    return SESSION_STORE[session]


@app.post("/analyze-full")
async def analyze_full(
    resume: UploadFile = File(...),
    job_description: str = Form(""),
    job_url: str = Form(""),
    job_title: str = Form(""),
):
    pdf_bytes = await resume.read()
    resume_text = extract_text_from_pdf(pdf_bytes)

    if not resume_text:
        return {"error": "Could not extract text from PDF"}

    job_input = job_url if job_url else job_description
    if not job_input:
        return {"error": "Provide job_description or job_url"}

    result = await run_full_analysis(
        job_input=job_input,
        resume_text=resume_text,
        job_title=job_title,
    )

    return {"status": "success", "result": result}