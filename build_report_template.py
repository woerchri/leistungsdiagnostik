"""Build templates/report.docx with Jinja2 placeholders for docxtpl."""
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

OUT = Path("templates/report.docx")
OUT.parent.mkdir(exist_ok=True)

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin    = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

def heading(text, level=1):
    p = doc.add_heading(text, level=level)
    p.runs[0].font.color.rgb = RGBColor(0x1F, 0x49, 0x7D)
    return p

def body(text):
    p = doc.add_paragraph(text)
    p.runs[0].font.size = Pt(11) if p.runs else None
    return p

def add_table(headers, row_tpl, loop_var, items_var):
    """Add a table with a Jinja for-loop."""
    # Write the for/endfor as literal text paragraphs that docxtpl will process
    doc.add_paragraph("{% for " + loop_var + " in " + items_var + " %}")
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = t.cell(0, i)
        cell.text = ""
        run = cell.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(10)
        cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    row_cells = t.add_row().cells
    for i, tpl in enumerate(row_tpl):
        row_cells[i].text = ""
        row_cells[i].paragraphs[0].add_run(tpl).font.size = Pt(10)
    doc.add_paragraph("{% endfor %}")
    return t

# ── Title ────────────────────────────────────────────────────────────────────
title = doc.add_heading("Leistungsdiagnostik — Ergebnisbericht", 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# ── Athletendaten ─────────────────────────────────────────────────────────────
heading("Athletendaten", 1)
doc.add_paragraph(
    "Name: {{ athlete.vorname }} {{ athlete.name }}  |  "
    "Alter: {{ athlete.alter }} J.  |  "
    "Geschlecht: {{ athlete.geschlecht }}  |  "
    "Gewicht: {{ athlete.gewicht_kg }} kg  |  "
    "Größe: {{ athlete.groesse_m }} m"
)
doc.add_paragraph(
    "Sportart: {{ athlete.sportart_label }}  |  "
    "Trainingsziel: {{ athlete.trainingsziel }}  |  "
    "Wettkampfziel: {{ athlete.wettkampfziel }}"
)
doc.add_paragraph(
    "Trainingsumfang/Woche: {{ athlete.trainingsumfang_wo }}  |  "
    "Leistungsniveau: {{ athlete.leistungsniveau }}"
)

# ── Testprotokoll ─────────────────────────────────────────────────────────────
heading("Testprotokoll", 1)
doc.add_paragraph(
    "Datum: {{ testprotokoll.testdatum }}  |  Uhrzeit: {{ testprotokoll.uhrzeit }}  |  "
    "Ort: {{ testprotokoll.durchfuehrungsort }}  |  Testleiter: {{ testprotokoll.testleiter }}"
)
doc.add_paragraph(
    "Gerät: {{ testprotokoll.geraet }}  |  "
    "Besonderheiten: {{ testprotokoll.besonderheiten }}"
)
doc.add_paragraph(
    "Anfangsintensität: {{ testprotokoll.anfangsintensitaet }}  |  "
    "Inkrement: {{ testprotokoll.stufeninkrement }}  |  "
    "Stufendauer: {{ testprotokoll.stufendauer_min }} min  |  "
    "v_max: {{ vmax_display }} km/h  |  "
    "Ausbelastung: {{ ausbelastung_de }}"
)

# ── Testdaten ─────────────────────────────────────────────────────────────────
heading("Testdaten", 1)
add_table(
    headers=["Stufe", "Intensität", "Herzfrequenz (bpm)", "Laktat (mmol/l)", "RPE"],
    row_tpl=[
        "{{ s.stufe }}",
        "{{ s.intensitaet }}",
        "{{ s.herzfrequenz_bpm }}",
        "{{ s.laktat_mmol }}",
        "{{ s.rpe }}",
    ],
    loop_var="s",
    items_var="steps",
)

# ── Diagramm ──────────────────────────────────────────────────────────────────
heading("Diagramm", 1)
doc.add_paragraph("{{ diagram }}")

# ── Pflichtprüfungen ──────────────────────────────────────────────────────────
heading("Pflichtprüfungen", 1)
doc.add_paragraph("{% if failed_checks %}")
doc.add_paragraph("Folgende Hinweise wurden vor der Interpretation festgestellt:")
doc.add_paragraph("{% for p in failed_checks %}⚠ {{ p.message_de }}\n{% endfor %}")
doc.add_paragraph("{% else %}")
doc.add_paragraph("Alle Pflichtprüfungen: OK.")
doc.add_paragraph("{% endif %}")

# ── Schwellen-Schnittpunkte ───────────────────────────────────────────────────
heading("Schwellen-Schnittpunkte", 1)
add_table(
    headers=["Laktat (mmol/l)", "Geschwindigkeit (km/h)", "Pace (min/km)", "Herzfrequenz (bpm)"],
    row_tpl=[
        "{{ r.laktat }}",
        "{{ r.intensitaet }}",
        "{{ r.pace_min_per_km }}",
        "{{ r.herzfrequenz_bpm }}",
    ],
    loop_var="r",
    items_var="intersections",
)

# ── Trainingsbereiche ─────────────────────────────────────────────────────────
heading("Trainingsbereiche", 1)
add_table(
    headers=[
        "Zone", "Ziel", "v min (km/h)", "v max (km/h)",
        "Pace (min/km)", "HF min (bpm)", "HF max (bpm)", "RPE"
    ],
    row_tpl=[
        "{{ z.name }}",
        "{{ z.ziel }}",
        "{{ z.intensitaet_min }}",
        "{{ z.intensitaet_max }}",
        "{{ z.pace_max_min_per_km }} – {{ z.pace_min_min_per_km }}",
        "{{ z.herzfrequenz_min }}",
        "{{ z.herzfrequenz_max }}",
        "{{ z.rpe_min }} – {{ z.rpe_max }}",
    ],
    loop_var="z",
    items_var="zones",
)

# ── Interpretation ────────────────────────────────────────────────────────────
heading("Interpretation", 1)

heading("Zusammenfassung", 2)
doc.add_paragraph("{{ interp_zusammenfassung }}")

heading("Schwellen & Zonen", 2)
doc.add_paragraph("{{ interp_schwellen }}")

heading("Trainingsbereiche", 2)
doc.add_paragraph("{{ interp_zonen }}")

heading("Empfehlungen", 2)
doc.add_paragraph("{{ interp_empfehlungen }}")

# ── Coaching-Notizen ──────────────────────────────────────────────────────────
heading("Coaching-Notizen", 1)
doc.add_paragraph(
    "Verletzungen: {{ coaching.verletzungen }}\n"
    "Aktuelle Probleme: {{ coaching.aktuelle_probleme }}\n"
    "Stärken: {{ coaching.staerken }}\n"
    "Schwächen: {{ coaching.schwaechen }}\n"
    "Geplante Wettkämpfe: {{ coaching.geplante_wettkaempfe }}\n"
    "Trainernotizen: {{ coaching.trainernotizen }}"
)

doc.save(OUT)
print(f"Report-Template gespeichert: {OUT}")
