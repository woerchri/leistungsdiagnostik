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


def test_prompt_forbids_beispielwoche_in_coaching_ausblick():
    """Round 3 revert (Anna 2026-05-17): the Round-2 Beispielwoche-decision
    was reversed — Mo-So sample weeks felt fabricated and pushed the report
    past 5 pages. The prompt must NOT instruct Codex to produce one.

    The string `Beispielwoche` may still appear as a NEGATIVE marker (i.e.
    'KEINE Beispielwoche'), so we look specifically for the imperative ask
    (Beispielwoche-Liste mit Mo:/Di:/… oder '"beispielwoche"' als JSON-Schlüssel)."""
    src = PROMPT.read_text().lower()
    # Mo-So week-format hints must be absent.
    assert "mo:" not in src, (
        "Prompt still shows Mo-So sample-week format — Round 3 removed it."
    )
    assert '"beispielwoche"' not in src, (
        "Prompt still has 'beispielwoche' as a JSON schema key — Round 3 removed it."
    )


def test_prompt_requires_vorname_in_ernaehrung():
    """Round 3 (Anna 2026-05-17): Energie & Regeneration must address the
    athlete by first name, mirroring the Zusammenfassung tone."""
    src = PROMPT.read_text().lower()
    # Look for both the rule wording AND a section anchor.
    assert "vorname" in src
    # The directive should be tied to the Energie/ernaehrung section name.
    assert "energie" in src or "ernährung" in src or "ernaehrung" in src


def test_prompt_allows_short_ernaehrung():
    """Anna 2026-05-17 decision #5 — Ernährung may be short when there's
    little to say (not a hard 120-word floor)."""
    src = PROMPT.read_text().lower()
    # Either the word cap was relaxed (1-100 phrasing) or the explicit
    # 'kurz halten' allowance is present.
    assert "1-100" in src or "kurz halten" in src or "ruhig kurz" in src
