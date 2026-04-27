from __future__ import annotations

import os
import re
from difflib import SequenceMatcher
from typing import Iterable, Mapping

import numpy as np
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer


def _cosine_similarity_matrix(query_embeddings: np.ndarray, candidate_embeddings: np.ndarray) -> np.ndarray:
    query_norm = np.linalg.norm(query_embeddings, axis=1, keepdims=True) + 1e-12
    cand_norm = np.linalg.norm(candidate_embeddings, axis=1, keepdims=True) + 1e-12
    normalized_query = query_embeddings / query_norm
    normalized_cands = candidate_embeddings / cand_norm
    return normalized_query @ normalized_cands.T


def _openai_embed_texts(texts: list[str], api_key: str, model: str) -> np.ndarray:
    client = OpenAI(api_key=api_key)
    vectors: list[list[float]] = []
    for i in range(0, len(texts), 64):
        response = client.embeddings.create(model=model, input=texts[i : i + 64])
        vectors.extend(item.embedding for item in response.data)
    return np.array(vectors, dtype=np.float32)


def _tfidf_embed_texts(texts: list[str]) -> np.ndarray:
    matrix = TfidfVectorizer(ngram_range=(1, 2)).fit_transform(texts)
    return matrix.toarray().astype(np.float32)


def _formula_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z]+|\d+|[+\-*/=^()<>]", text)
    return tokens


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(len(a | b), 1)


def _logic_similarity(a: str, b: str) -> float:
    key_terms = ["증명", "구하", "최댓값", "최솟값", "조건", "함수", "미분", "확률"]
    a_terms = {k for k in key_terms if k in a}
    b_terms = {k for k in key_terms if k in b}
    return _jaccard(a_terms, b_terms)


def _difficulty_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    order = {"하": 1, "중": 2, "상": 3}
    if a in order and b in order:
        return max(0.0, 1.0 - abs(order[a] - order[b]) * 0.5)
    return 0.3


def _intent_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a or "", b or "").ratio()


def _counsel_label(score: float, logic: float, formula: float, unit_match: bool, intent: float) -> str:
    if score >= 0.9:
        return "거의 동일 문항"
    if unit_match and score >= 0.75:
        return "동일 개념 숫자 변형"
    if logic >= 0.7:
        return "풀이 구조 유사"
    if formula >= 0.6:
        return "조건 변형"
    if intent >= 0.7:
        return "출제 의도 유사"
    if unit_match:
        return "단원만 동일"
    return "부분 유사"


def find_similar_questions(
    query_text: str,
    candidates: Iterable[Mapping[str, str]],
    query_unit: str = "",
    query_sub_concept: str = "",
    query_difficulty: str = "",
    query_teacher_intent_type: str = "",
    top_k: int = 5,
    embedding_mode: str = "auto",
) -> list[dict[str, str | float]]:
    query = query_text.strip()
    if not query:
        return []

    candidate_list = [dict(item) for item in candidates if (item.get("question_text") or "").strip()]
    if not candidate_list:
        return []

    model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    use_openai = embedding_mode == "openai" or (embedding_mode == "auto" and bool(api_key))

    texts = [query] + [row["question_text"].strip() for row in candidate_list]
    embeddings = _openai_embed_texts(texts, api_key, model) if use_openai else _tfidf_embed_texts(texts)
    text_scores = _cosine_similarity_matrix(embeddings[:1], embeddings[1:]).flatten()

    query_formula = set(_formula_tokens(query))

    results: list[dict[str, str | float]] = []
    for idx, cand in enumerate(candidate_list):
        cand_text = cand.get("question_text", "")
        formula_score = _jaccard(query_formula, set(_formula_tokens(cand_text)))
        concept_score = 1.0 if query_sub_concept and query_sub_concept == cand.get("sub_concept", "") else 0.0
        unit_score = 1.0 if query_unit and query_unit == cand.get("unit", "") else 0.0
        logic_score = _logic_similarity(query, cand_text)
        diff_score = _difficulty_similarity(query_difficulty, str(cand.get("difficulty", "")))
        intent_score = _intent_similarity(query_teacher_intent_type, str(cand.get("teacher_intent_type", "")))

        final_score = (
            float(text_scores[idx]) * 0.35
            + formula_score * 0.15
            + (unit_score * 0.6 + concept_score * 0.4) * 0.15
            + logic_score * 0.15
            + diff_score * 0.1
            + intent_score * 0.1
        )

        weight_multiplier = 1.0
        if unit_score > 0:
            weight_multiplier += 0.15
        if concept_score > 0:
            weight_multiplier += 0.1

        weighted = min(final_score * weight_multiplier, 1.0)
        label = _counsel_label(weighted, logic_score, formula_score, unit_score > 0, intent_score)

        results.append(
            {
                "question_id": cand.get("question_id", ""),
                "unit": cand.get("unit", ""),
                "sub_concept": cand.get("sub_concept", cand.get("sub_type", "")),
                "difficulty": cand.get("difficulty", ""),
                "teacher_intent_type": cand.get("teacher_intent_type", ""),
                "text_similarity": round(float(text_scores[idx]) * 100, 2),
                "formula_similarity": round(formula_score * 100, 2),
                "concept_similarity": round((unit_score * 0.6 + concept_score * 0.4) * 100, 2),
                "logic_similarity": round(logic_score * 100, 2),
                "difficulty_similarity": round(diff_score * 100, 2),
                "intent_similarity": round(intent_score * 100, 2),
                "weight_multiplier": round(weight_multiplier, 3),
                "similarity_score": round(weighted * 100, 2),
                "similarity_mode": "openai_embeddings" if use_openai else "tfidf_fallback",
                "counsel_interpretation": label,
                "source": cand.get("source", ""),
                "question_text": cand_text,
            }
        )

    results.sort(key=lambda x: float(x["similarity_score"]), reverse=True)
    return results[:top_k]


def find_similar_for_exam_questions(
    exam_questions: Iterable[Mapping[str, str]],
    candidates: Iterable[Mapping[str, str]],
    top_k: int = 5,
    embedding_mode: str = "auto",
) -> list[dict[str, object]]:
    bundled: list[dict[str, object]] = []
    for row in exam_questions:
        query_text = str(row.get("question_text", ""))
        if not query_text.strip():
            continue
        top_matches = find_similar_questions(
            query_text=query_text,
            candidates=candidates,
            query_unit=str(row.get("unit", "")),
            query_sub_concept=str(row.get("sub_concept", "")),
            query_difficulty=str(row.get("difficulty", "")),
            query_teacher_intent_type=str(row.get("teacher_intent_type", "")),
            top_k=top_k,
            embedding_mode=embedding_mode,
        )
        bundled.append(
            {
                "exam_question_number": str(row.get("question_number", "-")),
                "exam_question_text": query_text,
                "exam_unit": str(row.get("unit", "")),
                "exam_sub_concept": str(row.get("sub_concept", "")),
                "exam_difficulty": str(row.get("difficulty", "")),
                "top_matches": top_matches,
            }
        )
    return bundled
