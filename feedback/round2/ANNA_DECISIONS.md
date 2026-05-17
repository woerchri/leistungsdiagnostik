# Anna-Marias Entscheidungen zu den 5 Round-2-Produktfragen

Antwort eingegangen: 2026-05-17. Implementierungs-Commit folgt in Round-2.1.

| # | Frage | Antwort |
|---|---|---|
| 1 | Hartes 5-Seiten-Cap oder Edge-Case-Toleranz? | **Immer 5 Seiten, immer die gleiche Struktur** — hartes Cap. |
| 2 | Was bei sehr langen Trainernotizen? | **Kürzen, sodass die Notizen auf einer Seite Platz haben** — Truncation mit Warnung. |
| 3 | Sport AnnaLytics als sichtbare Marke? | **Ja** — bleibt wie aktuell (Subtext Deckblatt + Footer-Logo, Anna-Maria nur in Kontaktdaten). |
| 4 | Wie detailliert darf 3-4-Wochen-Ausblick sein? | **3-5 Leitlinien mit einer Beispielwoche** — also Leitlinien-Block + konkrete Wochenstruktur. |
| 5 | Ernährungstipps immer oder bedingt? | **Immer**, und wenn nicht passend oder wenig zu beschreiben: kurzer Absatz. |

## Umsetzung

| # | Code-Change |
|---|---|
| 1 | Sarah-Fixture-5-Seiten-Test als zweite Referenz; Coaching-Truncation (siehe #2) sichert den Standardfall. |
| 2 | `_truncate()`-Helper in `src/ld/report.py` — pro Coaching-Feld eigener Char-Cap, Trainernotizen großzügiger; Truncation-Warning in stdout der Pipeline. |
| 3 | Kein Change. |
| 4 | `.codex/prompts/ld-report.md` — `coaching_ausblick_3_4_wochen` bekommt Beispielwoche-Subsektion, Wortcap auf 280. Prompt-Schema-Test prüft "Beispielwoche". |
| 5 | `.codex/prompts/ld-report.md` — `ernaehrung` darf 1-100 Wörter (statt fix max. 120) sein; Hinweis "wenn nicht viel zu beschreiben ist, ruhig kurz halten". |
