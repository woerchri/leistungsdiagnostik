# Handoff: Korrekturfeedback Leistungsdiagnostik-Auswertung

Quelle: `26_05_LD_Dateneingabe_Korrektur.docx` von Anna-Maria, 13.05.2026.

Ziel: Das Feedback in umsetzbare Anforderungen fuer Christopher/Claude uebersetzen. Die Python-Pipeline bleibt die autoritative Recheninstanz. Keine Zahlen in `output/*.json` manuell veraendern.

## Produktziel

Die Auswertung soll sich wie ein professioneller, trainereditierbarer Leistungsdiagnostik-Report anfuehlen:

- Seite 1-4: kundenfertig fuer Athlet:innen.
- Seite 5: interne Trainerseite, vor Weitergabe entfernbar.
- Zonen sind Vorschlaege, die Trainer:innen final bestaetigen oder anpassen.
- Pflichtpruefungen werden vor Interpretation gezeigt, im finalen Report aber nur intern platziert.
- Interpretation ist fachlich mutiger als reine Vorsichtssprache: HIT/hochintensive Reize duerfen empfohlen werden, wenn Testbild, Trainingshistorie, Ziel und Belastbarkeit das hergeben.

## Kritische Produktentscheidungen

Diese Punkte bitte vor oder waehrend der Umsetzung bewusst entscheiden:

1. **"Nicht API verwenden - sondern Codex direkt" widerspricht dem aktuellen Fallback-Ziel.** Aktuell nutzt `src/ld/interpret.py` die OpenAI API, damit `uv run python -m ld.run ... --interpret` standalone funktioniert. Empfehlung: zwei Modi bauen, statt API komplett zu entfernen:
   - Codex-Modus: `/ld-report` laesst Codex die Interpretation im Dialog erstellen und in JSON/Docx patchen.
   - Fallback-Modus: API bleibt optional fuer standalone.
2. **"Exakt 5 Seiten" ist ein Layout-Ziel, aber kein rein technisches Naturgesetz.** Bei langen Coachingnotizen oder vielen Warnungen braucht es Inhaltslimits, feste Seitenumbrueche und visuelle Render-QA. Akzeptanzkriterium: Referenzfall Anna passt auf 5 Seiten A4 quer; bei Ueberlauf klare Warnung statt still verrutschendem PDF.
3. **Geburtsjahr optional?** Feedback sagt bei Athlet-Rohdaten "Geburtsjahr ok wenn leer". Aktuell ist Geburtsjahr Pflicht und Alter wird daraus abgeleitet. Klaeren: Soll Alter dann leer bleiben, manuell eingegeben werden, oder aus Datenschutzgruenden gar nicht mehr erscheinen?
4. **Z1 im Report:** Feedback sagt "Wenn Zone 1 sinnvoll ist". Aktuell ist Z1 leer angelegt. Entscheidung: Z1 automatisch aus Untergrenze Z2 ableiten (`< Geschwindigkeit`, `< HF`, `> Pace`) oder Z1 nur anzeigen, wenn Z2-Obergrenze valide ist.

## P0: Fachlich/mathematische Korrekturen

1. **Schwellenschnittpunkte sauber filtern**
   - Wenn ein Ziel-Laktat keinen validen Schnittpunkt im sinnvollen Testbereich hat: komplette Tabellenzeile entfernen, nicht mit `None`, `-` oder extrapolierten Fantasiewerten anzeigen.
   - Betrifft Geschwindigkeit/Leistung, Pace und HF.
   - Datei vermutlich: `src/ld/protocols/_common.py`, `src/ld/report.py`, Template.

2. **Kubische Polynom-Schnittpunkte richtig waehlen**
   - Bei mehreren realen Schnittpunkten im Testbereich den groesseren x-Wert verwenden.
   - Aktuell nimmt `intersection_table()` den kleinsten `in_range`-Root.
   - Akzeptanztest ergaenzen: kubische Kurve mit mehreren Roots im Bereich -> groesserer x-Wert wird gewaehlt.

3. **Keine rein fixen mmol-Zonen**
   - Bestehende Heuristik nutzt 2/3/4 mmol sehr direkt. Das widerspricht der Spezifikation, wenn es als Schwellenlogik verkauft wird.
   - Claude soll die Logik transparent machen: 2/3/4 mmol duerfen Orientierungspunkte sein, aber Zonevorschlag muss Kurvenform, HF-Verlauf und RPE-Muster beruecksichtigen und als Vorschlag markiert bleiben.

4. **Z6 als Max-Bereich formatieren**
   - Zone 6: Geschwindigkeit/Leistung, HF und Pace nicht als numerische Obergrenze ausgeben, sondern als `MAX`.
   - RPE fuer Z6 fix `10`, Z5 fix `9`.

5. **Z1 sinnvoll formatieren**
   - Wenn Z1 angezeigt wird: `Geschwindigkeit < x`, `HF < y`, `Pace > p`.
   - Keine leeren Z1-Zellen im kundenfertigen Report.

## P1: Input- und Workflow-Korrekturen

1. **Dateibenennung**
   - Gewuenscht: `XY_LD_Sportart_JJ_MM_TT`
   - X = erster Buchstabe Vorname, Y = erster Buchstabe Nachname.
   - Umsetzungsvorschlag: Warnung oder automatische Ausgabe-Basename-Normalisierung, nicht Eingabedateien zwangsweise umbenennen.

2. **Athlet-Rohdaten erweitern**
   - E-Mail-Adresse hinzufuegen.
   - Geburtsjahr optional klaeren und entsprechend parser/template anpassen.

3. **Testprotokoll-Rohdaten erweitern**
   - Nachbelastungslaktat nach 3 min und 5 min optional ergaenzen.
   - Leere Felder sind okay.

4. **Begriffe und Einheiten**
   - `Anfangsintensität` -> `Anfangsbelastung`.
   - Einheit sichtbar machen: bei Lauf `km/h`, Rad `W`, unspezifisch `Stufe`.
   - `Inkrement` ebenfalls mit Einheit.
   - `v_max` im Report und in Interpretation konsequent `Maximalgeschwindigkeit` nennen.
   - Sportart aus Athletendaten entfernen und bei Testprotokoll anzeigen.
   - Uhrzeit im Format `hh:mm`.

5. **Rundung**
   - Alle Geschwindigkeiten in km/h im Report auf eine Nachkommastelle.
   - Achtung: JSON-Werte nicht veraendern; Formatierung nur in Report-/Display-Schicht.

## P1: Report, Tabellen und Diagramm

1. **Diagramm mit Trainingszonen**
   - Zonen farbig hinterlegen: Z1 hellblau, Z2 gruen, Z3 gelb, Z4 dunkelgelb, Z5 orange, Z6 rot.
   - Farben transparent und hochwertig, nicht grell.
   - Letzter Datenpunkt muss sichtbar bleiben: x/y-Limits mit Padding setzen.
   - HF-Achse rechts:
     - Minimum = HF-Minimum abrunden minus 10.
     - Maximum = HF-Maximum aufrunden plus 10.
     - Hauptstriche alle 10 bpm.
     - Achsenbeschriftung: `Herzfrequenz (bpm)`.
     - HF als lineare Funktion plus markierte Datenpunkte, blau.

2. **Trainingsbereich-Tabelle**
   - `vmin` und `vmax` in einer Spalte `von-bis` kombinieren.
   - `HFmin` und `HFmax` in einer Spalte `von-bis` kombinieren.
   - Pace ebenfalls als Bereich darstellen.
   - Werte mittig ausrichten.
   - Nur ein Tabellenkopf fuer die ganze Tabelle, nicht ein separater Kopf pro Zone.

3. **Schwellenschnittpunkt-Tabelle**
   - Nur ein Tabellenkopf.
   - Nicht vorhandene Laktat-Schnittpunkte komplett entfernen.
   - Werte mittig ausrichten.

4. **Visuelles Zonen-Tool**
   - Spaeteres Ziel: Trainer:in kann Zonen direkt in der Grafik verschieben.
   - Fuer jetzt reicht ein Codex-Dialog/CLI-Override, aber das Datenmodell sollte Zonen-Grenzen als editierbare Bounds fuehren.

## P1: Layout-Zielbild

Format:

- DIN A4 quer.
- Modern, sportlich, hochwertig, Coaching-/Performance-Look.
- Clean, minimalistisch, sportwissenschaftlich-modern.
- Viel Weissraum, klare Typografie, kompakte Textbloecke, moderne Tabellen, hochwertige Diagramme, sparsame dezente Icons.
- PDF-exportfaehig ohne verrutschende Seitenumbrueche.

Farben:

- Primaer: Dunkelblau.
- Akzent: Tuerkis.
- Text: Dunkelgrau.
- Linien: Hellgrau.
- Trainingszonen: Z1 Hellblau, Z2 Gruen, Z3 Gelb, Z4 Dunkelgelb, Z5 Orange, Z6 Rot.

Logo:

- Scharf, proportional, nie verzerrt.
- Deckblatt: mittig, ca. 5-7 cm breit, viel Weissraum.
- Folgeseiten: kleines monochromes Logo rechts unten, ca. 1.8-2.2 cm.

Footer:

- Auf allen Seiten ausser Deckblatt.
- Kontaktdaten links: `anna-maria@woerndle.at`, `+43 677 62150496`.
- Seitenzahl rechts.
- Logo rechts unten.
- Duenne horizontale Trennlinie.
- Keine Seitenzahl auf Seite 1.

Seitenaufbau:

1. Deckblatt: `Leistungsdiagnostik Laufen`, Athlet:innenname, Testdatum, Testort, Trainerkontaktdaten, Trainerlogo.
2. Athlet:innenbezogene Daten, Rohdatentabelle Testprotokoll, Beschreibung Testprotokoll, Laktat-/HF-Kurve mit Trainingszonen.
3. Analyse der Leistungsdiagnostik, Schwellenschnittpunkte, Trainingsbereiche.
4. Interpretation: Zusammenfassung, Schwellen & Zonen, Empfehlungen.
5. Trainerseite intern: Fachnotizen, Kontrolle der Testqualitaet, Risikoanalyse, Schwellenlogik, Trainernotizen.

## P1: Interpretation und Sprache

Prompt-/Output-Regeln:

- Reportsprache Deutsch.
- Athlet:in direkt und persoenlich ansprechen, bevorzugt mit Vorname statt generischem `Athlet:in` oder `Teilnehmer:in`.
- `v_max` immer als `Maximalgeschwindigkeit` formulieren.
- Abschnitt `Zusammenfassung`: aktueller Output wird als stark bewertet; behalten, aber persoenlicher machen.
- Abschnitt `Schwellen & Zonen`: keinen ersten Satz, der nur die Schwellenschnittpunkt-Tabelle wiederholt. Auf Tabelle verweisen, Daten nicht doppelt aufzählen.
- Abschnitt `Trainingsbereiche`: entfernen, wenn er nur die Tabelle wiederholt.
- Abschnitt `Empfehlungen`: aktuelle Formulierung und Kompaktheit sind gut; Stil beibehalten.
- Pflichtpruefungen nicht als Athlet:innen-Hinweis formulieren, sondern auf Trainerseite intern platzieren.

## Fachliche Leitplanken zu HIT/hochintensivem Training

Die Interpretation soll nicht automatisch konservativ sein. Sinnvolle Leitlinie:

- HIT ist fuer trainierte Ausdauerathlet:innen ein valides Werkzeug zur Leistungsentwicklung, besonders wenn reine Umfangssteigerung keine starke Zusatzadaptation mehr bringt.
- Gleichzeitig ist HIT kein Standard-Rezept nach jeder Diagnostik. Dosierung haengt von Trainingsalter, aktueller Belastbarkeit, Verletzungshistorie, Wettkampfziel, Testqualitaet und Basisumfang ab.
- Bei Hobbyathlet:innen mit geringer Umfangsbasis oder orthopaedischen Themen: HIT nicht verbieten, aber dosiert, vorbereitet und klar begruendet einsetzen.
- Gute Formulierungen sind kontextsensitiv: "gezielt dosierte VO2max-Reize", "kurze kontrollierte hochintensive Intervalle", "erst nach Stabilisierung der Grundlagenumfaenge", "nicht als Ersatz fuer aerobe Basis".
- Schlechte Formulierungen: pauschal "keine hohen Intensitaeten", pauschal "HIT ist das Wichtigste", oder Trainingsempfehlungen ohne Bezug auf Testbild und Kontext.

Quellenanker:

- Laursen & Jenkins 2002: Bei bereits trainierten Athlet:innen koennen Leistungsverbesserungen besonders ueber HIT erreicht werden; optimale Programme bleiben kontextabhaengig. https://pubmed.ncbi.nlm.nih.gov/11772161/
- Esteve-Lanao et al. 2007: Bei Laeufer:innen war mehr niedrigintensives Training bei aehnlichem HIT-Anteil guenstig gegenueber mehr Schwellentraining. https://pubmed.ncbi.nlm.nih.gov/17685689/
- Systematische Uebersicht zu trainierten/Elite-Radfahrer:innen: Periodisierung, Volumen und Intensitaetsverteilung muessen sport- und zielbezogen gesteuert werden. https://pubmed.ncbi.nlm.nih.gov/36640771/
- Meta-Analyse 2025 zu Elite-/hochtrainierten Athlet:innen: HIIT kann performance-relevante Masse verbessern, Effekte haengen aber stark von Athlet:innengruppe, HIIT-Typ und Studiensetting ab. https://pubmed.ncbi.nlm.nih.gov/39830026/
- Review/Perspektive 2023: HIIT ist leistungs- und gesundheitsbezogen wirksam, aber Protokollwahl und Zielpopulation sind entscheidend. https://pubmed.ncbi.nlm.nih.gov/37804419/

## P2: Tests und Akzeptanzkriterien

1. `uv run pytest` bleibt gruen.
2. Neuer Unit-Test: mehrere kubische Schnittpunkte -> groesserer x-Wert im Testbereich.
3. Neuer Report-Test: nicht vorhandene Schnittpunkte erscheinen nicht im Docx.
4. Neuer Format-Test: Geschwindigkeiten im Report eine Nachkommastelle; JSON bleibt unveraendert.
5. Render-QA: Anna-Referenzreport als DOCX/PDF rendern und visuell pruefen:
   - exakt 5 Seiten A4 quer fuer Referenzfall,
   - keine abgeschnittenen Diagrammpunkte,
   - Tabellenkoepfe nur einmal,
   - Footer/Logo korrekt,
   - Seite 5 klar intern markiert.

## Empfohlene Umsetzungsreihenfolge

1. Datenmodell/Input-Felder und Begrifflichkeiten klaeren/anpassen.
2. Schnittpunktlogik und Zonenformatierung korrigieren.
3. Diagramm mit farbigen Zonen und Achsen-Padding bauen.
4. Reporttemplate auf 5-Seiten-Zielbild umbauen.
5. Interpretation-Prompt und Abschnittsauswahl schaerfen.
6. Optional: Codex-direkter Interpretationsmodus, API-Fallback beibehalten oder explizit entfernen.
