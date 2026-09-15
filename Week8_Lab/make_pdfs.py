#!/usr/bin/env python3
"""
make_pdfs.py

Turns our markdown write-ups into PDFs with ReportLab, so tables and code
blocks wrap properly instead of being cut off at the edge of the page.

    python3 make_pdfs.py                  builds every document listed in DOCS
    python3 make_pdfs.py in.md out.pdf    builds one document

Handles the markdown we actually use: headings, paragraphs, **bold**, `code`,
tables, fenced code blocks, lists, quotes, rules and ![images](path).
"""
import os
import re
import sys
import textwrap
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (HRFlowable, Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = [
    ("Task3_Performance_Evaluation.md", "Task3_Performance_Evaluation.pdf"),
    ("AI_Declaration.md", "AI_Declaration.pdf"),
    ("caas/results/caas_analysis.md", "caas/results/CAAS_Analysis.pdf"),
]
FOOTER = "FIT3143 Lab 2   |   Erwyna Soo Wen Xin (36555789) and Taabish Farooq Bhat (35473932)"
AUTHOR = "Erwyna Soo Wen Xin and Taabish Farooq Bhat"
PAGE_W = A4[0] - 30 * mm
FONT_DIR = "/System/Library/Fonts/Supplemental"


def _fonts():
    try:
        for name, file in [("Body", "Arial.ttf"), ("Body-Bold", "Arial Bold.ttf"),
                           ("Mono", "Courier New.ttf"), ("Mono-Bold", "Courier New Bold.ttf")]:
            pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, file)))
        for fam in ("Body", "Mono"):
            addMapping(fam, 0, 0, fam)
            addMapping(fam, 1, 0, fam + "-Bold")
            addMapping(fam, 0, 1, fam)
            addMapping(fam, 1, 1, fam + "-Bold")
        return "Body", "Mono"
    except Exception:
        return "Helvetica", "Courier"


BODY, MONO = _fonts()
GREY = colors.HexColor("#c9c9c9")
S = {
    "h1": ParagraphStyle("h1", fontName=BODY, fontSize=16, leading=20, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName=BODY, fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=2),
    "h3": ParagraphStyle("h3", fontName=BODY, fontSize=10.6, leading=14, spaceBefore=8, spaceAfter=3),
    "p": ParagraphStyle("p", fontName=BODY, fontSize=9.6, leading=13.2, spaceAfter=5),
    "li": ParagraphStyle("li", fontName=BODY, fontSize=9.6, leading=13.2, leftIndent=13,
                         bulletIndent=3, spaceAfter=2.5),
    "quote": ParagraphStyle("quote", fontName=BODY, fontSize=9.4, leading=13, leftIndent=10,
                            textColor=colors.HexColor("#333333"), spaceAfter=6),
    "cell": ParagraphStyle("cell", fontName=BODY, fontSize=8.3, leading=10.3),
    "code": ParagraphStyle("code", fontName=MONO, fontSize=8.2, leading=10.2),
    "caption": ParagraphStyle("caption", fontName=BODY, fontSize=8.3, leading=10.5,
                              alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=8),
    "meta": ParagraphStyle("meta", fontName=BODY, fontSize=8.6, leading=11, spaceBefore=7, spaceAfter=2),
    "record": ParagraphStyle("record", fontName=MONO, fontSize=7.8, leading=9.6, leftIndent=6),
}


def inline(text):
    """Escape text for ReportLab, turning `code` and **bold** into markup.
    Code spans are set aside first, so bold can wrap around them."""
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    t = escape(re.sub(r"`([^`]+)`", stash, text))
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: f'<font face="{MONO}">{escape(codes[int(m.group(1))])}</font>', t)


def wrap_lines(lines, width):
    wrapped = []
    for line in lines:
        line = line.replace("\t", "    ")
        wrapped.extend(textwrap.wrap(line, width, replace_whitespace=False, drop_whitespace=False,
                                     break_long_words=True, break_on_hyphens=False) or [""])
    return "\n".join(wrapped)


def code_block(lines):
    pre = Preformatted(wrap_lines(lines, 104), S["code"])
    box = Table([[pre]], colWidths=[PAGE_W], hAlign="LEFT")
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f5f5")),
                             ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                             ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return [box, Spacer(1, 6)]


def record_block(text):
    """A long verbatim block that is allowed to run across pages."""
    return Preformatted(wrap_lines(text.splitlines(), 112), S["record"])


def table_block(rows, head):
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    def need(i, c):
        text = re.sub(r"[`*]", "", rows[i][c])
        if head and i == 0:
            # header cells may wrap between words, so only their longest word counts
            return max((len(w) for w in text.split()), default=0)
        return len(text)

    lens = [min(max(need(i, c) for i in range(len(rows))), 55) + 2 for c in range(ncols)]
    natural = [max(l * 4.7 + 8, 30) for l in lens]
    if sum(natural) <= PAGE_W:
        widths = natural
    else:
        widths = [PAGE_W * l / sum(lens) for l in lens]
        short = [i for i, w in enumerate(widths) if w < 34]
        if short:
            spare = PAGE_W - 34 * len(short)
            rest = sum(lens[i] for i in range(ncols) if i not in short)
            widths = [34 if i in short else spare * lens[i] / rest for i in range(ncols)]
    data = [[Paragraph(f"<b>{inline(c)}</b>" if head and i == 0 else inline(c), S["cell"]) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0, hAlign="LEFT")
    style = [("GRID", (0, 0), (-1, -1), 0.5, GREY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
             ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if head:
        style.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef1f4")))
    t.setStyle(TableStyle(style))
    return [t, Spacer(1, 7)]


def image_block(path, caption):
    w, h = ImageReader(path).getSize()
    scale = min(PAGE_W / w, 125 * mm / h)
    parts = [Image(path, width=w * scale, height=h * scale)]
    if caption:
        parts.append(Paragraph(inline(caption), S["caption"]))
    return [KeepTogether(parts)]


def md_to_story(md, base_dir):
    lines = md.splitlines()
    story, para = [], []
    i = 0

    def flush():
        if para:
            if len(para) > 1 and all(x.strip().startswith("**") for x in para):
                # a block of "**Label:** value" lines keeps its line breaks
                story.append(Paragraph("<br/>".join(inline(x.strip()) for x in para), S["p"]))
            else:
                story.append(Paragraph(inline(" ".join(x.strip() for x in para)), S["p"]))
            para.clear()

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if s.startswith("```"):
            flush()
            code, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            story.extend(code_block(code))
            i += 1
            continue
        if not s:
            flush()
            i += 1
            continue
        if s == "\\pagebreak":
            flush()
            story.append(PageBreak())
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", s)
        if m:
            flush()
            level = len(m.group(1))
            story.append(Paragraph(f"<b>{inline(m.group(2))}</b>", S[f"h{level}"]))
            if level == 2:
                story.append(HRFlowable(width="100%", thickness=0.5, color=GREY, spaceBefore=1, spaceAfter=5))
            i += 1
            continue
        if re.match(r"^-{3,}$", s):
            flush()
            story.append(HRFlowable(width="100%", thickness=0.5, color=GREY, spaceBefore=4, spaceAfter=6))
            i += 1
            continue
        m = re.match(r"^!\[(.*?)\]\((.+?)\)$", s)
        if m:
            flush()
            story.extend(image_block(os.path.join(base_dir, m.group(2)), m.group(1)))
            i += 1
            continue
        if s.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head = len(rows) > 1 and all(re.match(r"^:?-{2,}:?$", c) for c in rows[1])
            story.extend(table_block([rows[0]] + rows[2:] if head else rows, head))
            continue
        if s.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            story.append(Paragraph(inline(" ".join(quote)), S["quote"]))
            continue
        if re.match(r"^(-|\d+\.)\s+", s):
            flush()
            while i < len(lines):
                t = lines[i]
                ts = t.strip()
                m = re.match(r"^(-|\d+\.)\s+(.*)$", ts)
                if m:
                    item, bullet = m.group(2), ("•" if m.group(1) == "-" else m.group(1))
                    i += 1
                    while i < len(lines) and lines[i].strip() and lines[i][:1] in (" ", "\t") \
                            and not re.match(r"^(-|\d+\.)\s+", lines[i].strip()):
                        item += " " + lines[i].strip()
                        i += 1
                    story.append(Paragraph(inline(item), S["li"], bulletText=bullet))
                else:
                    break
            story.append(Spacer(1, 3))
            continue
        para.append(raw)
        i += 1
    flush()
    return story


def make_pdf(pdf_path, story, title):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(BODY, 7.4)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(15 * mm, 9 * mm, FOOTER)
        canvas.drawRightString(A4[0] - 15 * mm, 9 * mm, f"Page {doc.page}")
        canvas.restoreState()

    part = pdf_path + ".part"
    doc = SimpleDocTemplate(part, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=14 * mm, bottomMargin=17 * mm,
                            title=title, author=AUTHOR, subject="FIT3143 Parallel Computing, Lab 2")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    os.replace(part, pdf_path)
    print("wrote", pdf_path)


def build(md_path, pdf_path):
    with open(md_path, encoding="utf-8") as fh:
        md = fh.read()
    m = re.search(r"^#\s+(.*)$", md, re.M)
    title = m.group(1).strip() if m else os.path.splitext(os.path.basename(pdf_path))[0]
    make_pdf(os.path.abspath(pdf_path), md_to_story(md, os.path.dirname(os.path.abspath(md_path))), title)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        build(sys.argv[1], sys.argv[2])
    else:
        for src, dst in DOCS:
            build(os.path.join(HERE, src), os.path.join(HERE, dst))
