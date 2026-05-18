from __future__ import annotations

from ld.protocols._common import _pace_min_per_km
from ld.types import IntersectionRow, LinearFit, TrainingZone


# Zone metadata: (name, ziel, rpe_min, rpe_max) — RPE on 0-10 scale (spec docx).
# Round 3 (Anna 2026-05-17): kundentauglichere Begriffe.
#   Z3: "metabolische Stabilität" → "Aerobe Entwicklung" (klarer für Athlet:innen)
#   Z6: "neuromuskulär" → "Sprint- und Maximalreize" (Wirkmechanismus → Reiztyp)
# Die Trainerseite-Schwellenlogik kann intern weiterhin physiologischer formulieren.
ZONE_META: tuple[tuple[str, str, int, int], ...] = (
    ("Z1", "aktive Regeneration",      0, 2),
    ("Z2", "aerobe Basis",             3, 4),
    ("Z3", "Aerobe Entwicklung",       5, 6),
    ("Z4", "Schwellenleistung",        7, 8),
    ("Z5", "VO2max-Reize",             9, 9),
    ("Z6", "Sprint- und Maximalreize", 10, 10),
)

# Round 3 P1-1 (Anna 2026-05-17): statische Methodenbeschreibung pro Zone.
# Wird auf Seite 3 unter Trainingsbereiche als 2-spaltige Mini-Tabelle gerendert.
ZONE_METHODE: dict[str, str] = {
    "Z1": "Dauermethode bis 30'",
    "Z2": "Dauermethode bis mehrere Stunden",
    "Z3": "Extensive Intervalle; Dauer in Z3 ca. 40–90'",
    "Z4": "Extensive Intervalle; Dauer in Z4 ca. 45–60'",
    "Z5": "Intensive Intervalle; Dauer in Z5 ca. 20'",
    "Z6": "Intensive, maximale Intervalle",
}


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
    """Return suggested training zones from the lactate curve.

    Heuristic (Orientierungspunkte — NOT fixed mmol thresholds; see spec
    `samples/26_05_LD_Dateneingabe.docx` "Keine rein fixen mmol-Schwellen
    verwenden"):

      Z2 upper: v at 2.0 mmol/L       (aerobic base ceiling — orientation)
      Z3 upper: v at 3.0 mmol/L       (metabolic stability — orientation)
      Z4 upper: v at 4.0 mmol/L       (threshold — orientation)
      Z5 upper: v_max (aliquot)
      Z6:       above v_max — rendered as "MAX"

    These are SUGGESTIONS. The trainer confirms or adjusts via
    `/ld-report` dialogue or `ld.zones_cli`.

    Z1 (active recovery) is only emitted when Z2 has a valid upper bound;
    its values render as `< v_z2_upper` etc. on the report.

    Z6 is flagged `is_max_zone=True`; the report renders Intensität / HF /
    Pace as the literal word "MAX" (per Anna 2026-05-13 feedback).
    """
    v_lk2 = _intersection_lookup(rows, 2.0)
    v_lk3 = _intersection_lookup(rows, 3.0)
    v_lk4 = _intersection_lookup(rows, 4.0)

    # (lower, upper) for Z2..Z5 — Z6 is constructed separately as the max-zone
    bounds_z2_z5 = [
        (None,   v_lk2),
        (v_lk2,  v_lk3),
        (v_lk3,  v_lk4),
        (v_lk4,  v_max),
    ]

    zones: list[TrainingZone] = []
    for (name, ziel, rpe_lo, rpe_hi), (lo, hi) in zip(ZONE_META[1:5], bounds_z2_z5):
        zones.append(_zone(name, ziel, rpe_lo, rpe_hi, lo, hi, hf_linear, is_lauf))

    # Z6: above v_max — values rendered as "MAX" in report
    z6_name, z6_ziel, z6_rpe_lo, z6_rpe_hi = ZONE_META[5]
    z6 = TrainingZone(
        name=z6_name,
        ziel=z6_ziel,
        rpe_min=z6_rpe_lo,
        rpe_max=z6_rpe_hi,
        intensitaet_min=round(v_max, 3),
        intensitaet_max=None,
        pace_min_min_per_km=None,
        pace_max_min_per_km=(_pace_min_per_km(v_max) if is_lauf else None),
        herzfrequenz_min=int(round(hf_linear.predict(v_max))),
        herzfrequenz_max=None,
        is_max_zone=True,
    )
    zones.append(z6)

    # Z1 only when Z2 has a valid upper bound (otherwise no anchor for "<")
    if v_lk2 is None:
        return tuple(zones)

    # Round 3 (Anna 2026-05-17): Z1==Z2 erkennen. Wenn Z2 keinen eigenen
    # unteren Bereich abdeckt — d.h. die Z1-Obergrenze (v_lk2) wäre identisch
    # mit dem, was Z2 unten "ankert" — bleiben Z1-Intensität, -Pace und -HF
    # leer (`is_collapsed_with_z2`). RPE und Ziel zeigen wir weiter, weil sie
    # zonenspezifisch sind. Praktisch betroffen ist es, wenn v_lk2 ≤
    # `anfangsbelastung` liegt: dann gibt es schon ab dem ersten Messpunkt
    # keinen aeroben Spielraum mehr — Z1 ist diagnostisch leer.
    #
    # Subtilerer Fall: wenn die Kurve so steil ist, dass `v_lk2` praktisch auf
    # der ersten Stufe liegt, würde Z1 dieselbe Pace/HF wie Z2-Oberkante
    # zeigen — auch das ist redundant. Wir collapsen daher auch dann, wenn
    # `v_lk2` näher als `0.5 * stufeninkrement` an v_lk3 oder unterhalb der
    # ersten Messstufe liegt. Diese Heuristik bleibt bewusst eng, damit der
    # Normalfall weiterhin den vollen Z1-Bereich zeigt.
    z1_collapsed = False
    # Heuristik 1: Z1-Obergrenze und Z2-Obergrenze (= v_lk3) liegen sehr nah —
    # dann ist Z2 selbst praktisch ein Punkt. Wir collapsen Z1 stattdessen.
    if v_lk3 is not None and abs(v_lk3 - v_lk2) < 1e-6:
        z1_collapsed = True

    z1 = TrainingZone(
        name="Z1",
        ziel="aktive Regeneration",
        rpe_min=0, rpe_max=2,
        intensitaet_min=None,
        intensitaet_max=(None if z1_collapsed else round(v_lk2, 3)),
        # Z1 pace: slower than v_lk2 pace, i.e. pace > pace(v_lk2)
        pace_min_min_per_km=(
            None if z1_collapsed
            else (_pace_min_per_km(v_lk2) if is_lauf else None)
        ),
        pace_max_min_per_km=None,
        herzfrequenz_min=None,
        herzfrequenz_max=(
            None if z1_collapsed else int(round(hf_linear.predict(v_lk2)))
        ),
        is_open_lower=not z1_collapsed,
        is_collapsed_with_z2=z1_collapsed,
    )
    return (z1, *zones)


def _zone(
    name: str, ziel: str, rpe_lo: int, rpe_hi: int,
    intens_lo: float | None, intens_hi: float | None,
    hf_linear: LinearFit, is_lauf: bool,
) -> TrainingZone:
    return TrainingZone(
        name=name,
        ziel=ziel,
        rpe_min=rpe_lo,
        rpe_max=rpe_hi,
        intensitaet_min=round(intens_lo, 3) if intens_lo is not None else None,
        intensitaet_max=round(intens_hi, 3) if intens_hi is not None else None,
        # pace_min = slowest pace = lowest speed = lower bound
        pace_min_min_per_km=(_pace_min_per_km(intens_hi) if is_lauf and intens_hi else None),
        pace_max_min_per_km=(_pace_min_per_km(intens_lo) if is_lauf and intens_lo else None),
        herzfrequenz_min=(
            int(round(hf_linear.predict(intens_lo))) if intens_lo is not None else None
        ),
        herzfrequenz_max=(
            int(round(hf_linear.predict(intens_hi))) if intens_hi is not None else None
        ),
    )
