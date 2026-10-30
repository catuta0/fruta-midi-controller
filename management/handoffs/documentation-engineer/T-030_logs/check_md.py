import re, sys, os, subprocess, collections
root = "/Users/rod/fruta-midi-controller"
def slug(h):
    s = h.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s, flags=re.UNICODE)
    return s.replace(" ", "-")
def headings(text):
    out = collections.Counter(); res = set()
    incode = False
    for line in text.splitlines():
        if line.startswith("```"): incode = not incode
        if incode: continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            s = slug(m.group(2)); n = out[s]; out[s] += 1
            res.add(s if n == 0 else f"{s}-{n}")
    return res
def nums(text):
    t = re.sub(r"(\d),(\d)", r"\1.\2", text)
    return collections.Counter(re.findall(r"\d+(?:\.\d+)?", t))
fails = 0
for rel in ["README.md", "hardware/README.md"]:
    path = os.path.join(root, rel); base = os.path.dirname(path)
    new = open(path, encoding="utf-8").read()
    old = subprocess.run(["git", "-C", root, "show", f"e4668d4:{rel}"], capture_output=True, text=True).stdout
    hs = headings(new)
    for target in re.findall(r"\]\(([^)\s]+)\)", new):
        if target.startswith("http"): continue
        file, _, anchor = target.partition("#")
        fpath = os.path.normpath(os.path.join(base, file)) if file else path
        if not os.path.exists(fpath):
            print(f"FAIL {rel}: missing target {target}"); fails += 1; continue
        if anchor:
            ths = hs if not file else headings(open(fpath, encoding="utf-8").read())
            if anchor not in ths:
                print(f"FAIL {rel}: anchor not found {target}"); fails += 1
    no, nn = nums(old), nums(new)
    if no != nn:
        print(f"FAIL {rel}: number multiset differs; removed={dict(no-nn)} added={dict(nn-no)}"); fails += 1
    ou = set(re.findall(r"https?://[^\s)>]+", old)); nu = set(re.findall(r"https?://[^\s)>]+", new))
    if ou != nu: print(f"FAIL {rel}: URLs differ {ou ^ nu}"); fails += 1
    strip=lambda t: re.sub(r"```.*?```", "", t, flags=re.S); oc = re.findall(r"`[^`\n]+`", strip(old)); nc = re.findall(r"`[^`\n]+`", strip(new))
    if collections.Counter(oc) != collections.Counter(nc): print(f"FAIL {rel}: code spans differ {set(oc) ^ set(nc)}"); fails += 1
    oi = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", old); ni = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", new)
    if oi != ni: print(f"FAIL {rel}: images differ"); fails += 1
    ot = sum(1 for l in old.splitlines() if l.lstrip().startswith("|")); nt = sum(1 for l in new.splitlines() if l.lstrip().startswith("|"))
    oh = len(re.findall(r"^#{1,6} ", old, re.M)); nh = len(re.findall(r"^#{1,6} ", new, re.M))
    print(f"{rel}: table lines old={ot} new={nt}; headings old={oh} new={nh}; images={len(ni)}; local links checked")
print("RESULT:", "PASS" if fails == 0 else f"FAIL ({fails})")
