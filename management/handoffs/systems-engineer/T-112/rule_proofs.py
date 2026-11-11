"""T-110, adapted T-112 (good set = current documents): prove that the four F4-001..F4-003 documentation rules of interface_check can PASS and can FAIL.
Builds corrected scratch copies of the three documents (good set: all four rules PASS), then single mutations of the good set
(each must turn its rule to FAIL), and runs the rules on the documents at git HEAD (the texts the T-108 review read).
Usage: python3 rule_proofs.py <scratch_dir>"""
import os, re, subprocess, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SCR = sys.argv[1]; os.makedirs(SCR, exist_ok=True)
PY = sys.executable
rd = lambda *p: open(os.path.join(ROOT, *p), encoding="utf-8").read()
HW, MAN, RR = rd("hardware", "README.md"), rd("docs", "manual", "MANUAL.md"), rd("README.md")
BOARD, BOM = os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb"), os.path.join(ROOT, "hardware", "fabrication", "bom-kicad.csv")
RULES = ["doc.usb_epoxy_not_on_end_face", "doc.usb_epoxy_side_beads", "doc.hw_readme.continuity_37_38", "doc.jp1_before_module"]
def write(n, t):
    p = os.path.join(SCR, n); open(p, "w", encoding="utf-8").write(t); return p
def run(hw, man, rr):
    out = subprocess.run([PY, os.path.join(ROOT, "sim/systems/interface_check.py"), BOARD, write("hw.md", hw), write("man.md", man), BOM, write("rr.md", rr)],
                         capture_output=True, text=True, cwd=ROOT).stdout
    res = {}
    for l in out.splitlines():
        if l.startswith(("PASS  ", "FAIL  ")):
            n = l[6:].split(" :: ")[0]
            if n in RULES: res[n] = l[:4]
    return res
def sub(t, a, b, regex=False):
    if regex:
        t2, n = re.subn(a, b, t, count=1, flags=re.M)
    else:
        n = t.count(a); t2 = t.replace(a, b, 1)
    if not n: raise SystemExit("text not found: %r" % a[:80])
    return t2
# ---- good set (T-112): the documents as fixed by T-109 / T-111, unchanged -------------------------------------
G_HW, G_MAN, G_RR = HW, MAN, RR
ok = bad = 0
def expect(desc, res, want):
    global ok, bad
    good = all(res.get(k) == v for k, v in want.items())
    ok += good; bad += not good
    print("%s  %s -> %s" % ("PROOF-OK " if good else "PROOF-BAD", desc, {k: res.get(k) for k in want}))
expect("good set: all four rules PASS", run(G_HW, G_MAN, G_RR), {k: "PASS" for k in RULES})
M = [
 ("doc.usb_epoxy_not_on_end_face", "root README back to 'USB end gets a bead'", lambda h, m, r: (h, m, r + "\n- The **USB end** of the Pico gets a small bead of 2-part epoxy; use a strain-relieved USB cable.\n")),
 ("doc.usb_epoxy_not_on_end_face", "hardware README step 6 'along the end of the Pico at the USB connector'", lambda h, m, r: (h + "\nApply a small bead of 2-part epoxy along the end of the Pico at the USB connector.\n", m, r)),
 ("doc.usb_epoxy_not_on_end_face", "manual table row 'Epoxy bead at the USB end'", lambda h, m, r: (h, m + "\n| Epoxy bead at the USB end | — |\n", r)),
 ("doc.usb_epoxy_side_beads", "manual loses every 38–40 bead", lambda h, m, r: (h, re.sub(r"38\s*[–-]\s*40", "38", m), r)),   # every mention, since the manual states it more than once
 ("doc.usb_epoxy_side_beads", "hardware README loses the re-check after curing", lambda h, m, r: (re.sub(r"After the epoxy has cured[^.]*\.", "", h), m, r)),
 ("doc.hw_readme.continuity_37_38", "37–38 checklist line removed", lambda h, m, r: (re.sub(r"^- \[ \] Pico pad \*\*37\*\*[^\n]*\n?", "", h, flags=re.M), m, r)),
 ("doc.hw_readme.continuity_37_38", "old 'pads 39 and 40 ... lie 0.94 mm' text back", lambda h, m, r: (h + "\nPads 39 and 40 have no track on this board but lie 0.94 mm from the GND pad 38.\n", m, r)),
 ("doc.jp1_before_module", "hardware README module step before JP1", lambda h, m, r: (re.sub(r"^(\d+)\. \*\*JP1\*\*", "99. **JP1**", h, count=1, flags=re.M), m, r)),
 ("doc.jp1_before_module", "manual order puts the module before JP1", lambda h, m, r: (h, sub(m, "bridge **JP1 before the module goes on**, solder the module", "solder the module, bridge **JP1**"), r)),
 ("doc.jp1_before_module", "'ORIG is hidden' statement removed", lambda h, m, r: (re.sub(r"[^.\n]*ORIG[^.\n]*hidden[^.\n]*\.?", "", h), m, r)),
]
for name, desc, f in M:
    expect("[%s] %s" % (name, desc), run(*f(G_HW, G_MAN, G_RR)), {name: "FAIL"})
# ---- the texts the T-108 review read (git HEAD) ----------------------------------------------------------
gs = lambda p: subprocess.run(["git", "show", "HEAD:" + p], capture_output=True, text=True, cwd=ROOT).stdout
res = run(gs("hardware/README.md"), gs("docs/manual/MANUAL.md"), gs("README.md"))
print("HEAD documents (as reviewed in T-108):", res)
expect("HEAD documents: F4-001, F4-002 and F4-003 rules FAIL", res, {"doc.usb_epoxy_not_on_end_face": "FAIL", "doc.hw_readme.continuity_37_38": "FAIL", "doc.jp1_before_module": "FAIL"})
print("RULE PROOF SUMMARY: %d proved, %d not proved" % (ok, bad))
sys.exit(0 if bad == 0 else 1)
