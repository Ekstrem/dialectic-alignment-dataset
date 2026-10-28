#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score the in-context usefulness test.

Reads a ratings CSV with columns:
    scenario_id,dimension,condition,judge,score,notes

Prints, per rubric dimension, the mean score under baseline and primed, the delta
and n, plus a verdict table matching README.md.

Usage:  python3 experiments/incontext/score.py experiments/incontext/ratings.csv
"""
import csv
import sys
from collections import defaultdict

CONDITIONS = ("baseline", "primed")


def verdict(delta):
    if delta >= 1.0:
        return "carries the procedure"
    if delta >= 0.3:
        return "weak effect"
    if delta > -0.3:
        return "no effect: praise was politeness"
    return "hurts: the card leaks the answer"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    sums = defaultdict(lambda: defaultdict(list))
    with open(argv[1], encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            cond = row["condition"].strip()
            if cond not in CONDITIONS:
                print("skip: unknown condition %r" % cond)
                continue
            sums[row["dimension"]][cond].append(float(row["score"]))

    if not sums:
        print("no ratings found")
        return 1

    print("| dimension | baseline | primed | delta | n | verdict |")
    print("|:---|:---:|:---:|:---:|:---:|:---|")
    total = {c: [] for c in CONDITIONS}
    for dim in sorted(sums):
        by = sums[dim]
        b = by["baseline"]
        p = by["primed"]
        mb = sum(b) / len(b) if b else float("nan")
        mp = sum(p) / len(p) if p else float("nan")
        delta = mp - mb if b and p else float("nan")
        total["baseline"] += b
        total["primed"] += p
        print("| %s | %.2f | %.2f | %+.2f | %d | %s |"
              % (dim, mb, mp, delta, min(len(b), len(p)), verdict(delta)))

    b, p = total["baseline"], total["primed"]
    if b and p:
        delta = sum(p) / len(p) - sum(b) / len(b)
        print("| **all** | %.2f | %.2f | %+.2f | %d | %s |"
              % (sum(b) / len(b), sum(p) / len(p), delta, len(b), verdict(delta)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
