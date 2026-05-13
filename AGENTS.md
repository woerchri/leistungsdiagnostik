# Leistungsdiagnostik repo — orientation

This repo turns raw sport-diagnostic test data into a German Word report.
Authoritative spec: samples/26_05_LD_Dateneingabe.docx (sister's own document).

Layout:
- input/     — athlete xlsx files the user drops in.
- output/    — generated reports.
- src/ld/    — the deterministic Python pipeline.
- templates/ — input + report Word templates.
- samples/   — reference files. Do not modify.

Hard rules:
- Never modify the numbers in output/*.json. The Python pipeline is authoritative.
- Never invent values that aren't in the input or pipeline output.
- All math goes through `uv run python -m ld.run`. Never re-derive thresholds yourself.
- Zone boundaries are SUGGESTIONS; always let the user confirm or adjust before finalizing.
- Plausibility checks (Pflichtprüfungen) results must be surfaced before interpretation.
- Report language is German. Interpretation prose must be German.
- The spec explicitly forbids purely fixed mmol thresholds — use the curve shape, HR pattern,
  and RPE pattern together.

When the user types /ld-report, follow .codex/prompts/ld-report.md exactly.
