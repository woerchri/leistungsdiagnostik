Run the Leistungsdiagnostik report flow for an xlsx file in `input/`.

Steps:
1. Identify the input file. If unclear, list `input/*.xlsx` and ask the user. If only one
   obviously-recent file matches, pick it.

2. Run the deterministic pipeline (no --interpret yet):
   `uv run python -m ld.run input/<filename>`
   This writes `output/<basename>.json`, `output/<basename>_for_llm.json`,
   `output/<basename>.pkl`, and `output/<basename>_draft_v<n>.docx`.

3. Read `output/<basename>_for_llm.json` (fall back to `output/<basename>.json` if missing).
   Present in German:
   - Sportart und Athletenname (nur Vorname).
   - v_max mit 2 Dezimalstellen.
   - Laktat-Schnittpunkttabelle als Markdown-Tabelle (Laktat | v | Pace | HF).
   - Vorgeschlagene Zonen als Tabelle (Z2-Z6: Intensitätsbereich, HF-Bereich).
   - Pflichtprüfungen-Fehlschläge: jede `message_de` mit "⚠️"-Prefix; falls alle OK:
     "Alle Pflichtprüfungen OK".
   - Diagramm-Pfad: `output/<basename>/diagramm.png`.

4. Frage die Nutzerin auf Deutsch:

   "Möchtest du die vorgeschlagenen Zonen so übernehmen oder anpassen?
   Falls anpassen: gib die neuen Grenzen an (z.B. 'Z3 bis 9.0', 'Z5 bis 12.5').
   Gibt es weiteren Kontext für die Interpretation? (z.B. 'erste Session der Saison')
   Enter zum Bestätigen und Übernehmen."

5. Wenn die Nutzerin Zonenanpassungen macht:
   - Parse die Anpassungen in explizite Grenzwerte.
   - Wende sie an:
     `uv run python -m ld.zones_cli output/<basename> Z3_upper=9.0 Z5_upper=12.5`
     (Anpassungen als `ZONE_upper=WERT` Argumente)
   - Lese das aktualisierte JSON um neue Zonen zu bestätigen.

6. Interpretationsschritt:
   - Baue einen Kontext-String aus dem Freitext der Nutzerin.
   - Starte mit Kontext (leer wenn keiner angegeben):
     `uv run python -m ld.run input/<filename> --interpret --context "<kontext>"`
     Dies schreibt `output/<basename>_v<n>.docx`.

7. Teile der Nutzerin mit: "Endbericht: output/<basename>_v<n>.docx ist fertig."

Falls die Nutzerin "redo ohne Stufe N" oder ähnliches sagt:
  Führe Schritt 2 mit `--exclude N` aus und starte ab Schritt 3 neu.
