"""Tests for the visual zone-tool helpers.

The Streamlit UI itself is not tested (would need browser automation); we
cover the pure-Python override-chaining logic, which is what reorders zone
bounds when the user moves a slider."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Skip the whole module if streamlit isn't installed.
streamlit = pytest.importorskip("streamlit")

from ld import io_input, protocols
from ld.zone_tool import _apply_overrides_to_result, _zone_upper


FIXTURE = Path(__file__).parent.parent / "protocols" / "fixtures" / "lauf" / "rainier.xlsx"


def _result():
    return protocols.analyze(io_input.parse_input(FIXTURE))


def test_zone_upper_lookup():
    r = _result()
    z2_upper = _zone_upper(r.zones_final, "Z2")
    assert z2_upper is not None
    # Rainier: v_lk2 ≈ 7.065
    assert abs(z2_upper - 7.065) < 0.01


def test_apply_overrides_chains_lower_bounds():
    """When the user drags Z3 upper, Z4 lower auto-shifts to match."""
    r = _result()
    new = _apply_overrides_to_result(r, z2_u=7.0, z3_u=8.5, z4_u=10.0, z5_u=11.5)
    by_name = {z.name: z for z in new.zones_final}

    # Upper bounds reflect slider values
    assert by_name["Z2"].intensitaet_max == 7.0
    assert by_name["Z3"].intensitaet_max == 8.5
    assert by_name["Z4"].intensitaet_max == 10.0
    assert by_name["Z5"].intensitaet_max == 11.5

    # Lower bounds chain: each zone's lower = previous zone's new upper
    assert by_name["Z3"].intensitaet_min == 7.0  # = Z2 upper
    assert by_name["Z4"].intensitaet_min == 8.5  # = Z3 upper
    assert by_name["Z5"].intensitaet_min == 10.0  # = Z4 upper
    # Z6 lower = Z5 new upper
    assert by_name["Z6"].intensitaet_min == 11.5


def test_apply_overrides_preserves_open_lower_and_max_zone_flags():
    r = _result()
    new = _apply_overrides_to_result(r, z2_u=7.5, z3_u=9.0, z4_u=10.5, z5_u=11.5)
    by_name = {z.name: z for z in new.zones_final}
    assert by_name["Z1"].is_open_lower is True
    assert by_name["Z6"].is_max_zone is True


def test_z1_upper_follows_new_z2_upper():
    """Z1's display upper bound mirrors Z2's new upper after a slider move."""
    r = _result()
    new = _apply_overrides_to_result(r, z2_u=8.2, z3_u=9.0, z4_u=10.5, z5_u=11.5)
    z1 = next(z for z in new.zones_final if z.name == "Z1")
    assert z1.intensitaet_max == 8.2
