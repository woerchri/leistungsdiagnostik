# Leistungsdiagnostik automation — brief

## Context

Personal side project for Christopher's sister Anna-Maria Wörndle (Sport Annalytics), a sport scientist running Leistungsdiagnostik for athletes. Today everything is manual: she enters raw test values into an Excel workbook with embedded formulas and intermediate calculation sheets, builds a Word/PDF report by hand, and writes the training recommendation prose herself.

Goal: she drops a structured input file in a folder, runs one command in **Codex CLI**, gets a German Word document with the polished graph, the lactate intersection table, suggested training zones (which she confirms or adjusts in dialogue), and an LLM-drafted interpretation. She then edits manually before sending to the athlete.

Authoritative input/output/math spec: **`samples/26_05_LD_Dateneingabe.docx`** (sister's own spec doc — read this when in doubt). Historical reference: `samples/RM_LD_LAUF_24_05.xlsx` (her old workbook) and `samples/SS_LD_LAUF_24_05.pdf` (a generated report). The new tool *improves* on the historical output — same numbers, better presentation, automated interpretation.

## Hard constraints

- **Number crunching deterministic** — same input → same numbers. No LLM in the math layer.
- **Threshold/zone *suggestions* via interpretive logic, not fixed mmol cutoffs.** Her spec explicitly says "Keine rein fixen mmol-Schwellen verwenden" — the zones come from the curve's shape, HR trajectory, RPE pattern, and her clinical judgement. The tool *proposes*; she confirms or adjusts.
- **Pre-interpretation plausibility checks** (Pflichtprüfungen): physiological plausibility, illogical lactate jumps, HR progression, RPE/load coherence, last-step completeness, measurement errors. The tool flags these before any interpretation prose is written.
- **Interactive zone adjustment** — she explicitly requests sliders to move zone boundaries. v1 implements this as Codex dialogue (she types adjustments; pipeline re-runs); a visual slider tool is a possible later milestone.
- **German output** — Word template, axis labels, prose, dialogue. All German.
- **Sport variants from day one (but built incrementally):** LAUF, RAD, TRIATHLON-RAD, TRIATHLON-LAUF, UNSPEZIFISCH. Triathlon variants reuse LAUF/RAD math with different reporting context. Build LAUF first, validate, then add RAD, then UNSPEZIFISCH.
- **Sister is non-technical** — copy-paste terminal commands fine, anything more is not.
- **Low maintenance** — Christopher iterates; sister pulls updates.

## Approach

A **standalone Python pipeline** that produces a complete report by itself (math + plots + LLM interpretation + Word doc), wrapped by a **Codex custom slash command** (`/ld-report`) that gives her a conversational UX including zone-boundary adjustment on top.

**Key design choice: Python is the engine, Codex is the driver.** If Codex breaks, `uv run python -m ld.run input.xlsx --interpret` produces the same report via the OpenAI API directly with Christopher's key. Engine never depends on Codex.

**Math layer (deterministic, from the spec):**
- **Polynomial degree 3** fit for lactate vs. intensity (km/h for LAUF, W for RAD, Stufe for UNSPEZIFISCH).
- **Linear** fit for HF vs. intensity.
- **Aliquot adjustment** for incomplete last step: `v_max = v_last_complete + (incomplete_duration / step_duration) × increment`.
- **Lactate intersection table** at fixed mmol values `{1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0}` — for each, compute intensity, pace (LAUF only), and HF.
- **Plot**: dual-y-axis (Laktat left red, HF right blue), X-axis from start to v_max with ticks at increment, polynomial curve with markers for lactate, linear line with markers for HF, title `<Sport>_<Start>_<Increment>_<Duration>; <Date>` (e.g. "Lauf_8_1_4; 23.05.2024").

**Zone suggestion layer (interpretive, defensible):**
- After deterministic math, suggest Z2–Z6 boundaries using a documented heuristic (e.g. Z2/Z3 boundary near 2 mmol, Z3/Z4 near LT2 / first inflection, Z4/Z5 near 4 mmol etc.) — but explicitly mark the suggestions as starting points.
- Codex presents suggested boundaries; sister confirms or adjusts in dialogue.
- Re-runs report.py with her final boundaries.

**LLM interpretation layer:**
- Takes the PII-redacted numeric JSON + her zone adjustments + her free-text "Kontext" from the dialogue.
- Drafts four sections of German prose: Zusammenfassung, Schwellen & Zonen, Trainingsbereiche, Empfehlungen.
- Cites specific numeric values; flags anomalies surfaced by Pflichtprüfungen; suggests training-zone implications.
- She edits the final Word doc anyway — LLM is a draft, not a final.

## Her happy-path flow

1. Fills in `Athlet_2026-05-13.xlsx` from the template (single workbook with sheets `Athlet`, `Testprotokoll`, `Testdaten`, `Coaching`), drops it into `~/Leistungsdiagnostik/input/`.
2. Opens Codex CLI via a `.command` file on her desktop.
3. Types `/ld-report`.
4. Codex runs the pipeline → shows the lactate curve + HF line plot, the intersection table, the suggested Z2–Z6 boundaries, AND any plausibility-check flags ("Laktatsprung zwischen Stufe 4 und 5 ungewöhnlich groß").
5. Codex asks: "Zonen so übernehmen oder anpassen? Kontext für die Interpretation?" She replies with adjustments + context, or hits enter.
6. If she adjusted boundaries, Codex re-runs report assembly with her values. Then drafts interpretation in German, splices into the Word doc.
7. Final `Athlet_2026-05-13_v1.docx` lands in `~/Leistungsdiagnostik/output/`. She opens it, edits, sends.

## Fallback flow (if Codex breaks or her ChatGPT lapses)

```
uv run python -m ld.run input/Athlet.xlsx --interpret
```
Same final Word doc. Uses Christopher's OpenAI API key from `.env`. Zone suggestions are accepted as-is (no interactive adjustment in fallback mode — she edits the final doc instead).

## Repo layout

```
leistungsdiagnostik/
├── AGENTS.md                       # Project-wide context Codex reads on session start
├── README.md                       # Onboarding for sister + dev notes for Christopher
├── USAGE_GUIDE.md                  # Written after M1-M7 (M8) — sister's how-to
├── src/ld/
│   ├── run.py                      # CLI entry: input.xlsx → JSON + draft.docx
│   ├── errors.py                   # LDInputError, LDError, LDProtocolError
│   ├── types.py                    # All dataclasses crossing module boundaries
│   ├── io_input.py                 # openpyxl parser; one sheet per section
│   ├── redact.py                   # Write PII-redacted JSON for LLM step
│   ├── protocols/
│   │   ├── __init__.py             # Dispatch by sportart
│   │   ├── lauf.py                 # First protocol — running step test
│   │   ├── rad.py                  # M7 — cycling
│   │   ├── unspezifisch.py         # M7 — generic step protocol
│   │   └── _common.py              # Curve fit, linear HF fit, aliquot, intersection table
│   ├── pflichtpruefungen.py        # Pre-interpretation plausibility checks
│   ├── zones.py                    # Suggested Z2-Z6 boundaries from curve
│   ├── plots.py                    # matplotlib, dual axis, German labels, spec from docx
│   ├── report.py                   # docxtpl: fills templates/report.docx
│   ├── interpret.py                # OpenAI API call (only with --interpret flag)
│   ├── patch_interpretation.py     # Splice prose JSON into Word doc
│   └── versioning.py               # _v1/_v2 output naming
├── templates/
│   ├── input_template.xlsx         # Pre-filled with a worked example (Rainier or Sarah)
│   └── report.docx                 # Jinja-placeholder Word template (German headings)
├── tests/
│   ├── unit/                       # Math helpers
│   ├── protocols/                  # Snapshot tests per protocol
│   ├── e2e/                        # Single end-to-end smoke
│   └── historical/                 # Rainier + Sarah cases as acceptance gate
├── samples/                        # Anna-Maria's reference files (committed)
│   ├── 26_05_LD_Dateneingabe.docx
│   ├── RM_LD_LAUF_24_05.xlsx
│   └── SS_LD_LAUF_24_05.pdf
├── pyproject.toml
├── .env.example
└── .codex/
    └── prompts/
        └── ld-report.md
```

## Codex orchestration files

**`AGENTS.md`** — loaded automatically when Codex opens in this folder:

```
# Leistungsdiagnostik repo — orientation

This repo turns raw sport-diagnostic test data into a German Word report.
Authoritative spec: samples/26_05_LD_Dateneingabe.docx (sister's own document).

Layout:
- input/ — athlete xlsx files the user drops in.
- output/ — generated reports.
- src/ld/ — the deterministic Python pipeline.
- templates/ — input + report Word templates.
- samples/ — reference files. Do not modify.

Hard rules:
- Never modify the numbers in output/*.json. The Python pipeline is authoritative.
- Never invent values that aren't in the input or pipeline output.
- All math goes through `uv run python -m ld.run`. Never re-derive thresholds yourself.
- Zone boundaries are SUGGESTIONS; always let the user confirm or adjust before finalizing.
- Plausibility checks (Pflichtprüfungen) results must be surfaced before interpretation.
- Report language is German. Interpretation prose must be German.
- The spec explicitly forbids purely fixed mmol thresholds — use the curve shape, HR pattern, and RPE pattern together.

When the user types /ld-report, follow .codex/prompts/ld-report.md exactly.
```

**`.codex/prompts/ld-report.md`** — full text in [FEATURE_PLAN.md](FEATURE_PLAN.md) M3.2.

## Determinism boundary

| Layer | Deterministic? | How |
|-------|---------------|-----|
| `io_input.py` | Yes | openpyxl cell reads; no inference |
| `protocols/*` | Yes | Polynomial fit (deg 3), linear fit, aliquot calc, intersection table — all pure |
| `pflichtpruefungen.py` | Yes | Rule-based flags, no LLM |
| `zones.py` | Yes — suggestions only | Heuristic Z2-Z6 boundaries from curve; user overrides via dialogue |
| `plots.py` | Yes (content) | matplotlib with fixed style, German labels. PNG bytes may vary across matplotlib versions; we test content, not bytes. |
| `report.py` / `patch_interpretation.py` | Yes (content) | docxtpl template + values; numbers in doc match JSON exactly |
| LLM interpretation | Non-deterministic | Reads PII-redacted JSON only; she edits final prose anyway |

## Testing

Three layers, proportionate to a one-person tool:

| Layer | What it covers | Lives in |
|-------|----------------|----------|
| **Unit tests on math** | Polynomial fit, linear fit, aliquot calc, intersection at fixed lactates, pace conversion. Known input → known output. | `tests/unit/` |
| **Per-protocol snapshot tests** | Full input.xlsx → expected_numbers.json. Drift fails. | `tests/protocols/` |
| **Historical-case validation** | Run on Rainier + Sarah cases; numbers must match the historical xlsx/PDF exactly. **v1 acceptance gate.** | `tests/historical/` |

Plus one **e2e smoke**: input.xlsx → final.docx, extract values from the docx, assert match the JSON.

CI: `uv run pytest` locally. No GitHub Actions.

**Not doing for v1:** PNG hash determinism (fragile across matplotlib versions), property tests with hypothesis (overkill).

## German localization specifics

- Sheet names in input template: `Athlet`, `Testprotokoll`, `Testdaten`, `Coaching`.
- Report template (`templates/report.docx`) headings: "Athletendaten", "Testprotokoll", "Testergebnisse", "Schwellen", "Trainingsbereiche", "Interpretation", "Empfehlungen".
- Plot axis labels: "Geschwindigkeit (km/h)" / "Leistung (W)" / "Stufe", "Laktat (mmol/l)", "Herzfrequenz (bpm)".
- Plot title format from spec: `<Sport>_<Start>_<Increment>_<Duration>; <Date>` — e.g. "Lauf_8_1_4; 23.05.2024".
- Zone names + Ziel der Zonen (from spec):
  - Z1 — aktive Regeneration (RPE 0-2 on 0-10 scale, RPE 6-9 on 6-20 scale)
  - Z2 — aerobe Basis (RPE 3-4 / 10-11)
  - Z3 — metabolische Stabilität (RPE 5-6 / 12-14)
  - Z4 — Schwellenleistung (RPE 7-8 / 15-17)
  - Z5 — VO2max-Reize (RPE 9 / 18)
  - Z6 — neuromuskulär (RPE 10 / 19-20)
- Interaction prompts in German.

## Output versioning

`src/ld/versioning.py` resolves the next available filename: `Athlet_2026-05-13_v1.docx`, `_v2.docx`, etc. Never overwrites. She decides which version is final.

## Privacy: redact PII before LLM

`output/<basename>_for_llm.json` strips name + DOB (keeps derived age). The LLM step reads only this redacted JSON. The Word doc still gets the real name via deterministic template fill.

## Build sequence

1. **M0 — Inputs in hand** (DONE: we have `samples/RM_LD_LAUF_24_05.xlsx`, `samples/SS_LD_LAUF_24_05.pdf`, and the spec `samples/26_05_LD_Dateneingabe.docx`).
2. **M1 — Deterministic core, LAUF only.** Math + intersection table + plot + draft Word doc. Acceptance: numbers match the Rainier xlsx exactly.
3. **M2 — Standalone fallback path.** `--interpret` flag → finished docx via OpenAI API.
4. **M3 — Codex UX layer.** `/ld-report` + interactive zone adjustment dialogue + Pflichtprüfungen surfacing.
5. **M4 — Privacy + versioning polish.**
6. **M5 — Test net.**
7. **M6 — Onboarding handoff.**
8. **M7 — Add RAD + UNSPEZIFISCH protocols.**
9. **M8 — Usage guide** (written from the real tool).
10. *(Optional later)* — visual slider UI for zone boundaries via Streamlit, if conversational adjustment proves too clunky.

## Onboarding sister (15 min, once, after v1 is built)

1. Confirm Node.js: `node --version`. If missing: `brew install node`.
2. `curl -LsSf https://astral.sh/uv/install.sh | sh`.
3. `npm install -g @openai/codex` + `codex login` with her ChatGPT account.
4. `git clone <repo> ~/Leistungsdiagnostik/tool` + `cd ~/Leistungsdiagnostik/tool && uv sync`.
5. `~/Desktop/Leistungsdiagnostik.command` shortcut (cd + codex).
6. Walk through `/ld-report` against the pre-filled example, then a fresh real case, including one "Zone anpassen" + one "redo ohne Stufe N".

## Update path

`git -C ~/Leistungsdiagnostik/tool pull && uv sync` from a sticky note.

## Verification (acceptance gates)

- **M1**: `uv run python -m ld.run samples/RM_LD_LAUF_24_05.xlsx` produces JSON whose intersection table matches `samples/RM_LD_LAUF_24_05.xlsx`'s "Auswertung" sheet rows 21-24 exactly. Plot visually matches the curve in `samples/SS_LD_LAUF_24_05.pdf` page 3.
- **M2**: `--interpret` produces a complete German Word doc.
- **M3**: `/ld-report` produces an identical final docx for the same input + same accepted zones.
- **M5**: `uv run pytest` green.
- **M6**: Sister runs `/ld-report` solo, including "Zone anpassen" and "redo ohne Stufe N".
- **M8**: Sister reads USAGE_GUIDE cold, runs end-to-end, no questions.
