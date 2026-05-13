# Leistungsdiagnostik — feature plan (implementer guide)

Implementer-grade spec. Pre-decided choices, exact signatures, exact German wording, verification commands. Where sister's spec leaves judgement to her (zone boundaries, interpretation tone), the plan calls that out and routes through interactive dialogue or LLM prose she edits.

Read [BRIEF.md](BRIEF.md) for the *why*. **The authoritative source for input/math/plot specs is `samples/26_05_LD_Dateneingabe.docx`** — open it when uncertain.

---

## Conventions

- All commands run from repo root (`~/Desktop/leistungsdiagnostik/`).
- Python 3.11+, `uv` for everything. Never `pip install`.
- Type hints mandatory. `from __future__ import annotations` at top of every module.
- `@dataclass(frozen=True)` for structured data crossing module boundaries.
- User-facing errors: raise `LDInputError` (`src/ld/errors.py`); never raw `KeyError`/`ValueError`. Error messages in German.
- Logging via `logging.getLogger("ld")`, INFO default. Error messages to user go via stderr in German; logger output is English/technical.
- `pathlib.Path`, never string paths.
- `TODO(spec)` marker = re-check against `samples/26_05_LD_Dateneingabe.docx`.
- No async, no plugins, no metaclasses. One-person tool.

---

## Reference data (use these for tests)

**Rainier Matzinger, 23.05.2024, Lauf** (`samples/RM_LD_LAUF_24_05.xlsx`):
- Athlet: Rainier Matzinger, Geburtsjahr 1968, Gewicht 71.5 kg, Größe 1.79 m, Sport Laufen
- Testprotokoll: Anfangsintensität 7 km/h, Inkrement 1 km/h, Stufendauer 4 min, Ort Laufcamp Achensee, Gerät Laufband Atoll Achensee, Besonderheiten "1% Steigung", letzte Stufe NICHT vollständig, Dauer letzte Stufe 1.75 min, max. Ausbelastung JA
- Stufen: (7, 133, 1.9, 9), (8, 141, 2.8, 9), (9, 150, 3.0, 14), (10, 159, 3.8, 16), (11, 167, 5.2, 17), (12, 173, 7.9, 18) — tuples are (v_km_h, hf_bpm, laktat_mmol, rpe)
- Expected `v_max` = 11.4375 km/h (= 11 + 1.75/4 × 1)
- Expected linear HF fit: k ≈ 8.2, d ≈ 75.933
- Expected polynomial (deg 3, in v-space): produces these intersection values at fixed lactates:
  - lak=1.0 → v=6.0 (extrapolation floor at start-1)
  - lak=1.5 → v=6.0
  - lak=2.0 → v=7.064, hf=133.86
  - lak=2.5 → v=7.658, hf=138.73
  - lak=3.0 → v=8.707, hf=147.33
  - lak=4.0 → v=10.230, hf=159.82
  - lak=6.0 → v=11.368, hf=169.15
  - lak=8.0 → v=12.023, hf=174.52

**Sarah Seckendorf, 23.05.2024, Lauf** (PDF `samples/SS_LD_LAUF_24_05.pdf`): same protocol shape, start 8 km/h, increment 1, Stufendauer 4 min, completed step 13 (last step IS complete, vmax=13.0). Use as second historical case.

These two cases are the M1 acceptance gate.

---

## Milestone map

| # | Name | Output | Acceptance gate |
|---|------|--------|-----------------|
| **M0** | Inputs in hand | DONE | `samples/26_05_LD_Dateneingabe.docx`, `samples/RM_LD_LAUF_24_05.xlsx`, `samples/SS_LD_LAUF_24_05.pdf` all readable |
| **M1** | Deterministic core (Lauf) | `uv run python -m ld.run input.xlsx` → JSON + draft.docx | Rainier intersection table matches reference; Sarah matches PDF |
| **M2** | Standalone fallback | `--interpret` → finished `.docx` via OpenAI API | One historical case end-to-end without agent |
| **M3** | Codex UX layer | `/ld-report` with interactive zone adjustment + Pflichtprüfungen surfacing | Sister runs it solo, including zone adjustment |
| **M4** | Privacy + versioning | PII-redacted LLM JSON; `_v1`/`_v2` naming | No raw name in `_for_llm.json`; re-runs never overwrite |
| **M5** | Test net | unit + protocol-snapshot + e2e smoke | `uv run pytest` green; sanity-bug fails |
| **M6** | Handoff | Sister set up on her machine | Solo run with zone adjustment |
| **M7** | RAD + UNSPEZIFISCH protocols | Same shape as M1 for cycling and generic | Numbers match her hand-calc per protocol |
| **M8** | Usage guide | `USAGE_GUIDE.md` from real tool | Sister reads cold, no questions |

---

## M0 — DONE

Files in place at `samples/`:
- `26_05_LD_Dateneingabe.docx` — authoritative input/output/math spec
- `RM_LD_LAUF_24_05.xlsx` — historical Excel (reference, not blueprint)
- `SS_LD_LAUF_24_05.pdf` — historical output PDF (target shape, will be improved)

First protocol: **Lauf** (running step test). RAD and UNSPEZIFISCH deferred to M7.

---

## M1 — Deterministic core (Lauf)

### M1.1 Repo bootstrap

```bash
uv init --python 3.11
uv add pandas openpyxl matplotlib numpy python-docx docxtpl python-dotenv pytest
uv add --dev pytest-snapshot docx2txt
git init
printf "%s\n" ".venv/" "output/" ".env" "__pycache__/" "*.pyc" > .gitignore
mkdir -p src/ld/protocols templates tests/unit tests/protocols tests/e2e tests/historical input output
```

`pyproject.toml` additions:
```toml
[project]
name = "ld"
version = "0.1.0"
requires-python = ">=3.11"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### M1.2 Errors

**`src/ld/errors.py`**

```python
from __future__ import annotations


class LDError(Exception):
    """Base class. Message must be a German, user-friendly sentence."""


class LDInputError(LDError):
    """User-facing: something is wrong with the input file."""


class LDProtocolError(LDError):
    """The Sportart in the input is not supported yet."""
```

### M1.3 Data structures

**`src/ld/types.py`**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


# === Athlete & test setup ===

@dataclass(frozen=True)
class Athlete:
    sportart: str             # "lauf" | "rad" | "triathlon-rad" | "triathlon-lauf" | "unspezifisch"
    vorname: str
    name: str
    geburtsjahr: int
    geschlecht: str | None    # "m" | "w" | "d" | None  (spec doesn't require but useful for interpretation)
    gewicht_kg: float
    groesse_m: float          # meters, not cm (historical uses meters)
    trainingsziel: str
    wettkampfziel: str
    trainingsumfang_wo: str
    leistungsniveau: str

    @property
    def alter(self) -> int:
        return date.today().year - self.geburtsjahr


@dataclass(frozen=True)
class Testprotokoll:
    testdatum: date
    uhrzeit: str               # "HH:MM"
    durchfuehrungsort: str
    testleiter: str
    geraet: str                # e.g. "Laufband Atoll Achensee"
    anfangsintensitaet: float  # km/h (lauf), W (rad), or step level (unspez)
    stufeninkrement: float
    stufendauer_min: float
    stufenlaenge_m: int | None # optional (lauf may have step length in meters)
    besonderheiten: str        # e.g. "1% Steigung"
    letzte_stufe_vollstaendig: bool
    dauer_letzte_stufe_min: float | None
    ausbelastung: bool


@dataclass(frozen=True)
class TestStep:
    """One measured step. intensitaet has units depending on sportart."""
    stufe: int                 # 1-based step index
    intensitaet: float
    herzfrequenz_bpm: int | None
    laktat_mmol: float | None
    rpe: int | None            # 6-20 scale (Lauf) or 0-10 scale — spec uses 6-20 in historical xlsx, 0-10 in docx tables. TODO(spec): pin once we ask her.


@dataclass(frozen=True)
class Coaching:
    verletzungen: str
    aktuelle_probleme: str
    staerken: str
    schwaechen: str
    geplante_wettkaempfe: str
    trainernotizen: str


@dataclass(frozen=True)
class TestRun:
    athlete: Athlete
    testprotokoll: Testprotokoll
    steps: tuple[TestStep, ...]
    coaching: Coaching


# === Derived / computed ===

@dataclass(frozen=True)
class LinearFit:
    """HF = slope * intensitaet + intercept."""
    slope: float
    intercept: float

    def predict(self, x: float) -> float:
        return self.slope * x + self.intercept


@dataclass(frozen=True)
class CubicFit:
    """Laktat = a*x^3 + b*x^2 + c*x + d, x in intensitaet-space (v km/h for Lauf)."""
    a: float
    b: float
    c: float
    d: float

    def predict(self, x: float) -> float:
        return self.a * x**3 + self.b * x**2 + self.c * x + self.d


@dataclass(frozen=True)
class IntersectionRow:
    laktat: float
    intensitaet: float | None     # None if out-of-range
    pace_min_per_km: str | None   # only meaningful for Lauf; None for Rad/Unspez
    herzfrequenz_bpm: int | None


@dataclass(frozen=True)
class TrainingZone:
    name: str                     # "Z1" .. "Z6"
    ziel: str                     # German label, e.g. "aktive Regeneration"
    rpe_min: int
    rpe_max: int
    intensitaet_min: float | None
    intensitaet_max: float | None
    pace_min_min_per_km: str | None
    pace_max_min_per_km: str | None
    herzfrequenz_min: int | None
    herzfrequenz_max: int | None


@dataclass(frozen=True)
class PflichtpruefungResult:
    """One plausibility check outcome."""
    name: str                     # e.g. "laktatsprung"
    ok: bool
    message_de: str               # human-readable note in German; empty if ok=True


@dataclass(frozen=True)
class AnalysisResult:
    test_run: TestRun
    v_max: float
    cubic: CubicFit
    hf_linear: LinearFit
    intersections: tuple[IntersectionRow, ...]
    zones_suggested: tuple[TrainingZone, ...]
    zones_final: tuple[TrainingZone, ...]   # equals zones_suggested unless overridden by --zones flag / interactive dialogue
    pflichtpruefungen: tuple[PflichtpruefungResult, ...]
    diagram_title: str            # e.g. "Lauf_8_1_4; 23.05.2024"


@dataclass(frozen=True)
class Paths:
    input_xlsx: Path
    output_dir: Path
    basename: str
    json_full: Path
    json_for_llm: Path
    draft_docx: Path
    final_docx: Path
    plots_dir: Path
    pickle_path: Path             # serialized AnalysisResult for patch_interpretation step
```

### M1.4 Input parser

**`src/ld/io_input.py`**

The input is a multi-sheet xlsx mirroring the spec doc. Sheets:
- `Athlet` — athlete metadata (key-value pairs in column A/B)
- `Testprotokoll` — test setup (key-value pairs in column A/B)
- `Testdaten` — step table starting at row 2
- `Coaching` — additional coaching info (key-value pairs)

```python
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import openpyxl

from ld.errors import LDInputError
from ld.types import Athlete, Coaching, TestRun, TestStep, Testprotokoll


def parse_input(path: Path) -> TestRun:
    if not path.exists():
        raise LDInputError(f"Eingabedatei nicht gefunden: {path}")
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as e:
        raise LDInputError(f"Eingabedatei konnte nicht geöffnet werden ({path.name}): {e}") from e

    return TestRun(
        athlete=_parse_athlete(wb),
        testprotokoll=_parse_testprotokoll(wb),
        steps=_parse_steps(wb),
        coaching=_parse_coaching(wb),
    )


def _require_sheet(wb, name: str):
    if name not in wb.sheetnames:
        raise LDInputError(
            f"Arbeitsblatt '{name}' fehlt in der Eingabedatei. "
            f"Bitte mit templates/input_template.xlsx als Basis arbeiten."
        )
    return wb[name]


def _kv(ws, key: str) -> str | None:
    """Read column-A keyed pairs (key in col A, value in col B). Returns string or None."""
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
        if row and row[0] == key:
            return row[1]
    return None


def _required_kv(ws, key: str) -> str:
    value = _kv(ws, key)
    if value is None or value == "":
        raise LDInputError(f"Pflichtfeld '{key}' auf Blatt '{ws.title}' ist leer.")
    return str(value).strip()


def _parse_athlete(wb) -> Athlete:
    ws = _require_sheet(wb, "Athlet")
    sportart_raw = _required_kv(ws, "Sportart").lower().strip()
    SUPPORTED = {"lauf", "rad", "triathlon-rad", "triathlon-lauf", "unspezifisch"}
    if sportart_raw not in SUPPORTED:
        raise LDInputError(
            f"Sportart '{sportart_raw}' nicht unterstützt. Erlaubt: {sorted(SUPPORTED)}."
        )
    try:
        return Athlete(
            sportart=sportart_raw,
            vorname=_required_kv(ws, "Vorname"),
            name=_required_kv(ws, "Name"),
            geburtsjahr=int(_required_kv(ws, "Geburtsjahr")),
            geschlecht=(_kv(ws, "Geschlecht") or None),
            gewicht_kg=float(_required_kv(ws, "Gewicht (kg)")),
            groesse_m=float(_required_kv(ws, "Größe (m)")),
            trainingsziel=str(_kv(ws, "Trainingsziel") or ""),
            wettkampfziel=str(_kv(ws, "Wettkampfziel") or ""),
            trainingsumfang_wo=str(_kv(ws, "Trainingsumfang/Woche") or ""),
            leistungsniveau=str(_kv(ws, "Leistungsniveau") or ""),
        )
    except (ValueError, TypeError) as e:
        raise LDInputError(f"Athletendaten konnten nicht gelesen werden: {e}") from e


def _parse_testprotokoll(wb) -> Testprotokoll:
    ws = _require_sheet(wb, "Testprotokoll")
    raw_date = _kv(ws, "Testdatum")
    if isinstance(raw_date, datetime):
        test_date = raw_date.date()
    elif isinstance(raw_date, date):
        test_date = raw_date
    elif isinstance(raw_date, str):
        # accept "DD.MM.YYYY"
        test_date = datetime.strptime(raw_date.strip(), "%d.%m.%Y").date()
    else:
        raise LDInputError(f"Testdatum auf Blatt 'Testprotokoll' fehlt oder hat falsches Format (erwartet TT.MM.JJJJ).")

    def yesno(key: str) -> bool:
        raw = _required_kv(ws, key).lower().strip()
        if raw in {"ja", "yes", "true", "1"}:
            return True
        if raw in {"nein", "no", "false", "0"}:
            return False
        raise LDInputError(f"Feld '{key}' auf 'Testprotokoll' erwartet JA oder NEIN, nicht '{raw}'.")

    letzte_voll = yesno("Letzte Stufe vollständig absolviert")
    dauer_letzte = None
    if not letzte_voll:
        raw = _required_kv(ws, "Dauer letzte Stufe (min)")
        try:
            dauer_letzte = float(raw)
        except ValueError as e:
            raise LDInputError(f"Dauer letzte Stufe muss eine Zahl in Minuten sein, nicht '{raw}'.") from e

    return Testprotokoll(
        testdatum=test_date,
        uhrzeit=str(_kv(ws, "Uhrzeit") or "00:00"),
        durchfuehrungsort=_required_kv(ws, "Durchführungsort"),
        testleiter=_required_kv(ws, "Testleiter"),
        geraet=_required_kv(ws, "Gerät"),
        anfangsintensitaet=float(_required_kv(ws, "Anfangsintensität")),
        stufeninkrement=float(_required_kv(ws, "Stufeninkrement")),
        stufendauer_min=float(_required_kv(ws, "Stufendauer (min)")),
        stufenlaenge_m=(int(_kv(ws, "Stufenlänge (m)")) if _kv(ws, "Stufenlänge (m)") else None),
        besonderheiten=str(_kv(ws, "Besonderheiten") or ""),
        letzte_stufe_vollstaendig=letzte_voll,
        dauer_letzte_stufe_min=dauer_letzte,
        ausbelastung=yesno("Ausbelastung"),
    )


def _parse_steps(wb) -> tuple[TestStep, ...]:
    ws = _require_sheet(wb, "Testdaten")
    # Header is at row 1; data starts at row 2. Columns:
    # A: Stufe | B: Intensität | C: Herzfrequenz | D: Laktat | E: RPE
    expected_headers = ["Stufe", "Intensität", "Herzfrequenz", "Laktat", "RPE"]
    actual = [str(ws.cell(row=1, column=c).value).strip() if ws.cell(row=1, column=c).value else "" for c in range(1, 6)]
    if actual != expected_headers:
        raise LDInputError(
            f"Spaltenüberschriften auf 'Testdaten' falsch. Erwartet: {expected_headers}, gefunden: {actual}."
        )

    steps: list[TestStep] = []
    for row_idx in range(2, ws.max_row + 1):
        stufe_val = ws.cell(row=row_idx, column=1).value
        if stufe_val is None or stufe_val == "":
            break  # end of data
        try:
            steps.append(TestStep(
                stufe=int(stufe_val),
                intensitaet=float(ws.cell(row=row_idx, column=2).value),
                herzfrequenz_bpm=_int_or_none(ws.cell(row=row_idx, column=3).value),
                laktat_mmol=_float_or_none(ws.cell(row=row_idx, column=4).value),
                rpe=_int_or_none(ws.cell(row=row_idx, column=5).value),
            ))
        except (ValueError, TypeError) as e:
            raise LDInputError(f"Zeile {row_idx} auf 'Testdaten' enthält ungültige Werte: {e}") from e

    if len(steps) < 4:
        raise LDInputError(
            f"Mindestens 4 Stufen mit Laktatwerten erforderlich (kubische Anpassung). Gefunden: {len(steps)}."
        )
    return tuple(steps)


def _parse_coaching(wb) -> Coaching:
    ws = _require_sheet(wb, "Coaching")
    return Coaching(
        verletzungen=str(_kv(ws, "Verletzungen") or ""),
        aktuelle_probleme=str(_kv(ws, "Aktuelle Probleme") or ""),
        staerken=str(_kv(ws, "Stärken") or ""),
        schwaechen=str(_kv(ws, "Schwächen") or ""),
        geplante_wettkaempfe=str(_kv(ws, "Geplante Wettkämpfe") or ""),
        trainernotizen=str(_kv(ws, "Trainernotizen") or ""),
    )


def _int_or_none(v):
    if v is None or v == "":
        return None
    return int(v)


def _float_or_none(v):
    if v is None or v == "":
        return None
    return float(v)
```

### M1.5 Common math

**`src/ld/protocols/_common.py`**

```python
from __future__ import annotations

import numpy as np

from ld.errors import LDInputError
from ld.types import (
    CubicFit, IntersectionRow, LinearFit, TestRun, TestStep,
)


# Fixed lactate targets from the spec.
LAKTAT_TARGETS: tuple[float, ...] = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0)


def fit_cubic_laktat(steps: tuple[TestStep, ...]) -> CubicFit:
    """Degree-3 polynomial fit of laktat vs intensitaet, in intensitaet-space."""
    xs = np.array([s.intensitaet for s in steps if s.laktat_mmol is not None], dtype=float)
    ys = np.array([s.laktat_mmol for s in steps if s.laktat_mmol is not None], dtype=float)
    if len(xs) < 4:
        raise LDInputError(
            f"Mindestens 4 Laktatwerte für die kubische Anpassung benötigt; gefunden: {len(xs)}."
        )
    # np.polyfit returns [a, b, c, d] for ax^3 + bx^2 + cx + d
    a, b, c, d = np.polyfit(xs, ys, deg=3)
    return CubicFit(a=float(a), b=float(b), c=float(c), d=float(d))


def fit_linear_hf(steps: tuple[TestStep, ...]) -> LinearFit:
    """Linear fit of HF vs intensitaet."""
    xs = np.array([s.intensitaet for s in steps if s.herzfrequenz_bpm is not None], dtype=float)
    ys = np.array([s.herzfrequenz_bpm for s in steps if s.herzfrequenz_bpm is not None], dtype=float)
    if len(xs) < 2:
        raise LDInputError(
            f"Mindestens 2 Herzfrequenzwerte für die lineare Anpassung benötigt; gefunden: {len(xs)}."
        )
    slope, intercept = np.polyfit(xs, ys, deg=1)
    return LinearFit(slope=float(slope), intercept=float(intercept))


def compute_vmax(test_run: TestRun) -> float:
    """Aliquot calculation:
       - If last step complete: v_max = last step's intensitaet.
       - If last step incomplete: v_max = previous_step_intensitaet + (dauer_letzte / stufendauer) * inkrement.
    """
    proto = test_run.testprotokoll
    steps = test_run.steps
    last = steps[-1]
    if proto.letzte_stufe_vollstaendig:
        return float(last.intensitaet)
    if proto.dauer_letzte_stufe_min is None:
        raise LDInputError(
            "Letzte Stufe ist unvollständig, aber 'Dauer letzte Stufe' fehlt."
        )
    if proto.dauer_letzte_stufe_min >= proto.stufendauer_min:
        # Treat as fully completed if duration matches
        return float(last.intensitaet)
    base = steps[-2].intensitaet if len(steps) >= 2 else proto.anfangsintensitaet - proto.stufeninkrement
    fraction = proto.dauer_letzte_stufe_min / proto.stufendauer_min
    return float(base + fraction * proto.stufeninkrement)


def intersection_table(
    cubic: CubicFit,
    hf_linear: LinearFit,
    intensitaet_min: float,
    intensitaet_max: float,
    is_lauf: bool,
) -> tuple[IntersectionRow, ...]:
    """For each fixed lactate target, find smallest real positive root of cubic(x)=target in
    a sensible range. Spec note: for targets below the curve's minimum on [min, max], we
    return intensitaet_min as a display floor (mirrors historical xlsx behavior). For
    targets the curve doesn't reach within [intensitaet_min, intensitaet_max+~10%], leave None.
    """
    rows: list[IntersectionRow] = []
    upper = intensitaet_max + 0.1 * (intensitaet_max - intensitaet_min)  # tolerate slight extrapolation
    poly = np.poly1d([cubic.a, cubic.b, cubic.c, cubic.d])

    for target in LAKTAT_TARGETS:
        shifted = poly - target
        roots = shifted.roots
        real_positive = sorted(
            r.real for r in roots
            if abs(r.imag) < 1e-6 and r.real > 0
        )
        in_range = [r for r in real_positive if intensitaet_min <= r <= upper]
        if in_range:
            x = in_range[0]
        elif real_positive and max(real_positive) < intensitaet_min:
            x = intensitaet_min - 1.0  # floor display, matches historical "Stufe-1" idiom
        else:
            x = None

        if x is None:
            rows.append(IntersectionRow(target, None, None, None))
            continue

        hf = int(round(hf_linear.predict(x)))
        pace = _pace_min_per_km(x) if is_lauf and x > 0 else None
        # Allow None intensitaet for floor case
        rows.append(IntersectionRow(
            laktat=target,
            intensitaet=round(float(x), 3),
            pace_min_per_km=pace,
            herzfrequenz_bpm=hf,
        ))
    return tuple(rows)


def _pace_min_per_km(v_km_h: float) -> str:
    """Convert km/h to pace as 'MM:SS' min/km."""
    if v_km_h <= 0:
        return "—"
    total_sec = 3600.0 / v_km_h
    minutes = int(total_sec // 60)
    seconds = int(round(total_sec - minutes * 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes:02d}:{seconds:02d}"


def diagram_title(test_run: TestRun) -> str:
    """Spec format: '<Sportart>_<Start>_<Inkrement>_<Stufendauer>; <Datum>'.
    Example: 'Lauf_8_1_4; 23.05.2024'.
    """
    proto = test_run.testprotokoll
    sportart_label = {
        "lauf": "Lauf",
        "rad": "Rad",
        "triathlon-rad": "Triathlon-Rad",
        "triathlon-lauf": "Triathlon-Lauf",
        "unspezifisch": "Unspezifisch",
    }[test_run.athlete.sportart]
    start = _trim_num(proto.anfangsintensitaet)
    inc = _trim_num(proto.stufeninkrement)
    dur = _trim_num(proto.stufendauer_min)
    datum = proto.testdatum.strftime("%d.%m.%Y")
    return f"{sportart_label}_{start}_{inc}_{dur}; {datum}"


def _trim_num(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(x)
```

### M1.6 Pflichtprüfungen module

**`src/ld/pflichtpruefungen.py`**

Spec rules (Pflichtprüfungen section in `samples/26_05_LD_Dateneingabe.docx`). All checks are deterministic, just-flag-don't-block.

```python
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
            message_de=f"Letzte Stufe nicht vollständig ({d:.2f} von {total:.0f} min). v_max wird aliquot berechnet.",
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
            message_de=f"Herzfrequenz fällt zwischen Stufen ab ({notes}). Messfehler oder Erholung mitten im Test?",
        )
    return PflichtpruefungResult("hf_monotonic", True, "")


def _check_laktat_monotonic(tr: TestRun) -> PflichtpruefungResult:
    lk = [s.laktat_mmol for s in tr.steps if s.laktat_mmol is not None]
    drops = [(i, lk[i], lk[i + 1]) for i in range(len(lk) - 1) if lk[i + 1] < lk[i] - 0.5]
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
    jumps = [(i, lk[i + 1] - lk[i]) for i in range(len(lk) - 1) if (lk[i + 1] - lk[i]) > 2.5]
    if jumps:
        notes = "; ".join(f"Stufe {i+1}→{i+2}: +{d:.1f} mmol/L" for i, d in jumps)
        return PflichtpruefungResult(
            name="laktatsprung",
            ok=False,
            message_de=f"Ungewöhnlich großer Laktatanstieg ({notes}). Schwellenpassage oder Messfehler?",
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
            message_de=f"RPE fällt mit steigender Belastung ({notes}). Eingabefehler?",
        )
    return PflichtpruefungResult("rpe_konsistenz", True, "")


def _check_ausbelastung(tr: TestRun) -> PflichtpruefungResult:
    if not tr.testprotokoll.ausbelastung:
        return PflichtpruefungResult(
            name="ausbelastung",
            ok=False,
            message_de="Keine vollständige Ausbelastung erreicht — Schwellenbestimmung ist vorsichtiger zu formulieren.",
        )
    return PflichtpruefungResult("ausbelastung", True, "")
```

### M1.7 Zone suggestion module

**`src/ld/zones.py`**

Suggest Z2–Z6 boundaries from the cubic + HF linear fit. **These are starting points only** — sister adjusts them in M3 dialogue.

Heuristic (defensible, transparent):
- Z2 upper bound: intensitaet at lactate = 2.0 mmol/L (or v_min if curve never goes that low)
- Z3 upper bound: intensitaet at lactate = 3.0 mmol/L
- Z4 upper bound: intensitaet at lactate = 4.0 mmol/L
- Z5 upper bound: v_max (or intensitaet at lactate = 6.0 if v_max not reliable)
- Z6: everything above v_max

These are conservative defaults aligned with how the historical Rainier xlsx came out. Sister will move them.

```python
from __future__ import annotations

from ld.protocols._common import _pace_min_per_km
from ld.types import IntersectionRow, LinearFit, TrainingZone


# Zone labels from spec (de_DE):
ZONE_META: tuple[tuple[str, str, int, int], ...] = (
    # (name, ziel, rpe_min, rpe_max)  — RPE on 0-10 scale per spec docx; mapping to 6-20 below
    ("Z1", "aktive Regeneration",      0, 2),
    ("Z2", "aerobe Basis",             3, 4),
    ("Z3", "metabolische Stabilität",  5, 6),
    ("Z4", "Schwellenleistung",        7, 8),
    ("Z5", "VO2max-Reize",             9, 9),
    ("Z6", "neuromuskulär",            10, 10),
)


def _intersection_lookup(rows: tuple[IntersectionRow, ...], target_lk: float) -> float | None:
    for r in rows:
        if abs(r.laktat - target_lk) < 1e-9:
            return r.intensitaet
    return None


def suggest_zones(
    rows: tuple[IntersectionRow, ...],
    hf_linear: LinearFit,
    v_max: float,
    is_lauf: bool,
) -> tuple[TrainingZone, ...]:
    """Return Z1..Z6 with suggested boundaries.

    Z1 has no upper intensity (it's just rest/active recovery).
    Z2: up to lactate=2.0 mmol/L crossing.
    Z3: 2.0 - 3.0 mmol/L crossings.
    Z4: 3.0 - 4.0.
    Z5: 4.0 - v_max.
    Z6: above v_max.
    """
    v_lk2 = _intersection_lookup(rows, 2.0)
    v_lk3 = _intersection_lookup(rows, 3.0)
    v_lk4 = _intersection_lookup(rows, 4.0)

    bounds = [
        (None,   v_lk2),    # Z2 upper
        (v_lk2,  v_lk3),    # Z3 lower..upper
        (v_lk3,  v_lk4),    # Z4
        (v_lk4,  v_max),    # Z5
        (v_max,  None),     # Z6 has no upper bound
    ]

    zones: list[TrainingZone] = []
    for (name, ziel, rpe_lo, rpe_hi), (lo, hi) in zip(ZONE_META[1:], bounds):
        zones.append(_zone(name, ziel, rpe_lo, rpe_hi, lo, hi, hf_linear, is_lauf))

    # Z1 placeholder: aktive Regeneration, no intensity bounds
    z1 = TrainingZone(
        name="Z1",
        ziel="aktive Regeneration",
        rpe_min=0, rpe_max=2,
        intensitaet_min=None, intensitaet_max=None,
        pace_min_min_per_km=None, pace_max_min_per_km=None,
        herzfrequenz_min=None, herzfrequenz_max=None,
    )
    return (z1, *zones)


def _zone(name, ziel, rpe_lo, rpe_hi, intens_lo, intens_hi, hf_linear, is_lauf) -> TrainingZone:
    return TrainingZone(
        name=name,
        ziel=ziel,
        rpe_min=rpe_lo,
        rpe_max=rpe_hi,
        intensitaet_min=intens_lo,
        intensitaet_max=intens_hi,
        pace_min_min_per_km=(_pace_min_per_km(intens_hi) if is_lauf and intens_hi else None),  # min pace = max speed
        pace_max_min_per_km=(_pace_min_per_km(intens_lo) if is_lauf and intens_lo else None),
        herzfrequenz_min=(int(round(hf_linear.predict(intens_lo))) if intens_lo is not None else None),
        herzfrequenz_max=(int(round(hf_linear.predict(intens_hi))) if intens_hi is not None else None),
    )
```

### M1.8 Protocol dispatch + Lauf analyzer

**`src/ld/protocols/__init__.py`**

```python
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
```

**`src/ld/protocols/lauf.py`**

```python
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

    rows = intersection_table(
        cubic=cubic,
        hf_linear=hf_linear,
        intensitaet_min=test_run.testprotokoll.anfangsintensitaet,
        intensitaet_max=v_max,
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
        zones_final=suggested,    # equals suggested until M3 dialogue overrides
        pflichtpruefungen=checks,
        diagram_title=diagram_title(test_run),
    )
```

### M1.9 Plots

**`src/ld/plots.py`**

Spec from `26_05_LD_Dateneingabe.docx` (translated to Python settings):
- Dual y-axis: laktat left (red), HF right (blue).
- X-axis: intensitaet from anfangsintensitaet to v_max; major ticks at stufeninkrement.
- Laktat axis: 0 → max(laktat) + 1.0; major tick = 1 if max ≤ 7 else 2.
- HF axis: floor((min hf - 10)/10)*10 → ceil(max hf / 10)*10; major tick = 10.
- Laktat shown as polynomial deg-3 curve through data point markers.
- HF shown as linear line through data point markers.
- Title: diagram_title from `_common.py`.
- Plot file: `output/<basename>/diagramm.png`.

```python
from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from ld.types import AnalysisResult


_FIGSIZE = (10.0, 6.0)
_DPI = 150
_COLOR_LAKTAT = "tab:red"
_COLOR_HF = "tab:blue"


def render_main_diagram(result: AnalysisResult, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "diagramm.png"

    proto = result.test_run.testprotokoll
    steps = result.test_run.steps
    x_data = np.array([s.intensitaet for s in steps], dtype=float)
    lk_data = np.array([s.laktat_mmol if s.laktat_mmol is not None else np.nan for s in steps])
    hf_data = np.array([s.herzfrequenz_bpm if s.herzfrequenz_bpm is not None else np.nan for s in steps])

    x_min = proto.anfangsintensitaet
    x_max = result.v_max
    x_fine = np.linspace(x_min, x_max, 200)
    lk_fit = np.array([result.cubic.predict(x) for x in x_fine])
    hf_fit = np.array([result.hf_linear.predict(x) for x in x_fine])

    fig, ax_lk = plt.subplots(figsize=_FIGSIZE, dpi=_DPI)

    # Laktat (left axis, red)
    ax_lk.plot(x_fine, lk_fit, color=_COLOR_LAKTAT, linewidth=2)
    ax_lk.plot(x_data, lk_data, "o", color=_COLOR_LAKTAT, markersize=6)
    ax_lk.set_xlabel(_x_label_de(result))
    ax_lk.set_ylabel("Laktat (mmol/l)", color=_COLOR_LAKTAT)
    ax_lk.tick_params(axis="y", labelcolor=_COLOR_LAKTAT)
    lk_max = float(np.nanmax(lk_data)) if len(lk_data) else 8.0
    ax_lk.set_ylim(0, lk_max + 1.0)
    lk_tick = 1 if lk_max <= 7 else 2
    ax_lk.set_yticks(np.arange(0, lk_max + 1.0 + 0.1, lk_tick))

    # HF (right axis, blue)
    ax_hf = ax_lk.twinx()
    ax_hf.plot(x_fine, hf_fit, color=_COLOR_HF, linewidth=2)
    ax_hf.plot(x_data, hf_data, "o", color=_COLOR_HF, markersize=6)
    ax_hf.set_ylabel("Herzfrequenz (bpm)", color=_COLOR_HF)
    ax_hf.tick_params(axis="y", labelcolor=_COLOR_HF)
    hf_clean = hf_data[~np.isnan(hf_data)]
    if len(hf_clean):
        hf_min = math.floor((float(hf_clean.min()) - 10) / 10) * 10
        hf_max = math.ceil(float(hf_clean.max()) / 10) * 10
    else:
        hf_min, hf_max = 70, 200
    ax_hf.set_ylim(hf_min, hf_max)
    ax_hf.set_yticks(np.arange(hf_min, hf_max + 1, 10))

    # X axis ticks at increment
    inc = proto.stufeninkrement
    ax_lk.set_xticks(np.arange(x_min, x_max + inc / 2, inc))
    ax_lk.set_xlim(x_min, x_max)

    fig.suptitle(result.diagram_title, fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(out_path, format="png")
    plt.close(fig)
    return out_path


def _x_label_de(result: AnalysisResult) -> str:
    sport = result.test_run.athlete.sportart
    if sport in {"lauf", "triathlon-lauf"}:
        return "Geschwindigkeit (km/h)"
    if sport in {"rad", "triathlon-rad"}:
        return "Leistung (W)"
    return "Stufe"
```

### M1.10 Report assembly

**`src/ld/report.py`**

```python
from __future__ import annotations

from pathlib import Path

from docx.shared import Cm
from docxtpl import DocxTemplate, InlineImage

from ld.types import AnalysisResult


_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "report.docx"
_PLOT_WIDTH_CM = 16.0


def render(result: AnalysisResult, plot_path: Path, out_path: Path, interpretation: dict[str, str] | None = None) -> Path:
    """Render the Word doc. If interpretation is None, fill interp slots with 'Interpretation: ausstehend'.

    Template placeholders the .docx MUST contain (Jinja syntax, typed as plain text in Word):
      Athletendaten:
        {{ athlete.vorname }}, {{ athlete.name }}, {{ athlete.alter }},
        {{ athlete.gewicht_kg }}, {{ athlete.groesse_m }}, {{ athlete.sportart_label }}
      Testprotokoll:
        {{ testprotokoll.testdatum }}, {{ testprotokoll.uhrzeit }},
        {{ testprotokoll.durchfuehrungsort }}, {{ testprotokoll.testleiter }},
        {{ testprotokoll.geraet }}, {{ testprotokoll.besonderheiten }},
        {{ testprotokoll.anfangsintensitaet }}, {{ testprotokoll.stufeninkrement }},
        {{ testprotokoll.stufendauer_min }}, {{ vmax_display }},
        {{ ausbelastung_de }}
      Test-Daten Tabelle (use {% for s in steps %}…{% endfor %}):
        {{ s.stufe }}, {{ s.intensitaet }}, {{ s.herzfrequenz_bpm }},
        {{ s.laktat_mmol }}, {{ s.rpe }}
      Intersection table (use {% for r in intersections %}…{% endfor %}):
        {{ r.laktat }}, {{ r.intensitaet }}, {{ r.pace_min_per_km }}, {{ r.herzfrequenz_bpm }}
      Zonen (use {% for z in zones %}…{% endfor %}):
        {{ z.name }}, {{ z.ziel }}, {{ z.intensitaet_min }}-{{ z.intensitaet_max }},
        {{ z.pace_max_min_per_km }}-{{ z.pace_min_min_per_km }},
        {{ z.herzfrequenz_min }}-{{ z.herzfrequenz_max }}, {{ z.rpe_min }}-{{ z.rpe_max }}
      Diagramm:
        {{ diagram }}  (InlineImage)
      Pflichtprüfungen (only if any failed):
        {% for p in failed_checks %}{{ p.message_de }}{% endfor %}
      Interpretation:
        {{ interp_zusammenfassung }}, {{ interp_schwellen }},
        {{ interp_zonen }}, {{ interp_empfehlungen }}
    """
    doc = DocxTemplate(_TEMPLATE_PATH)

    sport_labels = {
        "lauf": "Laufen",
        "rad": "Radfahren",
        "triathlon-rad": "Triathlon – Rad",
        "triathlon-lauf": "Triathlon – Lauf",
        "unspezifisch": "Unspezifisch",
    }

    interp = interpretation or {}
    context = {
        "athlete": {
            "vorname": result.test_run.athlete.vorname,
            "name": result.test_run.athlete.name,
            "alter": result.test_run.athlete.alter,
            "gewicht_kg": result.test_run.athlete.gewicht_kg,
            "groesse_m": result.test_run.athlete.groesse_m,
            "geschlecht": result.test_run.athlete.geschlecht or "—",
            "sportart_label": sport_labels[result.test_run.athlete.sportart],
            "trainingsziel": result.test_run.athlete.trainingsziel,
            "wettkampfziel": result.test_run.athlete.wettkampfziel,
            "trainingsumfang_wo": result.test_run.athlete.trainingsumfang_wo,
            "leistungsniveau": result.test_run.athlete.leistungsniveau,
        },
        "testprotokoll": {
            "testdatum": result.test_run.testprotokoll.testdatum.strftime("%d.%m.%Y"),
            "uhrzeit": result.test_run.testprotokoll.uhrzeit,
            "durchfuehrungsort": result.test_run.testprotokoll.durchfuehrungsort,
            "testleiter": result.test_run.testprotokoll.testleiter,
            "geraet": result.test_run.testprotokoll.geraet,
            "besonderheiten": result.test_run.testprotokoll.besonderheiten,
            "anfangsintensitaet": result.test_run.testprotokoll.anfangsintensitaet,
            "stufeninkrement": result.test_run.testprotokoll.stufeninkrement,
            "stufendauer_min": result.test_run.testprotokoll.stufendauer_min,
        },
        "vmax_display": round(result.v_max, 2),
        "ausbelastung_de": "ja" if result.test_run.testprotokoll.ausbelastung else "nein",
        "steps": result.test_run.steps,
        "intersections": result.intersections,
        "zones": result.zones_final,
        "diagram": InlineImage(doc, str(plot_path), width=Cm(_PLOT_WIDTH_CM)),
        "failed_checks": [p for p in result.pflichtpruefungen if not p.ok],
        "coaching": {
            "verletzungen": result.test_run.coaching.verletzungen,
            "aktuelle_probleme": result.test_run.coaching.aktuelle_probleme,
            "staerken": result.test_run.coaching.staerken,
            "schwaechen": result.test_run.coaching.schwaechen,
            "geplante_wettkaempfe": result.test_run.coaching.geplante_wettkaempfe,
            "trainernotizen": result.test_run.coaching.trainernotizen,
        },
        "interp_zusammenfassung": interp.get("zusammenfassung", "[Interpretation: ausstehend]"),
        "interp_schwellen": interp.get("schwellen", "[Interpretation: ausstehend]"),
        "interp_zonen": interp.get("zonen", "[Interpretation: ausstehend]"),
        "interp_empfehlungen": interp.get("empfehlungen", "[Interpretation: ausstehend]"),
    }

    doc.render(context)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    return out_path
```

### M1.11 Versioning

**`src/ld/versioning.py`** — identical to prior plan version. Resolves `_v1`, `_v2`, etc.

```python
from __future__ import annotations

from pathlib import Path


def next_version_path(directory: Path, basename: str, kind: str = "final") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        if kind == "final":
            p = directory / f"{basename}_v{n}.docx"
        else:
            p = directory / f"{basename}_{kind}_v{n}.docx"
        if not p.exists():
            return p
        n += 1
```

### M1.12 CLI entry point

**`src/ld/run.py`**

```python
from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from dataclasses import asdict, replace
from pathlib import Path

from dotenv import load_dotenv

from ld import io_input, plots, protocols, report, versioning
from ld.errors import LDError
from ld.types import AnalysisResult, Paths


logger = logging.getLogger("ld")


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="ld.run")
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--exclude", type=int, action="append", default=[])
    parser.add_argument("--interpret", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        paths = _resolve_paths(args.input_file, args.output_dir)
        result = _run_pipeline(paths, exclude_steps=args.exclude)
        if args.interpret:
            from ld import interpret, patch_interpretation
            interpret.run(result, paths)
            patch_interpretation.run(paths)
            print(f"Endbericht: {paths.final_docx}")
        else:
            print(f"Entwurf: {paths.draft_docx}")
            print(f"JSON:    {paths.json_full}")
            print("Mit --interpret aufrufen für eine erste Interpretation.")
        _print_check_summary(result)
        return 0
    except LDError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    except Exception:
        logger.exception("Unerwarteter Fehler")
        return 1


def _resolve_paths(input_file: Path, output_dir: Path) -> Paths:
    from ld.errors import LDInputError
    if not input_file.exists():
        raise LDInputError(f"Eingabedatei existiert nicht: {input_file}")
    basename = input_file.stem
    return Paths(
        input_xlsx=input_file,
        output_dir=output_dir,
        basename=basename,
        json_full=output_dir / f"{basename}.json",
        json_for_llm=output_dir / f"{basename}_for_llm.json",
        draft_docx=versioning.next_version_path(output_dir, basename, "draft"),
        final_docx=versioning.next_version_path(output_dir, basename, "final"),
        plots_dir=output_dir / basename,
        pickle_path=output_dir / f"{basename}.pkl",
    )


def _run_pipeline(paths: Paths, exclude_steps: list[int]) -> AnalysisResult:
    test_run = io_input.parse_input(paths.input_xlsx)
    if exclude_steps:
        kept = tuple(s for s in test_run.steps if s.stufe not in exclude_steps)
        test_run = replace(test_run, steps=kept)

    result = protocols.analyze(test_run)
    plot_path = plots.render_main_diagram(result, paths.plots_dir)
    paths.json_full.parent.mkdir(parents=True, exist_ok=True)
    paths.json_full.write_text(json.dumps(_to_jsonable(result), indent=2, default=str, ensure_ascii=False))
    paths.pickle_path.write_bytes(pickle.dumps(result))
    report.render(result, plot_path, paths.draft_docx, interpretation=None)
    return result


def _to_jsonable(result: AnalysisResult) -> dict:
    return asdict(result)


def _print_check_summary(result: AnalysisResult) -> None:
    failed = [p for p in result.pflichtpruefungen if not p.ok]
    if not failed:
        print("Pflichtprüfungen: alle OK.")
        return
    print("Pflichtprüfungen — Hinweise:")
    for p in failed:
        print(f"  • {p.message_de}")


if __name__ == "__main__":
    sys.exit(main())
```

### M1.13 Templates

- **`templates/input_template.xlsx`** — sheets `Athlet`, `Testprotokoll`, `Testdaten`, `Coaching`, pre-filled with Rainier's data so the template alone can be run end-to-end on day one. Headers + values exactly as parser expects (see M1.4).
- **`templates/report.docx`** — Word document with the placeholders documented in `report.py` docstring. Sections in German (headings as plain Word text, Jinja in body): `Athletendaten`, `Testprotokoll`, `Testdaten`, `Diagramm`, `Schwellen-Schnittpunkte`, `Trainingsbereiche`, `Pflichtprüfungen` (only if any failed), `Interpretation` (4 sub-sections: Zusammenfassung, Schwellen, Zonen, Empfehlungen), `Coaching-Notizen`.

Build the template by hand in Word. Commit both files.

### M1.14 Acceptance for M1

```bash
uv run python -m ld.run samples/RM_LD_LAUF_24_05.xlsx --output-dir samples/output
```

Expected:
- Exit 0.
- `samples/output/RM_LD_LAUF_24_05.json` contains:
  - `v_max` ≈ 11.4375 (±0.01).
  - `hf_linear.slope` ≈ 8.2, `hf_linear.intercept` ≈ 75.93 (±0.5).
  - `intersections` matches reference table from "Reference data" section above (intensitaet within ±0.01, hf within ±1).
- `samples/output/RM_LD_LAUF_24_05_draft_v1.docx` opens in Word, contains all data, diagram embedded, interpretation slots show `[Interpretation: ausstehend]`.

Repeat for `samples/SS_LD_LAUF_24_05.xlsx` (build this xlsx from the historical PDF data — see PDF page 2 transcription in BRIEF.md).

**Caveat:** the historical xlsx's polynomial was fit in Stufe-space; ours fits in v-space. Mathematically equivalent (same curve, different parameterization), so intersection values must match.

### Pitfalls

- **docxtpl Jinja in Word**: type `{{ x }}` and `{% for ... %}` as plain text, no Word fields, no autocorrect. Disable Word autocorrect-replacing of straight quotes if it interferes.
- **openpyxl date cells**: come back as `datetime`. Always `.date()`.
- **matplotlib backend**: `matplotlib.use("Agg")` MUST run before `import matplotlib.pyplot`. Module ordering in `plots.py` above is correct.
- **`np.polyfit` returns highest-degree-first**: `[a, b, c, d]` for `ax³ + bx² + cx + d`. Don't reverse.
- **`uv run`** auto-activates the venv. Do not `source .venv/bin/activate`.

---

## M2 — Standalone fallback path

### M2.1 OpenAI integration

**`src/ld/interpret.py`**

```python
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from openai import OpenAI

from ld.types import AnalysisResult, Paths


logger = logging.getLogger("ld")

_MODEL = "gpt-4o-2024-08-06"   # pinned

_PROMPT = """Du bist sportwissenschaftlicher Assistent. Verfasse eine erste Interpretation einer Leistungsdiagnostik auf Deutsch.

Regeln:
- Zitiere konkrete Werte aus den Daten (Schwellen, Zonen, abgeleitete Größen).
- Markiere alle Auffälligkeiten (Werte außerhalb erwartbarer Bereiche).
- Schlage Konsequenzen für das Training in den Zonen vor.
- Berücksichtige die in den Pflichtprüfungen markierten Hinweise.
- Berücksichtige den Kontext, den der Nutzer angegeben hat.
- Verwende keine rein fixen mmol-Schwellen — die Zonen ergeben sich aus dem Kurvenverlauf,
  Herzfrequenzverlauf und subjektiver Belastung. Du darfst die übergebenen Zonenwerte als
  Grundlage verwenden, aber bei Bedarf vorsichtiger formulieren.
- Erfinde keine Werte, die nicht in den Daten stehen.
- Format der Antwort: JSON mit den Schlüsseln "zusammenfassung", "schwellen", "zonen",
  "empfehlungen". Jeder Wert ist deutscher Fließtext (1-3 Absätze).

Daten (anonymisiert):
{data_json}

Pflichtprüfungen:
{checks}

Kontext vom Nutzer:
{context}

Antworte ausschließlich mit dem JSON-Objekt."""


def run(result: AnalysisResult, paths: Paths, user_context: str = "") -> dict[str, str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        from ld.errors import LDError
        raise LDError(
            "OPENAI_API_KEY ist nicht gesetzt. Erstelle eine .env-Datei mit OPENAI_API_KEY=... oder "
            "nutze /ld-report in Codex."
        )

    data_source = paths.json_for_llm if paths.json_for_llm.exists() else paths.json_full
    data_json = data_source.read_text()

    failed_checks = [p for p in result.pflichtpruefungen if not p.ok]
    checks_text = "\n".join(f"- {p.message_de}" for p in failed_checks) or "alle OK"

    prompt = _PROMPT.format(
        data_json=data_json,
        checks=checks_text,
        context=user_context.strip() or "(kein zusätzlicher Kontext)",
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)

    required = {"zusammenfassung", "schwellen", "zonen", "empfehlungen"}
    missing = required - parsed.keys()
    if missing:
        raise RuntimeError(f"LLM-Antwort fehlen Felder: {missing}")

    out_path = paths.output_dir / f"{paths.basename}_interpretation.json"
    out_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False))
    return parsed
```

Add deps:
```bash
uv add openai
```

### M2.2 Patch interpretation

**`src/ld/patch_interpretation.py`**

```python
from __future__ import annotations

import json
import pickle
from pathlib import Path

from ld import plots, report
from ld.errors import LDError
from ld.types import Paths


def run(paths: Paths) -> Path:
    interp_path = paths.output_dir / f"{paths.basename}_interpretation.json"
    if not interp_path.exists():
        raise LDError(f"Interpretation-JSON nicht gefunden: {interp_path}.")
    if not paths.pickle_path.exists():
        raise LDError(f"Analyse-Pickle nicht gefunden: {paths.pickle_path}.")

    interpretation = json.loads(interp_path.read_text())
    result = pickle.loads(paths.pickle_path.read_bytes())
    plot_path = paths.plots_dir / "diagramm.png"
    if not plot_path.exists():
        # Re-render if missing.
        plot_path = plots.render_main_diagram(result, paths.plots_dir)
    return report.render(result, plot_path, paths.final_docx, interpretation=interpretation)


def main(argv: list[str] | None = None) -> int:
    import argparse, sys
    parser = argparse.ArgumentParser(prog="ld.patch_interpretation")
    parser.add_argument("output_basename", type=Path,
                        help="e.g. output/Athlet_2026-05-13  (no extension)")
    args = parser.parse_args(argv)
    output_dir = args.output_basename.parent
    basename = args.output_basename.name
    from ld import versioning
    paths = Paths(
        input_xlsx=Path("/dev/null"),
        output_dir=output_dir,
        basename=basename,
        json_full=output_dir / f"{basename}.json",
        json_for_llm=output_dir / f"{basename}_for_llm.json",
        draft_docx=Path("/dev/null"),
        final_docx=versioning.next_version_path(output_dir, basename, "final"),
        plots_dir=output_dir / basename,
        pickle_path=output_dir / f"{basename}.pkl",
    )
    final = run(paths)
    print(f"Endbericht: {final}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
```

### M2.3 Acceptance for M2

```bash
uv run python -m ld.run samples/RM_LD_LAUF_24_05.xlsx --output-dir samples/output --interpret
```

- Exit 0.
- `samples/output/RM_LD_LAUF_24_05_v1.docx` exists.
- Numbers in final docx match the JSON.
- All four interpretation sections (Zusammenfassung, Schwellen, Zonen, Empfehlungen) contain non-empty German prose.

---

## M3 — Codex UX layer

### M3.1 AGENTS.md

**`AGENTS.md`** — exact content in [BRIEF.md](BRIEF.md) "Codex orchestration files" section. Copy verbatim.

### M3.2 The slash command

**`.codex/prompts/ld-report.md`** — exact content:

```markdown
Run the Leistungsdiagnostik report flow for an xlsx file in `input/`.

Steps:
1. Identify the input file. If unclear, list `input/*.xlsx` and ask the user. If only one obviously-recent file matches, pick it.

2. Run the deterministic pipeline (no --interpret yet):
   `uv run python -m ld.run input/<filename>`
   This writes `output/<basename>.json`, `output/<basename>_for_llm.json` (M4+),
   `output/<basename>.pkl`, and `output/<basename>_draft_v<n>.docx`.

3. Read `output/<basename>_for_llm.json` (fall back to `output/<basename>.json` if it doesn't exist). Present in German:
   - Sportart and Athletenname (vorname only).
   - v_max with 2 decimals.
   - Lactate intersection table — render as a short markdown table (Laktat | v | Pace | HF).
   - Suggested zones — short table (Z2-Z6: Intensitäts-Bereich, HF-Bereich).
   - Pflichtprüfungen failures: list each `message_de` with a "⚠️" prefix; if all OK, say "Alle Pflichtprüfungen OK".
   - Plot file path: `output/<basename>/diagramm.png`.

4. Ask the user in German:

   "Möchtest du die vorgeschlagenen Zonen so übernehmen oder anpassen?
   Falls anpassen: gib die neuen Grenzen an (z.B. 'Z3 bis 9.0', 'Z5 bis 12.5').
   Gibt es weiteren Kontext für die Interpretation? (z.B. 'erste Session der Saison')
   Enter zum Bestätigen und Übernehmen."

5. If the user provides zone adjustments:
   - Parse the adjustments into explicit boundary values.
   - Edit `output/<basename>.pkl` is NOT supported by Codex (binary file); instead:
     * Edit `output/<basename>.json` only to update `zones_final`.
     * Write a small Python helper invocation:
       `uv run python -c "from ld import zones_override; zones_override.apply('output/<basename>', {'Z3_upper': 9.0, ...})"`
     This helper updates the pickle's zones_final and re-renders the draft docx.
   Then re-read the JSON to confirm new zones.

6. Pass control to the LLM-interpretation step:
   - Build a context string from the user's free-text answer.
   - Invoke the interpretation step:
     `uv run python -c "from ld.interpret import run; from ld.run import _resolve_paths; import pickle; ..."`
     OR simpler: `uv run python -m ld.run input/<filename> --interpret` re-runs and writes a fresh `_v<n>` final docx.
     The simpler path is preferred for M3 v1; revisit if it's too slow.

   In practice: call `uv run python -m ld.run input/<filename> --interpret --output-dir output`. This re-uses the existing JSON and pickle if present; the interpretation step picks up the (possibly user-overridden) zones from the .pkl.

7. Tell the user in German: "Endbericht: output/<basename>_v<n>.docx ist fertig."

If the user says "redo ohne Stufe N" or similar, re-run step 2 with `--exclude N` and restart from step 3.
```

### M3.3 Zone override helper

**`src/ld/zones_override.py`** (new — implement in M3, not M1, to keep M1 strict).

```python
from __future__ import annotations

import pickle
from dataclasses import replace
from pathlib import Path

from ld.types import AnalysisResult, TrainingZone


def apply(basename_path: str, overrides: dict[str, float]) -> None:
    """basename_path = 'output/<basename>' (no extension).
    overrides keys: 'Z2_upper', 'Z3_upper', 'Z4_upper', 'Z5_upper'.
    Each value sets the upper bound of the named zone (and implicitly the lower of the next).
    """
    base = Path(basename_path)
    pkl_path = Path(f"{base}.pkl")
    result: AnalysisResult = pickle.loads(pkl_path.read_bytes())

    new_zones = list(result.zones_final)
    name_to_idx = {z.name: i for i, z in enumerate(new_zones)}
    # Apply upper bounds; ripple lower of next zone.
    for key, value in overrides.items():
        zone_name = key.split("_")[0]
        idx = name_to_idx.get(zone_name)
        if idx is None:
            continue
        new_zones[idx] = replace(new_zones[idx], intensitaet_max=value)
        if idx + 1 < len(new_zones):
            new_zones[idx + 1] = replace(new_zones[idx + 1], intensitaet_min=value)
    result = replace(result, zones_final=tuple(new_zones))
    pkl_path.write_bytes(pickle.dumps(result))
    # Re-render draft to reflect new zones
    from ld import plots, report, versioning
    plot_path = result.test_run  # placeholder; actually use plots.render_main_diagram(result, base)
    plot_path = plots.render_main_diagram(result, base)
    draft = versioning.next_version_path(base.parent, base.name, "draft")
    report.render(result, plot_path, draft)
```

### M3.4 Acceptance for M3

- Christopher launches Codex in the repo root.
- `/ld-report` against a historical case.
- Codex shows the suggested zones, intersection table, Pflichtprüfungen list.
- Christopher answers "Z3 bis 9.5; Kontext: erste Session der Saison" → Codex applies the override, regenerates, drafts interpretation, produces final docx.
- Numbers in final docx match the JSON; zones reflect the override.

### Pitfalls

- The slash command shell-quoting through Codex can break on `uv run python -c "..."`. Keep the command as a single line, escape carefully. If it gets unwieldy, add a small CLI wrapper `src/ld/zones_cli.py` that takes overrides as args and avoids inline Python.
- Codex may need approval for `uv run` each session. Accept once.

---

## M4 — Privacy + versioning polish

### M4.1 Redacted JSON

**`src/ld/redact.py`**

```python
from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

from ld.types import AnalysisResult


def write_redacted(result: AnalysisResult, out_path: Path) -> Path:
    data = asdict(result)
    athlete = data["test_run"]["athlete"]
    athlete["vorname"] = "Athlet:in"
    athlete["name"] = "X"
    athlete["geburtsjahr"] = None
    athlete["alter_keep"] = result.test_run.athlete.alter
    out_path.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    return out_path
```

Wire in `run.py._run_pipeline` after writing `json_full`:
```python
from ld import redact
redact.write_redacted(result, paths.json_for_llm)
```

Update `interpret.py` to prefer `paths.json_for_llm` (already does).

### M4.2 Acceptance for M4

- `grep -i 'rainier\|matzinger' samples/output/RM_LD_LAUF_24_05_for_llm.json` returns nothing.
- The final docx still contains "Rainier Matzinger".
- Two consecutive runs → `_v1` and `_v2`, no overwrites.

---

## M5 — Test net

### M5.1 Unit tests

**`tests/unit/test_common.py`** — golden values for math helpers. Examples:

```python
import numpy as np
from ld.protocols._common import (
    LAKTAT_TARGETS, _pace_min_per_km, fit_cubic_laktat, fit_linear_hf,
)
from ld.types import TestStep


_RAINIER = (
    TestStep(stufe=1, intensitaet=7.0, herzfrequenz_bpm=133, laktat_mmol=1.9, rpe=9),
    TestStep(stufe=2, intensitaet=8.0, herzfrequenz_bpm=141, laktat_mmol=2.8, rpe=9),
    TestStep(stufe=3, intensitaet=9.0, herzfrequenz_bpm=150, laktat_mmol=3.0, rpe=14),
    TestStep(stufe=4, intensitaet=10.0, herzfrequenz_bpm=159, laktat_mmol=3.8, rpe=16),
    TestStep(stufe=5, intensitaet=11.0, herzfrequenz_bpm=167, laktat_mmol=5.2, rpe=17),
    TestStep(stufe=6, intensitaet=12.0, herzfrequenz_bpm=173, laktat_mmol=7.9, rpe=18),
)


def test_hf_linear_fit():
    fit = fit_linear_hf(_RAINIER)
    assert abs(fit.slope - 8.2) < 0.3
    assert abs(fit.intercept - 75.9) < 1.0


def test_cubic_passes_through_data_points_approximately():
    fit = fit_cubic_laktat(_RAINIER)
    for s in _RAINIER:
        assert abs(fit.predict(s.intensitaet) - s.laktat_mmol) < 0.6


def test_pace_conversion():
    assert _pace_min_per_km(12.0) == "05:00"
    assert _pace_min_per_km(10.0) == "06:00"
    assert _pace_min_per_km(11.368) == "05:16"
```

### M5.2 Protocol snapshot tests

**`tests/protocols/test_lauf.py`** — snapshot against expected JSON.

```python
import json
from pathlib import Path

from ld import io_input, protocols
from dataclasses import asdict


FIXTURES = Path(__file__).parent / "fixtures" / "lauf"


def test_rainier_snapshot():
    test_run = io_input.parse_input(FIXTURES / "rainier.xlsx")
    result = protocols.analyze(test_run)
    actual = json.loads(json.dumps(asdict(result), default=str))
    expected = json.loads((FIXTURES / "rainier_expected.json").read_text())
    # Compare key numbers (some fields like 'zones_final' may differ if M3 overrides applied later)
    assert abs(actual["v_max"] - 11.4375) < 0.01
    for actual_row, expected_row in zip(actual["intersections"], expected["intersections"]):
        assert abs(actual_row["intensitaet"] - expected_row["intensitaet"]) < 0.05 if actual_row["intensitaet"] else True
```

Fixture: `tests/protocols/fixtures/lauf/rainier.xlsx` = new-format xlsx with Rainier's data; `rainier_expected.json` = expected analysis result.

### M5.3 E2E smoke

**`tests/e2e/test_smoke.py`**

```python
import json
import subprocess
import sys
from pathlib import Path

import docx2txt


def test_full_pipeline(tmp_path):
    repo = Path(__file__).parent.parent.parent
    fixture = repo / "tests" / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"
    result = subprocess.run(
        [sys.executable, "-m", "ld.run", str(fixture), "--output-dir", str(tmp_path)],
        capture_output=True, text=True, check=True,
    )
    assert result.returncode == 0
    data = json.loads((tmp_path / "rainier.json").read_text())
    docx_path = next(tmp_path.glob("rainier_draft_v*.docx"))
    text = docx2txt.process(str(docx_path))
    # The v_max should be in the doc.
    assert "11" in text  # weak but real
    # Some intersection value should appear.
    for row in data["intersections"]:
        if row["intensitaet"]:
            assert str(round(row["intensitaet"], 1)) in text or str(round(row["intensitaet"])) in text
            break
```

### M5.4 Sanity bug check

Manually change `LAKTAT_TARGETS` to `(2.0, 4.0)` in `_common.py`, run `uv run pytest`. The snapshot test must fail. Revert. Document outcome in `notes/test_sanity.md`.

### M5.5 Acceptance

- `uv run pytest` green.
- Sanity check catches the deliberate bug.

---

## M6 — Onboarding handoff

Same as prior plan version: install Node, uv, Codex CLI, clone repo, `uv sync`, desktop `.command` shortcut, walk through `/ld-report` against pre-filled template + a real case, including one zone adjustment.

Acceptance: sister solo runs `/ld-report` end-to-end and adjusts at least one zone via dialogue.

---

## M7 — RAD + UNSPEZIFISCH protocols

For each new protocol:
- Add `src/ld/protocols/<name>.py` following `lauf.analyze` shape.
- Add to `ANALYZERS` dispatch.
- For RAD: x-axis is "Leistung (W)"; no pace conversion; intersection table has columns Laktat / Leistung / HF.
- For UNSPEZIFISCH: x-axis is "Stufe"; intersection table has Laktat / Stufe / HF.
- Add a sport selector handling to `templates/input_template.xlsx` (or distribute three template variants — simpler).
- Add report.docx variants OR conditional sections in one template.
- Snapshot + historical-case validation per protocol.

Acceptance: numbers match her hand-calculations on 2-3 historical cases per new protocol.

---

## M8 — Usage guide

**`USAGE_GUIDE.md`** at repo root, German, written from the real tool. Sections:

```markdown
# Anleitung — Leistungsdiagnostik-Werkzeug

## Was das Werkzeug macht
## Voraussetzungen (einmalig)
## Einen Bericht erstellen — Schritt für Schritt
## Häufige Situationen
  ### Eine Stufe weglassen
  ### Zonen anpassen
  ### Bericht neu erstellen
  ### Eingabedatei wurde geändert
## Wenn etwas schiefgeht
  ### "Fehler: …" Meldungen (mit Übersetzung der häufigsten LDInputError-Texte)
  ### Codex zeigt nichts an
  ### Aktualisierungen einspielen
## Datenschutz
## Wer hilft
```

**Critical:** write from the *real tool*, not the plan. After M1-M7 are validated, the implementer should actually run `/ld-report` end-to-end against the Rainier and Sarah cases and document exactly what appears, copy-pasting real error messages and screenshots of the Word output where helpful.

### Acceptance for M8

- Sister reads `USAGE_GUIDE.md` cold (Christopher not present) and runs `/ld-report` on a fresh real case end-to-end. Any question she has → that question becomes a new section. Iterate until clean.

---

## Open decisions to resolve during build

1. **RPE scale**: spec docx uses 0-10; historical xlsx uses 6-20. Pin one in the input template (recommend 6-20 since that's what she actually used) and document the choice in `templates/input_template.xlsx`.
2. **Repo hosting**: Christopher decides — private GitHub recommended.
3. **Codex version pin**: confirm a working version on Christopher's machine; record in README.

## Risks and mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Codex CLI breaking change | Medium | M2 fallback covers; pin version in README |
| Sister's xlsx layout in M0 differs from spec | Medium | Build template that mirrors the spec doc; if she insists on different layout, parser is contained in `io_input.py` |
| Spec ambiguous on RPE scale | Low (caught in M0) | Pin in template |
| Polynomial fit ill-conditioned for atypical data | Low | Catch in M1; if cubic fails, fall back to quadratic with a logged warning |
| Word template breaks on long German words | Low | docxtpl handles; e2e smoke catches |

## Out of scope

- Visual slider UI (deferred; conversational adjustment in M3 covers the spec's "Schieberegler" requirement for v1).
- Trend across multiple tests of one athlete.
- Multi-language output.
- Athlete database.
- Web UI.

## "Stop here" criteria

Plan ends at M8. Streamlit slider tool only if M6's conversational zone adjustment proves too clunky after a few weeks of real use. Don't pre-build it.
