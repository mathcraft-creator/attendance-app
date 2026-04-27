from __future__ import annotations

import csv
import json
import os
from io import StringIO
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from db import MATERIAL_COLUMNS, get_academy_questions, init_db, save_academy_questions
from math_analysis import analyze_questions
from mathpix_pipeline import parse_mathpix_lines, split_questions_from_lines
from report_generator import generate_excel_report
from similarity import find_similar_for_exam_questions
from trend_analysis import analyze_exam_trend

app = FastAPI(title="Exam Similarity API", version="2.0.0")
init_db()


class AnalyzeRequest(BaseModel):
    exam_questions: list[dict[str, str]] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)


class ReportRequest(BaseModel):
    exam_questions: list[dict[str, Any]]
    similarity_results: list[dict[str, Any]] = Field(default_factory=list)
    ocr_logs: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/materials/upload-csv")
async def upload_material_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    decoded = None
    for encoding in ("utf-8-sig", "cp949"):
        try:
            decoded = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if decoded is None:
        raise HTTPException(status_code=400, detail="CSV 인코딩은 UTF-8 또는 CP949만 지원합니다.")

    rows = list(csv.DictReader(StringIO(decoded)))
    if not rows:
        raise HTTPException(status_code=400, detail="CSV 데이터가 비어 있습니다.")
    missing = [col for col in MATERIAL_COLUMNS if col not in rows[0]]
    if missing:
        raise HTTPException(status_code=400, detail=f"필수 컬럼 누락: {', '.join(missing)}")

    return {"saved_count": save_academy_questions(rows)}


@app.post("/mathpix/analyze-lines")
async def analyze_mathpix_lines(file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    payload = json.loads(content.decode("utf-8"))
    lines = parse_mathpix_lines(payload)
    questions = split_questions_from_lines(lines)
    analyzed = analyze_questions(questions)
    return {"question_count": len(analyzed), "questions": analyzed}


@app.post("/similarity/analyze")
def analyze_similarity(payload: AnalyzeRequest) -> dict[str, Any]:
    if not payload.exam_questions:
        raise HTTPException(status_code=400, detail="시험 문항이 비어 있습니다.")

    materials = get_academy_questions()
    if not materials:
        raise HTTPException(status_code=400, detail="교재 문항 DB가 비어 있습니다.")

    analyzed_exam = analyze_questions(payload.exam_questions)
    analyzed_material = analyze_questions(materials)
    mode = "openai" if os.getenv("OPENAI_API_KEY", "").strip() else "tfidf"

    sim = find_similar_for_exam_questions(
        exam_questions=analyzed_exam,
        candidates=analyzed_material,
        top_k=payload.top_k,
        embedding_mode=mode,
    )
    trend = analyze_exam_trend(analyzed_exam)
    return {"embedding_mode": mode, "results": sim, "trend": trend}


@app.post("/report/excel")
def build_excel_report(payload: ReportRequest) -> dict[str, str]:
    analyzed_exam = analyze_questions(payload.exam_questions)
    trend = analyze_exam_trend(analyzed_exam)
    path = generate_excel_report(
        exam_questions=analyzed_exam,
        similarity_results=payload.similarity_results,
        trend=trend,
        ocr_logs=payload.ocr_logs,
        output_path=os.getenv("REPORT_XLSX_PATH", "outputs/consulting_report.xlsx"),
    )
    return {"report_path": path}
