from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from ld.types import AnalysisResult, Paths


logger = logging.getLogger("ld")

_MODEL = "gpt-4o-2024-08-06"

_PROMPT = """Du bist sportwissenschaftlicher Assistent. Verfasse eine erste Interpretation einer Leistungsdiagnostik auf Deutsch.

Regeln:
- Zitiere konkrete Werte aus den Daten (Schwellen, Zonen, abgeleitete Größen).
- Markiere alle Auffälligkeiten (Werte außerhalb erwartbarer Bereiche).
- Schlage Konsequenzen für das Training in den Zonen vor.
- Berücksichtige die in den Pflichtprüfungen markierten Hinweise.
- Berücksichtige den Kontext, den der Nutzer angegeben hat.
- Verwende keine rein fixen mmol-Schwellen — die Zonen ergeben sich aus dem Kurvenverlauf,
  Herzfrequenzverlauf und subjektiver Belastung. Du darfst die übergebenen Zonenwerte als
  Grundlage verwenden, aber bei Bedarf vorsichtiger formulieren.
- Erfinde keine Werte, die nicht in den Daten stehen.
- Format der Antwort: JSON mit den Schlüsseln "zusammenfassung", "schwellen", "zonen",
  "empfehlungen". Jeder Wert ist deutscher Fließtext (1-3 Absätze).

Daten (anonymisiert):
{data_json}

Pflichtprüfungen:
{checks}

Kontext vom Nutzer:
{context}

Antworte ausschließlich mit dem JSON-Objekt."""


def run(result: AnalysisResult, paths: Paths, user_context: str = "") -> dict[str, str]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        from ld.errors import LDError
        raise LDError(
            "OPENAI_API_KEY ist nicht gesetzt. Erstelle eine .env-Datei mit OPENAI_API_KEY=... oder "
            "nutze /ld-report in Codex."
        )

    from openai import OpenAI

    data_source = paths.json_for_llm if paths.json_for_llm.exists() else paths.json_full
    data_json = data_source.read_text()

    failed_checks = [p for p in result.pflichtpruefungen if not p.ok]
    checks_text = "\n".join(f"- {p.message_de}" for p in failed_checks) or "alle OK"

    prompt = _PROMPT.format(
        data_json=data_json,
        checks=checks_text,
        context=user_context.strip() or "(kein zusätzlicher Kontext)",
    )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)

    required = {"zusammenfassung", "schwellen", "zonen", "empfehlungen"}
    missing = required - parsed.keys()
    if missing:
        raise RuntimeError(f"LLM-Antwort fehlen Felder: {missing}")

    out_path = paths.output_dir / f"{paths.basename}_interpretation.json"
    out_path.write_text(json.dumps(parsed, indent=2, ensure_ascii=False))
    return parsed
