from __future__ import annotations

from typing import Iterable


def _pick_difficulty(text: str) -> str:
    length_score = len(text)
    if "증명" in text or "최댓값" in text or length_score > 180:
        return "상"
    if "이차" in text or "함수" in text or length_score > 90:
        return "중"
    return "하"


def _infer_unit(text: str) -> str:
    if "확률" in text:
        return "확률과 통계"
    if "미분" in text or "극한" in text:
        return "미적분"
    if "수열" in text:
        return "수열"
    if "함수" in text or "기울기" in text:
        return "함수"
    if "도형" in text or "삼각" in text:
        return "기하"
    return "대수"


def analyze_math_question(question: dict[str, str]) -> dict[str, str]:
    text = question.get("question_text", "")
    unit = question.get("unit") or _infer_unit(text)
    difficulty = question.get("difficulty") or _pick_difficulty(text)

    if any(k in text for k in ["보기", "옳은", "고르"]):
        item_format = "객관식"
    elif any(k in text for k in ["서술", "증명", "설명"]):
        item_format = "서술형"
    else:
        item_format = "단답형"

    if "증명" in text:
        production_method = "정의/정리 기반 증명형"
        teacher_intent_type = "개념 정교화"
        expected_error_point = "정의 조건 누락"
        training_method = "증명 구조 템플릿 반복"
    elif "계산" in text or "구하시오" in text:
        production_method = "계산 절차형"
        teacher_intent_type = "절차 숙련도 점검"
        expected_error_point = "부호/연산 실수"
        training_method = "연산 속도+검산 루틴"
    else:
        production_method = "개념 적용형"
        teacher_intent_type = "개념 전이"
        expected_error_point = "문제 해석 오류"
        training_method = "문장-수식 변환 훈련"

    return {
        "unit": unit,
        "sub_concept": "핵심 개념 적용",
        "difficulty": difficulty,
        "item_format": item_format,
        "production_method": production_method,
        "variation_level": "중",
        "teacher_intent_type": teacher_intent_type,
        "expected_error_point": expected_error_point,
        "study_direction": "오답 원인 분류 후 유형별 재풀이",
        "final_link_level": "기말 연계 가능성 높음" if difficulty != "하" else "기본기 점검용",
        "training_method": training_method,
    }


def analyze_questions(questions: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for q in questions:
        enriched = dict(q)
        enriched.update(analyze_math_question(q))
        results.append(enriched)
    return results
