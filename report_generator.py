from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def generate_excel_report(
    exam_questions: list[dict[str, Any]],
    similarity_results: list[dict[str, Any]],
    trend: dict[str, Any],
    ocr_logs: list[dict[str, Any]],
    output_path: str = "outputs/consulting_report.xlsx",
) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    overview = pd.DataFrame(
        [
            {
                "생성시각": datetime.utcnow().isoformat(),
                "총 문항 수": len(exam_questions),
                "유사도 분석 문항 수": len(similarity_results),
            }
        ]
    )

    q_df = pd.DataFrame(exam_questions)

    sim_rows: list[dict[str, Any]] = []
    for item in similarity_results:
        q_num = item.get("exam_question_number")
        for rank, match in enumerate(item.get("top_matches", []), start=1):
            row = {"exam_question_number": q_num, "rank": rank}
            row.update(match)
            sim_rows.append(row)
    sim_df = pd.DataFrame(sim_rows)

    trend_df = pd.DataFrame(
        [
            {
                "unit_counts": trend.get("unit_counts", {}),
                "difficulty_distribution": trend.get("difficulty_distribution", {}),
                "item_format_distribution": trend.get("item_format_distribution", {}),
                "variation_distribution": trend.get("variation_distribution", {}),
                "teacher_style_analysis": trend.get("teacher_style_analysis", ""),
                "production_logic_analysis": trend.get("production_logic_analysis", ""),
            }
        ]
    )

    current_next = pd.DataFrame(
        [{"현재 범위": trend.get("unit_counts", {}), "다음 범위 제안": trend.get("expected_final_scope", "")}]
    )
    final_strategy = pd.DataFrame([{"기말 대비 전략": trend.get("final_preparation_strategy", "")}])
    class_strategy = pd.DataFrame(
        [
            {
                "수업 설계 전략": "핵심 단원 개념 재정리 + 고빈도 오답 유형 교정 + 변형문항 루프 훈련",
            }
        ]
    )
    ocr_df = pd.DataFrame(ocr_logs)

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        overview.to_excel(writer, index=False, sheet_name="1_시험개요")
        q_df.to_excel(writer, index=False, sheet_name="2_문항별분석")
        sim_df.to_excel(writer, index=False, sheet_name="3_유사도분석")
        trend_df.to_excel(writer, index=False, sheet_name="4_출제경향분석")
        current_next.to_excel(writer, index=False, sheet_name="5_현재_다음범위")
        final_strategy.to_excel(writer, index=False, sheet_name="6_기말대비전략")
        class_strategy.to_excel(writer, index=False, sheet_name="7_수업설계전략")
        ocr_df.to_excel(writer, index=False, sheet_name="8_OCR검수로그")

    return str(out)
