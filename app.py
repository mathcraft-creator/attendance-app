from __future__ import annotations

import csv
import json
import os
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from db import MATERIAL_COLUMNS, get_academy_questions, init_db, save_academy_questions
from math_analysis import analyze_questions
from mathpix_pipeline import parse_mathpix_lines, split_questions_from_lines
from ocr_utils import ocr_image_bytes, ocr_pdf_bytes
from question_parser import split_questions
from report_generator import generate_excel_report
from similarity import find_similar_for_exam_questions
from trend_analysis import analyze_exam_trend

load_dotenv()
init_db()

st.set_page_config(page_title="시험지 유사도 분석", page_icon="📘", layout="wide")
st.title("📘 시험지 유사도 분석 웹앱")


def parse_csv_upload(file_bytes: bytes) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(StringIO(file_bytes.decode(encoding))))
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 인코딩은 UTF-8 또는 CP949만 지원합니다.")


def validate_material_rows(rows: list[dict[str, str]]) -> tuple[bool, str]:
    if not rows:
        return False, "CSV 데이터가 비어 있습니다."
    missing = [col for col in MATERIAL_COLUMNS if col not in rows[0]]
    if missing:
        return False, f"필수 컬럼 누락: {', '.join(missing)}"
    return True, "ok"


def parse_exam_text_blob(text: str) -> list[dict[str, str]]:
    return [{"question_number": num, "question_text": t} for num, t in split_questions(text)]


for key, default in {
    "exam_questions_raw": [],
    "exam_questions_analyzed": [],
    "similarity_results": [],
    "trend": {},
    "ocr_logs": [],
    "excel_report_path": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

st.subheader("1) 교재 문항 DB 업로드")
csv_file = st.file_uploader("교재 CSV 업로드", type=["csv"], key="material_csv")
if csv_file:
    try:
        rows = parse_csv_upload(csv_file.read())
        ok, msg = validate_material_rows(rows)
        if not ok:
            st.error(msg)
        else:
            st.success(f"CSV 검증 완료: {len(rows)}개")
            st.dataframe(rows[:20], use_container_width=True)
            if st.button("교재 DB 저장"):
                saved = save_academy_questions(rows)
                st.success(f"저장 완료: {saved}개")
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))

st.divider()
st.subheader("2) 시험지 OCR 입력 (Mathpix lines.json 또는 일반 파일)")
mathpix_json = st.file_uploader("Mathpix lines.json 업로드", type=["json"], key="mathpix_json")
exam_mode = st.radio("시험지 입력 방식", ["텍스트 입력", "파일 업로드"], horizontal=True)
exam_text = ""

if exam_mode == "텍스트 입력":
    exam_text = st.text_area("시험지 문항 텍스트", height=220)
else:
    exam_file = st.file_uploader("시험지 파일", type=["txt", "pdf", "png", "jpg", "jpeg"], key="exam_file")
    if exam_file:
        data = exam_file.read()
        if exam_file.type == "application/pdf":
            exam_text = ocr_pdf_bytes(data)
        elif exam_file.type.startswith("image/"):
            exam_text = ocr_image_bytes(data)
        else:
            for enc in ("utf-8-sig", "cp949"):
                try:
                    exam_text = data.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
        st.text_area("추출 텍스트", value=exam_text, height=180)

if st.button("시험지 OCR 분석 실행", type="primary"):
    logs: list[dict[str, str]] = []
    questions: list[dict[str, str]] = []

    if mathpix_json:
        payload = json.loads(mathpix_json.read().decode("utf-8"))
        lines = parse_mathpix_lines(payload)
        questions = split_questions_from_lines(lines)
        logs.append({"step": "mathpix_lines_parse", "status": "ok", "message": f"lines={len(lines)}"})
    elif exam_text.strip():
        questions = parse_exam_text_blob(exam_text)
        logs.append({"step": "text_split", "status": "ok", "message": f"questions={len(questions)}"})
    else:
        logs.append({"step": "input_check", "status": "fail", "message": "입력 없음"})

    st.session_state.exam_questions_raw = questions
    st.session_state.ocr_logs = logs
    st.success(f"OCR 파이프라인 완료: {len(questions)}문항")

if st.session_state.exam_questions_raw:
    st.dataframe(st.session_state.exam_questions_raw, use_container_width=True)

st.divider()
st.subheader("3) 문항별 수학 분석")
if st.button("문항별 수학 분석 실행", type="primary"):
    if not st.session_state.exam_questions_raw:
        st.warning("먼저 OCR 분석을 실행하세요.")
    else:
        analyzed = analyze_questions(st.session_state.exam_questions_raw)
        st.session_state.exam_questions_analyzed = analyzed
        st.success(f"문항 분석 완료: {len(analyzed)}문항")

if st.session_state.exam_questions_analyzed:
    st.dataframe(pd.DataFrame(st.session_state.exam_questions_analyzed), use_container_width=True)

st.divider()
st.subheader("4) 유사도 분석")
if st.button("유사도 분석 실행", type="primary"):
    exam_items = st.session_state.exam_questions_analyzed or st.session_state.exam_questions_raw
    if not exam_items:
        st.warning("시험 문항 데이터가 없습니다.")
    else:
        materials = get_academy_questions()
        if not materials:
            st.warning("교재 DB가 비어 있습니다.")
        else:
            # 교재 문항도 분석 필드가 없으면 자동 보강
            analyzed_materials = analyze_questions(materials)
            mode = "openai" if os.getenv("OPENAI_API_KEY", "").strip() else "tfidf"
            sim_results = find_similar_for_exam_questions(
                exam_questions=exam_items,
                candidates=analyzed_materials,
                top_k=5,
                embedding_mode=mode,
            )
            st.session_state.similarity_results = sim_results
            st.success(f"유사도 분석 완료 ({mode})")

if st.session_state.similarity_results:
    for block in st.session_state.similarity_results:
        st.markdown(f"### 시험 문항 {block['exam_question_number']}")
        st.write(block["exam_question_text"])
        st.dataframe(pd.DataFrame(block.get("top_matches", [])), use_container_width=True)

st.divider()
st.subheader("5) 출제 경향 분석")
if st.session_state.exam_questions_analyzed:
    st.session_state.trend = analyze_exam_trend(st.session_state.exam_questions_analyzed)
    trend = st.session_state.trend
    col1, col2 = st.columns(2)
    with col1:
        st.write("단원별 문항 수", trend.get("unit_counts", {}))
        st.write("난이도 분포", trend.get("difficulty_distribution", {}))
        st.write("출제방식 분포", trend.get("item_format_distribution", {}))
    with col2:
        st.write("변형수준 분포", trend.get("variation_distribution", {}))
        st.write("출제 선생님 성향", trend.get("teacher_style_analysis", ""))
        st.write("문항 제작 로직", trend.get("production_logic_analysis", ""))
        st.write("기말 예상 범위", trend.get("expected_final_scope", ""))
        st.write("기말 대비 전략", trend.get("final_preparation_strategy", ""))

st.divider()
st.subheader("6) 엑셀 리포트")
if st.button("엑셀 상담자료 생성", type="primary"):
    if not st.session_state.exam_questions_analyzed:
        st.warning("문항별 수학 분석 실행 후 생성하세요.")
    else:
        report_path = generate_excel_report(
            exam_questions=st.session_state.exam_questions_analyzed,
            similarity_results=st.session_state.similarity_results,
            trend=st.session_state.trend,
            ocr_logs=st.session_state.ocr_logs,
            output_path=os.getenv("REPORT_XLSX_PATH", "outputs/consulting_report.xlsx"),
        )
        st.session_state.excel_report_path = report_path
        st.success(f"엑셀 생성 완료: {report_path}")

if st.session_state.excel_report_path:
    file_path = Path(st.session_state.excel_report_path)
    if file_path.exists():
        st.download_button(
            "엑셀 다운로드",
            data=file_path.read_bytes(),
            file_name=file_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
