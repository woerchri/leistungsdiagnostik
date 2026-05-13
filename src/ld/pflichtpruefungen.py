from __future__ import annotations

from ld.types import PflichtpruefungResult, TestRun


def run_all(test_run: TestRun) -> tuple[PflichtpruefungResult, ...]:
    return tuple([
        _check_letzte_stufe(test_run),
        _check_hf_monotonic(test_run),
        _check_laktat_monotonic(test_run),
        _check_laktatsprung(test_run),
        _check_rpe_konsistenz(test_run),
        _check_ausbelastung(test_run),
    ])


def _check_letzte_stufe(tr: TestRun) -> PflichtpruefungResult:
    if not tr.testprotokoll.letzte_stufe_vollstaendig:
        d = tr.testprotokoll.dauer_letzte_stufe_min or 0
        total = tr.testprotokoll.stufendauer_min
        return PflichtpruefungResult(
            name="letzte_stufe",
            ok=False,
            message_de=(
                f"Letzte Stufe nicht vollständig ({d:.2f} von {total:.0f} min). "
                f"v_max wird aliquot berechnet."
            ),
        )
    return PflichtpruefungResult("letzte_stufe", True, "")


def _check_hf_monotonic(tr: TestRun) -> PflichtpruefungResult:
    hf = [s.herzfrequenz_bpm for s in tr.steps if s.herzfrequenz_bpm is not None]
    drops = [(i, hf[i], hf[i + 1]) for i in range(len(hf) - 1) if hf[i + 1] < hf[i]]
    if drops:
        notes = ", ".join(f"Stufe {i+1}→{i+2}: {a}→{b}" for i, a, b in drops)
        return PflichtpruefungResult(
            name="hf_monotonic",
            ok=False,
            message_de=(
                f"Herzfrequenz fällt zwischen Stufen ab ({notes}). "
                f"Messfehler oder Erholung mitten im Test?"
            ),
        )
    return PflichtpruefungResult("hf_monotonic", True, "")


def _check_laktat_monotonic(tr: TestRun) -> PflichtpruefungResult:
    lk = [s.laktat_mmol for s in tr.steps if s.laktat_mmol is not None]
    drops = [
        (i, lk[i], lk[i + 1])
        for i in range(len(lk) - 1)
        if lk[i + 1] < lk[i] - 0.5
    ]
    if drops:
        notes = "; ".join(f"Stufe {i+1}→{i+2}: {a:.1f}→{b:.1f}" for i, a, b in drops)
        return PflichtpruefungResult(
            name="laktat_monotonic",
            ok=False,
            message_de=f"Laktat fällt deutlich zwischen Stufen ab ({notes}). Messfehler?",
        )
    return PflichtpruefungResult("laktat_monotonic", True, "")


def _check_laktatsprung(tr: TestRun) -> PflichtpruefungResult:
    """Flag jumps > 2.5 mmol/L between consecutive steps as unusual."""
    lk = [s.laktat_mmol for s in tr.steps if s.laktat_mmol is not None]
    jumps = [
        (i, lk[i + 1] - lk[i])
        for i in range(len(lk) - 1)
        if (lk[i + 1] - lk[i]) > 2.5
    ]
    if jumps:
        notes = "; ".join(f"Stufe {i+1}→{i+2}: +{d:.1f} mmol/L" for i, d in jumps)
        return PflichtpruefungResult(
            name="laktatsprung",
            ok=False,
            message_de=(
                f"Ungewöhnlich großer Laktatanstieg ({notes}). "
                f"Schwellenpassage oder Messfehler?"
            ),
        )
    return PflichtpruefungResult("laktatsprung", True, "")


def _check_rpe_konsistenz(tr: TestRun) -> PflichtpruefungResult:
    rpes = [(s.stufe, s.rpe) for s in tr.steps if s.rpe is not None]
    drops = [(a, b) for a, b in zip(rpes, rpes[1:]) if b[1] < a[1]]
    if drops:
        notes = ", ".join(f"Stufe {a[0]}→{b[0]}: {a[1]}→{b[1]}" for a, b in drops)
        return PflichtpruefungResult(
            name="rpe_konsistenz",
            ok=False,
            message_de=(
                f"RPE fällt mit steigender Belastung ({notes}). Eingabefehler?"
            ),
        )
    return PflichtpruefungResult("rpe_konsistenz", True, "")


def _check_ausbelastung(tr: TestRun) -> PflichtpruefungResult:
    if not tr.testprotokoll.ausbelastung:
        return PflichtpruefungResult(
            name="ausbelastung",
            ok=False,
            message_de=(
                "Keine vollständige Ausbelastung erreicht — "
                "Schwellenbestimmung ist vorsichtiger zu formulieren."
            ),
        )
    return PflichtpruefungResult("ausbelastung", True, "")
