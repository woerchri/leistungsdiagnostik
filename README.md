# Leistungsdiagnostik — Automatisierungswerkzeug

Automatische Auswertung von Laktatstufentests. Eingabe: xlsx → Ausgabe: 5-seitiger
Word-Bericht (DIN A4 quer) mit Laktatkurve, Schnittpunkttabelle, Trainingszonen
und einer von Codex erstellten Interpretation auf Deutsch.

---

## Einrichtung (einmalig, ca. 15 Minuten)

### Voraussetzungen

```bash
node --version          # muss erscheinen; falls nicht: brew install node
uv --version            # muss erscheinen; falls nicht: curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Optional, aber empfohlen**: LibreOffice für Render-QA (5-Seiten-Test im CI):

```bash
brew install --cask libreoffice
```

Ohne LibreOffice werden die Render-QA-Tests (`tests/e2e/test_reference_5pages.py`)
übersprungen statt zu scheitern — das 5-Seiten-Layout ist dann nicht automatisch
gegen Regressionen abgesichert.

### Installation

```bash
git clone https://github.com/woerchri/leistungsdiagnostik.git ~/Desktop/leistungsdiagnostik
cd ~/Desktop/leistungsdiagnostik
uv sync
```

Optional — wenn das **visuelle Zonen-Tool** genutzt werden soll:

```bash
uv pip install -e ".[visual]"
```

### Codex CLI

```bash
npm install -g @openai/codex
codex login    # mit ChatGPT-Account einloggen
```

Anna's ChatGPT-Account übernimmt die Interpretationsprosa — das Werkzeug selbst
macht keine API-Calls und braucht keinen API-Key.

### Desktop-Verknüpfung

Das Skript `Leistungsdiagnostik.command` auf dem Desktop öffnet ein Terminal im
Werkzeugordner und startet Codex. Einmalig ausführbar machen:

```bash
chmod +x ~/Desktop/Leistungsdiagnostik.command
```

---

## Täglicher Betrieb

1. Eingabedatei `XY_LD_Sportart_JJ_MM_TT.xlsx` aus `templates/input_template.xlsx`
   erstellen. Der genaue Dateiname spielt für die Pipeline keine Rolle — das
   Werkzeug normalisiert den Ausgabenamen aus Athlet:innendaten und Testdatum.
2. Datei in `~/Desktop/leistungsdiagnostik/input/` ablegen.
3. `Leistungsdiagnostik.command` auf dem Desktop doppelklicken.
4. `/ld-report` tippen.
5. Vorgeschlagene Zonen prüfen → bestätigen oder anpassen → Enter.
6. Endbericht liegt in `output/` als `XY_LD_Sportart_JJ_MM_TT_final_v<n>.docx`.

### Alternativer Ablauf: Visuelles Zonen-Tool

Nach der ersten Pipeline-Ausführung können Zonen statt im Codex-Dialog auch
grafisch verschoben werden:

```bash
uv run streamlit run src/ld/zone_tool.py
```

Im Browser öffnet sich ein Slider-UI mit Live-Vorschau des Plots. Beim
"Übernehmen"-Klick werden die neuen Grenzen über `ld.zones_override` zurück in
den Bericht geschrieben.

### Direkter Pipeline-Aufruf (ohne Codex)

```bash
uv run python -m ld.run input/<datei.xlsx>
```

Schreibt JSON + Draft-Bericht (ohne Interpretationsabsätze). Zur
Interpretation kann Codex später aufgerufen werden — der Pipeline-Schritt
ist deterministisch und unabhängig.

---

## Aktualisierungen einspielen

```bash
git -C ~/Desktop/leistungsdiagnostik pull && uv sync
```

---

## Entwicklerhinweise (Christopher)

- Protokolle: `src/ld/protocols/`  — lauf.py, rad.py, unspezifisch.py
- Mathematik: `src/ld/protocols/_common.py` — polyfit, HF-Fit, Aliquot, Schnittpunkte
- Zonen: `src/ld/zones.py` (Vorschlag) + `src/ld/zones_override.py` (manuelle Anpassung)
- Pflichtprüfungen: `src/ld/pflichtpruefungen.py`
- Plot: `src/ld/plots.py` — mit farbigen Trainingszonen-Banden
- Report-Template: `templates/report.docx` (generiert via `build_report_template.py`)
- Eingabe-Template: `templates/input_template.xlsx` (generiert via `build_template.py`)
- Visuelles Zonen-Tool: `src/ld/zone_tool.py` (Streamlit)
- Codex-Anweisungen: `.codex/prompts/ld-report.md`
- Tests: `uv run python -m pytest`
- Spec: `samples/26_05_LD_Dateneingabe.docx`
- Korrekturfeedback (Round 1): `feedback/round1/`
- Produktverfeinerung (Round 2): `feedback/round2/` inkl. [IMPLEMENTATION_PLAN.md](feedback/round2/IMPLEMENTATION_PLAN.md)
- Render-QA: `src/ld/render_qa.py` (LibreOffice → PDF → Seitenzahl)
- **RPE-Skala**: 0-10 (Borg CR10) — Round 2; alte 6-20-Werte werden vom Parser abgewiesen

Alle Ausgaben (Zahlen, Tabellen, Plot, Word-Doc) sind deterministisch.
Nicht-deterministische Interpretationsprosa wird ausschließlich von Codex
erzeugt — kein API-Call aus dem Werkzeug.
