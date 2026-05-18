# Produktverfeinerung Runde 3: Leistungsdiagnostik-Auswertung

Quelle: `feedback/round3/26_05_LD_Dateneingabe_Korrektur_3.docx`, Anna-Maria, 17.05.2026.

Rolle dieses Dokuments: Delta zu Runde 2. Runde 3 ist keine komplette Neuausrichtung, sondern ein Feinschliff nach sichtbarem Fortschritt. Wichtig: neuere Rückmeldung schlägt ältere Entscheidungen, besonders bei Seite 4.

## Executive Take

Das Produkt ist näher am Ziel: Seite 5 passt laut Feedback, Schwellenschnittpunkte sind näher am gewünschten Layout, Footer/Branding gehen in die richtige Richtung. Das Problem ist jetzt präziser: **6 statt 5 Seiten**. Es fehlt also nicht mehr ein kompletter Reportumbau, sondern eine harte Layout-Kompression an den richtigen Stellen.

Der gefährlichste neue Wunsch ist die zusätzliche Tabelle `Beschreibung / Methode Trainingsformen` auf Seite 3. Fachlich sinnvoll, aber layoutkritisch. Wenn sie als dritte separate Tabelle gebaut wird, wird das 5-Seiten-Ziel wahrscheinlich wieder brechen. Empfehlung: **nicht als eigene große Tabelle**, sondern als kompakte Zusatzspalte oder kurze zweite Tabelle unterhalb der Trainingsbereiche, mit sehr engem Wortbudget.

## Prioritätsänderungen gegenüber Runde 2

1. **Seite 5 nicht weiter umbauen.**
   - Feedback: "Seite 5: Trainerseite – Intern passt".
   - Produktregel: ab jetzt einfrieren, nur Bugfixes.

2. **Seite 4: Abschnitt umbenennen und Beispielwoche entfernen.**
   - Runde 2 sagte: 3-5 Leitlinien + Beispielwoche.
   - Runde 3 sagt: Abschnitt `Nächste 3-4 Wochen` in `Empfehlungen` umbenennen; Beispielwoche entfernen.
   - Neue Regel: Empfehlungen = konkrete Leitlinien, aber keine Beispielwoche.

3. **6 statt 5 Seiten ist jetzt P0.**
   - Nicht neue Inhalte addieren, bevor die 5 Seiten stabil sind.
   - Neue Inhalte nur erlauben, wenn an anderer Stelle Text/Tabelle verdichtet wird.

## P0: Harte Round-3-Fixes

### P0-1 — 5 Seiten erzwingen, nicht 6

Akzeptanz:

- Referenzfall rendert exakt 5 Seiten.
- Keine inhaltliche Verschiebung auf Seite 6.
- Seite 5 bleibt intern und unverändert in Struktur.

Wahrscheinliche Hebel:

- Seite 2: Grafik etwas höher platzieren und den maximalen Restplatz ausnutzen.
- Seite 2: Testprotokoll-Felder noch kompakter darstellen.
- Seite 3: Trainingsformen nicht als große Extra-Tabelle, sondern platzsparend integrieren.
- Seite 4: Beispielwoche entfernen; Empfehlungen kompakt halten.

Produktkritik:

- Ein zusätzlicher Inhalt bei gleichzeitigem 5-Seiten-Cap ist kein Designproblem, sondern ein Priorisierungsproblem. Jeder neue Block braucht ein klares Platzbudget.

### P0-2 — Testprotokoll-Tabelle erweitern

Seite 2, Testprotokoll-Tabelle ergänzen:

- Ruhelaktat.
- Steigung.
- Dauer der letzten Stufe.

Umsetzungshinweis:

- `Dauer letzte Stufe` existiert im Datenmodell bereits teilweise, muss im Report sichtbar sein.
- `Steigung` nicht nur in `Besonderheiten` verstecken, sondern als eigenes Feld führen, wenn sie regelmäßig relevant ist.
- `Ruhelaktat` als eigenes optionales Feld in Input, Parser, JSON und Report.

Akzeptanz:

- Leere optionale Felder rendern als `—`.
- Keine erfundenen Werte.
- Feldnamen sind im Input und Report identisch verständlich.

### P0-3 — Deckblatt-Kontakt

Feedback: Deckblatt soll Unternehmenskontaktdaten zeigen: Email | Telefonnummer.

Produktentscheidung:

- Deckblatt bleibt ruhig und premium, aber Kontakt darf unten klein erscheinen.
- Nicht wieder "Erstellt von Anna-Maria Wörndle" einführen.
- Kontaktformat: `anna-maria@woerndle.at | +43 677 62150496`.

Marketingkritik:

- Kontakt auf dem Deckblatt kann sinnvoll sein, weil das Deckblatt separat geteilt/gedruckt wird. Aber bitte klein, nicht administrativ. Das Logo und der Reporttitel bleiben die Hauptsignale.

### P0-4 — Energie & Regeneration persönlich ansprechen

Problem:

- Abschnitt spricht aktuell offenbar generisch von `Athlet:in`.

Regel:

- In `Energie & Regeneration` muss derselbe direkte Stil gelten wie in der Zusammenfassung: Vorname verwenden.
- Keine generischen Labels wie `Athlet:in`, `Teilnehmer:in`.

Prompt-Regel:

- `ernaehrung` muss mit dem Vornamen kompatibel sein, z.B. "Anna, vor intensiven Einheiten..."

### P0-5 — Schwellenschnittpunkte: Word-Report strenger als Codex

Feedback:

- Wert `8` nicht im Wordbericht berechnen/anzeigen, wenn dieser Wert in den Rohdaten nicht vorhanden bzw. nicht erreicht ist.
- Wert `2,5` im Wordbericht weglassen.
- In Codex darf der Wert zur Korrektur/Bewertung bleiben.

Produktregel:

- Rechen-/Review-Schicht darf mehr enthalten als der Athlet:innenreport.
- Wordbericht ist kuratiert, nicht vollständig.

Akzeptanz:

- JSON/Codex kann `2.5` und `8.0` weiterhin enthalten.
- Wordbericht zeigt für den Referenzfall nur die freigegebenen Spalten, z.B. `1.5`, `2.0`, `3.0`, `4.0`, `6.0`.
- Alle Werte in der Tabelle mittig ausrichten.

### P0-6 — Trainingsbereiche: Z1/Z2 und Z6 korrekt darstellen

Feedback:

- Wenn Z1 und Z2 dieselben Grenzen haben: Z1-Felder für Intensität, Pace und HF frei lassen; Z2 bleibt.
- Z6: Pace wie Intensität mit `MAX` darstellen.
- Z6: HF-Feld frei lassen.

Akzeptanz:

- Z1 darf nicht redundant dieselben Zahlen wie Z2 zeigen.
- Z6 ist klar als Maximalbereich erkennbar, ohne falsche numerische Präzision.

### P0-7 — Plot: erster HF-/Laktatpunkt überlappt

Feedback:

- 1. Punkt HF und 1. Punkt Laktat überlappen sich.
- Ziel: alle Punkte sichtbar.

Kritische Einordnung:

- Nicht primär die Achsen "irgendwie" verzerren, nur damit Marker auseinandergehen. Das kann die diagnostische Aussage optisch verfälschen.

Empfehlung:

- Unterschiedliche Markerformen: HF Kreis, Laktat Quadrat.
- Weiße Marker-Ränder (`markeredgecolor="white"`, `markeredgewidth=0.8`).
- Z-Order bewusst setzen.
- Optional minimaler horizontaler Marker-Offset nur für Rohdatenmarker, nicht für Fit-Linien, und nur wenn Overlap erkannt wird.

Akzeptanz:

- Kein Marker verschwindet vollständig hinter dem anderen.
- Achsenskalierung bleibt fachlich plausibel.

## P1: Neue Tabelle Trainingsformen

Feedback: Seite 3 Tabelle `Beschreibung / Methode Trainingsformen` hinzufügen, im selben Layout wie `Trainingsbereiche`.

Gewünschte Inhalte:

| Zone | Methode / Trainingsform |
|---|---|
| Z1 | Dauermethode bis 30' |
| Z2 | Dauermethode bis mehrere Stunden |
| Z3 | Extensive Intervalle; Dauer in Z3 ca. 40-90' |
| Z4 | Extensive Intervalle; Dauer in Z4 ca. 45-60' |
| Z5 | Intensive Intervalle; Dauer in Z5 ca. 20' |
| Z6 | Intensive, maximale Intervalle |

Produktkritik:

- Inhaltlich wertvoll, weil er Trainingszonen in Handlung übersetzt.
- Layoutseitig riskant, weil Seite 3 schon Analyse- und Zonenseite ist.

Empfehlung:

- Variante A, bevorzugt: Trainingsformen als zusätzliche Spalte in der bestehenden Trainingsbereiche-Tabelle.
- Variante B: separate Mini-Tabelle mit nur zwei Spalten (`Zone`, `Methode`) und kleiner Schrift, direkt unter Trainingsbereiche.
- Variante C, vermeiden: große zweite Tabelle mit vollem Tabellenkopf und breiten Zellen.

Akzeptanz:

- Seite 3 bleibt auf einer Seite.
- Farben der Zonen bleiben konsistent.
- Text ist kurz genug, um nicht mehrzeilig zu überlaufen.

## P1: Footer-Feinschliff

Feedback:

- Kontaktdaten links untereinander.
- Seitenzahl mittig.
- Logo rechts unten.
- Dünne horizontale Trennlinie.

Umsetzung:

- Links nicht `email · telefon`, sondern zwei Zeilen:
  - `anna-maria@woerndle.at`
  - `+43 677 62150496`
- Seitenzahl mittig bleibt.
- Logo rechts bleibt.

Marketingkritik:

- Untereinander wirkt ruhiger und professioneller als eine lange Kontaktzeile. Wichtig ist genügend Abstand zur Trennlinie.

## P1: Seite 2 Layout-Feinschliff

Feedback:

- Grafik etwas höher.
- Maximalen Restplatz ausnützen.

Empfehlung:

- Die Grafik nicht kleiner machen, wenn dadurch Kompetenzwirkung verloren geht.
- Stattdessen vertikale Abstände vor der Grafik reduzieren.
- Testprotokoll- und Athletendaten-Tabellen kompakter machen.
- Rohdatentabelle sehr flach halten.

Akzeptanz:

- Die Grafik ist weiterhin der visuelle Hauptanker von Seite 2.
- Keine zweite Seite durch Überlauf.

## P1: Seite 4 Textstruktur

Neue Struktur:

1. Zusammenfassung.
2. Schwellen & Zonen.
3. Empfehlungen.
4. Energie & Regeneration.

Änderungen:

- `Nächste 3-4 Wochen` wird in `Empfehlungen` umbenannt.
- Beispielwoche wird entfernt.
- Empfehlungen bleiben konkret, aber nicht als Wochenplan.

Prompt-Regel:

- Keine Beispielwoche generieren.
- 3-5 konkrete Empfehlungen als kompakter Absatz oder kurze Liste.
- Bezug auf die nächsten 3-4 Wochen darf bestehen bleiben, aber nicht als eigene Überschrift.

## P2: Begriffsschärfung der Zonen

Feedback:

- `metabolische Stabilität` wirkt wissenschaftlich nicht ideal.
- `neuromuskulär` ebenfalls prüfen.

Kritik:

- Beide Begriffe klingen fachlich, sind aber für Athlet:innen nicht klar genug. `metabolische Stabilität` ist besonders diffus: Stabilität von was? Laktat? Fettstoffwechsel? Tempoökonomie?
- `neuromuskulär` beschreibt eher einen Wirkmechanismus als eine Trainingszone. Für Z6 ist der Athlet:innen-Nutzen klarer mit Maximal-/Sprint-/anaeroben Spitzenreizen beschrieben.

Empfohlene Zonennamen:

| Zone | Aktuell | Vorschlag |
|---|---|---|
| Z1 | aktive Regeneration / Regenerativ | Regeneration |
| Z2 | aerobe Basis / Grundlage | Grundlagenausdauer |
| Z3 | metabolische Stabilität / Schwelle | Aerobe Entwicklung |
| Z4 | Schwellenleistung / Entwicklung | Schwellenbereich |
| Z5 | VO2max-Reize / HIT | VO2max / hochintensive Intervalle |
| Z6 | neuromuskulär / Max | Sprint- und Maximalreize |

Alternative, noch sportwissenschaftlicher:

- Z3: `Aerob-anaerober Übergangsbereich`.
- Z6: `Anaerobe Spitzenreize`.

Produktentscheidung:

- Für Kund:innen lieber klar als pseudoakademisch. Die interne Trainerseite kann die physiologische Logik ausführlicher beschreiben.

## P2: Literatur- und Empfehlungston

Runde 3 bestätigt: Empfehlungen sollen ehrlich, kritisch und auf aktueller Ausdauerliteratur basieren.

Aktuelle Quellenanker:

- HIIT vs. SIT Meta-Analyse 2026: https://pubmed.ncbi.nlm.nih.gov/41740126/
- HIIT in Elite-/hochtrainierten Athlet:innen, Meta-Analyse 2025: https://pubmed.ncbi.nlm.nih.gov/39830026/
- HIIT/SIT bei trainierten Läufer:innen, 2026-nah publiziert: https://pubmed.ncbi.nlm.nih.gov/41666911/
- Running economy HIIT/MICT Meta-Analyse 2025: https://pubmed.ncbi.nlm.nih.gov/41766811/

Produktregel:

- HIT darf empfohlen werden, aber nur, wenn Testbild, Trainingshistorie und Belastbarkeit es tragen.
- Für Hobbyathlet:innen: nicht reflexhaft verbieten, aber dosiert und vorbereitet.
- Keine aggressiven Pläne erfinden, wenn Inputdaten fehlen.

## Konkrete Claude-Aufgaben

1. Round-3-DOCX in `feedback/round3/` als Quelle beachten.
2. Seite 5 einfrieren, außer bei klaren Bugs.
3. Deckblatt-Kontakt klein ergänzen; `Erstellt von...` bleibt entfernt.
4. Testprotokollfelder `Ruhelaktat`, `Steigung`, `Dauer letzte Stufe` ergänzen.
5. Wordbericht-Schwellenschnittpunkte: `2.5` und nicht erreichte hohe Zielwerte wie `8.0` ausblenden; Codex/JSON darf sie behalten.
6. Trainingsformen platzsparend in Seite 3 integrieren.
7. Plotmarker so ändern, dass erster HF-/Laktatpunkt beide sichtbar bleiben.
8. Footer-Kontakte untereinander setzen.
9. Seite 4 Überschrift `Nächste 3-4 Wochen` zu `Empfehlungen`; Beispielwoche entfernen.
10. Zonennamen prüfen und kundentauglicher machen.
11. Danach Render-QA: exakt 5 Seiten, nicht 6.

## Ein-Satz-Produktregel

Runde 3 verlangt keinen größeren Report, sondern einen besser kuratierten: weniger Beispielplan, mehr Klarheit, sichtbare Messdaten, handlungsnahe Trainingsformen und weiterhin exakt 5 Seiten.
