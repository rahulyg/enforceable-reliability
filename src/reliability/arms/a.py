"""The intentionally unconstrained free-form answer arm."""

from __future__ import annotations

from typing import Protocol

from reliability.eval.evidence import EvidenceRow


class ModelClient(Protocol):
    def answer(self, question: str, evidence_row: EvidenceRow) -> str: ...


class ArmA:
    def __init__(self, client: ModelClient) -> None:
        self._client = client

    def answer(self, question: str, evidence_row: EvidenceRow) -> str:
        return self._client.answer(question, evidence_row)
