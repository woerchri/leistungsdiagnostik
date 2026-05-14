# Anleitung — Leistungsdiagnostik-Werkzeug

---

## Was das Werkzeug macht

Du gibst eine Excel-Datei mit den Rohdaten des Tests ein. Das Werkzeug berechnet
daraus automatisch:

- Maximalgeschwindigkeit / Maximalleistung / Maximalstufe (aliquot, falls die
  letzte Stufe nicht vollständig war)
- Laktatkurve und Herzfrequenzgerade
- Schnittpunkte bei 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 6.0 und 8.0 mmol/L
  (nur Werte mit gültigem Schnittpunkt im Testbereich erscheinen im Bericht)
- Vorgeschlagene Trainingszonen Z1–Z6 (mit Farbcode im Diagramm)
- Pflichtprüfungen (intern auf Seite 5)
- Diagramm mit farbig hinterlegten Trainingszonen
- 5-seitiger Word-Bericht (DIN A4 quer) als Entwurf

Codex generiert die Interpretationsabsätze auf Deutsch und schreibt sie in
den finalen Bericht. Du bearbeitest den Bericht anschließend selbst.

---

## Einen Bericht erstellen — Schritt für Schritt

### Schritt 1: Eingabedatei vorbereiten

1. Öffne `templates/input_template.xlsx` (die Vorlage ist mit Beispieldaten
   gefüllt).
2. Ersetze alle Daten mit den echten Werten der Athletin / des Athleten.
3. Speichere sie an einem beliebigen Namen im Ordner `input/`. Der Dateiname
   spielt keine Rolle — das Werkzeug benennt die Ausgabe automatisch nach
   dem Schema `XY_LD_Sportart_JJ_MM_TT`.

Die Vorlage hat vier Arbeitsblätter:
- **Athlet** — Vorname, Name, Email (optional), Geburtsjahr (optional),
  Gewicht, Größe, Sportart, Ziele
- **Testprotokoll** — Datum, Uhrzeit (hh:mm), Gerät, Anfangsbelastung,
  Stufeninkrement, letzte Stufe, Nachbelastungslaktat 3/5min (optional) usw.
- **Testdaten** — die eigentliche Messtabelle (Stufe | Intensität | HF | Laktat | RPE)
- **Coaching** — Verletzungen, Stärken, Schwächen, Wettkämpfe

> **RPE-Skala:** Verwende die Borg-Skala 6–20 (6 = keine Belastung, 20 = maximal).
> Diese Skala ist in der Vorlage als Hinweis in Spalte G der Testdaten eingetragen.

### Schritt 2: Bericht generieren

1. Doppelklicke auf `Leistungsdiagnostik.command` auf dem Desktop.
2. Ein Terminal-Fenster öffnet sich mit Codex bereit.
3. Tippe `/ld-report` und drücke Enter.
4. Codex führt die Pipeline aus und zeigt:
   - Maximalgeschwindigkeit / -leistung
   - Schnittpunkttabelle
   - Vorgeschlagene Zonen (Z1–Z6, Z6 als MAX)
   - Pflichtprüfungen-Ergebnis (intern)
5. Codex fragt: *„Möchtest du die vorgeschlagenen Zonen so übernehmen oder anpassen?"*
6. Antworte z.B.: `Z3 bis 9.0; Kontext: erste Session der Saison`
   — oder drücke Enter, um die Vorschläge zu übernehmen.
7. Codex erstellt den Endbericht: `output/<XY_LD_Sportart_JJ_MM_TT>_final_v1.docx`.

### Schritt 3: Bericht bearbeiten und versenden

Öffne den finalen Bericht in Word und überarbeite den Text. Seiten 1–4 sind
kundenfertig; Seite 5 ist die Trainerseite (Pflichtprüfungen, interne
Notizen). Lösche Seite 5 vor dem Versand an die Athletin / den Athleten.

---

## Visuelles Zonen-Tool (optional)

Wenn dir die Codex-Eingabe zu textlastig ist, kannst du Zonen auch grafisch
verschieben — ein Browser-UI mit vier Slidern für die Zonen-Obergrenzen
(Z2/Z3/Z4/Z5) und Live-Vorschau des Plots:

```bash
uv run streamlit run src/ld/zone_tool.py
```

Voraussetzung: einmaliges Setup mit `uv pip install -e ".[visual]"` (Phase 8).
Beim "Übernehmen"-Klick werden die neuen Zonen gespeichert und ein neuer Draft
erzeugt. Danach wieder Codex `/ld-report` aufrufen, um die Interpretation
einzubauen.

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

---

## Pflichtprüfungen verstehen

Vor der Interpretation prüft das Werkzeug automatisch die Plausibilität der Daten.
Diese Hinweise erscheinen NUR auf Seite 5 des Berichts (Trainerseite — intern).
Falls du sie löscht oder Seite 5 entfernst, sehen die Athlet:innen sie nicht.

| Was du siehst | Was es bedeutet |
|---------------|-----------------|
| „Letzte Stufe nicht vollständig (X von Y min). Maximalgeschwindigkeit wird aliquot berechnet." | Normal wenn der Athlet mittendrin abgebrochen hat — das Werkzeug rechnet das korrekt heraus. |
| „Herzfrequenz fällt zwischen Stufen ab." | Möglicher Messfehler oder kurze Erholung — prüfe die HF-Werte. |
| „Laktat fällt deutlich zwischen Stufen ab." | Ungewöhnlich — prüfe ob die Werte richtig eingetragen sind. |
| „Ungewöhnlich großer Laktatanstieg … Schwellenpassage oder Messfehler?" | Häufig an der Schwelle normal; prüfe trotzdem die Eingabe. |
| „RPE fällt mit steigender Belastung." | Wahrscheinlich Tippfehler in der Excel. |
| „Keine vollständige Ausbelastung erreicht." | Schwellen in der Interpretation vorsichtiger formulieren. |

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

### „Fehler: Uhrzeit muss im Format hh:mm sein"
→ Im Testprotokoll-Blatt das Feld Uhrzeit als z.B. `14:00` eintragen (nicht `2pm`).

### Codex zeigt nichts an
→ Prüfe `codex --version` im Terminal. Falls nicht installiert:
```bash
npm install -g @openai/codex && codex login
```

---

## Datenschutz

Der Entwurf und die vollständige JSON-Datei enthalten den echten Namen
der Athletin / des Athleten. Für die Codex-Interpretation wird automatisch eine
anonymisierte Version (`_for_llm.json`) verwendet — Name, Geburtsjahr und Email
werden ersetzt, nur das Alter bleibt (sofern angegeben).

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
