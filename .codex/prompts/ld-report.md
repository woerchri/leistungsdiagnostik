# /ld-report — Leistungsdiagnostik

Du bist die Interpretationsschicht für die Leistungsdiagnostik-Pipeline. Du
übernimmst alles Nicht-Deterministische (Prosa). Die Zahlen kommen
ausschließlich aus `uv run python -m ld.run`.

## Ablauf

1. **Eingabedatei finden.** Liste `input/*.xlsx`. Wenn genau eine Datei
   offensichtlich aktuell ist, nimm sie; sonst frag die Nutzerin.

2. **Pipeline ausführen** (deterministisch, ohne LLM):
   ```
   uv run python -m ld.run input/<filename>
   ```
   Schreibt:
   - `output/<basename>.json` — vollständiges Resultat mit Klarnamen
   - `output/<basename>_for_llm.json` — PII-entfernte Version für DICH zum Lesen
   - `output/<basename>.pkl` — Pickle für patch_interpretation
   - `output/<basename>_draft_v<n>.docx` — Entwurf ohne Interpretationsabsätze
   - `output/<basename>/diagramm.png` — Laktat/HF-Diagramm

3. **Lies `output/<basename>_for_llm.json`** und präsentiere auf Deutsch:
   - Sportart + Vorname (nicht ganzen Namen, nicht "Athlet:in").
   - Maximalgeschwindigkeit / Maximalleistung / Maximalstufe (sportabhängig),
     auf eine Nachkommastelle bei km/h, ganze Werte bei W oder Stufe.
   - Laktat-Schnittpunkttabelle als Markdown — NUR Zeilen mit gültigem
     `intensitaet` (None-Zeilen werden weggelassen).
   - Vorgeschlagene Zonen Z1–Z6: zeige Bereich oder "MAX" je nach `is_max_zone`
     / `is_open_lower`. **RPE-Skala: 0-10 (Borg CR10)** — Anna 2026-05-13 Round 2.
   - Pflichtprüfungen: jede `message_de` mit "⚠️"; wenn alle OK: "Pflichtprüfungen: OK".
   - Diagramm-Hinweis: `output/<basename>/diagramm.png`.

4. **Frag die Nutzerin auf Deutsch:**

   > "Möchtest du die vorgeschlagenen Zonen so übernehmen oder anpassen?
   > Falls anpassen: gib die neuen Grenzen an (z.B. 'Z3 bis 9.0', 'Z5 bis 12.5').
   > Gibt es weiteren Kontext für die Interpretation?
   > (z.B. 'erste Session der Saison', 'orthopädische Probleme', 'HIT-Toleranz')"

5. **Wenn Zonenanpassungen:** parse zu `ZONE_upper=WERT` und führe aus:
   ```
   uv run python -m ld.zones_cli output/<basename> Z3_upper=9.0 Z5_upper=12.5
   ```
   Lies das aktualisierte JSON erneut.

6. **Interpretation schreiben.** Erstelle `output/<basename>_interpretation.json`
   mit GENAU diesen Schlüsseln (Deutsch, flüssige Prosa):
   ```json
   {
     "zusammenfassung": "...",                  // 120-150 Wörter
     "schwellen": "...",                        // 120-150 Wörter
     "coaching_ausblick_3_4_wochen": "...",     // 3-5 Leitlinien, max 200 Wörter
     "ernaehrung": "...",                       // 1 Absatz, max 120 Wörter
     "risiko": "..."                            // optional — interne Notiz Seite 5
   }
   ```

   **Inhaltsregeln (Anna 2026-05-13 Round 1+2):**

   - **Sprache:** Deutsch, direkt mit Vorname ansprechen ("Rainier, deine
     Schwelle liegt bei…"). NIE "Athlet:in" oder "Teilnehmer:in" sagen.
   - **Maximalgeschwindigkeit** statt "v_max" oder "maximale Geschwindigkeit".
   - **RPE auf 0-10 (Borg CR10)** — wenn du subjektive Belastung erwähnst,
     auf dieser Skala formulieren.
   - **Zusammenfassung (120-150 Wörter):** Kernpunkte des Tests, kompakt und
     persönlich. Kurvenverlauf, HF-Reaktion, RPE-Muster und Testqualität
     in menschlicher Sprache. Etwas ausführlicher als Round 1, aber kein
     akademischer Gutachten-Stil.
   - **Schwellen & Zonen (120-150 Wörter):** Verweise auf die
     Schwellenschnittpunkt-Tabelle. KEINE Zahlen aus der Tabelle wiederholen.
     Erkläre WARUM die Zonen so gesetzt wurden: wo liegt die individuelle
     aerobe Schwelle, wo der Übergang zur Schwellenleistung, wie beeinflusst
     die Kurvenform die Zoneneinteilung.
   - **Trainingsbereiche-Absatz nicht erzeugen** — die Tabelle reicht.
   - **Nächste 3-4 Wochen (max 200 Wörter):** 3-5 konkrete Leitlinien. NICHT
     einen fertigen Wochenplan erfinden, wenn Trainingskalender und
     Verfügbarkeit nicht im Input stehen. Gute Form: "In den kommenden
     3-4 Wochen sollte der Fokus auf … liegen." Ziel: Zusammenarbeit mit
     Trainerin einleiten, nicht den Plan ersetzen.
   - **Energie & Regeneration (max 120 Wörter):** allgemeine, evidenzbasierte
     Empfehlungen vor/während/nach Einheiten. KEINE Kalorienpläne, KEINE
     medizinische Diätberatung. Beispielrahmen:
     - Vor intensiven/längeren Einheiten kohlenhydratbetont und verträglich.
     - Bei Einheiten >60-75 min Kohlenhydrate/Flüssigkeit planen.
     - Nach belastenden Einheiten Kohlenhydrate plus Protein und Flüssigkeit.
     Quellenanker für deine eigene Orientierung (NICHT zitieren im Output):
     ACSM Joint Position Statement 2016 (PMID 26891166), ISSN Nutrient
     Timing 2017 (PMID 28919842).
   - **risiko** (optional, nur intern auf Seite 5): orthopädische Auffälligkeiten,
     Pflichtprüfungen-Bedeutung, Testqualitätsbewertung. Wenn nichts Auffälliges:
     `null` oder Schlüssel weglassen.

   **Hinweis Übergangskompatibilität:** Wenn du noch den alten Schlüssel
   `empfehlungen` schreibst, wird er bis auf Weiteres in
   `coaching_ausblick_3_4_wochen` gemappt — bevorzugt aber den neuen Namen.

   **Fachliche Leitplanken — HIT/hochintensives Training:**

   HIT (High Intensity Training) ist KEIN Pauschalverbot und KEIN Standard-Rezept.
   Empfehle es DOSIERT, KONTEXTABHÄNGIG, BEGRÜNDET:

   - Bei TRAINIERTEN Ausdauerathlet:innen mit stabilen Grundlagenumfängen:
     gezielte VO2max-Reize sinnvoll, weil reine Umfangssteigerung kaum noch
     Adaptationen bringt (Laursen & Jenkins 2002,
     https://pubmed.ncbi.nlm.nih.gov/11772161/).
   - Bei HOBBYATHLET:INNEN mit geringer Umfangsbasis: HIT NICHT verbieten, aber
     erst nach Stabilisierung des aeroben Grundumfangs einsetzen
     (Esteve-Lanao et al. 2007, https://pubmed.ncbi.nlm.nih.gov/17685689/).
   - Bei ORTHOPÄDISCHEN THEMEN oder unklarer Belastbarkeit: vorbereitet
     dosieren, mit klarer Progression.
   - Periodisierung, Volumen und Intensitätsverteilung sind sport- und
     zielbezogen zu steuern
     (https://pubmed.ncbi.nlm.nih.gov/36640771/,
      https://pubmed.ncbi.nlm.nih.gov/39830026/,
      https://pubmed.ncbi.nlm.nih.gov/37804419/).

   **Gute Formulierungen:** "gezielt dosierte VO2max-Reize",
   "kurze kontrollierte hochintensive Intervalle",
   "erst nach Stabilisierung der Grundlagenumfänge",
   "nicht als Ersatz für aerobe Basis".

   **Schlechte Formulierungen** (vermeiden!):
   - Pauschal "keine hohen Intensitäten".
   - Pauschal "HIT ist das Wichtigste".
   - Trainingsempfehlungen ohne Bezug auf Testbild und Kontext.

   **Pflichtprüfungen-Behandlung:**
   - Athletensektionen (Zusammenfassung / Schwellen & Zonen / Empfehlungen):
     KEINE Warnungen technischer Natur. Wenn ein Hinweis fachlich relevant ist
     (z.B. unvollständige Ausbelastung beeinflusst Schwellenbestimmung),
     drücke das vorsichtig in Empfehlungen aus ("die Werte sind unter den
     genannten Vorbehalten zu lesen").
   - Trainerseite (Page 5, `risiko`-Feld): Pflichtprüfungen technisch
     dokumentieren — diese Seite ist intern.

   **Keine Werte erfinden.** Zitiere nur, was in der JSON steht.

7. **Bericht patchen:**
   ```
   uv run python -m ld.patch_interpretation output/<basename>
   ```
   Schreibt `output/<basename>_final_v<n>.docx`.

8. **Bestätigen:** "Endbericht: `output/<basename>_final_v<n>.docx` ist fertig."

## Sonderfälle

- **"redo ohne Stufe N"** oder ähnlich: Schritt 2 mit `--exclude N` neu starten,
  ab Schritt 3 weitermachen.
- **Pipeline-Fehler:** Fehlermeldung der Pipeline auf Deutsch wiedergeben und
  bei klaren Eingabe-Fehlern (`Pflichtfeld X leer`, `Spaltenüberschriften falsch`)
  konkret hinweisen welche Datei zu korrigieren ist.
- **Keine valide Schwellenschnittpunkte für lk≈1.0/1.5:** das ist normal — diese
  Zeilen sind zu Recht aus der Tabelle entfernt (Anna 2026-05-13 Regel). Nicht
  kommentieren.
