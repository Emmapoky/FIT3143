"""
render_pdf.py
Turns Task1_Answers.md into Task1_Answers.html and Task1_Answers.pdf
(markdown-it-py for HTML, headless Google Chrome for the PDF).
Erwyna Soo Wen Xin (36555789), Taabish Farooq Bhat (35473932)
Run: python3 tools/render_pdf.py
"""

import os
import subprocess

from markdown_it import MarkdownIt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
body { font-family: -apple-system, Helvetica, Arial, sans-serif;
       font-size: 10.5pt; line-height: 1.45; color: #1F2933;
       max-width: 180mm; margin: 0 auto; }
h1 { font-size: 18pt; margin-bottom: 4pt; }
h2 { font-size: 14pt; color: #2F6DB5; border-bottom: 1px solid #ccd;
     padding-bottom: 2pt; margin-top: 18pt; }
img { width: 100%; border: 1px solid #e3e6ea; margin: 6pt 0; }
table { border-collapse: collapse; width: 100%; font-size: 9pt;
        margin: 6pt 0; }
th, td { border: 1px solid #c9ced6; padding: 3pt 5pt; vertical-align: top;
         text-align: left; }
th { background: #EEF3FA; }
code { font-size: 9pt; background: #F3F4F6; padding: 0 2pt; }
hr { border: none; border-top: 1px solid #e3e6ea; margin: 14pt 0; }
p { margin: 5pt 0; }
@page { size: A4; margin: 15mm 14mm; }
"""


def main():
    md = open(os.path.join(ROOT, "Task1_Answers.md")).read()
    body = MarkdownIt("commonmark").enable("table").render(md)
    html = ("<!doctype html><html><head><meta charset='utf-8'>"
            "<title>FIT3143 Applied 2 Task 1</title><style>" + CSS +
            "</style></head><body>" + body + "</body></html>")
    html_path = os.path.join(ROOT, "Task1_Answers.html")
    with open(html_path, "w") as f:
        f.write(html)
    pdf_path = os.path.join(ROOT, "Task1_Answers.pdf")
    subprocess.run([CHROME, "--headless", "--disable-gpu",
                    "--no-pdf-header-footer",
                    "--print-to-pdf=" + pdf_path, "file://" + html_path],
                   check=True, capture_output=True)
    print("wrote", html_path, "and", pdf_path)


if __name__ == "__main__":
    main()
