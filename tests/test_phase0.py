from __future__ import annotations

import math
from pathlib import Path

import pytest

from reliability.arms.a import ArmA
from reliability.arms.openrouter import ENV_VAR, _key_from_environment
from reliability.data.synthetic import (
    Observation,
    load_observations,
    seasonal_naive,
    split_at_origin,
)
from reliability.eval.evidence import EvidenceRow, find_evidence, mae_evidence
from reliability.eval.smoke import EXPECTED_TEXT, QUESTION, run
from reliability.metrics.core import mae

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_weekly_01.csv"


class InspectingFake:
    def __init__(self, text: str = EXPECTED_TEXT) -> None:
        self.text = text
        self.calls: list[tuple[str, EvidenceRow]] = []

    def answer(self, question: str, evidence_row: EvidenceRow) -> str:
        self.calls.append((question, evidence_row))
        return self.text


def test_end_to_end_real_fixture_preserves_answer() -> None:
    client = InspectingFake()
    evidence, answer = run(client)
    assert evidence.value == 3.0
    assert answer == EXPECTED_TEXT
    assert client.calls == [(QUESTION, evidence)]
    assert (
        evidence.row_id == "synthetic_weekly_01__seasonal_naive_v0__origin_7__h1__mae"
    )
    assert ArmA(InspectingFake("99")).answer(QUESTION, evidence) == "99"


@pytest.mark.parametrize("period", [0, -1])
def test_seasonal_naive_rejects_bad_period(period: int) -> None:
    with pytest.raises(ValueError, match="period"):
        seasonal_naive((), period=period, horizon=1)


def test_seasonal_naive_requires_full_history_and_one_step_horizon() -> None:
    history = (Observation("x", 1, 1.0),)
    with pytest.raises(ValueError, match="history"):
        seasonal_naive(history, period=7, horizon=1)
    with pytest.raises(ValueError, match="horizon"):
        seasonal_naive(history * 7, period=7, horizon=2)


@pytest.mark.parametrize(
    ("actual", "predicted"),
    [
        ([], []),
        ([1.0], []),
        ([math.nan], [1.0]),
        ([math.inf], [1.0]),
        ([-math.inf], [1.0]),
    ],
)
def test_mae_rejects_invalid_inputs(
    actual: list[float], predicted: list[float]
) -> None:
    with pytest.raises(ValueError):
        mae(actual, predicted)


def test_mae_mean() -> None:
    assert mae([1.0, 5.0], [3.0, 2.0]) == 2.5


def test_lookup_requires_exactly_one_row() -> None:
    row = mae_evidence(series_id="x", origin_day=7, horizon=1, value=3.0)
    kwargs = {
        "series_id": "x",
        "model_version": "seasonal_naive_v0",
        "origin_day": 7,
        "horizon": 1,
        "metric": "mae",
    }
    with pytest.raises(LookupError, match="0"):
        find_evidence((), **kwargs)
    with pytest.raises(LookupError, match="2"):
        find_evidence((row, row), **kwargs)


def test_arm_a_bubbles_provider_exception() -> None:
    class Broken:
        def answer(self, question: str, evidence_row: EvidenceRow) -> str:
            raise RuntimeError("provider failed")

    with pytest.raises(RuntimeError, match="provider failed"):
        ArmA(Broken()).answer(
            QUESTION, mae_evidence(series_id="x", origin_day=7, horizon=1, value=3.0)
        )


def test_openrouter_placeholder_key_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(ENV_VAR, "replace_with_your_openrouter_api_key")
    with pytest.raises(RuntimeError, match="missing or a placeholder"):
        _key_from_environment()


def test_loader_and_split_real_fixture() -> None:
    observations = load_observations(FIXTURE)
    train, target = split_at_origin(observations, origin_day=7)
    assert len(train) == 7 and target[0].value == 13.0
