import re, os, sys
sys.path.insert(0, "/private/tmp/claude-501/-Users-rod-fruta-midi-controller/f323d487-2875-40b3-84cc-8ec2fbba0998/scratchpad")
def slug(h): return re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-")
def heads(t): return {slug(m) for m in re.findall(r"^#{1,6}\s+(.*)$", t, re.M)}
p = sys.argv[1]; base = os.path.dirname(p); t = open(p, encoding="utf-8").read(); fails = 0; n = 0
for tgt in re.findall(r"\]\(([^)\s]+)\)", t):
    if tgt.startswith("http"): continue
    n += 1; f, _, a = tgt.partition("#"); fp = os.path.normpath(os.path.join(base, f)) if f else p
    if not os.path.exists(fp): print("FAIL missing", tgt); fails += 1; continue
    if a and a not in heads(open(fp, encoding="utf-8").read()): print("FAIL anchor", tgt); fails += 1
print(f"{p}: {n} local links checked; RESULT:", "PASS" if not fails else f"FAIL ({fails})")
