from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import openpyxl

from ld.errors import LDInputError
from ld.types import Athlete, Coaching, TestRun, TestStep, Testprotokoll


def parse_input(path: Path) -> TestRun:
    if not path.exists():
        raise LDInputError(f"Eingabedatei nicht gefunden: {path}")
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as e:
        raise LDInputError(f"Eingabedatei konnte nicht geöffnet werden ({path.name}): {e}") from e

    return TestRun(
        athlete=_parse_athlete(wb),
        testprotokoll=_parse_testprotokoll(wb),
        steps=_parse_steps(wb),
        coaching=_parse_coaching(wb),
    )


def _require_sheet(wb, name: str):
    if name not in wb.sheetnames:
        raise LDInputError(
            f"Arbeitsblatt '{name}' fehlt in der Eingabedatei. "
            f"Bitte mit templates/input_template.xlsx als Basis arbeiten."
        )
    return wb[name]


def _kv(ws, key: str) -> str | None:
    """Read column-A keyed pairs (key in col A, value in col B). Returns string or None."""
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True):
        if row and row[0] == key:
            return row[1]
    return None


def _required_kv(ws, key: str) -> str:
    value = _kv(ws, key)
    if value is None or value == "":
        raise LDInputError(f"Pflichtfeld '{key}' auf Blatt '{ws.title}' ist leer.")
    return str(value).strip()


def _parse_athlete(wb) -> Athlete:
    ws = _require_sheet(wb, "Athlet")
    sportart_raw = _required_kv(ws, "Sportart").lower().strip()
    SUPPORTED = {"lauf", "rad", "triathlon-rad", "triathlon-lauf", "unspezifisch"}
    if sportart_raw not in SUPPORTED:
        raise LDInputError(
            f"Sportart '{sportart_raw}' nicht unterstützt. Erlaubt: {sorted(SUPPORTED)}."
        )
    try:
        return Athlete(
            sportart=sportart_raw,
            vorname=_required_kv(ws, "Vorname"),
            name=_required_kv(ws, "Name"),
            geburtsjahr=int(_required_kv(ws, "Geburtsjahr")),
            geschlecht=(_kv(ws, "Geschlecht") or None),
            gewicht_kg=float(_required_kv(ws, "Gewicht (kg)")),
            groesse_m=float(_required_kv(ws, "Größe (m)")),
            trainingsziel=str(_kv(ws, "Trainingsziel") or ""),
            wettkampfziel=str(_kv(ws, "Wettkampfziel") or ""),
            trainingsumfang_wo=str(_kv(ws, "Trainingsumfang/Woche") or ""),
            leistungsniveau=str(_kv(ws, "Leistungsniveau") or ""),
        )
    except (ValueError, TypeError) as e:
        raise LDInputError(f"Athletendaten konnten nicht gelesen werden: {e}") from e


def _parse_testprotokoll(wb) -> Testprotokoll:
    ws = _require_sheet(wb, "Testprotokoll")
    raw_date = _kv(ws, "Testdatum")
    if isinstance(raw_date, datetime):
        test_date = raw_date.date()
    elif isinstance(raw_date, date):
        test_date = raw_date
    elif isinstance(raw_date, str):
        test_date = datetime.strptime(raw_date.strip(), "%d.%m.%Y").date()
    else:
        raise LDInputError(
            "Testdatum auf Blatt 'Testprotokoll' fehlt oder hat falsches Format (erwartet TT.MM.JJJJ)."
        )

    def yesno(key: str) -> bool:
        raw = _required_kv(ws, key).lower().strip()
        if raw in {"ja", "yes", "true", "1"}:
            return True
        if raw in {"nein", "no", "false", "0"}:
            return False
        raise LDInputError(
            f"Feld '{key}' auf 'Testprotokoll' erwartet JA oder NEIN, nicht '{raw}'."
        )

    letzte_voll = yesno("Letzte Stufe vollständig absolviert")
    dauer_letzte = None
    if not letzte_voll:
        raw = _required_kv(ws, "Dauer letzte Stufe (min)")
        try:
            dauer_letzte = float(raw)
        except ValueError as e:
            raise LDInputError(
                f"Dauer letzte Stufe muss eine Zahl in Minuten sein, nicht '{raw}'."
            ) from e

    stufenlaenge_raw = _kv(ws, "Stufenlänge (m)")
    return Testprotokoll(
        testdatum=test_date,
        uhrzeit=str(_kv(ws, "Uhrzeit") or "00:00"),
        durchfuehrungsort=_required_kv(ws, "Durchführungsort"),
        testleiter=_required_kv(ws, "Testleiter"),
        geraet=_required_kv(ws, "Gerät"),
        anfangsintensitaet=float(_required_kv(ws, "Anfangsintensität")),
        stufeninkrement=float(_required_kv(ws, "Stufeninkrement")),
        stufendauer_min=float(_required_kv(ws, "Stufendauer (min)")),
        stufenlaenge_m=(int(stufenlaenge_raw) if stufenlaenge_raw else None),
        besonderheiten=str(_kv(ws, "Besonderheiten") or ""),
        letzte_stufe_vollstaendig=letzte_voll,
        dauer_letzte_stufe_min=dauer_letzte,
        ausbelastung=yesno("Ausbelastung"),
    )


def _parse_steps(wb) -> tuple[TestStep, ...]:
    ws = _require_sheet(wb, "Testdaten")
    expected_headers = ["Stufe", "Intensität", "Herzfrequenz", "Laktat", "RPE"]
    actual = [
        str(ws.cell(row=1, column=c).value).strip()
        if ws.cell(row=1, column=c).value else ""
        for c in range(1, 6)
    ]
    if actual != expected_headers:
        raise LDInputError(
            f"Spaltenüberschriften auf 'Testdaten' falsch. "
            f"Erwartet: {expected_headers}, gefunden: {actual}."
        )

    steps: list[TestStep] = []
    for row_idx in range(2, ws.max_row + 1):
        stufe_val = ws.cell(row=row_idx, column=1).value
        if stufe_val is None or stufe_val == "":
            break
        try:
            steps.append(TestStep(
                stufe=int(stufe_val),
                intensitaet=float(ws.cell(row=row_idx, column=2).value),
                herzfrequenz_bpm=_int_or_none(ws.cell(row=row_idx, column=3).value),
                laktat_mmol=_float_or_none(ws.cell(row=row_idx, column=4).value),
                rpe=_int_or_none(ws.cell(row=row_idx, column=5).value),
            ))
        except (ValueError, TypeError) as e:
            raise LDInputError(
                f"Zeile {row_idx} auf 'Testdaten' enthält ungültige Werte: {e}"
            ) from e

    if len(steps) < 4:
        raise LDInputError(
            f"Mindestens 4 Stufen mit Laktatwerten erforderlich (kubische Anpassung). "
            f"Gefunden: {len(steps)}."
        )
    return tuple(steps)


def _parse_coaching(wb) -> Coaching:
    ws = _require_sheet(wb, "Coaching")
    return Coaching(
        verletzungen=str(_kv(ws, "Verletzungen") or ""),
        aktuelle_probleme=str(_kv(ws, "Aktuelle Probleme") or ""),
        staerken=str(_kv(ws, "Stärken") or ""),
        schwaechen=str(_kv(ws, "Schwächen") or ""),
        geplante_wettkaempfe=str(_kv(ws, "Geplante Wettkämpfe") or ""),
        trainernotizen=str(_kv(ws, "Trainernotizen") or ""),
    )


def _int_or_none(v):
    if v is None or v == "":
        return None
    return int(v)


def _float_or_none(v):
    if v is None or v == "":
        return None
    return float(v)
