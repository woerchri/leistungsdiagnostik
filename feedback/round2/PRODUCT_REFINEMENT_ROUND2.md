# Produktverfeinerung Runde 2: Leistungsdiagnostik-Auswertung

Quelle: `feedback/round2/26_05_LD_Dateneingabe_Korrektur_2.docx`, Anna-Maria, 13.05.2026.

Rolle dieses Dokuments: kritischer Produkt- und Implementierungsbrief fuer Christopher/Claude. Runde 2 ist keine neue Wunschliste, sondern eine Schaerfung des Produkts: Der Report soll fachlich belastbar, trainereditierbar und marketingtauglich wirken.

## Executive Take

Das groesste Produktproblem ist nicht mehr die Berechnung, sondern die Wahrnehmung von Professionalitaet. Ein 9-seitiger Report wirkt trotz guter Inhalte nicht wie ein hochwertiges, effizientes Coaching-Produkt. Das Ziel muss ein kontrollierter 5-Seiten-Report sein: klare Diagnose, gute Grafik, kompakte Tabellen, persoenliche Interpretation, interne Trainerseite.

Gleichzeitig verlangt Runde 2 mehr Inhalt auf Seite 4: etwas ausfuehrlichere Zusammenfassung, ausfuehrlichere Schwellen-/Zonen-Logik, 3-4-Wochen-Plan und Ernaehrungstipps. Das ist der zentrale Trade-off. Empfehlung: Seite 4 nicht als Fliesstextseite aufblasen, sondern als modularen Coaching-Ausblick bauen:

- 1 kurzer Lead-Absatz.
- 3 kompakte Bloecke: `Was bedeutet das?`, `Naechste 3-4 Wochen`, `Energie & Regeneration`.
- Maximal 350-450 Woerter insgesamt.

Wenn Claude einfach "ausfuehrlicher" umsetzt, wird das 5-Seiten-Ziel wieder brechen.

## Produktpositionierung und Marketing-Kritik

Der Report darf nicht wie eine automatisch ausgespuckte KI-Auswertung wirken. Er soll wie ein professionelles Diagnostikprodukt einer Sportwissenschafterin wirken, das KI nur intern zur Effizienzsteigerung nutzt.

### Was aktuell stark ist

- Die Kombination aus Laktatkurve, HF-Verlauf und Trainingsbereichen ist fuer Athlet:innen unmittelbar greifbar.
- Die Trennung zwischen kundenseitigem Report und interner Trainerseite ist produktstrategisch sehr gut.
- Der direkte, kompakte Schreibstil passt zu einem Coaching-Produkt besser als akademisches Gutachten.

### Was aktuell kritisch ist

- **9 Seiten statt 5**: Das zerstoert den Premium-Eindruck. Es wirkt wie ein Word-Export, nicht wie ein bewusst designtes Produkt.
- **Zu viel generische Tabellenflaeche**: Tabellen sind notwendig, aber sie duerfen nicht den Report dominieren. Ein Premium-Report kuratiert Daten, er kippt sie nicht ab.
- **"KI Leistungsdiagnostik automatisch" als framing**: Fuer Marketing riskant. Der Kundennutzen ist nicht "KI", sondern schnellere, konsistentere, professionellere Diagnostik mit Trainerfreigabe.
- **Deckblatt mit "Erstellt von Anna-Maria Woerndle"**: Wirkt administrativ. Besser: Sport AnnaLytics als Marke sichtbar, Anna-Maria als Kontakt/Footer.

### Empfohlene Produktformulierung

Nicht: "automatisch generierte KI-Leistungsdiagnostik".

Besser: "Digitale Leistungsdiagnostik-Auswertung mit trainergepruefter Trainingsableitung."

Oder noch klarer fuer Endkund:innen: "Deine Leistungsdiagnostik, kompakt ausgewertet: Schwellen, Zonen und die naechsten Trainingsschritte."

## P0: Harte Akzeptanzkriterien

Diese Punkte muessen Tests oder zumindest automatisierte Checks bekommen. Sie sind in Runde 1 und Runde 2 wiederholt aufgetaucht.

1. **Report exakt 5 Seiten fuer Referenzfall**
   - A4 quer.
   - Seite 1 Deckblatt.
   - Seite 2 Daten + Rohdaten/Testprotokoll + Grafik.
   - Seite 3 Analyse + Schwellen + Trainingsbereiche.
   - Seite 4 Interpretation + 3-4-Wochen-Ausblick + Ernaehrung.
   - Seite 5 intern.
   - Wenn der Report mehr als 5 Seiten rendert: Build/QA fail.

2. **Render-QA ist Pflicht**
   - Entwicklungsumgebung braucht LibreOffice/`soffice` oder eine gleichwertige DOCX->PDF/PNG-Renderstrecke.
   - Ohne Render-QA wird das Layoutproblem nicht geloest.
   - Aktueller Befund: In dieser Umgebung fehlt `soffice`; das muss fuer echte Layoutfreigabe behoben werden.

3. **Rohdaten-Tabelle auf Seite 2**
   - Die Stufendaten muessen sichtbar sein: Stufe, Geschwindigkeit/Leistung, Herzfrequenz, Laktat, RPE.
   - Diese Tabelle muss kompakt sein, sonst sprengt sie Seite 2.

4. **Plot endet am letzten Messpunkt**
   - Laktat- und HF-Linien duerfen nicht ueber den letzten realen Datenpunkt hinaus weiterlaufen.
   - Optional: Fit-Kurve nur bis letztem Datenpunkt bzw. bis `v_max`, aber klar unterscheiden zwischen gemessen und geschaetzt.
   - Wenn `v_max` aliquot aus unvollstaendiger letzter Stufe berechnet wird, darf die Linie nicht suggerieren, dass dort ein Laktat/HF-Messpunkt existiert.

5. **Alle Messpunkte sichtbar**
   - Wenn HF- und Laktatpunkte visuell ueberlappen, muss die Skalierung/Annotation so angepasst werden, dass beide Punkte erkennbar bleiben.
   - Akzeptanz: kein Marker vollstaendig verdeckt; notfalls Markerform unterscheiden.

6. **RPE komplett auf 0-10 umstellen**
   - Input-Template.
   - Parser/Plausibilitaetscheck.
   - Zonendefinition.
   - Codex-Prompt.
   - Reporttabellenkopf: `RPE (0-10)`.
   - Aktuell sind im Code/Template noch Hinweise auf Borg 6-20 vorhanden. Das ist inkonsistent.

## P0: Fachliche Korrekturen, erneut bestaetigt

Diese Regeln bleiben unveraendert und duerfen nicht wieder verwischen:

- Nicht vorhandene Schwellenschnittpunkte werden komplett aus der Tabelle entfernt.
- Bei mehreren Schnittpunkten der kubischen Funktion im Testbereich wird der groessere x-Wert gewaehlt.
- Z1, wenn sinnvoll: `< Geschwindigkeit`, `< HF`, `> Pace`.
- Z6: Geschwindigkeit/Leistung, HF und Pace als `MAX`, nicht als numerischer Bereich.
- Keine rein fixen mmol-Schwellen als fachliche Begruendung. 2/3/4 mmol duerfen Orientierungspunkte sein, aber Kurvenform, HF-Verlauf und RPE muessen in der Logik auftauchen.

## P1: Layout und Informationsarchitektur

### Seite 1: Deckblatt

Ziel: Premium, ruhig, markenfaehig.

Anforderungen:

- Entferne "Erstellt von Anna-Maria Woerndle".
- Logo mittig, 5-7 cm, proportional, viel Weissraum.
- Titel: `Leistungsdiagnostik Laufen` oder sportartspezifisch.
- Darunter: Name, Testdatum, Testort.
- Keine Seitenzahl.

Produktkritik:

- Das Deckblatt darf nicht nach Word-Vorlage aussehen. Es ist die Marketingflaeche. Weniger Text, staerkerer Markenanker.

### Seite 2: Daten, Rohdaten, Testprotokoll, Grafik

Ziel: Der/die Athlet:in versteht sofort: Das sind meine Daten und so wurde getestet.

Anforderungen:

- Athlet:innenbezogene Daten kompakt.
- Testprotokoll als Tabelle, nicht als lange Liste.
- Rohdaten-Tabelle ergaenzen.
- Laktat-/HF-Kurve mit Trainingszonen.
- Bei Platzproblem: Athletendaten und Testprotokoll nebeneinander, Rohdaten als breite kompakte Tabelle darunter, Grafik gross und klar.

Kritik:

- Seite 2 ist die dichteste Seite. Wenn sie nicht streng kuratiert wird, ist das 5-Seiten-Ziel verloren.

### Seite 3: Analyse

Ziel: Die beiden zentralen Tabellen sollen schnell scannbar sein.

Schwellenschnittpunkte:

- Gewuenschtes Layout aus Screenshot: Laktatwerte als Spaltenkopf.
- Erste Spalte: `Laktat (mmol/l)`, `Geschwindigkeit (km/h)`, `Pace (min/km)`, `Herzfrequenz (bpm)`.
- Nicht vorhandene Ziel-Laktate als Spalten weglassen.
- Das ist fuer Marketing/Lesbarkeit besser als viele Zeilen, weil die Tabelle kompakter und "diagnostischer" wirkt.

Trainingsbereiche:

- Bei Lauf nicht `Bereich`, sondern `Geschwindigkeit (km/h)`.
- Kopfzeile `RPE (0-10)`.
- Zonenzeilen farblich hinterlegen wie in der Grafik, aber transparent/dezent.
- Werte mittig.
- Bei Platzproblem Tabellen nebeneinander oder mit reduzierter Typografie, aber nicht auf neue Seiten auslaufen lassen.

### Seite 4: Interpretation und Coaching-Bruecke

Ziel: Seite 4 ist der wichtigste Kundennutzen. Sie soll nicht nur erklaeren, sondern die Zusammenarbeit mit Anna-Maria als Trainerin einleiten.

Strukturvorschlag:

1. **Zusammenfassung**
   - Etwas ausfuehrlicher als bisher, aber maximal 120-150 Woerter.
   - Direkt mit Vorname.
   - Kurvenverlauf, HF-Reaktion, RPE und Testqualitaet in menschlicher Sprache.

2. **Schwellen & Zonen**
   - Etwas ausfuehrlicher, maximal 120-150 Woerter.
   - Nicht die Tabelle wiederholen.
   - Erklaeren, warum die Zonen so gesetzt wurden.

3. **Naechste 3-4 Wochen**
   - 3-5 konkrete Leitlinien.
   - Ziel: Zusammenarbeit mit Trainerin einleiten, ohne einen kompletten Trainingsplan zu erfinden.
   - Gute Form: "In den kommenden 3-4 Wochen sollte der Fokus auf ... liegen."
   - Wichtig: Keine Wochenplaene mit erfundenen Einheiten, wenn Trainingskalender und Verfuegbarkeit nicht im Input stehen.

4. **Energie & Regeneration**
   - Ein kurzer Absatz mit Tipps vor, waehrend und nach Einheiten.
   - Nur allgemeine, evidenzbasierte Empfehlungen; keine medizinische Ernaehrungsberatung.
   - Beispielrahmen:
     - Vor intensiven/laengeren Einheiten kohlenhydratbetont und vertraeglich essen.
     - Bei Einheiten ueber ca. 60-75 min Kohlenhydrate/Fluessigkeit planen.
     - Nach belastenden Einheiten Kohlenhydrate plus Protein und Fluessigkeit fuer Regeneration.

### Seite 5: Trainerseite intern

Ziel: Fachliche Tiefe fuer Anna-Maria, nicht fuer Athlet:innen.

Anforderungen:

- Sichtbar als intern markieren.
- Fachliche Notizen.
- Kontrolle der Testqualitaet.
- Risikoanalyse.
- Schwellenlogik ausfuehrlicher als bisher.
- Trainernotizen als kompakte Tabelle.

Kritik:

- Die Trainerseite darf dichter sein als Kundenseiten. Sie ist ein Arbeitsblatt. Trotzdem: Keine Wand aus Bulletpoints. Besser 2x2-Kachelstruktur plus kurze Tabelle.

## P1: Footer und Branding

Anforderungen:

- Footer auf allen Seiten ausser Deckblatt.
- Kontaktdaten links.
- Seitenzahl mittig.
- Logo rechts unten.
- Duenne horizontale Trennlinie.
- Logo proportional, nie verzerren.

Kritik:

- Der Footer ist ein Markenanker. Er darf nicht aussehen wie nachtraeglich eingefuegt. Abstand und Grauwert muessen ruhig wirken.

## P1: Diagramm-Verfeinerung

Aktuelle Frage: Soll die Fit-Linie ueber den letzten Messpunkt hinausgehen?

Empfehlung:

- Gemessene Datenpunkte klar markieren.
- Fit-Kurve nur im Messbereich zeigen, ausser es wird explizit extrapoliert.
- Wenn `v_max` aliquot aus unvollstaendiger Stufe berechnet wird, dann `Maximalgeschwindigkeit` als vertikale Markierung oder Label darstellen, nicht als weiterer Messpunkt.
- HF-Linie nicht ueber den letzten HF-Messpunkt hinaus fortsetzen.
- Laktatfit kann als glatte Kurve dienen, aber nicht so, dass ein nicht gemessener Endwert suggeriert wird.

Marker:

- HF: blaue Kreise.
- Laktat: rote Quadrate oder andere Markerform.
- Dadurch bleiben Punkte unterscheidbar, falls Achsenskalierung sie naeher zusammenbringt.

## P1: Codex-/Prompt-Verfeinerung

Der Prompt sollte nicht nur "Interpretation schreiben", sondern die Seitenbudgets erzwingen.

Neue Output-Struktur fuer Interpretation:

```json
{
  "zusammenfassung": "...",
  "schwellen": "...",
  "empfehlungen": "...",
  "coaching_ausblick_3_4_wochen": "...",
  "ernaehrung": "...",
  "risiko": "..."
}
```

Wichtig:

- Wenn das Template weiterhin nur drei Felder auf Seite 4 hat, sollen `coaching_ausblick_3_4_wochen` und `ernaehrung` in `empfehlungen` integriert werden.
- Besser ist aber, diese Abschnitte separat zu fuehren, damit Layout und Laenge kontrollierbar bleiben.

Prompt-Regeln:

- Keine erfundenen Trainingsplaene.
- Keine medizinischen Versprechen.
- Keine technischen Pflichtpruefungsdetails auf Kundenseiten.
- Ehrliche Empfehlung auf Basis Testbild, Ziel, Historie und Belastbarkeit.
- HIT darf empfohlen werden, aber nur dosiert und begruendet.

## Fachliche Leitplanken: Training und Ernaehrung

### HIT / hochintensives Training

Aktuelle Studienlage stuetzt eine differenzierte Position:

- HIIT kann bei trainierten und hochtrainierten Ausdauerathlet:innen leistungsrelevante Parameter verbessern; Effekte haengen stark von Protokoll, Athlet:innengruppe und Studiensetting ab.
- Bei Hobbyathlet:innen ist HIT nicht verboten, aber es braucht Basisumfang, orthopaedische Belastbarkeit und klare Dosierung.
- Intensitaetsverteilung bleibt kontextabhaengig; pauschal polarisiert, pyramidal oder schwellenlastig ist zu simpel.

Produktregel:

- Das System soll weder konservativ reflexhaft bremsen noch aggressiv HIT verkaufen. Es soll begruenden.

Quellenanker:

- HIIT Meta-Analyse Elite/hochtrainierte Athlet:innen, 2025: https://pubmed.ncbi.nlm.nih.gov/39830026/
- HIIT vs. MICT bei Ausdauerathlet:innen, 2024: https://pubmed.ncbi.nlm.nih.gov/38904772/
- Training periodization/intensity distribution in trained cyclists, 2023: https://pubmed.ncbi.nlm.nih.gov/36640771/
- Perspektive zu HIIT fuer Performance/Gesundheit, 2023: https://pubmed.ncbi.nlm.nih.gov/37804419/
- HIIT vs. SIT Meta-Analyse, 2026: https://pubmed.ncbi.nlm.nih.gov/41740126/

### Ernaehrung rund um Einheiten

Produktregel:

- Ernaehrungsempfehlungen kurz, allgemein und sportpraktisch halten.
- Keine Kalorienplaene, keine medizinische Diaetberatung.
- Empfehlungen an Belastungsdauer und Intensitaet koppeln.

Quellenanker:

- ACSM Joint Position Statement "Nutrition and Athletic Performance", 2016: https://pubmed.ncbi.nlm.nih.gov/26891166/
- ISSN Position Stand "Nutrient Timing", 2017: https://pubmed.ncbi.nlm.nih.gov/28919842/

## P2: Konkrete Implementierungsaufgaben

1. **RPE-Migration**
   - `templates/input_template.xlsx` und `build_template.py`: RPE-Hinweis auf 0-10.
   - Parser prueft RPE 0-10.
   - Plausibilitaetschecks auf 0-10 umstellen.
   - Zonenmeta bleibt 0-10.
   - `/ld-report` Prompt auf 0-10.

2. **Schwellenschnittpunkt-Tabelle pivotieren**
   - Aus Zeilentabelle wird Matrix:
     - Kopf: valide Laktatwerte.
     - Zeilen: Geschwindigkeit/Leistung, Pace, HF.
   - Nicht valide Laktatwerte komplett weglassen.

3. **Rohdaten-Tabelle ergaenzen**
   - Auf Seite 2, kompakt.
   - Bei vielen Stufen: kleine Schrift, aber lesbar; notfalls max. 8-10 Stufen sichtbar und Ueberlauf warnen.

4. **Plot-Linien begrenzen**
   - HF-Linie bis letztem HF-Messpunkt.
   - Laktatfit nicht irrefuehrend ueber Messbereich hinaus.
   - `v_max` ggf. separat markieren.

5. **5-Seiten-Template neu verdichten**
   - Seite 2 Tabellen nebeneinander pruefen.
   - Seite 3 Tabellen kompakter machen.
   - Seite 4 strukturierte Bloecke statt lange Abschnitte.
   - Seite 5 2x2-Kachel plus Trainernotiz-Tabelle.

6. **Interpretationsschema erweitern**
   - Neue Felder fuer 3-4-Wochen-Ausblick und Ernaehrung.
   - Maximalwortzahlen in Prompt.
   - Fallback, falls Felder fehlen.

7. **Layout-QA automatisieren**
   - Render DOCX zu PDF/PNG.
   - Page count pruefen.
   - Optional OCR/Textcheck fuer Footer/Seitenzahl.
   - Build fail bei >5 Seiten fuer Referenzfall.

## Priorisierte Roadmap

### Sprint 1: Vertrauen und Korrektheit

- RPE 0-10 durchziehen.
- Plot-Linien und Marker korrigieren.
- Rohdaten-Tabelle ergaenzen.
- Schwellenschnittpunkt-Tabelle pivotieren.
- Pflicht: Tests fuer diese Punkte.

### Sprint 2: Premium-Layout

- 5-Seiten-Template verdichten.
- Footer nach Beispiel.
- Deckblatt bereinigen.
- Zonenzeilen farbig hinterlegen.
- Render-QA etablieren.

### Sprint 3: Coaching-Mehrwert

- Seite-4-Interpretation neu strukturieren.
- 3-4-Wochen-Ausblick.
- Ernaehrungsabsatz.
- Trainerseite mit ausfuehrlicherer Schwellenlogik.

## Offene Produktfragen

1. Soll der Report fuer alle Faelle hart auf 5 Seiten begrenzt werden, oder nur fuer den Standardfall?
2. Was passiert bei sehr langen Trainernotizen: kuerzen, Warnung, oder Seite 6 intern erlauben?
3. Soll `Sport AnnaLytics` als sichtbare Marke auf Deckblatt/Footer stehen, auch wenn der/die Trainer:in Anna-Maria namentlich im Kontakt steht?
4. Wie detailliert darf der 3-4-Wochen-Ausblick sein, ohne einen vollstaendigen Trainingsplan zu versprechen?
5. Sollen Ernaehrungstipps immer erscheinen oder nur bei Lauf-/Ausdauerfaellen mit laengerer Belastungsdauer?

## Claude-Anweisung in einem Satz

Baue keinen laengeren Report, sondern einen kuratierten 5-Seiten-Premiumreport: gemessene Daten klar, Zonen editierbar, Interpretation persoenlich, Coaching-Ausblick kompakt, interne Risiken getrennt.
