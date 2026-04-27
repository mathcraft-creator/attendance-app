from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


def save_similarity_results(
    results: list[dict[str, Any]],
    save_mode: str,
    json_path: str,
    google_sheets_webhook_url: str,
) -> str:
    if save_mode == "google_sheets":
        if not google_sheets_webhook_url:
            raise ValueError("GOOGLE_SHEETS_WEBHOOK_URL 환경변수가 비어 있습니다.")

        payload = {
            "saved_at": datetime.utcnow().isoformat(),
            "results": results,
        }
        response = requests.post(google_sheets_webhook_url, json=payload, timeout=15)
        response.raise_for_status()
        return "Google Sheets 저장 완료"

    out_path = Path(json_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {
                "saved_at": datetime.utcnow().isoformat(),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return f"JSON 저장 완료: {out_path}"
