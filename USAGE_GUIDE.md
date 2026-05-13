# Anleitung — Leistungsdiagnostik-Werkzeug

Diese Anleitung erklärt, wie du einen Leistungsdiagnostik-Bericht erstellst.
Sie wurde anhand des echten Werkzeugs geschrieben — alle Befehle und Ausgaben
stammen aus echten Testläufen.

---

## Was das Werkzeug macht

Du gibst eine Excel-Datei mit den Rohdaten des Tests ein. Das Werkzeug berechnet
daraus automatisch:

- Die maximale Leistung/Geschwindigkeit (aliquot, falls die letzte Stufe nicht abgeschlossen wurde)
- Die Laktatkurve (Polynom 3. Grades) und Herzfrequenzgerade
- Schnittpunkte bei festen Laktatwerten (1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0, 8.0 mmol/L)
- Vorgeschlagene Trainingszonen Z1–Z6
- Pflichtprüfungen (Plausibilitätschecks)
- Ein Diagramm (Laktat + Herzfrequenz)
- Einen Word-Bericht als Entwurf

Auf Wunsch ergänzt das Werkzeug eine erste Interpretation auf Deutsch (LLM-Entwurf),
die du danach selbst bearbeitest.

---

## Voraussetzungen (einmalig)

→ Siehe [README.md](README.md) für die vollständige Einrichtungsanleitung.

Kurzfassung:
1. `uv sync` im Werkzeugordner ausführen.
2. `Leistungsdiagnostik.command` auf dem Desktop ausführbar machen.
3. Bei Bedarf: `.env`-Datei mit `OPENAI_API_KEY=sk-...` anlegen.

---

## Einen Bericht erstellen — Schritt für Schritt

### Schritt 1: Eingabedatei vorbereiten

1. Öffne `templates/input_template.xlsx` (die Vorlage ist mit Beispieldaten gefüllt).
2. Ersetze alle Daten mit den echten Werten des/der Athlet:in.
3. Benenne die Datei um: `Vorname_JJJJ-MM-TT.xlsx` (z.B. `Lisa_2024-09-14.xlsx`).
4. Lege die Datei in den Ordner `input/`.

Die Vorlage hat vier Arbeitsblätter:
- **Athlet** — Name, Geburtsjahr, Gewicht, Größe, Sportart, Ziele
- **Testprotokoll** — Datum, Gerät, Anfangsintensität, Stufendauer, letzte Stufe usw.
- **Testdaten** — die eigentliche Messtabelle (Stufe | Intensität | HF | Laktat | RPE)
- **Coaching** — Verletzungen, Stärken, Schwächen, Wettkämpfe

> **RPE-Skala:** Verwende die Borg-Skala 6–20 (6 = keine Belastung, 20 = maximale Belastung).
> Diese Skala ist in der Vorlage als Hinweis in Spalte G der Testdaten eingetragen.

### Schritt 2: Bericht generieren (Codex-Modus)

1. Doppelklicke auf `~/Desktop/Leistungsdiagnostik.command`.
2. Tippe `/ld-report` und drücke Enter.
3. Codex führt die Pipeline aus und zeigt:
   - v_max
   - Schnittpunkttabelle
   - Vorgeschlagene Zonen (Z2–Z6)
   - Pflichtprüfungen-Ergebnis
4. Codex fragt: *"Möchtest du die vorgeschlagenen Zonen so übernehmen oder anpassen?"*
5. Antworte z.B.: `Z3 bis 9.0; Kontext: erste Session der Saison`
   — oder drücke einfach Enter um die Vorschläge zu übernehmen.
6. Codex erstellt den Endbericht: `output/<Name>_v1.docx`.

### Schritt 3: Bericht bearbeiten und versenden

Öffne `output/<Name>_v1.docx` in Word und überarbeite den Text.
Das Werkzeug liefert einen Entwurf — du entscheidest über Schwellen und Formulierungen.

---

## Fallback ohne Codex (OpenAI API direkt)

Falls Codex nicht verfügbar ist:

```bash
cd ~/Leistungsdiagnostik/tool
uv run python -m ld.run input/Lisa_2024-09-14.xlsx --interpret
```

**Ausgabe:**
```
Endbericht: output/Lisa_2024-09-14_v1.docx
Pflichtprüfungen: alle OK.
```

Ohne `--interpret` erhältst du nur den Entwurf (ohne Interpretation):
```bash
uv run python -m ld.run input/Lisa_2024-09-14.xlsx
```
```
Entwurf:    output/Lisa_2024-09-14_draft_v1.docx
JSON:       output/Lisa_2024-09-14.json
Mit --interpret aufrufen für eine erste Interpretation.
Pflichtprüfungen — Hinweise:
  • Letzte Stufe nicht vollständig (1.75 von 4 min). v_max wird aliquot berechnet.
```

---

## Häufige Situationen

### Eine Stufe weglassen

Falls eine Stufe fehlerhaft gemessen wurde (z.B. Stufe 4):

```bash
uv run python -m ld.run input/Lisa.xlsx --exclude 4
```

Im Codex-Modus: Tippe `redo ohne Stufe 4`, Codex führt das automatisch aus.

### Zonen anpassen

**Im Codex-Modus:** Beantworte die Zonenfrage mit konkreten Werten:
```
Z3 bis 9.2, Z4 bis 10.5; Kontext: guter Trainingszustand, Vorbereitung Halbmarathon
```

**Direkt über die Kommandozeile:**
```bash
uv run python -m ld.zones_cli output/Lisa Z3_upper=9.2 Z4_upper=10.5
```
Das erstellt automatisch einen neuen Entwurf `output/Lisa_draft_v2.docx`.

### Bericht neu erstellen (neue Version)

Führe den Befehl einfach nochmals aus. Das Werkzeug überschreibt nie — es erstellt
automatisch `_v2.docx`, `_v3.docx` usw.

### Eingabedatei wurde geändert

Führe den Befehl erneut aus. Das JSON und der Pickle werden aktualisiert.

---

## Pflichtprüfungen verstehen

Das Werkzeug prüft vor der Interpretation automatisch:

| Prüfung | Bedeutung |
|---------|-----------|
| `letzte_stufe` | Letzte Stufe war unvollständig → v_max wird aliquot berechnet |
| `hf_monotonic` | HF fällt zwischen Stufen → möglicher Messfehler |
| `laktat_monotonic` | Laktat fällt stark ab → möglicher Messfehler |
| `laktatsprung` | Laktatanstieg > 2.5 mmol/L zwischen zwei Stufen → Schwellenpassage oder Fehler |
| `rpe_konsistenz` | RPE fällt trotz steigender Belastung → Eingabefehler prüfen |
| `ausbelastung` | Keine vollständige Ausbelastung → Schwellen vorsichtiger formulieren |

Ein Hinweis blockiert nicht den Bericht, zeigt aber an, was zu beachten ist.

---

## Wenn etwas schiefgeht

### „Fehler: Eingabedatei nicht gefunden"
→ Prüfe ob die xlsx-Datei in `input/` liegt und der Pfad stimmt.

### „Fehler: Pflichtfeld 'X' auf Blatt 'Y' ist leer"
→ Öffne die xlsx-Datei und fülle das fehlende Feld aus.

### „Fehler: Sportart 'X' nicht unterstützt"
→ Erlaubte Werte im Feld Sportart: `lauf`, `rad`, `triathlon-rad`, `triathlon-lauf`, `unspezifisch`

### „Fehler: Spaltenüberschriften auf 'Testdaten' falsch"
→ Die Spaltenköpfe der Testdaten-Tabelle müssen exakt lauten:
  `Stufe | Intensität | Herzfrequenz | Laktat | RPE` (erste Zeile).
  Immer von der Vorlage `templates/input_template.xlsx` ausgehen.

### „Fehler: OPENAI_API_KEY ist nicht gesetzt"
→ Erstelle eine Datei `.env` im Werkzeugordner:
```
OPENAI_API_KEY=sk-...
```

### Codex zeigt nichts an
→ Prüfe `codex --version` im Terminal. Falls nicht installiert:
```bash
npm install -g @openai/codex && codex login
```

---

## Datenschutz

Der Entwurf (`_draft_v<n>.docx`) und die vollständige JSON-Datei enthalten den echten Namen
des/der Athlet:in. Für die LLM-Interpretation wird automatisch eine anonymisierte Version
(`_for_llm.json`) verwendet — Name und Geburtsjahr werden ersetzt, nur das Alter bleibt.

---

## Aktualisierungen einspielen

```bash
git -C ~/Leistungsdiagnostik/tool pull && uv sync
```

Danach ist das Werkzeug auf dem neuesten Stand.

---

## Wer hilft

Bei technischen Fragen: **Christopher** (hat das Werkzeug gebaut und wartet es).
Bei inhaltlichen Fragen zu Schwellen und Interpretation: **du** (du bist die Expertin).
