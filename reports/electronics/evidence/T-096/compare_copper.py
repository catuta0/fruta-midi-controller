#!/usr/bin/env python3
"""T-096: confirm the copper artwork did not change with the part swap. Compares the working-tree F.Cu Gerber with the one at a git revision.
Aperture numbers are resolved to shapes, then the multiset of (aperture, operation, X, Y) is compared. Usage: compare_copper.py <rev>"""
import collections
import re
import subprocess
import sys

P = "hardware/fabrication/gerbers/frutamidi-F_Cu.gtl"


def ops(text):
    ap, cur, x, y, out = {}, None, None, None, collections.Counter()
    for line in text.splitlines():
        m = re.match(r"%ADD(\d+)(.*)\*%", line)
        if m:
            ap[m.group(1)] = m.group(2)
            continue
        m = re.match(r"D(\d+)\*$", line)
        if m and int(m.group(1)) >= 10:
            cur = ap[m.group(1)]
            continue
        m = re.match(r"(?:X(-?\d+))?(?:Y(-?\d+))?(?:I-?\d+J-?\d+)?D0([123])\*$", line)
        if m:
            x = m.group(1) or x
            y = m.group(2) or y
            out[(cur, m.group(3), x, y)] += 1
    return out


old = ops(subprocess.check_output(["git", "show", sys.argv[1] + ":" + P], text=True))
new = ops(open(P).read())
print("operations at %s: %d; working tree: %d" % (sys.argv[1], sum(old.values()), sum(new.values())))
print("only at revision: %d; only in working tree: %d" % (sum((old - new).values()), sum((new - old).values())))
print("PASS copper operations identical" if old == new else "FAIL copper operations differ")
