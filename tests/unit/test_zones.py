from __future__ import annotations

from ld.types import IntersectionRow, LinearFit
from ld.zones import suggest_zones


_HF_LINEAR = LinearFit(slope=8.0, intercept=80.0)


def _row(laktat: float, intensitaet: float | None) -> IntersectionRow:
    """Build an IntersectionRow stub for zone tests."""
    if intensitaet is None:
        return IntersectionRow(laktat=laktat, intensitaet=None, pace_min_per_km=None, herzfrequenz_bpm=None)
    return IntersectionRow(
        laktat=laktat,
        intensitaet=intensitaet,
        pace_min_per_km=None,
        herzfrequenz_bpm=int(round(_HF_LINEAR.predict(intensitaet))),
    )


def _full_rows() -> tuple[IntersectionRow, ...]:
    """A complete intersection set with valid roots for 2.0/3.0/4.0 mmol."""
    return (
        _row(1.0, None),
        _row(1.5, None),
        _row(2.0, 9.0),
        _row(2.5, 9.5),
        _row(3.0, 10.0),
        _row(4.0, 11.0),
        _row(6.0, 12.0),
        _row(8.0, 13.0),
    )


def test_z1_only_when_z2_valid_present():
    """Per Anna 2026-05-13: Z1 is only emitted when Z2 has a valid upper bound."""
    zones = suggest_zones(_full_rows(), _HF_LINEAR, v_max=13.5, is_lauf=True)
    names = [z.name for z in zones]
    assert names == ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6"]


def test_z1_omitted_when_z2_upper_missing():
    """If lk=2.0 has no in-range root, Z1 has no anchor — omit it entirely."""
    rows = tuple(_row(t, None) if t == 2.0 else _row(t, None) for t in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0))
    # Override 3.0/4.0 to non-None so Z3/Z4 still produce values; the missing
    # piece is only Z2-upper.
    rows = (
        _row(1.0, None), _row(1.5, None), _row(2.0, None),
        _row(2.5, None), _row(3.0, 10.0), _row(4.0, 11.0),
        _row(6.0, 12.0), _row(8.0, 13.0),
    )
    zones = suggest_zones(rows, _HF_LINEAR, v_max=13.5, is_lauf=True)
    names = [z.name for z in zones]
    assert "Z1" not in names
    assert names[0] == "Z2"


def test_z1_has_open_lower_and_anchored_upper():
    """Z1 shape: no lower bound, upper bound = v at 2.0 mmol; is_open_lower flag set."""
    zones = suggest_zones(_full_rows(), _HF_LINEAR, v_max=13.5, is_lauf=True)
    z1 = next(z for z in zones if z.name == "Z1")
    assert z1.intensitaet_min is None
    assert z1.intensitaet_max == 9.0
    assert z1.is_open_lower is True
    assert z1.is_max_zone is False
    # Pace anchor: Z1 means "slower than the pace at lk=2.0", so pace_min_min_per_km
    # holds the boundary pace (template renders "> {pace_min_min_per_km}").
    assert z1.pace_min_min_per_km is not None
    assert z1.pace_max_min_per_km is None
    # HF max = HF at v_lk2; no HF min (open lower).
    assert z1.herzfrequenz_min is None
    assert z1.herzfrequenz_max == int(round(_HF_LINEAR.predict(9.0)))


def test_z6_is_max_zone_flag_set():
    """Z6 must be marked is_max_zone=True so the report renders Intensität / HF /
    Pace as the literal word 'MAX'."""
    zones = suggest_zones(_full_rows(), _HF_LINEAR, v_max=13.5, is_lauf=True)
    z6 = next(z for z in zones if z.name == "Z6")
    assert z6.is_max_zone is True
    assert z6.is_open_lower is False


def test_z5_z6_rpe_fixed_values():
    """Per Anna 2026-05-13: Z5 RPE fixed at 9, Z6 RPE fixed at 10."""
    zones = suggest_zones(_full_rows(), _HF_LINEAR, v_max=13.5, is_lauf=True)
    z5 = next(z for z in zones if z.name == "Z5")
    z6 = next(z for z in zones if z.name == "Z6")
    assert z5.rpe_min == 9 and z5.rpe_max == 9
    assert z6.rpe_min == 10 and z6.rpe_max == 10


def test_z2_bounds_anchored_to_lk2_and_lk3():
    """Heuristic anchors: Z2 [None .. v_lk2], Z3 [v_lk2 .. v_lk3], Z4 [v_lk3 .. v_lk4]."""
    zones = suggest_zones(_full_rows(), _HF_LINEAR, v_max=13.5, is_lauf=True)
    by_name = {z.name: z for z in zones}
    assert by_name["Z2"].intensitaet_min is None
    assert by_name["Z2"].intensitaet_max == 9.0
    assert by_name["Z3"].intensitaet_min == 9.0
    assert by_name["Z3"].intensitaet_max == 10.0
    assert by_name["Z4"].intensitaet_min == 10.0
    assert by_name["Z4"].intensitaet_max == 11.0
    assert by_name["Z5"].intensitaet_min == 11.0
    assert by_name["Z5"].intensitaet_max == 13.5  # v_max


def test_round3_customer_friendly_zone_labels():
    """Round 3 (Anna 2026-05-17): Z3 and Z6 ziel-Labels updated for clarity.
    Z3 was 'metabolische Stabilität', Z6 was 'neuromuskulär' — both replaced."""
    zones = suggest_zones(_full_rows(), _HF_LINEAR, v_max=13.5, is_lauf=True)
    by_name = {z.name: z for z in zones}
    assert by_name["Z3"].ziel == "Aerobe Entwicklung"
    assert by_name["Z6"].ziel == "Sprint- und Maximalreize"
    # No regression on the still-valid old labels:
    assert by_name["Z2"].ziel == "aerobe Basis"
    assert by_name["Z4"].ziel == "Schwellenleistung"
    assert by_name["Z5"].ziel == "VO2max-Reize"


def test_z1_collapsed_when_v_lk2_equals_v_lk3():
    """Round 3 (Anna 2026-05-17): when Z2 has no diagnostic range (v_lk2
    equals v_lk3), Z1 should render with empty Intensität/Pace/HF — i.e.
    `is_collapsed_with_z2=True` — instead of repeating Z2's bounds."""
    # Force lk=2.0 and lk=3.0 to the same x-value: Z2 collapses to a point,
    # which means Z1 has no diagnostic content distinct from Z2.
    rows = (
        _row(1.0, None),
        _row(1.5, None),
        _row(2.0, 9.0),
        _row(2.5, 9.0),
        _row(3.0, 9.0),     # SAME as Z2 anchor
        _row(4.0, 11.0),
        _row(6.0, 12.0),
        _row(8.0, 13.0),
    )
    zones = suggest_zones(rows, _HF_LINEAR, v_max=13.5, is_lauf=True)
    by_name = {z.name: z for z in zones}
    assert "Z1" in by_name, "Z1 should still be present, just collapsed"
    z1 = by_name["Z1"]
    assert z1.is_collapsed_with_z2 is True
    assert z1.is_open_lower is False
    # Empty fields → renderer shows "—" instead of duplicating Z2 anchor.
    assert z1.intensitaet_max is None
    assert z1.pace_min_min_per_km is None
    assert z1.herzfrequenz_max is None


def test_z1_not_collapsed_in_normal_case():
    """Normal Rainier-like spread: Z1 stays open-lower, NOT collapsed."""
    zones = suggest_zones(_full_rows(), _HF_LINEAR, v_max=13.5, is_lauf=True)
    z1 = next(z for z in zones if z.name == "Z1")
    assert z1.is_collapsed_with_z2 is False
    assert z1.is_open_lower is True
    assert z1.intensitaet_max == 9.0
