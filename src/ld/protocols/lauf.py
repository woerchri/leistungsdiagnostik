from __future__ import annotations

from ld import pflichtpruefungen, zones
from ld.protocols._common import (
    compute_vmax, diagram_title, fit_cubic_laktat, fit_linear_hf, intersection_table,
)
from ld.types import AnalysisResult, TestRun


def analyze(test_run: TestRun) -> AnalysisResult:
    cubic = fit_cubic_laktat(test_run.steps)
    hf_linear = fit_linear_hf(test_run.steps)
    v_max = compute_vmax(test_run)

    # Use the last measured step intensity (not aliquot v_max) as the upper search bound
    # so that high-lactate intersections beyond the aliquot correction can still be found.
    v_measured_max = test_run.steps[-1].intensitaet

    rows = intersection_table(
        cubic=cubic,
        hf_linear=hf_linear,
        intensitaet_min=test_run.testprotokoll.anfangsbelastung,
        intensitaet_max=v_measured_max,
        is_lauf=True,
    )

    suggested = zones.suggest_zones(
        rows=rows,
        hf_linear=hf_linear,
        v_max=v_max,
        is_lauf=True,
    )

    checks = pflichtpruefungen.run_all(test_run)

    return AnalysisResult(
        test_run=test_run,
        v_max=round(v_max, 4),
        cubic=cubic,
        hf_linear=hf_linear,
        intersections=rows,
        zones_suggested=suggested,
        zones_final=suggested,
        pflichtpruefungen=checks,
        diagram_title=diagram_title(test_run),
    )
