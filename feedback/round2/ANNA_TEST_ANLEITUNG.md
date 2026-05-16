# Round-2-Test — Anleitung für Anna-Maria

Status: Round-2-Feedback ist umgesetzt, 62 Tests grün, finaler Bericht
visuell geprüft. Jetzt bist du dran mit Feedback für Round 3.

---

## 1. Update einspielen (ZIP-Workflow)

Falls Codex noch läuft: vorher beenden (`Ctrl+C`).

**Schritt 1a — Eingabe- und Ausgabe-Daten sichern**, damit nichts verloren geht:

```
mv ~/Desktop/leistungsdiagnostik/input ~/Desktop/ld_input_backup
mv ~/Desktop/leistungsdiagnostik/output ~/Desktop/ld_output_backup
```

**Schritt 1b — Neue Version laden:**

1. Gehe auf https://github.com/woerchri/leistungsdiagnostik
2. Wechsle oben links den Branch auf **`main`** (falls nicht schon ausgewählt).
3. Klicke auf den grünen **"Code"**-Button → **"Download ZIP"**.
4. Entpacke die ZIP, sodass der Ordner heißt: `~/Desktop/leistungsdiagnostik`
   (alten Ordner vorher in `~/Desktop/leistungsdiagnostik_alt` umbenennen
   oder löschen).

**Schritt 1c — Daten zurückspielen:**

```
mv ~/Desktop/ld_input_backup ~/Desktop/leistungsdiagnostik/input
mv ~/Desktop/ld_output_backup ~/Desktop/leistungsdiagnostik/output
```

**Schritt 1d — Abhängigkeiten aktualisieren:**

```
cd ~/Desktop/leistungsdiagnostik
uv sync
```

**Optional, aber empfohlen — LibreOffice installieren**, damit der 5-Seiten-
Check beim Bauen automatisch geprüft wird:

```
brew install --cask libreoffice
```

## 2. Bericht generieren

Wie gewohnt:

1. Datei in `~/Desktop/leistungsdiagnostik/input/` ablegen.
2. `Leistungsdiagnostik.command` auf dem Desktop doppelklicken.
3. `/ld-report` tippen.
4. Vorgeschlagene Zonen prüfen → bestätigen oder anpassen.
5. Endbericht liegt in `output/` als `XY_LD_Sportart_JJ_MM_TT_v<n>.docx`.

**Neu seit Round 2**: Codex fragt jetzt nicht nur nach drei Interpretations-
absätzen, sondern nach vier — `zusammenfassung`, `schwellen`,
`coaching_ausblick_3_4_wochen` und `ernaehrung`. Plus optional `risiko`
für die Trainerseite. Bitte beim Schreiben kurz prüfen ob die neuen
Vorgaben (max. 120-200 Wörter pro Block, kein erfundener Wochenplan,
keine medizinische Ernährungsberatung) im Output ankommen.

## 3. Was sich geändert hat (Round 2 → was du jetzt prüfen sollst)

**Layout** — Bitte konkret darauf achten:
- Bericht ist exakt 5 Seiten? (Ja oder nein? Bei "nein": welche Seite springt um?)
- Plot auf Seite 2 zusammen mit Daten + Rohdaten?
- Schwellenschnittpunkt-Tabelle in der neuen Pivot-Form (Laktatwerte als
  Spaltenköpfe, Metriken als Zeilen)? Fühlt sich das diagnostischer an als
  vorher die lange Zeilentabelle?
- Trainingsbereiche-Tabelle mit farbig hinterlegten Zonenzeilen? Farbintensität ok?
- Z1 zeigt `≤ Geschwindigkeit`, `≥ Pace`, `≤ HF`? Z6 zeigt `MAX`?
- HF-Punkte als Kreise, Laktat-Punkte als Quadrate — gut unterscheidbar?
- Plot-Fit-Kurve endet beim letzten Messpunkt, NICHT bei vmax? (Wenn vmax
  aliquot extrapoliert wurde, sollte er als gestrichelte vertikale Linie
  + Label erscheinen, NICHT als weiterer Messpunkt.)
- Seite 5 als 2×2-Kachel + Trainernotizen-Tabelle — übersichtlicher als
  die Round-1-Bulletliste?

**Sprache & RPE**:
- Bitte beim Einlesen der Excel-Daten: RPE-Skala ist jetzt 0-10 (Borg CR10).
  Alte Borg-6-20-Werte werden vom Werkzeug abgewiesen. Falls du Altdatensätze
  testest: RPE umrechnen (Borg 9→2, 12→3, 14→5, 16→7, 18→9, 20→10).
- Codex spricht dich konsequent mit Vornamen an?
- "Maximalgeschwindigkeit" überall statt "v_max"?

**Marketing-Look**:
- Deckblatt clean, ohne "Erstellt von Anna-Maria Wörndle"?
- "Sport AnnaLytics" als Marken-Subtext sichtbar?
- Footer ruhig (heller Grauton, durchgehende Trennlinie)?

## 4. Offene Entscheidungen, die ich von dir brauche

Diese 5 Fragen stehen aus Round 2 noch offen und beeinflussen Folgeentwicklung.
Bitte je ein, zwei Sätze:

### Frage 1 — Hartes 5-Seiten-Cap?
Soll der Bericht IMMER auf 5 Seiten begrenzt sein (Build/Test fail bei mehr),
oder darf bei sehr langen Trainernotizen / vielen Pflichtprüfungs-Hinweisen
eine 6. Seite intern entstehen?

**Empfehlung**: Hart für Standardfall (Test rot bei >5), Warnung statt Fail
bei Edge Cases.

### Frage 2 — Lange Trainernotizen
Wenn du auf Seite 5 sehr viel reinschreibst: Kürzen-Warnung, automatisch
abschneiden, oder Seite 6 intern erlauben (nur intern, nie kundenseitig)?

### Frage 3 — Sport AnnaLytics als sichtbare Marke?
Aktuell steht "Sport AnnaLytics" als Marken-Subtext auf dem Deckblatt und
im Footer-Logo. Anna-Maria erscheint nur in den Kontaktdaten im Footer.
Passt das, oder soll dein Name größer / sichtbarer?

### Frage 4 — Wie detailliert darf der 3-4-Wochen-Ausblick sein?
Aktuell sind es 3-5 konkrete Leitlinien, KEIN fertiger Wochenplan
(weil Trainingskalender und Verfügbarkeit ja nicht im Input stehen).
Reicht das, oder willst du mehr konkrete Einheitenvorschläge?

### Frage 5 — Ernährungstipps immer oder bedingt?
Aktuell erscheint der Energie-&-Regenerations-Block IMMER auf Seite 4
(damit das 4-Block-Layout konsistent bleibt). Soll der Block bei sehr
kurzen Tests (z.B. 30-Minuten-Stufentests ohne lange Belastungsdauer)
weggelassen werden, oder soll er immer erscheinen — ggf. kürzer?

## 5. Wie du Feedback gibst

Wie in Round 1+2 am liebsten: kommentiere direkt in der `.docx` (Word
Kommentare oder gelbe Markierungen). Spezifisch:

- Layout-Probleme: Screenshot oder Word-Kommentar.
- Falsche Zahlen / Formulierungen: Word-Kommentar an der Stelle.
- Strukturelle Wünsche: lieber als neue Markdown-Datei
  (`feedback/round3/...`) oder eben als Kommentar in der `.docx`.

Speichere die kommentierte Datei mit `_Korrektur` im Namen und schick sie
mir zurück. Ich übersetze das wieder in einen Plan und implementiere es.

Round 3 ist hoffentlich der finale Schliff vor dem ersten echten
Athletinnen-Testbericht.
