from __future__ import annotations

from collections import Counter
from typing import Any


def analyze_exam_trend(questions: list[dict[str, str]]) -> dict[str, Any]:
    unit_counts = Counter(q.get("unit", "미분류") for q in questions)
    difficulty_counts = Counter(q.get("difficulty", "미분류") for q in questions)
    item_format_counts = Counter(q.get("item_format", "미분류") for q in questions)
    variation_counts = Counter(q.get("variation_level", "미분류") for q in questions)
    intent_counts = Counter(q.get("teacher_intent_type", "미분류") for q in questions)
    prod_counts = Counter(q.get("production_method", "미분류") for q in questions)

    strongest_unit = unit_counts.most_common(1)[0][0] if unit_counts else "미정"
    hard_ratio = difficulty_counts.get("상", 0) / max(len(questions), 1)

    exam_scope = f"{strongest_unit} 중심 출제, 연계 단원 보강 필요"
    strategy = (
        "고난도 문항 비중이 높으므로 풀이 구조 훈련과 오답 유형별 재학습 권장"
        if hard_ratio >= 0.3
        else "중하 난도 기반이므로 개념-유형 매칭과 실수 방지 루틴 권장"
    )

    teacher_style = ", ".join([f"{k}:{v}" for k, v in intent_counts.most_common(3)]) or "데이터 부족"
    production_logic = ", ".join([f"{k}:{v}" for k, v in prod_counts.most_common(3)]) or "데이터 부족"

    return {
        "unit_counts": dict(unit_counts),
        "difficulty_distribution": dict(difficulty_counts),
        "item_format_distribution": dict(item_format_counts),
        "variation_distribution": dict(variation_counts),
        "teacher_style_analysis": teacher_style,
        "production_logic_analysis": production_logic,
        "expected_final_scope": exam_scope,
        "final_preparation_strategy": strategy,
    }
