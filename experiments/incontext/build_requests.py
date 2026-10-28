#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the in-context usefulness test requests.

For each scenario in evaluation/test_scenarios.jsonl emit two requests:
  baseline - the scenario alone
  primed   - the scenario plus one canon lesson card as an internal note

The note is offered, not imposed: it says "a note from previous work", it does not
say "apply this". That is deliberate. A lesson that changes behaviour only when the
model is told to apply it has not been learned, it has been obeyed.

Usage:  python3 experiments/incontext/build_requests.py
Writes: experiments/incontext/requests.jsonl
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
CANON = os.path.join(ROOT, "canon", "lessons.yaml")
SCENARIOS = os.path.join(ROOT, "evaluation", "test_scenarios.jsonl")
MAPPING = os.path.join(HERE, "mapping.json")
CARDS_EN = os.path.join(HERE, "cards_en.json")
OUT = os.path.join(HERE, "requests.jsonl")

SYSTEM = "You are a helpful assistant. Answer the user's message."

NOTE_ORDER = ["idea", "indicator", "scale", "checklist", "algorithm", "rule", "stop_phrase"]


def parse_canon():
    """Return {lesson_id: {field: text}} for the flat fields we need."""
    lessons, cur, field, buf = {}, None, None, []

    def flush():
        nonlocal field, buf
        if cur and field and buf:
            lessons.setdefault(cur, {})[field] = "\n".join(buf).strip()
        field, buf = None, []

    for raw in open(CANON, encoding="utf-8"):
        line = raw.rstrip("\n")
        m = re.match(r'\s{2}- id: "([^"]+)"', line)
        if m:
            flush()
            cur = m.group(1)
            continue
        m = re.match(r"\s{6}([a-z_0-9]+): \|-", line)
        if m:
            flush()
            field = m.group(1)
            continue
        if field is not None:
            if line.startswith("        "):
                buf.append(line[8:])
            elif line.strip():
                flush()
    flush()
    return lessons


def note_from(lesson, fields):
    parts = ["Internal note from previous work on a similar case (not a reply to the user):"]
    labels = {
        "idea": "Key idea",
        "indicator": "Indicator",
        "scale": "Scale",
        "checklist": "Checklist",
        "algorithm": "Algorithm",
        "rule": "Rule",
        "stop_phrase": "Stop-question",
    }
    used = 0
    for key in NOTE_ORDER:
        text = fields.get(key)
        if not text:
            continue
        if key in ("algorithm", "scale", "checklist"):
            text = "; ".join(s.strip() for s in text.splitlines() if s.strip())
        parts.append("%s: %s" % (labels[key], text))
        used += 1
    if used == 0:
        return None
    return "\n".join(parts)


def main():
    lessons = parse_canon()
    mapping = json.load(open(MAPPING, encoding="utf-8"))
    cards = json.load(open(CARDS_EN, encoding="utf-8"))
    scenarios = [json.loads(l) for l in open(SCENARIOS, encoding="utf-8") if l.strip()]
    requests, problems = [], []

    for sc in scenarios:
        sid = sc["id"]
        entry = mapping.get(sid)
        if not entry:
            problems.append("%s: no lesson mapped" % sid)
            entry = {}
        lesson = entry.get("lesson")
        fields = cards.get(lesson) or lessons.get(lesson, {})
        if lesson and not fields:
            problems.append("%s: lesson %r not found in canon" % (sid, lesson))
        note = note_from(lesson, fields) if lesson else None
        if lesson and note is None:
            problems.append("%s: lesson %r has no usable card fields" % (sid, lesson))

        requests.append({
            "id": "%s-baseline" % sid,
            "scenario": sid,
            "dimension": sc["dimension"],
            "lesson": lesson,
            "condition": "baseline",
            "system": SYSTEM,
            "user": sc["prompt"],
        })
        if note:
            requests.append({
                "id": "%s-primed" % sid,
                "scenario": sid,
                "dimension": sc["dimension"],
                "lesson": lesson,
                "condition": "primed",
                "system": SYSTEM,
                "user": sc["prompt"] + "\n\n" + note,
            })

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for r in requests:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("scenarios: %d | requests: %d -> %s" % (len(scenarios), len(requests), os.path.basename(OUT)))
    print("lessons used:", len({r["lesson"] for r in requests}))
    if problems:
        print("problems:")
        for p in problems:
            print("  -", p)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
