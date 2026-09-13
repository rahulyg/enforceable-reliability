"""Run the Phase 0 synthetic path, with an explicitly opt-in live boundary."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from reliability.arms.a import ArmA, ModelClient
from reliability.arms.openrouter import OpenRouterClient
from reliability.data.synthetic import (
    load_observations,
    seasonal_naive,
    split_at_origin,
)
from reliability.eval.evidence import EvidenceRow, find_evidence, mae_evidence
from reliability.metrics.core import mae

QUESTION = "What was the MAE for synthetic_weekly_01 at origin day 7, horizon 1?"
EXPECTED_TEXT = "The MAE was 3 units."


class DeterministicClient:
    def answer(self, question: str, evidence_row: EvidenceRow) -> str:
        if question != QUESTION:
            raise ValueError("unexpected smoke question")
        if evidence_row.value != 3.0:
            raise ValueError("unexpected smoke evidence")
        return EXPECTED_TEXT


def fixture_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "tests"
        / "fixtures"
        / "synthetic_weekly_01.csv"
    )


def run(client: ModelClient) -> tuple[EvidenceRow, str]:
    observations = load_observations(fixture_path())
    train, target = split_at_origin(observations, origin_day=7)
    prediction = seasonal_naive(train, period=7, horizon=1)
    metric_value = mae([target[0].value], [prediction])
    evidence = mae_evidence(
        series_id=train[0].series_id, origin_day=7, horizon=1, value=metric_value
    )
    looked_up = find_evidence(
        (evidence,),
        series_id="synthetic_weekly_01",
        model_version="seasonal_naive_v0",
        origin_day=7,
        horizon=1,
        metric="mae",
    )
    return looked_up, ArmA(client).answer(QUESTION, looked_up)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Phase 0 synthetic smoke runner")
    parser.add_argument(
        "--live", action="store_true", help="make one OpenRouter request"
    )
    arguments = parser.parse_args(argv)
    client: ModelClient = (
        OpenRouterClient() if arguments.live else DeterministicClient()
    )
    evidence, answer = run(client)
    label = "LIVE" if arguments.live else "DETERMINISTIC"
    print(f"{label} SYNTHETIC SMOKE — not an evaluation")
    print(
        f"Evidence: {evidence.row_id} -> {evidence.metric}={evidence.value:g} {evidence.unit}"
    )
    print(f"Raw answer: {answer}")


if __name__ == "__main__":
    main()
