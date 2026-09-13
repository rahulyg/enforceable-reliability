"""Deterministic metric primitives."""

from __future__ import annotations

from collections.abc import Sequence
from math import fsum, isfinite


def mae(actual: Sequence[float], predicted: Sequence[float]) -> float:
    if not actual:
        raise ValueError("actual must be nonempty")
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted must have equal lengths")
    if not all(isfinite(value) for value in (*actual, *predicted)):
        raise ValueError("actual and predicted must contain only finite values")
    return fsum(
        abs(observed - forecast) for observed, forecast in zip(actual, predicted)
    ) / len(actual)
