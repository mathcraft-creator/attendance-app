from __future__ import annotations

import re
from typing import Any

GUIDE_PATTERNS = [
    r"시험\s*안내",
    r"OMR\s*안내",
    r"총점\s*안내",
    r"답안지\s*작성\s*유의",
    r"수험생\s*유의사항",
]

OCR_KOR_CORRECTIONS = {
    "갓": "것",
    "합니디": "합니다",
    "증명하시오오": "증명하시오",
    "구하시요": "구하시오",
    "다음을 보교": "다음을 보고",
    "옳은것": "옳은 것",
}


def _is_guide_line(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return True
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in GUIDE_PATTERNS)


def _split_keep_math_regions(text: str) -> list[tuple[str, bool]]:
    # $...$, \(...\), \[...\] 구간은 수식으로 간주하여 보존
    math_pattern = re.compile(r"(\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\])")
    parts: list[tuple[str, bool]] = []
    last = 0
    for match in math_pattern.finditer(text):
        if match.start() > last:
            parts.append((text[last : match.start()], False))
        parts.append((match.group(0), True))
        last = match.end()
    if last < len(text):
        parts.append((text[last:], False))
    return parts


def correct_korean_ocr_errors_preserve_math(text: str) -> str:
    parts = _split_keep_math_regions(text)
    corrected: list[str] = []
    for segment, is_math in parts:
        if is_math:
            corrected.append(segment)
            continue

        updated = segment
        for wrong, right in OCR_KOR_CORRECTIONS.items():
            updated = updated.replace(wrong, right)
        corrected.append(updated)

    return "".join(corrected)


def parse_mathpix_lines(lines_json: dict[str, Any]) -> list[str]:
    lines = lines_json.get("lines", [])
    extracted: list[str] = []
    for row in lines:
        if isinstance(row, dict):
            text = str(row.get("text", "")).strip()
        else:
            text = str(row).strip()
        if text and not _is_guide_line(text):
            extracted.append(text)
    return extracted


def split_questions_from_lines(lines: list[str]) -> list[dict[str, str]]:
    merged = "\n".join(lines)
    pattern = re.compile(r"(?m)^\s*(?:\[?(\d{1,3})\]?\s*(?:[.)]|번))\s*")
    matches = list(pattern.finditer(merged))

    if not matches:
        text = correct_korean_ocr_errors_preserve_math(merged.strip())
        return [{"question_number": "1", "question_text": text}] if text else []

    results: list[dict[str, str]] = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(merged)
        block = merged[start:end].strip()
        if not block:
            continue
        cleaned = correct_korean_ocr_errors_preserve_math(block)
        results.append(
            {
                "question_number": match.group(1),
                "question_text": cleaned,
            }
        )
    return results
