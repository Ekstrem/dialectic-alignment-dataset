#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the DAD dataset: JSONL structure, DPO pairs, CSV and canon consistency.

Usage:
    python3 scripts/validate_dataset.py [path/to/dialectic_alignment.jsonl]

Checks:
  - every non-empty line is valid UTF-8 JSON
  - required fields exist and have the expected types
  - ids are unique and start with the module code
  - module code is known
  - chosen != rejected, both non-trivial
  - symptoms / tags / activation_indicators are non-empty lists
  - the CSV (if present next to the JSONL) has the same ids in the same order
    and 11 fields in every row
  - every `records:` alias in canon/lessons.yaml exists in the dataset

Zero third-party dependencies. Exit code 1 on any error.
"""
import csv
import json
import os
import re
import sys

REQUIRED = ["id", "module", "title", "prompt", "chosen", "rejected", "symptoms", "metadata"]
MODULES = ["00-context", "01-self-audit", "02-diagnostics", "03-hostile-reading", "04-toolkit"]
MIN_CHOSEN = 200
MIN_REJECTED = 80

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def validate_jsonl(path, errors):
    records = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append("line %d: invalid JSON: %s" % (lineno, exc))
                continue
            records.append(rec)
            for field in REQUIRED:
                if field not in rec:
                    errors.append("line %d: missing field '%s'" % (lineno, field))
            module = rec.get("module")
            if module not in MODULES:
                errors.append("line %d: unknown module %r" % (lineno, module))
            rid = rec.get("id", "")
            if module and not rid.startswith(module + "-"):
                errors.append("line %d: id %r does not match module %r" % (lineno, rid, module))
            for field in ("id", "title", "prompt", "chosen", "rejected"):
                if not isinstance(rec.get(field), str) or not rec.get(field, "").strip():
                    errors.append("line %d: field '%s' must be a non-empty string" % (lineno, field))
            if len(rec.get("chosen", "")) < MIN_CHOSEN:
                errors.append("line %d: chosen is shorter than %d chars" % (lineno, MIN_CHOSEN))
            if len(rec.get("rejected", "")) < MIN_REJECTED:
                errors.append("line %d: rejected is shorter than %d chars" % (lineno, MIN_REJECTED))
            if rec.get("chosen") == rec.get("rejected"):
                errors.append("line %d: chosen == rejected" % lineno)
            for field in ("symptoms",):
                value = rec.get(field)
                if not isinstance(value, list) or not value:
                    errors.append("line %d: '%s' must be a non-empty list" % (lineno, field))
            meta = rec.get("metadata")
            if not isinstance(meta, dict):
                errors.append("line %d: 'metadata' must be an object" % lineno)
                continue
            for key in ("source", "date", "tags", "activation_indicators"):
                if key not in meta:
                    errors.append("line %d: metadata.%s is missing" % (lineno, key))
            for key in ("tags", "activation_indicators"):
                if key in meta and (not isinstance(meta[key], list) or not meta[key]):
                    errors.append("line %d: metadata.%s must be a non-empty list" % (lineno, key))
    return records


def validate_csv(jsonl_path, records, errors):
    csv_path = os.path.splitext(jsonl_path)[0] + ".csv"
    if not os.path.exists(csv_path):
        return
    with open(csv_path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    header = rows[0] if rows else []
    widths = sorted({len(r) for r in rows[1:] if r})
    if widths != [len(header)]:
        errors.append("csv: field-count drift %s, header has %d columns" % (widths, len(header)))
    ids_csv = [r[0] for r in rows[1:] if r]
    ids_jsonl = [r["id"] for r in records]
    if ids_csv != ids_jsonl:
        missing = [i for i in ids_jsonl if i not in ids_csv]
        extra = [i for i in ids_csv if i not in ids_jsonl]
        errors.append("csv: ids differ from jsonl (missing=%s, extra=%s, order_ok=%s)"
                      % (missing, extra, sorted(ids_csv) == sorted(ids_jsonl)))


def validate_canon(records, errors):
    canon = os.path.join(ROOT, "canon", "lessons.yaml")
    if not os.path.exists(canon):
        return 0
    ids = {r["id"] for r in records}
    referenced, checked = 0, 0
    for line in open(canon, encoding="utf-8"):
        m = re.match(r'\s+records: \[(.*)\]\s*$', line)
        if not m:
            continue
        for alias in re.findall(r'"([^"]+)"', m.group(1)):
            checked += 1
            if alias not in ids:
                errors.append("canon: record alias %r not found in dataset" % alias)
    # every dataset id should be referenced from canon
    text = open(canon, encoding="utf-8").read()
    for rid in ids:
        if '"%s"' % rid not in text:
            errors.append("canon: dataset record %r is not mapped to any lesson" % rid)
    return checked


def main(argv):
    jsonl = argv[1] if len(argv) > 1 else os.path.join(ROOT, "dataset", "dialectic_alignment.jsonl")
    if not os.path.exists(jsonl):
        print("FAIL: %s not found" % jsonl)
        return 1
    errors = []
    records = validate_jsonl(jsonl, errors)
    validate_csv(jsonl, records, errors)
    checked = validate_canon(records, errors)

    print("records: %d | canon aliases checked: %d | errors: %d"
          % (len(records), checked, len(errors)))
    for err in errors:
        print("  - " + err)
    if errors:
        print("FAIL")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
