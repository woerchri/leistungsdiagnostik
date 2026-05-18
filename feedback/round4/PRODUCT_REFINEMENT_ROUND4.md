# Produktverfeinerung Runde 4: Leistungsdiagnostik-Auswertung

Quelle: `feedback/round4/26_05_LD_Dateneingabe_Korrektur_4.docx`, Anna-Maria, 18.05.2026.

Rolle dieses Dokuments: kompaktes Delta zu Runde 3. Runde 4 bestätigt im Wesentlichen die Richtung und schärft wenige Punkte nach: Steigung als echtes Inputfeld, Z1/Z2-Darstellung, größere Grafik, Trainingsformen in die bestehende Tabelle integrieren und saubere deutsche Umlaute.

## Executive Take

Runde 4 ist ein gutes Zeichen: Das Feedback wird kürzer. Das heißt, das Produkt nähert sich dem Zielbild. Die verbleibenden Punkte sind keine Grundsatzprobleme mehr, sondern Akzeptanzkriterien für den finalen Report.

Der wichtigste Produktpunkt bleibt: **Die Grafik darf nicht zu klein werden.** Für Marketing und Kund:innenvertrauen ist die Kurve der Beweis, dass hier nicht nur Text generiert wurde. Wenn Seite 2 die Grafik nicht groß genug tragen kann, ist es besser, die Grafik auf Seite 3 zu verschieben, als sie zu einem kleinen Belegbild zu degradieren.

## P0: Runde-4-Akzeptanzkriterien

### P0-1 — Steigung als eigenes Inputfeld

Feedback:

- `Steigung` als Inputfeld vorsehen.
- Dieses Feld muss in der Tabelle `Testprotokoll` verwendet werden.

Umsetzung:

- Input-Template: neues Feld `Steigung`.
- Parser: optionales Feld lesen.
- Datenmodell/JSON: Feld speichern.
- Report Seite 2: in Testprotokoll-Tabelle anzeigen.
- Leeres Feld als `—` rendern.

Produktkritik:

- Steigung ist bei Laufbandtests kein Detail. Sie beeinflusst Belastung und Vergleichbarkeit. Es gehört deshalb nicht nur in `Besonderheiten`, sondern als strukturiertes Feld ins Protokoll.

### P0-2 — Z1/Z2-Duplikat sauber anzeigen

Feedback:

- Wenn Z1 und Z2 dieselben Grenzen haben, Felder `Geschwindigkeit`, `Pace` und `HF` in Z1 frei lassen.
- Z2 bleibt vollständig.

Akzeptanz:

- Z1 zeigt dann nur Zone/Ziel/RPE bzw. Methode, aber keine redundanten Grenzwerte.
- Z2 behält die Grenzwerte.
- Diese Regel muss als Reporttest abgesichert werden.

Produktkritik:

- Doppelte Zahlen in Z1 und Z2 wirken wie ein Rechenfehler, auch wenn sie technisch erklärbar sind. Für Kund:innen ist die leere Z1-Zeile sauberer.

### P0-3 — Grafik größer, Restplatz ausnutzen

Feedback:

- Seite 2: Grafik muss größer sein.
- Maximalen Restplatz ausnützen.
- Wenn auf Seite 2 nicht möglich, dann auf Seite 3 verschieben.

Produktentscheidung:

- Grafikgröße hat Vorrang vor der starren Annahme, dass die Grafik zwingend auf Seite 2 bleiben muss.
- Der Report muss nicht beweisen, dass alles auf Seite 2 passt. Er muss hochwertig wirken.

Umsetzungsoptionen:

1. **Bevorzugt:** Seite 2 bleibt Daten-/Grafikseite, aber Tabellen werden stärker komprimiert und die Grafik wird größer.
2. **Fallback:** Seite 2 = Daten & Testablauf; Seite 3 startet mit großer Grafik und darunter Analyse/Trainingsbereiche.
3. **Nicht empfohlen:** Grafik klein lassen, nur um die alte Seitenlogik zu retten.

Akzeptanz:

- Grafik ist als primäres visuelles Element klar erkennbar.
- Achsen, Marker und Zonenflächen sind lesbar.
- Report bleibt bei exakt 5 Seiten.

### P0-4 — Methoden/Trainingsformen in Trainingsbereiche integrieren

Feedback:

- Methoden/Trainingsformen doch in die Tabelle `Trainingsbereiche` einbauen.

Entscheidung:

- Runde 4 bestätigt die bevorzugte Variante aus Runde 3: keine separate große Tabelle.
- Neue Spalte in `Trainingsbereiche`: `Methode / Trainingsform`.

Inhalte:

| Zone | Methode / Trainingsform |
|---|---|
| Z1 | Dauermethode bis 30' |
| Z2 | Dauermethode bis mehrere Stunden |
| Z3 | Extensive Intervalle, ca. 40-90' |
| Z4 | Extensive Intervalle, ca. 45-60' |
| Z5 | Intensive Intervalle, ca. 20' |
| Z6 | Intensive, maximale Intervalle |

Akzeptanz:

- Trainingsbereiche-Tabelle bleibt auf Seite 3.
- Keine zusätzliche Seite durch die neue Spalte.
- Spaltentext ist kurz genug für sauberen Umbruch.

### P0-5 — Footer: Seitenzahl mittig

Feedback:

- Fußzeile auf allen Seiten außer Deckblatt.
- Seitenzahl mittig.

Akzeptanz:

- Deckblatt ohne Seitenzahl.
- Seiten 2-5 mit mittiger Seitenzahl.
- Logo rechts und Kontaktdaten links bleiben gemäß vorheriger Runden.

### P0-6 — Umlaute statt Umschreibungen

Feedback:

- Verwende statt `ue`, `ae`, `oe` die Zeichen `ü`, `ä`, `ö`.

Umsetzung:

- In allen sichtbaren deutschen Reporttexten, Prompts, Fehlermeldungen und Feedbackdokumenten Umlaute verwenden.
- Code-Identifier, JSON-Keys und technische Dateinamen dürfen weiterhin ASCII bleiben, wenn es Stabilität und Kompatibilität verbessert.

Akzeptanz:

- Im Wordbericht steht z.B. `Schwellenbereiche`, `Ernährung`, `Nächste`, `für`, `können`, nicht `Schwellenbereiche` gemischt mit `fuer/koennen`.
- Keine künstliche ASCII-Schreibweise in kundensichtbarem Text.

Produktkritik:

- Für einen deutschsprachigen Premiumreport wirken `ae/oe/ue` billig und technisch. Das ist klein, aber markenrelevant.

## P1: Bestehende Regeln aus Runde 3 bleiben aktiv

Diese Punkte wurden in Runde 4 nicht aufgehoben:

- Seite 1-4 kundenfertig.
- Seite 5 ausschließlich intern für Trainer.
- Exakt 5 Seiten.
- Z1/Z2-Duplikate nicht anzeigen.
- Empfehlungen bleiben exakt, kompakt und kritisch.
- Keine erfundenen Werte.
- Trainingsempfehlungen müssen weiterhin kritisch und literaturbasiert sein.

## P1: Literatur- und Empfehlungston

Runde 4 bestätigt erneut: ehrlich, kritisch, aktuelle Ausdauerliteratur.

Aktuelle Quellenanker:

- HIIT vs. SIT Meta-Analyse 2026: https://pubmed.ncbi.nlm.nih.gov/41740126/
- HIIT in Elite-/hochtrainierten Athlet:innen, Meta-Analyse 2025: https://pubmed.ncbi.nlm.nih.gov/39830026/
- HIIT vs. MICT bei Ausdauerathlet:innen, 2024: https://pubmed.ncbi.nlm.nih.gov/38904772/
- Perspektive zu HIIT für Performance und Gesundheit, 2023: https://pubmed.ncbi.nlm.nih.gov/37804419/

Produktregel:

- HIT nicht pauschal vermeiden.
- HIT nicht aggressiv verkaufen.
- Trainingsableitungen aus Testbild, Belastbarkeit, Ziel und Kontext begründen.

## Konkrete Claude-Aufgaben

1. `Steigung` als strukturiertes optionales Inputfeld ergänzen und im Testprotokoll anzeigen.
2. Z1-Felder für Geschwindigkeit/Pace/HF leer lassen, wenn Z1 und Z2 identische Grenzen haben.
3. Grafik deutlich größer darstellen; wenn Seite 2 dafür zu eng ist, Grafik auf Seite 3 verschieben.
4. Methoden/Trainingsformen als Spalte in `Trainingsbereiche` einbauen.
5. Footer-Seitenzahl mittig prüfen.
6. Kundensichtbare deutsche Texte auf echte Umlaute umstellen.
7. Danach Render-QA: exakt 5 Seiten, Grafik lesbar, keine Layoutverschiebung.

## Ein-Satz-Produktregel

Runde 4 sagt: Nicht mehr Inhalt, sondern bessere Präsentation — strukturierte Steigung, größere Grafik, Trainingsmethoden direkt in der Zonentabelle und ein deutschsprachiger Premium-Look ohne ASCII-Ersatzschreibweise.
