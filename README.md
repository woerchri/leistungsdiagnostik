# Leistungsdiagnostik — Automatisierungswerkzeug

Automatische Auswertung von Laktatstufentests. Eingabe: xlsx → Ausgabe: Word-Bericht mit
Laktatkurve, Schnittpunkttabelle, Trainingszonen und LLM-Interpretation auf Deutsch.

---

## Einrichtung (einmalig, ca. 15 Minuten)

### Voraussetzungen

```bash
node --version          # muss erscheinen; falls nicht: brew install node
uv --version            # muss erscheinen; falls nicht: curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Installation

```bash
git clone <REPO-URL> ~/Leistungsdiagnostik/tool
cd ~/Leistungsdiagnostik/tool
uv sync
```

### Codex CLI (für den Dialogmodus)

```bash
npm install -g @openai/codex
codex login    # mit ChatGPT-Account einloggen
```

### Desktop-Verknüpfung

Das Skript `Leistungsdiagnostik.command` auf dem Desktop öffnet ein Terminal im Werkzeugordner
und startet Codex. Einmalig ausführbar machen:

```bash
chmod +x ~/Desktop/Leistungsdiagnostik.command
```

---

## Täglicher Betrieb

1. Eingabedatei `Athlet_DATUM.xlsx` aus `templates/input_template.xlsx` erstellen.
2. Datei in `~/Leistungsdiagnostik/tool/input/` ablegen.
3. `Leistungsdiagnostik.command` auf dem Desktop doppelklicken.
4. `/ld-report` tippen.
5. Zonen bestätigen oder anpassen → Enter.
6. Endbericht liegt in `output/`.

### Fallback (ohne Codex)

```bash
cd ~/Leistungsdiagnostik/tool
uv run python -m ld.run input/Athlet.xlsx --interpret
```

Benötigt `OPENAI_API_KEY` in einer `.env`-Datei.

---

## Aktualisierungen einspielen

```bash
git -C ~/Leistungsdiagnostik/tool pull && uv sync
```

---

## Entwicklerhinweise (Christopher)

- Protokolle: `src/ld/protocols/`  — lauf.py, rad.py, unspezifisch.py
- Mathematik:  `src/ld/protocols/_common.py` — polyfit, HF-Fit, Aliquot, Schnittpunkte
- Tests:       `uv run pytest`
- Vorlagen:    `templates/input_template.xlsx`, `templates/report.docx`
- Spec:        `samples/26_05_LD_Dateneingabe.docx`

Alle Ausgaben sind deterministisch (Python). Die LLM-Interpretation ist ein Entwurf;
Anna-Maria bearbeitet den finalen Word-Bericht selbst.
