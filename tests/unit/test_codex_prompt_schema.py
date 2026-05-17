"""Codex prompt enforces the Round 2 JSON schema — grep-level smoke test.

If someone edits the prompt and removes one of the required keys, this test
catches it before it ships."""
from __future__ import annotations

from pathlib import Path


PROMPT = Path(__file__).parent.parent.parent / ".codex" / "prompts" / "ld-report.md"


def test_prompt_lists_all_five_interpretation_keys():
    src = PROMPT.read_text()
    for key in (
        "zusammenfassung",
        "schwellen",
        "coaching_ausblick_3_4_wochen",
        "ernaehrung",
        "risiko",
    ):
        assert f'"{key}"' in src, f"Codex prompt missing key {key!r}"


def test_prompt_mentions_rpe_cr10():
    """RPE migration must be visible in the prompt so Codex doesn't reach for
    Borg 6-20 phrasing."""
    src = PROMPT.read_text().lower()
    assert "cr10" in src or "0-10" in src


def test_prompt_warns_against_invented_weekplans():
    """Anna 2026-05-13 Round 2 — 'Keine erfundenen Trainingspläne'."""
    src = PROMPT.read_text().lower()
    # Match either the explicit warning or the equivalent rule.
    assert "wochenplan" in src or "trainingsplan" in src or "erfinden" in src or "erfundene" in src


def test_prompt_requires_beispielwoche_in_coaching_ausblick():
    """Anna 2026-05-17 Round 2.1 decision #4 — the 3-4-Wochen-Ausblick
    must include a concrete Beispielwoche (Mo-So sample week)."""
    src = PROMPT.read_text().lower()
    assert "beispielwoche" in src, "Codex prompt must request a Beispielwoche"
    # Sanity-check: the Mo-So week format should be hinted at.
    assert "mo:" in src or "montag" in src or "mo-so" in src, \
        "Prompt should show the Mo-So sample-week format"


def test_prompt_allows_short_ernaehrung():
    """Anna 2026-05-17 decision #5 — Ernährung may be short when there's
    little to say (not a hard 120-word floor)."""
    src = PROMPT.read_text().lower()
    # Either the word cap was relaxed (1-100 phrasing) or the explicit
    # 'kurz halten' allowance is present.
    assert "1-100" in src or "kurz halten" in src or "ruhig kurz" in src
