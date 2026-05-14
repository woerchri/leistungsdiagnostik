# Leistungsdiagnostik repo — orientation

This repo turns raw sport-diagnostic test data into a 5-page A4-landscape German
Word report.

Authoritative spec: `samples/26_05_LD_Dateneingabe.docx` (sister's own document).
Round-1 correction feedback (May 2026): `feedback/round1/`.

## Layout

- `input/` — athlete xlsx files the user drops in.
- `output/` — generated reports (basename: `XY_LD_Sportart_JJ_MM_TT`).
- `src/ld/` — the deterministic Python pipeline.
- `templates/` — input + report Word templates.
- `assets/` — logo and brand assets.
- `samples/` — reference files. Do not modify.
- `feedback/` — incoming product feedback rounds.
- `.codex/prompts/ld-report.md` — instructions for Codex when generating the
  interpretation prose.

## Hard rules

- Never modify the numbers in `output/*.json`. The Python pipeline is authoritative.
- Never invent values that aren't in the input or pipeline output.
- All math goes through `uv run python -m ld.run`. Never re-derive thresholds
  yourself.
- Zone boundaries are SUGGESTIONS; always let the user confirm or adjust before
  finalizing (`/ld-report` dialog OR the visual `zone_tool.py`).
- Plausibility checks (Pflichtprüfungen) appear ONLY on Page 5 (Trainerseite —
  intern), never in the athlete-facing sections.
- Report language is German. Interpretation prose is German.
- No fixed mmol thresholds — use curve shape, HR pattern, and RPE pattern together.
- v_max / Maximalgeschwindigkeit naming is sport-aware:
  Lauf/Triathlon-Lauf → "Maximalgeschwindigkeit"; Rad/Triathlon-Rad → "Maximalleistung";
  Unspezifisch → "Maximalstufe".
- Schwellenschnittpunkte without a valid in-range root are DROPPED from the
  report (no `-`, no extrapolated fantasy values).
- Cubic polynomial with multiple in-range roots: pick the LARGEST x.
- Tool makes NO LLM calls itself. The OpenAI API integration was removed in
  Phase 6 (May 2026). Codex (the user's ChatGPT account) writes the prose.

## When the user types /ld-report

Follow `.codex/prompts/ld-report.md` exactly. Key points:

1. Run `uv run python -m ld.run input/<file>` (deterministic, no LLM).
2. Read `output/<basename>_for_llm.json` (PII-stripped).
3. Generate German interpretation prose with HIT/intensity guidance per
   `.codex/prompts/ld-report.md` (Vorname-based address, no
   Trainingsbereiche-Absatz, evidence-based HIT recommendations).
4. Save as `output/<basename>_interpretation.json`.
5. Patch into the docx: `uv run python -m ld.patch_interpretation output/<basename>`.

## Useful commands

- Run pipeline: `uv run python -m ld.run input/<file>`
- Run all tests: `uv run python -m pytest`
- Regenerate input template: `uv run python build_template.py`
- Regenerate report template: `uv run python build_report_template.py`
- Override zones via CLI: `uv run python -m ld.zones_cli output/<basename> Z3_upper=9.0`
- Visual zone tool: `uv run streamlit run src/ld/zone_tool.py` (after `uv pip install -e ".[visual]"`)
