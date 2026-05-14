"""Build templates/report.docx — 5-page A4 landscape Leistungsdiagnostik report.

Layout (per Anna 2026-05-13 feedback):
  Page 1: Deckblatt (cover, no footer, no page number).
  Page 2: Athletendaten + Testprotokoll + Plot.
  Page 3: Schwellenschnittpunkte + Trainingsbereiche tables.
  Page 4: Interpretation (Zusammenfassung, Schwellen & Zonen, Empfehlungen).
          NOTE: separate "Trainingsbereiche" prose section removed by request.
  Page 5: Trainerseite — intern (Pflichtprüfungen + Fachnotizen + Risikoanalyse
          + Schwellenlogik + Trainernotizen).

Brand:
  Primary  Dunkelblau   #0B2545
  Accent   Türkis       #16C5A5
  Text     Dunkelgrau   #2C2C2C
  Lines    Hellgrau     #D1D5DB

Tables use docxtpl `{%tr ... %}` row-loop syntax so the header appears exactly
once per table (Anna 2026-05-13 — "nur ein Tabellenkopf").
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path("templates/report.docx")
LOGO = Path("assets/logo_placeholder.png")
OUT.parent.mkdir(exist_ok=True)

# ── Brand tokens ─────────────────────────────────────────────────────────────
PRIMARY = RGBColor(0x0B, 0x25, 0x45)   # Dunkelblau
ACCENT  = RGBColor(0x16, 0xC5, 0xA5)   # Türkis
TEXT    = RGBColor(0x2C, 0x2C, 0x2C)   # Dunkelgrau
LINE    = RGBColor(0xD1, 0xD5, 0xDB)   # Hellgrau
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)

# Trainer contact (Anna 2026-05-13)
CONTACT_EMAIL = "anna-maria@woerndle.at"
CONTACT_PHONE = "+43 677 62150496"


# ── Document setup: A4 landscape ─────────────────────────────────────────────
doc = Document()

# Configure base styles
styles = doc.styles
for sname in ("Normal",):
    style = styles[sname]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)
    style.font.color.rgb = TEXT

section = doc.sections[0]
section.orientation = WD_ORIENT.LANDSCAPE
section.page_width  = Cm(29.7)
section.page_height = Cm(21.0)
section.top_margin    = Cm(1.6)
section.bottom_margin = Cm(1.8)
section.left_margin   = Cm(1.8)
section.right_margin  = Cm(1.8)
section.different_first_page_header_footer = True  # no footer on cover


# ── Helpers ──────────────────────────────────────────────────────────────────
def _set_cell_bg(cell, hex_no_hash: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_no_hash)
    tc_pr.append(shd)


def _set_cell_borders(cell, color_hex: str = "D1D5DB", size_pt: int = 4) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), str(size_pt))
        b.set(qn("w:color"), color_hex)
        borders.append(b)
    tc_pr.append(borders)


def heading(text: str, level: int = 1, color: RGBColor = PRIMARY) -> None:
    p = doc.add_heading(text, level=level)
    if p.runs:
        run = p.runs[0]
        run.font.color.rgb = color
        run.font.size = Pt({1: 16, 2: 13, 3: 11}.get(level, 11))
        run.font.bold = True


def body(text: str, *, bold: bool = False, color: RGBColor = TEXT, size_pt: int = 10) -> None:
    p = doc.add_paragraph(text)
    if p.runs:
        run = p.runs[0]
        run.font.size = Pt(size_pt)
        run.font.color.rgb = color
        run.font.bold = bold


def page_break() -> None:
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_table_with_loop(*, headers: list[str], row_template: list[str], loop_var: str, items_var: str,
                        header_widths_cm: list[float] | None = None) -> None:
    """Build a table with ONE header row + a docxtpl `{%tr%}` body-row loop.

    docxtpl's `{%tr%}` preprocessing REPLACES the entire `<w:tr>` containing
    the tag with the equivalent Jinja tag (see template.py lines 180-191).
    So tags MUST be on their own dedicated rows, not mixed with the data row.

    Layout:
      Row 0: header (visible, static)
      Row 1: contains only `{%tr for X in ITEMS %}` — deleted at preprocess
      Row 2: data row with `{{ X.field }}` placeholders — looped N times
      Row 3: contains only `{%tr endfor %}` — deleted at preprocess
    """
    t = doc.add_table(rows=4, cols=len(headers))
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    t.autofit = False

    # Column widths
    if header_widths_cm:
        for i, w in enumerate(header_widths_cm):
            for row in t.rows:
                row.cells[i].width = Cm(w)

    # ── Row 0: Header (visible) ──
    for i, h in enumerate(headers):
        cell = t.cell(0, i)
        cell.text = ""
        _set_cell_bg(cell, "0B2545")
        _set_cell_borders(cell, "0B2545")
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(h)
        run.font.bold = True
        run.font.size = Pt(9.5)
        run.font.color.rgb = WHITE

    # ── Row 1: `{%tr for ... %}` tag row (gets eaten by docxtpl) ──
    tag_open = t.cell(1, 0)
    tag_open.text = ""
    tag_open.paragraphs[0].add_run("{%tr for " + loop_var + " in " + items_var + " %}")

    # ── Row 2: Data row (visible, repeated per iteration) ──
    for i, tpl in enumerate(row_template):
        cell = t.cell(2, i)
        cell.text = ""
        _set_cell_borders(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(tpl)
        run.font.size = Pt(10)
        run.font.color.rgb = TEXT

    # ── Row 3: `{%tr endfor %}` tag row (gets eaten by docxtpl) ──
    tag_close = t.cell(3, 0)
    tag_close.text = ""
    tag_close.paragraphs[0].add_run("{%tr endfor %}")


def add_kv_table(rows: list[tuple[str, str]], *, key_width_cm: float = 5.5, val_width_cm: float = 9.0) -> None:
    """Two-column key/value table without a header — used for athlete data,
    test protocol summaries, etc."""
    t = doc.add_table(rows=len(rows), cols=2)
    t.autofit = False
    for i, (k, v) in enumerate(rows):
        kc, vc = t.cell(i, 0), t.cell(i, 1)
        kc.width = Cm(key_width_cm); vc.width = Cm(val_width_cm)
        _set_cell_borders(kc); _set_cell_borders(vc)
        kc.text = ""; vc.text = ""
        kr = kc.paragraphs[0].add_run(k)
        kr.font.bold = True; kr.font.size = Pt(10); kr.font.color.rgb = PRIMARY
        vr = vc.paragraphs[0].add_run(v)
        vr.font.size = Pt(10); vr.font.color.rgb = TEXT


# ── PAGE 1: Deckblatt ────────────────────────────────────────────────────────
# Empty paragraphs to push content vertically (cover is intentionally airy).
for _ in range(2):
    doc.add_paragraph()

# Logo, mittig
if LOGO.exists():
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.add_run().add_picture(str(LOGO), width=Cm(6.0))

for _ in range(2):
    doc.add_paragraph()

# Test title — sportart-aware
title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_run = title_p.add_run("Leistungsdiagnostik {{ athlete.sportart_label }}")
title_run.font.size = Pt(32); title_run.font.bold = True; title_run.font.color.rgb = PRIMARY

# Spacer
for _ in range(2):
    doc.add_paragraph()

# Athlete name
name_p = doc.add_paragraph()
name_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
name_run = name_p.add_run("{{ athlete.vorname }} {{ athlete.name }}")
name_run.font.size = Pt(22); name_run.font.color.rgb = ACCENT

# Date + location
meta_p = doc.add_paragraph()
meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta_run = meta_p.add_run("{{ testprotokoll.testdatum }}  ·  {{ testprotokoll.durchfuehrungsort }}")
meta_run.font.size = Pt(13); meta_run.font.color.rgb = TEXT

# Trainer
for _ in range(4):
    doc.add_paragraph()

trainer_p = doc.add_paragraph()
trainer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
trainer_run = trainer_p.add_run("Erstellt von Anna-Maria Wörndle")
trainer_run.font.size = Pt(11); trainer_run.font.color.rgb = TEXT; trainer_run.font.italic = True

contact_p = doc.add_paragraph()
contact_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
contact_run = contact_p.add_run(f"{CONTACT_EMAIL}  ·  {CONTACT_PHONE}")
contact_run.font.size = Pt(10); contact_run.font.color.rgb = TEXT


# ── PAGE 2: Athletendaten + Testprotokoll + Plot ─────────────────────────────
page_break()
heading("Athletendaten", level=1)

add_kv_table([
    ("Name",            "{{ athlete.vorname }} {{ athlete.name }}"),
    ("Email",           "{{ athlete.email }}"),
    ("Geburtsjahr",     "{{ athlete.geburtsjahr }}"),
    ("Alter",           "{{ athlete.alter }} Jahre"),
    ("Geschlecht",      "{{ athlete.geschlecht }}"),
    ("Gewicht",         "{{ athlete.gewicht_kg }} kg"),
    ("Größe",           "{{ athlete.groesse_m }} m"),
    ("Trainingsziel",   "{{ athlete.trainingsziel }}"),
    ("Wettkampfziel",   "{{ athlete.wettkampfziel }}"),
    ("Trainingsumfang", "{{ athlete.trainingsumfang_wo }}"),
    ("Leistungsniveau", "{{ athlete.leistungsniveau }}"),
])

doc.add_paragraph()

heading("Testprotokoll", level=2)
add_kv_table([
    ("Sportart",        "{{ testprotokoll.sportart_label }}"),
    ("Datum",           "{{ testprotokoll.testdatum }}"),
    ("Uhrzeit",         "{{ testprotokoll.uhrzeit }}"),
    ("Ort",             "{{ testprotokoll.durchfuehrungsort }}"),
    ("Testleiter",      "{{ testprotokoll.testleiter }}"),
    ("Gerät",           "{{ testprotokoll.geraet }}"),
    ("Anfangsbelastung","{{ testprotokoll.anfangsbelastung_display }}"),
    ("Stufeninkrement", "{{ testprotokoll.stufeninkrement_display }}"),
    ("Stufendauer",     "{{ testprotokoll.stufendauer_min }} min"),
    ("Besonderheiten",  "{{ testprotokoll.besonderheiten }}"),
    ("Ausbelastung",    "{{ ausbelastung_de }}"),
    ("{{ v_max_label }}", "{{ v_max_display }}"),
    ("Nachbelastungslaktat 3 min", "{{ testprotokoll.nachbelastungslaktat_3min }}"),
    ("Nachbelastungslaktat 5 min", "{{ testprotokoll.nachbelastungslaktat_5min }}"),
])

doc.add_paragraph()
heading("Laktat- und Herzfrequenzverlauf", level=2)
plot_p = doc.add_paragraph()
plot_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
plot_p.add_run("{{ diagram }}")


# ── PAGE 3: Schwellenschnittpunkte + Trainingsbereiche ──────────────────────
page_break()
heading("Analyse der Leistungsdiagnostik", level=1)

heading("Schwellenschnittpunkte", level=2)
add_table_with_loop(
    headers=["Laktat (mmol/l)", "{{ x_axis_label }}", "Pace (min/km)", "Herzfrequenz (bpm)"],
    row_template=[
        "{{ r.laktat }}",
        "{{ r.intensitaet }}",
        "{{ r.pace_min_per_km }}",
        "{{ r.herzfrequenz_bpm }}",
    ],
    loop_var="r",
    items_var="intersections",
    header_widths_cm=[4.5, 6.0, 5.5, 5.5],
)

doc.add_paragraph()
heading("Trainingsbereiche", level=2)
add_table_with_loop(
    headers=["Zone", "Ziel", "Bereich", "Pace (min/km)", "Herzfrequenz (bpm)", "RPE"],
    row_template=[
        "{{ z.name }}",
        "{{ z.ziel }}",
        "{{ z.intensitaet_range }}",
        "{{ z.pace_range }}",
        "{{ z.herzfrequenz_range }}",
        "{{ z.rpe }}",
    ],
    loop_var="z",
    items_var="zones",
    header_widths_cm=[1.8, 4.0, 4.5, 4.5, 4.5, 2.0],
)


# ── PAGE 4: Interpretation ──────────────────────────────────────────────────
page_break()
heading("Interpretation", level=1)

heading("Zusammenfassung", level=2)
body("{{ interp_zusammenfassung }}")
doc.add_paragraph()

heading("Schwellen & Zonen", level=2)
body("{{ interp_schwellen }}")
doc.add_paragraph()

heading("Empfehlungen", level=2)
body("{{ interp_empfehlungen }}")


# ── PAGE 5: Trainerseite — INTERN ───────────────────────────────────────────
page_break()
intern_p = doc.add_paragraph()
intern_run = intern_p.add_run("Trainerseite — Intern (nicht für Athlet:in)")
intern_run.font.size = Pt(10); intern_run.font.italic = True; intern_run.font.color.rgb = ACCENT
heading("Fachliche Notizen", level=1)

heading("Pflichtprüfungen — Kontrolle der Testqualität", level=2)
# `{%p ... %}` removes the host paragraph so if/else/endif don't leave blank
# lines. The for-loop body stays on one paragraph (plain `{% %}`), so each
# iteration's text concatenates within that paragraph.
body("{%p if internal_failed_checks %}")
body("Folgende Hinweise wurden vor der Interpretation festgestellt:")
body("{% for p in internal_failed_checks %}⚠ {{ p.message_de }}\n{% endfor %}")
body("{%p else %}")
body("Alle Pflichtprüfungen: OK.")
body("{%p endif %}")

doc.add_paragraph()
heading("Risikoanalyse", level=2)
body("{{ interp_risiko if interp_risiko else 'Keine besonderen Risiken aus den Daten ableitbar — siehe Pflichtprüfungen.' }}")

doc.add_paragraph()
heading("Schwellenlogik", level=2)
body(
    "Die Zonengrenzen sind Orientierungspunkte. Z2-Obergrenze: v bei 2.0 mmol/l. "
    "Z3-Obergrenze: v bei 3.0 mmol/l. Z4-Obergrenze: v bei 4.0 mmol/l. "
    "Z5-Obergrenze: Maximalgeschwindigkeit (aliquot-korrigiert). "
    "Z6 darüber. Diese Werte werden mit Kurvenform, HF-Verlauf und RPE-Muster "
    "kombiniert (keine rein fixen mmol-Schwellen). Der/die Trainer:in bestätigt "
    "oder passt die Vorschläge an.",
    size_pt=9,
)

doc.add_paragraph()
heading("Trainernotizen", level=2)
add_kv_table([
    ("Verletzungen",          "{{ coaching.verletzungen }}"),
    ("Aktuelle Probleme",     "{{ coaching.aktuelle_probleme }}"),
    ("Stärken",               "{{ coaching.staerken }}"),
    ("Schwächen",             "{{ coaching.schwaechen }}"),
    ("Geplante Wettkämpfe",   "{{ coaching.geplante_wettkaempfe }}"),
    ("Trainernotizen",        "{{ coaching.trainernotizen }}"),
])


# ── Footer (pages 2–5, suppressed on page 1) ─────────────────────────────────
def _build_footer(section, *, primary_color: RGBColor = PRIMARY) -> None:
    """3-column footer: contact left, page number center-right, mini-logo right.
    Plus a thin top border for visual separation."""
    footer = section.footer
    footer.is_linked_to_previous = False
    # Clear default footer paragraph
    for p in list(footer.paragraphs):
        p._element.getparent().remove(p._element)

    table = footer.add_table(rows=1, cols=3, width=Cm(26.0))
    table.autofit = False
    cells = table.rows[0].cells
    cells[0].width = Cm(13.0); cells[1].width = Cm(7.0); cells[2].width = Cm(6.0)

    # Thin top border on each footer cell
    for c in cells:
        tc_pr = c._tc.get_or_add_tcPr()
        borders = OxmlElement("w:tcBorders")
        top = OxmlElement("w:top")
        top.set(qn("w:val"), "single"); top.set(qn("w:sz"), "4"); top.set(qn("w:color"), "D1D5DB")
        borders.append(top)
        tc_pr.append(borders)

    # Left: contact
    cl = cells[0].paragraphs[0]
    cl.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = cl.add_run(f"{CONTACT_EMAIL}  ·  {CONTACT_PHONE}")
    run.font.size = Pt(8); run.font.color.rgb = TEXT

    # Center: page number (via field code)
    cm = cells[1].paragraphs[0]
    cm.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cm.add_run("Seite ")
    run.font.size = Pt(8); run.font.color.rgb = TEXT

    # Field code: PAGE
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.text = "PAGE"
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    page_run = cm.add_run()
    page_run.font.size = Pt(8); page_run.font.color.rgb = TEXT
    page_run._r.append(fld_char_begin); page_run._r.append(instr); page_run._r.append(fld_char_end)

    # Right: mini logo
    cr = cells[2].paragraphs[0]
    cr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if LOGO.exists():
        cr.add_run().add_picture(str(LOGO), width=Cm(2.0))


def _hide_first_page_footer(section) -> None:
    """Make the first-page footer empty so the cover has no page number/contact."""
    fp = section.first_page_footer
    for p in list(fp.paragraphs):
        p._element.getparent().remove(p._element)
    fp.add_paragraph()  # one empty paragraph to satisfy schema


_build_footer(section)
_hide_first_page_footer(section)


# ── Save ─────────────────────────────────────────────────────────────────────
doc.save(OUT)
print(f"Report-Template gespeichert: {OUT}")
