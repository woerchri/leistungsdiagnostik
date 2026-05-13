# Anleitung — Leistungsdiagnostik-Werkzeug

---

## Was das Werkzeug macht

Du gibst eine Excel-Datei mit den Rohdaten des Tests ein. Das Werkzeug berechnet
daraus automatisch:

- Maximale Geschwindigkeit/Leistung (aliquot, falls die letzte Stufe nicht vollständig war)
- Laktatkurve und Herzfrequenzgerade
- Schnittpunkte bei 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0 und 8.0 mmol/L
- Vorgeschlagene Trainingszonen Z1–Z6
- Plausibilitätsprüfungen
- Diagramm (Laktat + Herzfrequenz)
- Word-Bericht als Entwurf, den du danach selbst bearbeitest

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

### Schritt 2: Bericht generieren

Wähle einen der beiden Wege — der Ablauf ab Punkt 3 ist für beide gleich.

---

**Weg A — Terminal (.command-Datei)**

1. Doppelklicke auf `Leistungsdiagnostik.command` auf dem Desktop.
2. Ein Terminal-Fenster öffnet sich automatisch im richtigen Ordner.

---

**Weg B — Codex-App**

1. Öffne die Codex-App (Programme-Ordner oder Spotlight: „Codex").
2. Öffne den Projektordner: **Datei → Ordner öffnen → `~/Desktop/leistungsdiagnostik`**.

---

**Ab hier ist der Ablauf für beide Wege gleich:**

3. Tippe `/ld-report` und drücke Enter.
4. Codex führt die Pipeline aus und zeigt:
   - v_max
   - Schnittpunkttabelle
   - Vorgeschlagene Zonen (Z2–Z6)
   - Pflichtprüfungen-Ergebnis
5. Codex fragt: *„Möchtest du die vorgeschlagenen Zonen so übernehmen oder anpassen?"*
6. Antworte z.B.: `Z3 bis 9.0; Kontext: erste Session der Saison`
   — oder drücke einfach Enter um die Vorschläge zu übernehmen.
7. Codex erstellt den Endbericht: `output/<Name>_v1.docx`.

### Schritt 3: Bericht bearbeiten und versenden

Öffne `output/<Name>_v1.docx` in Word und überarbeite den Text.
Das Werkzeug liefert einen Entwurf — du entscheidest über Schwellen und Formulierungen.

---

## Häufige Situationen

### Eine Stufe weglassen

Falls eine Stufe fehlerhaft gemessen wurde (z.B. Stufe 4):

Tippe in Codex: `redo ohne Stufe 4` — Codex führt das automatisch aus.

### Zonen anpassen

Beantworte die Zonenfrage von Codex mit konkreten Werten:
```
Z3 bis 9.2, Z4 bis 10.5; Kontext: guter Trainingszustand, Vorbereitung Halbmarathon
```
Codex erstellt automatisch einen aktualisierten Bericht.

### Bericht neu erstellen (neue Version)

Führe den Befehl einfach nochmals aus. Das Werkzeug überschreibt nie — es erstellt
automatisch `_v2.docx`, `_v3.docx` usw.

### Eingabedatei wurde geändert

Führe den Befehl einfach erneut aus. Das Werkzeug liest die Datei neu ein.

---

## Pflichtprüfungen verstehen

Vor der Interpretation prüft das Werkzeug automatisch die Plausibilität der Daten.
Falls etwas auffällt, erscheint ein Hinweis wie:

| Was du siehst | Was es bedeutet |
|---------------|-----------------|
| „Letzte Stufe nicht vollständig (X von Y min). v_max wird aliquot berechnet." | Normal wenn der Athlet mittendrin abgebrochen hat — das Werkzeug rechnet das korrekt heraus. |
| „Herzfrequenz fällt zwischen Stufen ab." | Möglicher Messfehler oder kurze Erholung — prüfe die HF-Werte in der Excel. |
| „Laktat fällt deutlich zwischen Stufen ab." | Ungewöhnlich — prüfe ob die Werte richtig eingetragen sind. |
| „Ungewöhnlich großer Laktatanstieg … Schwellenpassage oder Messfehler?" | Häufig an der Schwelle normal; prüfe trotzdem die Eingabe. |
| „RPE fällt mit steigender Belastung." | Wahrscheinlich Tippfehler in der Excel. |
| „Keine vollständige Ausbelastung erreicht." | Schwellen in der Interpretation vorsichtiger formulieren. |

Kein Hinweis blockiert den Bericht — du siehst die Ausgabe trotzdem vollständig.

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
git -C ~/Desktop/leistungsdiagnostik pull && uv sync
```

Danach ist das Werkzeug auf dem neuesten Stand.

---

## Wer hilft

Bei technischen Fragen: **Christopher** (hat das Werkzeug gebaut und wartet es).
Bei inhaltlichen Fragen zu Schwellen und Interpretation: **du** (du bist die Expertin).
