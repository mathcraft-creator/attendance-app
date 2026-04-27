from __future__ import annotations

from typing import Protocol


class CardNewsGenerator(Protocol):
    def generate(self, report_path: str) -> str:
        """향후 카드뉴스 자동생성 기능 확장용 인터페이스(미구현)."""


class NotImplementedCardNewsGenerator:
    def generate(self, report_path: str) -> str:
        raise NotImplementedError("카드뉴스 자동생성 기능은 추후 단계에서 구현 예정입니다.")
