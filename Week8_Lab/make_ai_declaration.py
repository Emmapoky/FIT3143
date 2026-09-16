#!/usr/bin/env python3
"""
make_ai_declaration.py

Builds AI_Declaration.pdf as our one AI declaration file for Moodle:

    Part 1  the declaration, from AI_Declaration.md
    Part 2  the Gemini Pro prompt record: a cover page with our names, then the
            transcript exported from Gemini (ai_records/gemini_pro_transcript.pdf),
            unedited, with our names stamped along the bottom of each page
    Part 3  the Claude prompt record, rebuilt from the Claude Code session logs
            by make_prompt_records.py

    python3 make_ai_declaration.py

Run it again right before uploading, so Part 3 includes the latest session,
then run ./make_zip.sh.
"""
import io
import os
import tempfile

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import Paragraph

import make_prompt_records
from make_pdfs import AUTHOR, BODY, FOOTER, S, build, make_pdf

HERE = os.path.dirname(os.path.abspath(__file__))
DECLARATION_MD = os.path.join(HERE, "AI_Declaration.md")
GEMINI_PDF = os.path.join(HERE, "ai_records", "gemini_pro_transcript.pdf")
OUT_PDF = os.path.join(HERE, "AI_Declaration.pdf")


def gemini_cover(path, pages):
    story = [
        Paragraph("<b>Part 2. AI Prompt Record: Gemini Pro (Google)</b>", S["h1"]),
        Paragraph("<b>Unit:</b> FIT3143 Parallel Computing, Semester 2 2026<br/>"
                  "<b>Assessment:</b> Lab 2, Message Passing Interface (Week 8)<br/>"
                  "<b>Team:</b> Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and "
                  "Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)", S["p"]),
        Paragraph(f"The next {pages} pages are the full transcript of our one Gemini Pro session for "
                  "Lab 2, \"Hybrid MPI and OpenMP Programming\", which Taabish and Erwyna worked "
                  "through together. It was exported from Gemini on 16 September 2026 and is "
                  "included unedited: all six prompts and every response. The only thing added is "
                  "the line with our names along the bottom of each page.", S["p"]),
    ]
    make_pdf(path, story, "AI Prompt Record: Gemini Pro", "Part 2")


def stamp(page, text_right):
    """Our names and the part page number, below Gemini's own print footer."""
    w, h = float(page.mediabox.width), float(page.mediabox.height)
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(w, h))
    c.setFont(BODY, 6.8)
    c.setFillColor(colors.HexColor("#666666"))
    c.drawString(42, 7, FOOTER)
    c.drawRightString(w - 42, 7, text_right)
    c.save()
    buf.seek(0)
    page.merge_page(PdfReader(buf).pages[0])
    return page


def main():
    tmp = tempfile.mkdtemp()
    part1 = os.path.join(tmp, "part1.pdf")
    cover = os.path.join(tmp, "part2_cover.pdf")
    part3 = os.path.join(tmp, "part3.pdf")

    build(DECLARATION_MD, part1, "Part 1")
    gemini = PdfReader(GEMINI_PDF)
    gemini_cover(cover, len(gemini.pages))
    make_prompt_records.build(part3, "Part 3")

    out = PdfWriter()
    start = {}

    start["Part 1. Declaration of generative AI use"] = len(out.pages)
    for p in PdfReader(part1).pages:
        out.add_page(p)

    start["Part 2. Prompt record: Gemini Pro"] = len(out.pages)
    cover_pages = PdfReader(cover).pages
    for p in cover_pages:
        out.add_page(p)
    for i, p in enumerate(gemini.pages, start=len(cover_pages) + 1):
        out.add_page(stamp(p, f"Part 2, page {i}"))

    start["Part 3. Prompt record: Claude"] = len(out.pages)
    for p in PdfReader(part3).pages:
        out.add_page(p)

    for title, page in start.items():
        out.add_outline_item(title, page)
    out.add_metadata({"/Title": "FIT3143 Lab 2: Declaration of Generative AI Use",
                      "/Author": AUTHOR, "/Subject": "FIT3143 Parallel Computing, Lab 2"})

    part = OUT_PDF + ".part"
    with open(part, "wb") as fh:
        out.write(fh)
    os.replace(part, OUT_PDF)
    print(f"wrote {OUT_PDF}: {len(out.pages)} pages")
    for title, page in start.items():
        print(f"  {title} starts on page {page + 1}")


if __name__ == "__main__":
    main()
