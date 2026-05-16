# Round 2 — Implementation Plan

Quelle: [PRODUCT_REFINEMENT_ROUND2.md](PRODUCT_REFINEMENT_ROUND2.md) (Anna-Maria, 13.05.2026)
Verfasst: 2026-05-16 — basiert auf Code-Audit nach Round-1-Commit `90b194c`.

Dieses Dokument verknüpft jedes Round-2-Feedback mit einer konkreten
Code-Stelle, einer Diagnose ("warum war Round 1 nicht genug?") und einer
Umsetzungsentscheidung.

---

## 1. Was Round 1 falsch gemacht hat (Root-Cause-Analyse)

Round 1 hat die **Mathematik** und die **Datenschicht** weitgehend richtig
adressiert, ist aber an drei strukturellen Punkten gescheitert:

### 1.1 Kein automatisiertes Render-QA → 5-Seiten-Ziel war ein Wunsch, keine Garantie

- `build_report_template.py` setzt 4× `page_break()` und nimmt an, das ergibt
  exakt 5 Seiten.
- `soffice`/LibreOffice ist auf dem Entwicklungssystem **nicht installiert**
  (`which soffice` → leer). Damit existiert keine Möglichkeit, die generierte
  `.docx` in PDF zu rendern und Seiten zu zählen.
- Resultat: Der Referenzfall rendert **9 Seiten** (Anna's Befund), weil
  Seite 2 (Athletendaten-KV + Testprotokoll-KV + Plot) und Seite 5
  (Pflichtprüfungen + Risiko + Schwellenlogik + Trainernotizen-KV) jeweils
  in zwei Seiten umbrechen. Ohne Render-Loop konnte das nicht bemerkt werden.
- **Lehre**: "Layout-Ziel ohne Render-Check" ist kein Layout, sondern eine
  Hoffnung. Sprint 1 dieses Plans liefert deshalb zuerst die Render-QA-Strecke.

### 1.2 Plot-Linien laufen über den Messbereich hinaus

In [src/ld/plots.py](../../src/ld/plots.py):

```python
x_rightmost = max(result.v_max, x_data_max)
x_padding = proto.stufeninkrement * 0.5
x_max = x_rightmost + x_padding
x_fine = np.linspace(x_min, x_max, 200)
lk_fit = np.array([result.cubic.predict(x) for x in x_fine])
hf_fit = np.array([result.hf_linear.predict(x) for x in x_fine])
```

- Die Fit-Kurven (`lk_fit`, `hf_fit`) werden bis `x_max` (also bis hinter
  `v_max`) gerechnet und gezeichnet.
- Damit suggeriert die Grafik einen gemessenen Laktatwert bzw. HF-Wert bei
  `v_max`, obwohl `v_max` aliquot aus einer unvollständigen Stufe geschätzt
  wurde.
- Round 2 ist hier explizit: *"Plot endet am letzten Messpunkt"* +
  *"`v_max` als vertikale Markierung oder Label, nicht als weiterer Messpunkt"*.

### 1.3 RPE-Migration halb durchgezogen

Round 1 hat in `zones.py` die Zonen-RPE-Werte auf 0-10 umgestellt, aber:

| Stelle | Stand | Erwartet |
|---|---|---|
| [src/ld/types.py:62](../../src/ld/types.py) | `# 6-20 scale (default per template)` | Kommentar 0-10 |
| [build_template.py:104](../../build_template.py) | `"RPE-Skala: 6-20 (Borg). 6=keine, 20=maximale Belastung"` | "RPE 0-10 (CR10): 0=keine, 10=maximal" |
| [build_template.py:108-115](../../build_template.py) | Beispieldaten `rpe=9,9,14,16,17,18` (Borg) | `rpe=2,3,5,6,7,8` (CR10) |
| [tests/unit/test_common.py:24-29](../../tests/unit/test_common.py) | Borg-Werte 9-18 | CR10 0-10 |
| [tests/protocols/fixtures/lauf/rainier_expected.json](../../tests/protocols/fixtures/lauf/rainier_expected.json) | Borg | CR10 |
| `io_input.py` | Keine RPE-Range-Validierung | Validate 0-10 |
| [build_report_template.py:309](../../build_report_template.py) | `"RPE"` Spaltenkopf | `"RPE (0-10)"` |
| [.codex/prompts/ld-report.md](../../.codex/prompts/ld-report.md) | RPE-Skala nicht erwähnt | Explizit 0-10 |

Round 2 nennt das *"inkonsistent"*. Korrekt.

### 1.4 Strukturelle Lücken (nicht in Round 1 adressiert)

- **Rohdaten-Tabelle auf Seite 2 fehlt komplett.** Round 1 zeigt nur Athlete-KV
  und Testprotokoll-KV, dann den Plot. Die Stufendaten (Stufe / Intensität /
  HF / Laktat / RPE) als Tabelle waren in Round 1 nicht im Template.
- **Schwellenschnittpunkt-Tabelle hat falsche Achsen.** Aktuell:
  1 Zeile pro Laktat-Zielwert, Spalten = Geschwindigkeit/Pace/HF. Round 2 will
  das **pivotiert**: Spaltenköpfe = gültige Laktatwerte, Zeilen =
  Geschwindigkeit/Pace/HF.
- **Seite 4 hat 3 Sektionen, braucht 4-5.** Aktuell: Zusammenfassung,
  Schwellen & Zonen, Empfehlungen. Round 2 will: Zusammenfassung,
  Schwellen & Zonen, **Nächste 3-4 Wochen**, **Energie & Regeneration**.
- **Deckblatt-Branding falsch.** [build_report_template.py:234](../../build_report_template.py)
  zeigt *"Erstellt von Anna-Maria Wörndle"*. Round 2 sagt: entfernen,
  stattdessen Sport AnnaLytics als Marke, Anna-Maria nur im Footer.
- **Marker-Form** für HF und Laktat ist identisch (Kreise). Round 2 will
  unterscheidbare Formen (HF = Kreise, Laktat = Quadrate).

---

## 2. P0-Akzeptanzkriterien (Sprint 1: Vertrauen & Korrektheit)

Diese Punkte müssen alle einen **Test** bekommen, der bei Regression rot wird.

### P0-1 — Render-QA-Strecke etablieren

**Was:** Build-Schritt, der den Referenzfall rendert und die Seitenzahl prüft.

**Wie:**
1. `soffice` als optionale Dev-Dependency dokumentieren (`brew install --cask libreoffice`).
2. Neuer Modul `src/ld/render_qa.py`:
   - `render_to_pdf(docx_path: Path) -> Path` via `soffice --headless --convert-to pdf`.
   - `count_pages(pdf_path: Path) -> int` via `pypdf` (bereits potenziell verfügbar; sonst hinzufügen).
3. Neuer pytest-Eintrag `tests/e2e/test_reference_5pages.py`:
   - Skip wenn `soffice` nicht gefunden (`pytest.skip(...)`).
   - Rendert `samples/<referenz>.xlsx` via `ld.run`, hängt Mock-Interpretation an,
     patcht, rendert via LibreOffice, prüft `count_pages == 5`.
4. CI-Hook: wenn Test rot, Build fail.

**Acceptance:** Test grün auf System mit installierter LibreOffice; sauber
geskippt ohne.

### P0-2 — Seitenzahl auf 5 Seiten zwingen (Referenzfall)

**Was:** Das Layout so verdichten, dass der Rainier-Referenzfall bei
LibreOffice-Render genau 5 Seiten ergibt.

**Wie:** Strukturelle Eingriffe in [build_report_template.py](../../build_report_template.py):

- **Seite 2 (Daten + Plot):**
  - Athletendaten + Testprotokoll als **zweispaltiges Layout** (eine docx-Table mit zwei "Spalten" à 2 Sub-Tables).
  - Rohdaten-Tabelle als breite, kompakte Tabelle darunter (max 10 sichtbare
    Stufen — bei mehr Stufen Hinweis im Trainerteil).
  - Plot kleiner (`_PLOT_WIDTH_CM` reduzieren von 22.0 auf ~18.0).
  - Schriftgröße auf Seite 2 systematisch auf 9pt (statt 10).
- **Seite 5 (Trainerseite):**
  - 2×2-Kachelstruktur: oben links Pflichtprüfungen, oben rechts Risikoanalyse,
    unten links Schwellenlogik, unten rechts Testqualitätskontrolle.
  - Trainernotizen als kompakte 6-zeilige Tabelle DARUNTER (eine Spalte
    "Feld" + eine Spalte "Inhalt", kein zusätzlicher KV-Block).

**Acceptance:** Render-QA-Test grün — exakt 5 Seiten für Rainier-Fixture.

### P0-3 — RPE komplett auf 0-10 (CR10)

**Was:** Alle Stellen einheitlich auf 0-10 Borg-CR10.

**Wie:**
1. [src/ld/types.py:62](../../src/ld/types.py) — Kommentar auf `# 0-10 (Borg CR10)` updaten.
2. [build_template.py:104](../../build_template.py) — Hinweistext: `"RPE-Skala: 0-10 (Borg CR10). 0=keine Anstrengung, 10=maximale Anstrengung"`.
3. [build_template.py:110-116](../../build_template.py) — Rainier-Beispieldaten auf CR10 ableiten
   (Mapping: Borg 9→2, 9→2, 14→5, 16→7, 17→8, 18→9 — Annäherung gemäß
   Borg-Konversionstabelle, finaler Wert mit Anna abstimmen).
4. [src/ld/io_input.py](../../src/ld/io_input.py) — In `_parse_steps()` nach dem Cast `rpe = _int_or_none(...)`
   einen Range-Check ergänzen: `if rpe is not None and not (0 <= rpe <= 10): raise LDInputError("RPE muss zwischen 0 und 10 liegen.")`.
5. [tests/unit/test_common.py:24-29](../../tests/unit/test_common.py) — Fixture-Werte auf CR10.
6. [tests/protocols/fixtures/lauf/rainier_expected.json](../../tests/protocols/fixtures/lauf/rainier_expected.json) — analog.
7. [build_report_template.py:309](../../build_report_template.py) — Zonen-Tabellenkopf `"RPE (0-10)"`.
8. [.codex/prompts/ld-report.md](../../.codex/prompts/ld-report.md) — In Schritt 3 nach "Vorgeschlagene Zonen" einen Hinweis
   einfügen: "RPE wird auf 0-10 (Borg CR10) angegeben."

**Acceptance:** Neuer Test `tests/unit/test_rpe_validation.py` — eine Datei
mit RPE=18 (Borg-Wert) erzeugt `LDInputError`.

### P0-4 — Plot endet am letzten Messpunkt

**Was:** Fit-Linien dürfen `x_data_max` nicht überschreiten. `v_max` separat
als vertikale Markierung.

**Wie:** In [src/ld/plots.py](../../src/ld/plots.py):

1. Den Bereich für `x_fine` auf `[x_min, x_data_max]` begrenzen — NICHT auf
   `x_max` (das ist der Anzeige-Edge inkl. Padding).
2. `x_max` (Anzeige) bleibt `max(v_max, x_data_max) + padding`, damit der
   `v_max`-Marker visuell hineinpasst.
3. Wenn `result.v_max > x_data_max` (aliquot-Fall):
   - `ax_lk.axvline(v_max, color="#0B2545", linestyle="--", linewidth=1.2, zorder=2)`
   - `ax_lk.text(v_max, lk_max + 0.5, "vmax", ha="center", va="bottom", fontsize=8, color="#0B2545")`
   - Kein Datenmarker bei `v_max`.
4. Datenmarker auf unterschiedliche Formen umstellen:
   - HF: `"o"` (Kreis, blau) — bleibt.
   - Laktat: `"s"` (Quadrat, rot).

**Acceptance:** Visueller Test (Snapshot) — die rechte Kante der Laktat-Fit-Linie
liegt bei `x_data_max`, nicht bei `x_max`. `v_max`-Vertikale ist sichtbar,
wenn `v_max > x_data_max`.

### P0-5 — Rohdaten-Tabelle auf Seite 2

**Was:** Sichtbare Tabelle der Stufendaten (Stufe / Intensität / HF / Laktat / RPE).

**Wie:** In [build_report_template.py](../../build_report_template.py) nach dem Testprotokoll-KV-Block
einen Aufruf von `add_table_with_loop()` mit:

```
headers=["Stufe", "{{ x_axis_label }}", "Herzfrequenz (bpm)", "Laktat (mmol/l)", "RPE (0-10)"]
row_template=["{{ s.stufe }}", "{{ s.intensitaet }}", "{{ s.herzfrequenz_bpm }}", "{{ s.laktat_mmol }}", "{{ s.rpe }}"]
loop_var="s", items_var="steps"
```

Tabelle in 9pt Schrift, kompakte Zellen. Bei mehr als 10 Stufen: Warnung
im Trainerteil, Tabelle bleibt voll im Render (Vereinfachung erste Iteration).

**Acceptance:** Render-Test prüft Existenz der Tabelle und Spaltenanzahl.

### P0-6 — Schwellenschnittpunkt-Tabelle pivotieren

**Was:** Matrix-Layout statt Zeilentabelle.

**Wie:** Aktuell:

```
| Laktat | Geschwindigkeit | Pace | HF |
| 2.0    | 9.2             | 6:31 | 145 |
| 3.0    | 10.4            | 5:46 | 158 |
```

Neu:

```
|                          | 2.0  | 3.0  | 4.0  |
| Geschwindigkeit (km/h)   | 9.2  | 10.4 | 11.2 |
| Pace (min/km)            | 6:31 | 5:46 | 5:21 |
| Herzfrequenz (bpm)       | 145  | 158  | 167  |
```

Ungültige Laktatwerte werden als ganze Spalte weggelassen, nicht als
"—"-Platzhalter.

**Implementierung:**
- In [src/ld/report.py](../../src/ld/report.py) `_render_intersections()` umbauen, sodass es zwei
  Kontextvariablen erzeugt:
  - `intersection_columns`: tuple of laktat values (nur die mit valid root).
  - `intersection_rows`: tuple of dicts mit `label` + `values` (eine Zeile
    pro Metrik, eine Spalte pro gültigem Laktatwert).
- In [build_report_template.py](../../build_report_template.py) eine neue Helper-Funktion `add_pivot_table()`,
  die einen docxtpl-Inner-Loop in den Spalten der ersten Zeile + einen
  äußeren Loop über die Metric-Zeilen generiert. (Achtung: docxtpl `{%tc%}`
  für Tabellenzellen-Loops verwenden.)

**Acceptance:** Neuer Test `tests/unit/test_intersections_pivot.py` —
Wenn `lk=1.0` ungültig ist, hat die Pivot-Tabelle 3 statt 4 Spalten.

### P0-7 — Marker-Formen unterscheiden

Siehe P0-4 (im selben Plot-Refactor erledigt).

---

## 3. P1 — Layout & Informationsarchitektur (Sprint 2: Premium-Layout)

### P1-1 — Deckblatt bereinigen

[build_report_template.py:228-240](../../build_report_template.py):

- **Entfernen**: Zeile 234, `"Erstellt von Anna-Maria Wörndle"`.
- **Behalten**: Kontaktzeile (Email + Telefon), da auch im Footer.
  → Cleaner: nur Logo, Titel, Name, Datum/Ort. Kontakt nur im Footer ab Seite 2.
- **Titel ändern**: `"Leistungsdiagnostik {{ athlete.sportart_label }}"` —
  Logikfrage: bei "Lauf" wird daraus "Leistungsdiagnostik Lauf" (gewünscht),
  bei "Rad" "Leistungsdiagnostik Rad". Sportart-Label-Mapping ist bereits
  korrekt in [src/ld/report.py:34-40](../../src/ld/report.py).
- **Logo-Größe**: bereits 6.0 cm — bleibt im 5-7-cm-Korridor.
- **Marken-Subtext** ergänzen: kleine Zeile unter dem Titel:
  `"Sport AnnaLytics"` in `ACCENT` Türkis, 14pt. (Anna abstimmen — siehe
  offene Frage 3 im Round-2-Brief.)

### P1-2 — Footer als Markenanker

Aktuell vorhanden ([build_report_template.py:387-449](../../build_report_template.py)). Anpassungen:

- Footer-Schriftgröße auf 8pt — passt.
- Grauwert `TEXT` (#2C2C2C) ist zu dunkel für Footer-Ruhe. Auf
  `RGBColor(0x6B, 0x6B, 0x6B)` umstellen, nur für Footer-Runs.
- Trennlinie oben: aktuell pro Zelle → erzeugt segmentierte Optik.
  Auf eine einzige durchgehende Linie umstellen (Paragraph-Border am
  ersten Footer-Paragraph statt Cell-Border).

### P1-3 — Zonen-Tabelle farbig hinterlegen

[build_report_template.py:307-322](../../build_report_template.py):

- Aktuell: alle Zellen weiß, Trennlinien grau.
- Neu: Pro Zonen-Zeile Zellhintergrund mit der entsprechenden Zonenfarbe aus
  [src/ld/plots.py:22-29](../../src/ld/plots.py) (Hex), mit ~15% Opacity → in DOCX kein echtes Alpha,
  daher die Farbe in **aufgehellter Version** verwenden:
  - Z1: `#E3F0FA` (Hellblau aufgehellt)
  - Z2: `#E4F4DC` (Grün aufgehellt)
  - Z3: `#FFF6CC` (Gelb aufgehellt)
  - Z4: `#F7E9B0` (Dunkelgelb aufgehellt)
  - Z5: `#FFE0CC` (Orange aufgehellt)
  - Z6: `#FBDBDC` (Rot aufgehellt)
- Umsetzung: docxtpl unterstützt keine bedingte Zellfärbung über Loop direkt.
  Workaround: in [src/ld/report.py](../../src/ld/report.py) `_render_zones()` ein Feld `bg_hex` pro Zone
  ergänzen; im Template `{%tr for z in zones %}` durch eine vordefinierte
  Zeilenstruktur ersetzen, in der jede Zelle einen `<w:shd>` mit einem
  Jinja-eval'd `w:fill` enthält. Falls das docxtpl-XML zu sperrig wird:
  Workaround Post-Render mit python-docx, der das fertige Dokument nochmal
  öffnet und die Zonen-Tabelle einfärbt.

**Acceptance:** Visuelle Begutachtung; Tabellenzeile Z3 hat gelben Hintergrund.

### P1-4 — Codex-Prompt erweitern (4. + 5. Sektion)

[.codex/prompts/ld-report.md](../../.codex/prompts/ld-report.md):

In Schritt 6 das JSON-Schema erweitern:

```json
{
  "zusammenfassung": "...",                     // 120-150 Wörter
  "schwellen": "...",                           // 120-150 Wörter
  "coaching_ausblick_3_4_wochen": "...",        // 3-5 konkrete Leitlinien
  "ernaehrung": "...",                          // 1 Absatz
  "risiko": "..."                               // optional, intern
}
```

**Prompt-Regeln ergänzen:**

- Maximale Wortzahlen pro Sektion explizit nennen.
- "Kein erfundener Wochenplan" — keine konkreten Einheiten-Listen.
- "Allgemeine, evidenzbasierte Ernährungstipps; keine medizinische
  Beratung" + die ACSM/ISSN-Quellenanker als Footnote-ähnliche Erinnerung
  für Codex (nicht im Output).
- "empfehlungen" als Feldname wird durch `coaching_ausblick_3_4_wochen`
  ersetzt — alter Schlüssel als Alias akzeptieren in `patch_interpretation`
  für Übergangskompatibilität.

### P1-5 — Seite 4 strukturell umbauen

[build_report_template.py:326-337](../../build_report_template.py):

Aktuell: Zusammenfassung / Schwellen & Zonen / Empfehlungen (3 Blöcke).

Neu (4 Blöcke):

```python
heading("Interpretation", level=1)
heading("Zusammenfassung", level=2)
body("{{ interp_zusammenfassung }}")

heading("Schwellen & Zonen", level=2)
body("{{ interp_schwellen }}")

heading("Nächste 3-4 Wochen", level=2)
body("{{ interp_coaching_ausblick }}")

heading("Energie & Regeneration", level=2)
body("{{ interp_ernaehrung }}")
```

In [src/ld/report.py](../../src/ld/report.py) Context-Dict:
- `interp_coaching_ausblick = interp.get("coaching_ausblick_3_4_wochen", interp.get("empfehlungen", "[Interpretation: ausstehend]"))`
- `interp_ernaehrung = interp.get("ernaehrung", "[Interpretation: ausstehend]")`

**Risiko**: Wenn Codex die neuen Felder nicht füllt, fällt es zurück auf
`empfehlungen` → "Nächste 3-4 Wochen" zeigt den alten Empfehlungstext,
"Energie & Regeneration" zeigt den Platzhalter. Das ist sichtbar im Render
und treibt Codex zur Korrektur.

### P1-6 — Seite-5-Restrukturierung

Aktuell: 4 lineare Absätze. Neu: 2×2-Kachel-Layout.

In [build_report_template.py](../../build_report_template.py):

- Eine 2×2-Tabelle (4 Zellen, jede mit eigener Mini-Sektion).
- Zelle 1 (oben links): Pflichtprüfungen.
- Zelle 2 (oben rechts): Risikoanalyse.
- Zelle 3 (unten links): Schwellenlogik.
- Zelle 4 (unten rechts): Testqualitäts-Bewertung (NEU — kommt aus
  `pflichtpruefungen.run_all()`-Summary: "X von 6 Checks OK").
- Darunter: 6-zeilige Trainernotizen-Tabelle (kompakt, 2 Spalten).

---

## 4. P2 — Sonstige Verfeinerungen (Sprint 3 oder später)

### P2-1 — Marken-Subtext / Sport AnnaLytics
Siehe P1-1. Bedarf eine Entscheidung von Anna (offene Frage 3).

### P2-2 — Plot-Höhe optional reduzieren
Falls Page 2 trotz Rohdaten-Tabelle + zweispaltigem KV-Block überläuft:
`_FIGSIZE = (10.0, 5.0)` statt `(10.0, 6.0)`.

### P2-3 — Visuelles Zonen-Tool
Bleibt P2 wie in Round 1. Nicht für diese Iteration.

---

## 5. Tests, die neu hinzukommen müssen

| Test | Zweck |
|---|---|
| `tests/unit/test_rpe_validation.py` | RPE outside 0-10 → `LDInputError` |
| `tests/unit/test_intersections_pivot.py` | Pivot-Tabelle hat richtige Spalten/Zeilen, ungültige Laktatwerte gefiltert |
| `tests/unit/test_plot_no_extrapolation.py` | Fit-Linien enden bei `x_data_max`, nicht bei `x_max` (Snapshot oder Array-Check via mock-matplotlib) |
| `tests/e2e/test_reference_5pages.py` | Referenzfall rendert in 5 Seiten (skip ohne soffice) |
| `tests/unit/test_zone_meta_rpe_010.py` | `ZONE_META` Werte alle in [0, 10] |
| `tests/unit/test_interpretation_fields.py` | `report.render()` mit neuen Feldern (`coaching_ausblick_3_4_wochen`, `ernaehrung`) im Context |
| `tests/unit/test_codex_prompt_schema.py` | Markdown-Prompt nennt alle 5 Schlüssel inkl. neuer Felder (Grep-basiert) |

---

## 6. Reihenfolge — empfohlene Umsetzung

### Sprint 1 — Korrektheit & QA-Strecke (P0-1 bis P0-7)
1. Render-QA-Infrastruktur (P0-1).
2. RPE-Migration komplett durchziehen (P0-3) — kleinste, isolierte Änderung, zuerst.
3. Plot-Fix (P0-4 + P0-7).
4. Rohdaten-Tabelle (P0-5) und Pivot-Tabelle (P0-6) — beide ändern den Template-Aufbau.
5. **Render-QA-Test grün bekommen** (P0-2) — wahrscheinlich erst nach
   Layout-Verdichtung auf Seite 2 und Seite 5.

### Sprint 2 — Premium-Look (P1-1 bis P1-6)
6. Deckblatt (P1-1).
7. Footer-Politur (P1-2).
8. Codex-Prompt erweitern + Seite 4 neu (P1-4 + P1-5).
9. Seite-5-Kachel (P1-6).
10. Zonen-Tabelle farbig (P1-3) — am Ende, weil python-docx Cell-Shading
    am sperrigsten ist.

### Sprint 3 — Coaching-Mehrwert
Greift wenn Sprint 2 Render-QA-grün ist. Hier vor allem den Codex-Prompt
mit konkreten Beispieltexten für `coaching_ausblick_3_4_wochen` und
`ernaehrung` füttern, damit Anna nicht jede Iteration manuell nachschärft.

---

## 7. Offene Punkte, die Anna entscheiden muss

(Übernommen aus Round-2-Brief, Sektion "Offene Produktfragen")

1. **Hard 5-Seiten-Cap oder nur Referenzfall?** Empfehlung: Hard für
   Referenzfall (Test rot bei >5), Warning für Edge Cases.
2. **Sehr lange Trainernotizen** — kürzen, warnen, oder Seite 6 intern?
   Empfehlung: Warnung im stdout der Pipeline, Seite 6 nicht erlauben.
3. **`Sport AnnaLytics` als sichtbare Marke?** Empfehlung: ja, im
   Marken-Subtext Deckblatt + dezenter Footer-Reminder.
4. **Detail-Tiefe des 3-4-Wochen-Ausblicks** — siehe Prompt-Regeln in P1-4:
   "3-5 Leitlinien, keine konkreten Wochenpläne".
5. **Ernährungstipps immer oder bedingt?** Empfehlung: immer, weil sonst
   die 4-Block-Struktur auf Seite 4 inkonsistent bricht. Bei kurzen
   Belastungsdauern: kürzerer Absatz statt Weglassen.

---

## 8. Risiken

- **Page-Count-Verdichtung schlägt fehl.** Wenn Seite 2 mit Athlet-KV +
  Testprotokoll-KV + Rohdaten-Tabelle + Plot trotz zweispaltigem Layout
  überläuft: Plan-B = Athletendaten verkleinern (nur Name, Sportart, Alter,
  Gewicht, Größe — Rest in Trainerseite verschieben).
- **docxtpl Pivot-Tabelle.** Der `{%tc%}` (Tabellenzellen-Loop) ist weniger
  robust als `{%tr%}`. Wenn das nicht sauber rendert: Plan-B = Pivot in
  Python im Renderer aus python-docx direkt bauen (template hat Platzhalter,
  Renderer ersetzt die Tabelle als Ganzes).
- **Cell-Shading per docxtpl.** Erfahrungswert: docxtpl handhabt direkte
  XML-Manipulation in Loops schlecht. Plan-B (siehe P1-3): Post-Render-
  Color-Pass in `report.py`.

---

## 9. Zusammenfassung in einem Satz

Round 1 hat die Mathematik richtig gemacht, aber das Layout-Ziel ohne
Render-QA nur gehofft; Round 2 erfordert (a) eine echte Render-QA-Strecke
mit LibreOffice, (b) konsequente RPE-CR10-Migration, (c) Plot-Linien nur
im Messbereich + unterscheidbare Marker, (d) Pivot-Schwellentabelle +
Rohdaten-Tabelle auf Seite 2, und (e) eine 4-Block-Interpretation auf
Seite 4 mit neuen Codex-Schlüsseln für Coaching-Ausblick und Ernährung —
durchgesetzt durch automatisierten 5-Seiten-Test.
