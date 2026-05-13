from __future__ import annotations

from typing import Callable

from ld.errors import LDProtocolError
from ld.types import AnalysisResult, TestRun

from ld.protocols import lauf


ANALYZERS: dict[str, Callable[[TestRun], AnalysisResult]] = {
    "lauf": lauf.analyze,
    "triathlon-lauf": lauf.analyze,
    # M7: "rad": rad.analyze, "triathlon-rad": rad.analyze, "unspezifisch": unspezifisch.analyze
}


def analyze(test_run: TestRun) -> AnalysisResult:
    sport = test_run.athlete.sportart
    if sport not in ANALYZERS:
        raise LDProtocolError(f"Sportart '{sport}' wird noch nicht unterstützt.")
    return ANALYZERS[sport](test_run)
