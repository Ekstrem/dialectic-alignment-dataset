#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build and validate DAD v2 preference pairs.

Inputs:
  canon/lessons.yaml            - lesson ids, skills, module and record aliases
  dataset/pairs/batch-*.jsonl   - authored pairs (schema: dataset/pairs/README.md)
  dataset/dialectic_alignment.jsonl - legacy v1 records (source=dialogue)

Output:
  dataset/dialectic_alignment_v2.jsonl  - legacy pairs + authored pairs, normalised

Validation is intentionally strict: a pair that names an unknown lesson, uses a
skill the lesson does not own, or pairs a rejected_type with a mismatched skill
is a build error, not a warning.

Usage:  python3 scripts/build_pairs.py
"""
import glob
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = os.path.join(ROOT, "canon", "lessons.yaml")
PAIRS = os.path.join(ROOT, "dataset", "pairs")
LEGACY = os.path.join(ROOT, "dataset", "dialectic_alignment.jsonl")
OUT = os.path.join(ROOT, "dataset", "dialectic_alignment_v2.jsonl")

LANGS = {"ru", "en"}
SOURCES = {"authored", "dialogue", "legacy", "translated"}
REVIEW = {"pending", "accepted", "rework"}

# Which error types may legitimately be paired with which skill.
ALLOWED = {
    "distinction": {"binary_frame", "literal_reading", "canon_check", "knowledge_imitation"},
    "hold_contradiction": {"vulgar_synthesis", "binary_frame", "domestication", "knowledge_imitation"},
    "mark_boundary": {"knowledge_imitation", "false_continuity"},
    "contextual_reading": {"literal_reading", "canon_check", "domestication", "knowledge_imitation"},
    "depathologize": {"premature_psychologization", "sycophancy"},
    "artifact": {"artifact_missing", "sycophancy", "false_continuity"},
}
ALL_TYPES = set().union(*ALLOWED.values()) | {"legacy"}

MIN = {"prompt": 60, "chosen": 300, "rejected": 150}
RECOMMENDED = {"chosen": (350, 1200), "rejected": (170, 800)}


def parse_canon():
    """Return {lesson_id: {'skills': [...], 'layer': str, 'records': [...]}}."""
    lessons, cur = {}, None
    with open(CANON, encoding="utf-8") as f:
        for line in f:
            m = re.match(r'\s{2}- id: "([^"]+)"', line)
            if m:
                cur = m.group(1)
                lessons[cur] = {"skills": [], "layer": "corpus", "records": []}
                continue
            if cur is None:
                continue
            m = re.match(r"\s+skills: \[(.*)\]\s*$", line)
            if m:
                lessons[cur]["skills"] = [s.strip() for s in m.group(1).split(",") if s.strip()]
                continue
            m = re.match(r"\s+layer: (\w+)", line)
            if m:
                lessons[cur]["layer"] = m.group(1)
                continue
            m = re.match(r'\s+records: \[(.*)\]\s*$', line)
            if m:
                lessons[cur]["records"] = re.findall(r'"([^"]+)"', m.group(1))
    return lessons


def check_pair(pair, lessons, errors, where):
    pid = pair.get("id", where)
    for field in ("id", "lesson", "skill", "lang", "prompt", "chosen", "rejected",
                  "rejected_type", "source", "review"):
        if field not in pair:
            errors.append("%s: missing field '%s'" % (pid, field))
    if errors and any(e.startswith(pid + ":") for e in errors):
        return
    lesson = lessons.get(pair["lesson"])
    if lesson is None:
        errors.append("%s: unknown lesson %r" % (pid, pair["lesson"]))
        return
    if pair["skill"] not in lesson["skills"]:
        errors.append("%s: skill %r not declared for lesson %r (has %s)"
                      % (pid, pair["skill"], pair["lesson"], lesson["skills"]))
        return
    if pair["lang"] not in LANGS:
        errors.append("%s: lang must be one of %s" % (pid, sorted(LANGS)))
    if pair["source"] not in SOURCES:
        errors.append("%s: source must be one of %s" % (pid, sorted(SOURCES)))
    if pair["review"] not in REVIEW:
        errors.append("%s: review must be one of %s" % (pid, sorted(REVIEW)))
    if pair["rejected_type"] not in ALL_TYPES:
        errors.append("%s: unknown rejected_type %r" % (pid, pair["rejected_type"]))
    elif pair["rejected_type"] != "legacy" and pair["rejected_type"] not in ALLOWED[pair["skill"]]:
        errors.append("%s: rejected_type %r does not fit skill %r (allowed: %s)"
                      % (pid, pair["rejected_type"], pair["skill"], sorted(ALLOWED[pair["skill"]])))
    if pair["chosen"].strip() == pair["rejected"].strip():
        errors.append("%s: chosen == rejected" % pid)
    for field, minimum in MIN.items():
        if len(pair.get(field, "")) < minimum:
            errors.append("%s: %s shorter than %d chars" % (pid, field, minimum))


def load_authored(lessons, errors):
    pairs, seen = [], set()
    for path in sorted(glob.glob(os.path.join(PAIRS, "batch-*.jsonl"))):
        where = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                if not line.strip():
                    continue
                loc = "%s:%d" % (where, lineno)
                try:
                    pair = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append("%s: invalid JSON: %s" % (loc, exc))
                    continue
                if pair.get("id") in seen:
                    errors.append("%s: duplicate pair id %r" % (loc, pair.get("id")))
                    continue
                seen.add(pair.get("id"))
                check_pair(pair, lessons, errors, loc)
                pairs.append(pair)
    return pairs


def load_legacy(lessons, errors):
    by_record = {}
    for lid, meta in lessons.items():
        for rec in meta["records"]:
            by_record[rec] = (lid, meta["skills"])
    pairs = []
    if not os.path.exists(LEGACY):
        return pairs
    with open(LEGACY, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            lid, skills = by_record.get(rec["id"], (None, []))
            if lid is None:
                errors.append("legacy %s: not mapped to any canon lesson" % rec["id"])
                continue
            pairs.append({
                "id": "legacy-%s" % rec["id"],
                "lesson": lid,
                "skill": skills[0],
                "lang": "ru",
                "prompt": rec["prompt"],
                "chosen": rec["chosen"],
                "rejected": rec["rejected"],
                "rejected_type": "legacy",
                "source": "dialogue",
                "review": "accepted",
            })
    return pairs


def main():
    lessons = parse_canon()
    errors = []
    legacy = load_legacy(lessons, errors)
    authored = load_authored(lessons, errors)
    all_pairs = legacy + authored

    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for pair in all_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    by_skill = Counter(p["skill"] for p in all_pairs)
    by_type = Counter(p["rejected_type"] for p in all_pairs)
    by_review = Counter(p["review"] for p in all_pairs)
    by_lesson = Counter(p["lesson"] for p in all_pairs)
    thin = [lid for lid in lessons if lessons[lid]["layer"] == "corpus" and by_lesson[lid] < 2]

    by_source = Counter(p["source"] for p in all_pairs)
    by_lang = Counter(p["lang"] for p in all_pairs)
    print("pairs: %d by source %s -> %s"
          % (len(all_pairs), dict(sorted(by_source.items())), os.path.basename(OUT)))
    print("by lang:", dict(sorted(by_lang.items())))
    print("by skill:", dict(sorted(by_skill.items(), key=lambda kv: -kv[1])))
    print("by rejected_type:", dict(sorted(by_type.items(), key=lambda kv: -kv[1])))
    print("by review:", dict(by_review))
    print("lessons covered: %d/%d" % (len(by_lesson), len(lessons)))
    if thin:
        print("lessons with <2 pairs (%d): %s" % (len(thin), ", ".join(thin)))
    for pair in all_pairs:
        for field in ("chosen", "rejected"):
            lo, hi = RECOMMENDED[field]
            if not lo <= len(pair[field]) <= hi:
                print("  note: %s %s len %d outside %d-%d" % (pair["id"], field, len(pair[field]), lo, hi))
    if errors:
        print("\nFAIL with %d errors:" % len(errors))
        for err in errors:
            print("  - " + err)
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
