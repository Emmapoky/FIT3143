#!/usr/bin/env python3
"""
make_prompt_records.py

Builds AI_Prompt_Records_Claude.pdf: every prompt typed into Claude (Anthropic)
for FIT3143 Lab 2, taken straight from the Claude Code session logs on
Erwyna's laptop, in the order they were sent.

    python3 make_prompt_records.py [output.pdf]

Run it again right before submitting so the last session is complete.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

from xml.sax.saxutils import escape

from reportlab.platypus import Paragraph

from make_pdfs import S, make_pdf, record_block

LOG_DIR = os.path.expanduser("~/.claude/projects/-Users-erwynasoo-Desktop-Obsidian-Vault")
SESSIONS = [
    ("54a57b0e-35d1-4ca9-9e4f-4f7db3448dd5.jsonl",
     "Session 1, 8 and 9 September 2026: reviewing Task 1 and Task 2, the slides, "
     "the Task 3 measurements, the CAAS run and packaging the submission"),
    ("9d76bc22-df48-443c-8ff7-8dc3b695fed0.jsonl",
     "Session 2, 15 September 2026: final check against the specification and rubric, "
     "per rank timing, the Task 3 sweep over n, and Q&A practice"),
]
MYT = timezone(timedelta(hours=8))
LONG = 6000                 # a prompt longer than this is mostly pasted course material
KEEP_HEAD, KEEP_TAIL = 900, 400
SKIP = ("[Request interrupted by user", "<task-notification>", "<local-command", "Caveat:")

def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(x.get("text", "") for x in content
                         if isinstance(x, dict) and x.get("type") == "text")
    return ""


def records(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("type") != "user" or d.get("isMeta") or "timestamp" not in d:
                continue
            when = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).astimezone(MYT)
            content = d.get("message", {}).get("content")

            if isinstance(content, list) and any(
                    isinstance(x, dict) and x.get("type") == "tool_result" for x in content):
                # The only tool results kept are answers typed or picked in
                # reply to Claude's multiple choice questions.
                for x in content:
                    if isinstance(x, dict) and x.get("type") == "tool_result":
                        t = text_of(x.get("content"))
                        m = re.search(r"(?:Your questions have been answered|The user answered):\s*(.*?)"
                                      r"(?:\.\s*(?:You can now continue|Read the answers carefully)|$)",
                                      t, re.S)
                        if m:
                            out.append((when, "answer", m.group(1).strip()))
                continue

            t = re.sub(r"<system-reminder>.*?</system-reminder>", "", text_of(content), flags=re.S).strip()
            if not t or t.startswith(SKIP) or "<command-name>" in t:
                continue
            out.append((when, "prompt", t))
    return out


def shorten(t):
    if len(t) <= LONG:
        return t
    left_out = len(t) - KEEP_HEAD - KEEP_TAIL
    return (t[:KEEP_HEAD]
            + f"\n\n[... {left_out:,} characters of pasted course material left out here. "
              f"The full prompt was {len(t):,} characters long ...]\n\n"
            + t[-KEEP_TAIL:])


def main():
    out_pdf = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "AI_Prompt_Records_Claude.pdf")
    today = datetime.now(MYT).strftime("%-d %B %Y")
    story = [
        Paragraph("<b>AI Prompt Records: Claude (Anthropic)</b>", S["h1"]),
        Paragraph("<b>Unit:</b> FIT3143 Parallel Computing, Semester 2 2026<br/>"
                  "<b>Assessment:</b> Lab 2, Message Passing Interface (Week 8)<br/>"
                  "<b>Team:</b> Erwyna Soo Wen Xin (36555789, esoo0013@student.monash.edu) and "
                  "Taabish Farooq Bhat (35473932, ttaa0006@student.monash.edu)", S["p"]),
        Paragraph(escape(
            f"This file holds every prompt Erwyna typed into Claude for Lab 2, exported from the "
            f"Claude Code session logs on {today}. The prompts are in the order they were sent, with "
            "the time in Malaysia time (UTC+8), and are copied exactly as typed, including typing and "
            "voice typing mistakes. Where a prompt contained a very long block of pasted course "
            "material, the middle of the pasted block is left out and marked. Answers picked in reply "
            "to Claude's multiple choice questions are included. Automatic system notifications and "
            "\"request interrupted\" markers are not, and neither are Claude's replies. Taabish's "
            "Gemini chats are in AI_Prompt_Records_Gemini.pdf."), S["p"]),
    ]
    count = 0
    for fname, title in SESSIONS:
        path = os.path.join(LOG_DIR, fname)
        if not os.path.exists(path):
            print("missing log:", path)
            continue
        story.append(Paragraph(f"<b>{escape(title)}</b>", S["h2"]))
        for when, kind, t in records(path):
            count += 1
            stamp = when.strftime("%A %-d %B %Y, %-I:%M %p")
            if kind == "answer":
                pairs = re.findall(r'"(.*?)"="(.*?)"', t, re.S)
                text = "\n\n".join(f"Question: {q}\nAnswer: {a}" for q, a in pairs) or t
                label = f"{count}. Answer to Claude's questions"
            else:
                text = shorten(t)
                label = f"{count}. Prompt"
            story.append(Paragraph(f"<b>{escape(label)}</b>, {escape(stamp)}", S["meta"]))
            story.append(record_block(text))
    make_pdf(out_pdf, story, "AI Prompt Records: Claude")
    print(count, "records")


if __name__ == "__main__":
    main()
