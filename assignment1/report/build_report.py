"""Build the report (report/Assignment01_CastilloGarcera_Report.docx) from the results.

All numbers in the tables are read from results/*.csv, so the report always matches
the measurements. Convert to PDF with LibreOffice:
    soffice --headless --convert-to pdf --outdir report report/Assignment01_CastilloGarcera_Report.docx

Usage: python report/build_report.py
"""
import csv
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from text import SECTIONS  # the written text of the report (report/text.py)

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
FIG = ROOT / "figures"
OUT = ROOT / "report" / "Assignment01_CastilloGarcera_Report.docx"
NAMES = {"c": "C", "java": "Java", "python": "Python"}
BLUE = RGBColor(0x1F, 0x4E, 0x79)


def read(name):
    with open(RES / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- formatting helpers
def add_runs(par, text):
    """Add text to a paragraph; **bold** and `code` segments are formatted."""
    import re
    for part in re.split(r"(\*\*[^*]+\*\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**"):
            par.add_run(part[2:-2]).bold = True
        elif part.startswith("`"):
            r = par.add_run(part[1:-1])
            r.font.name = "Consolas"
            r.font.size = Pt(9.5)
        else:
            par.add_run(part)


def para(doc, text, style=None):
    p = doc.add_paragraph(style=style)
    add_runs(p, text)
    p.paragraph_format.space_after = Pt(4)
    return p


def shade(cell, hex_color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def is_number(v):
    """True for values like 512, 4.41, 1.8e-15, 0.112 ms, 40.48 s, 4733 s."""
    text = str(v).replace(" ms", "").replace(" s", "")
    try:
        float(text)
        return True
    except ValueError:
        return False


def table(doc, header, rows, caption, widths=None):
    cap = doc.add_paragraph()
    r = cap.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    cap.paragraph_format.space_before = Pt(6)
    cap.paragraph_format.space_after = Pt(2)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(h)
        run.bold = True
        run.font.size = Pt(8.5)
        shade(c, "DCE6F1")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(v))
            run.font.size = Pt(8.5)
            if i > 0 and is_number(v):
                cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    # keep the caption and the table on the same page
    cap.paragraph_format.keep_with_next = True
    for row in t.rows:
        no_split = OxmlElement("w:cantSplit")          # a row never breaks across pages
        row._tr.get_or_add_trPr().append(no_split)
    for row in t.rows[:-1]:
        for c in row.cells:
            c.paragraphs[0].paragraph_format.keep_with_next = True
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return t


def figure(doc, file, caption, width_cm=13):
    doc.add_picture(str(FIG / file), width=Cm(width_cm))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap = doc.add_paragraph()
    r = cap.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER


def fmt_s(x):
    x = float(x)
    if x < 0.01:
        return f"{x * 1000:.3f} ms"
    if x < 1:
        return f"{x * 1000:.1f} ms"
    return f"{x:.2f} s"


# ---------------------------------------------------------------- data tables
def tables_from_results():
    summary = read("summary.csv")
    runs = read("raw/runs.csv")
    slopes = read("slopes.csv")
    validation = read("validation.csv")
    env = json.load(open(RES / "environment.json", encoding="utf-8"))
    extra = read("extra_power_of_two.csv") if (RES / "extra_power_of_two.csv").exists() else []
    return summary, runs, slopes, validation, env, extra


def build():
    summary, runs, slopes, validation, env, extra = tables_from_results()

    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for side in ("left_margin", "right_margin"):
        setattr(sec, side, Cm(2.2))
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    for name, size in (("Heading 1", 14), ("Heading 2", 11.5)):
        st = doc.styles[name]
        st.font.name = "Calibri"
        st.font.size = Pt(size)
        st.font.color.rgb = BLUE

    # ---- title block
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run(SECTIONS["title"])
    r.bold = True
    r.font.size = Pt(17)
    r.font.color.rgb = BLUE
    for line in SECTIONS["byline"]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        p.add_run(line).font.size = Pt(10)
    doc.add_paragraph()

    for block in SECTIONS["body"]:
        kind = block[0]
        if kind == "h1":
            doc.add_heading(block[1], level=1)
        elif kind == "h2":
            doc.add_heading(block[1], level=2)
        elif kind == "p":
            para(doc, block[1])
        elif kind == "bullets":
            for item in block[1]:
                para(doc, item, style="List Bullet")
        elif kind == "table":
            table(doc, block[1], block[2], block[3])
        elif kind == "figure":
            figure(doc, block[1], block[2])
        elif kind == "env_table":
            rows = [["CPU", env["cpu"]],
                    ["Cores", f"{env['physical_cores']} physical, {env['logical_processors']} logical"],
                    ["RAM", f"{env['ram_gb']} GB"],
                    ["Operating system", env["os"]],
                    ["Python", f"{env['python']} (NumPy {env['numpy']}, psutil {env['psutil']}, matplotlib {env['matplotlib']})"],
                    ["Java", env["java_runtime"].split(" | ")[2] + f"; options {' '.join(env['java_options'])}"],
                    ["C compiler", env["c_compiler"] + f"; flags {' '.join(env['c_flags'])}"],
                    ["Threads", "kernels single-threaded; no BLAS; the JVM also runs its own JIT and GC threads"]]
            table(doc, ["Item", "Value"], rows, block[1])
        elif kind == "summary_table":
            rows = []
            for s in summary:
                rows.append([NAMES[s["language"]], s["n"], s["measured_runs"], fmt_s(s["median_s"]),
                             fmt_s(s["iqr_s"]), f"{float(s['ns_per_inner_iteration']):.2f}",
                             f"{float(s['relative_to_c']):.2f}", f"{float(s['peak_memory_mib']):.1f}"])
            table(doc, ["Language", "n", "Runs", "Median time", "IQR", "ns / iteration", "× C", "Peak memory (MiB)"],
                  rows, block[1])
        elif kind == "status_table":
            rows = []
            for r in runs:
                if r["status"] == "ok":
                    continue
                rows.append([NAMES[r["language"]], r["n"], r["status"].replace("_", " "),
                             f"{float(r['predicted_total_s']):.0f} s" if r["predicted_total_s"] else "-"])
            table(doc, ["Language", "n", "Status", "Predicted total time"], rows, block[1])
        elif kind == "slope_table":
            rows = [[NAMES[s["language"]], s["sizes_used"], s["exponent_b"]] for s in slopes]
            table(doc, ["Language", "Sizes used for the fit", "Exponent b (time ≈ a × nᵇ)"], rows, block[1])
        elif kind == "validation_table":
            rows = []
            for n in sorted({int(v["n"]) for v in validation}):
                vs = [v for v in validation if int(v["n"]) == n]
                rows.append([n, max(float(v["max_abs_error"]) for v in vs), max(float(v["max_rel_error"]) for v in vs),
                             "yes" if all(v["passed"] == "True" for v in vs) else "NO",
                             "yes" if vs[0]["bit_identical_across_languages"] == "True" else "no"])
            rows = [[r[0], f"{r[1]:.1e}", f"{r[2]:.1e}", r[3], r[4]] for r in rows]
            table(doc, ["n", "Max abs. error", "Max rel. error", "All pass", "C = Java = Python bit by bit"],
                  rows, block[1])
        elif kind == "extra_table" and extra:
            rows = []
            for lang in ("c", "java"):
                for center in (256, 512, 1024):
                    vals = {int(r["n"]): float(r["ns_per_inner_iteration"]) for r in extra if r["language"] == lang}
                    rows.append([NAMES[lang], center, f"{vals[center - 1]:.2f}", f"{vals[center]:.2f}",
                                 f"{vals[center + 1]:.2f}"])
            table(doc, ["Language", "n", "n - 1", "n (power of 2)", "n + 1"], rows, block[1])
        elif kind == "pagebreak":
            doc.add_page_break()
        else:
            raise ValueError(kind)

    doc.save(OUT)
    print("Wrote", OUT)


if __name__ == "__main__":
    build()
