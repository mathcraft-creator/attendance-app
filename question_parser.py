from __future__ import annotations

import re
from typing import List, Tuple

# 예: 1. / 1) / 1번 / [1] 형태의 문항 번호 인식
QUESTION_PATTERN = re.compile(
    r"(?m)^\s*(?:\[?(\d{1,3})\]?\s*(?:[.)]|번))\s*"
)


def split_questions(raw_text: str) -> List[Tuple[str, str]]:
    matches = list(QUESTION_PATTERN.finditer(raw_text))
    if not matches:
        cleaned = raw_text.strip()
        return [("1", cleaned)] if cleaned else []

    results: List[Tuple[str, str]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_text)
        block = raw_text[start:end].strip()
        number = match.group(1)
        if block:
            results.append((number, block))

    return results
