from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


# === Athlete & test setup ===

@dataclass(frozen=True)
class Athlete:
    sportart: str                 # "lauf" | "rad" | "triathlon-rad" | "triathlon-lauf" | "unspezifisch"
    vorname: str
    name: str
    geburtsjahr: int | None       # Optional per Anna 2026-05-13 feedback (privacy/age omission)
    geschlecht: str | None        # "m" | "w" | "d" | None
    gewicht_kg: float
    groesse_m: float              # meters
    trainingsziel: str
    wettkampfziel: str
    trainingsumfang_wo: str
    leistungsniveau: str
    email: str | None = None      # Anna 2026-05-13 — added for athlete contact

    @property
    def alter(self) -> int | None:
        """Returns None if geburtsjahr is omitted (e.g. for privacy)."""
        if self.geburtsjahr is None:
            return None
        return date.today().year - self.geburtsjahr


@dataclass(frozen=True)
class Testprotokoll:
    testdatum: date
    uhrzeit: str                                # "HH:MM"
    durchfuehrungsort: str
    testleiter: str
    geraet: str
    # Renamed from "anfangsintensitaet" per Anna 2026-05-13 (more natural German term).
    # Units depend on sportart: km/h (lauf), W (rad), Stufe (unspezifisch).
    anfangsbelastung: float
    stufeninkrement: float
    stufendauer_min: float
    stufenlaenge_m: int | None
    besonderheiten: str
    letzte_stufe_vollstaendig: bool
    dauer_letzte_stufe_min: float | None
    ausbelastung: bool
    # Post-exertion lactate (optional) — Anna 2026-05-13 added these to track recovery.
    nachbelastungslaktat_3min_mmol: float | None = None
    nachbelastungslaktat_5min_mmol: float | None = None


@dataclass(frozen=True)
class TestStep:
    """One measured step. intensitaet has units depending on sportart."""
    stufe: int                 # 1-based step index
    intensitaet: float
    herzfrequenz_bpm: int | None
    laktat_mmol: float | None
    rpe: int | None            # 0-10 (Borg CR10) — Anna 2026-05-13 Round 2


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
    """Laktat = a*x^3 + b*x^2 + c*x + d, x in intensitaet-space."""
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
    ziel: str                     # German label
    rpe_min: int
    rpe_max: int
    intensitaet_min: float | None
    intensitaet_max: float | None
    pace_min_min_per_km: str | None
    pace_max_min_per_km: str | None
    herzfrequenz_min: int | None
    herzfrequenz_max: int | None
    # Render hints (set by zones.suggest_zones, consumed by report.py):
    is_max_zone: bool = False     # Z6: render Intensität/HF/Pace as "MAX"
    is_open_lower: bool = False   # Z1: render Intensität/HF as "< x", Pace as "> p"


@dataclass(frozen=True)
class PflichtpruefungResult:
    """One plausibility check outcome."""
    name: str
    ok: bool
    message_de: str               # empty if ok=True


@dataclass(frozen=True)
class AnalysisResult:
    test_run: TestRun
    v_max: float
    cubic: CubicFit
    hf_linear: LinearFit
    intersections: tuple[IntersectionRow, ...]
    zones_suggested: tuple[TrainingZone, ...]
    zones_final: tuple[TrainingZone, ...]
    pflichtpruefungen: tuple[PflichtpruefungResult, ...]
    diagram_title: str


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
    pickle_path: Path
