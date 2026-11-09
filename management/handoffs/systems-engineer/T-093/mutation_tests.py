#!/usr/bin/env python3
"""T-093: prove each new or changed design-file check can fail. Each mutation edits a scratch copy of the board, drill file,
README, manual or BOM, runs the check, and requires the named check line to read FAIL while the unmodified input reads PASS.
Nothing under hardware/ is modified. Usage: python3 mutation_tests.py <scratch_dir> > mutation_results.txt"""
import os, re, shutil, subprocess, sys
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
SCR = sys.argv[1]; os.makedirs(SCR, exist_ok=True)
BOARD = open(os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb"), encoding="utf-8").read()
DRL = open(os.path.join(ROOT, "hardware", "fabrication", "gerbers", "frutamidi.drl"), encoding="utf-8", errors="replace").read()
HWR = open(os.path.join(ROOT, "hardware", "README.md"), encoding="utf-8").read()
MAN = open(os.path.join(ROOT, "docs", "manual", "MANUAL.md"), encoding="utf-8").read()
BOM = open(os.path.join(ROOT, "hardware", "fabrication", "bom-kicad.csv"), encoding="utf-8").read()
PY = sys.executable

def fp_block(ref):
    i = BOARD.index('(property "Reference" "%s"' % ref)
    s = BOARD.rfind("\n\t(footprint ", 0, i)
    e = BOARD.index("\n\t)\n", i) + 3
    return s, e
def in_fp(t, ref, a, b):
    s, e = fp_block(ref); blk = t[s:e]
    if a not in blk: raise SystemExit("mutation text not found in %s: %s" % (ref, a))
    return t[:s] + blk.replace(a, b, 1) + t[e:]
def sub1(t, a, b):
    if a not in t: raise SystemExit("mutation text not found: %s" % a)
    return t.replace(a, b, 1)
def seg_nth(t, net, w):
    return re.sub(r'(\(segment\s+\(start [^)]*\)\s+\(end [^)]*\)\s+\(width )[\d.]+(\)\s+\(layer "[^"]+"\)\s+\(net "%s"\))' % re.escape(net), lambda m: m.group(1) + str(w) + m.group(2), t)
def remove_first(t, pat):
    m = re.search(pat, t, re.S)
    if not m: raise SystemExit("not found: " + pat)
    return t[:m.start()] + t[m.end():]
def add_top(t, text):
    i = t.rindex("\n)")
    return t[:i] + text + t[i:]
def hole_centre(ref):
    s, e = fp_block(ref); m = re.search(r'\(layer "[^"]+"\)\s*\(uuid "[^"]+"\)\s*\(at ([-\d.]+) ([-\d.]+)', BOARD[s:e])
    return float(m.group(1)), float(m.group(2))
def ko_centre():
    z = BOARD[BOARD.index("(zone"):]
    pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', z)[:4]]
    return sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4
def seg(x1, y1, x2, y2, w, net="GND", lay="F.Cu"):
    return '\n\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "00000000-0000-0000-0000-000000000000")\n\t)' % (x1, y1, x2, y2, w, lay, net)
VIA = '\n\t(via\n\t\t(at 100 100)\n\t\t(size 1.6)\n\t\t(drill 0.8)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "GND")\n\t\t(uuid "00000000-0000-0000-0000-000000000001")\n\t)'
ZONE = '\n\t(zone\n\t\t(net "GND")\n\t\t(layer "F.Cu")\n\t\t(uuid "00000000-0000-0000-0000-000000000002")\n\t\t(polygon\n\t\t\t(pts\n\t\t\t\t(xy 50 50) (xy 60 50) (xy 60 60)\n\t\t\t)\n\t\t)\n\t)'
hx, hy = hole_centre("H1")
kx, ky = ko_centre()
PCB_MUT = [
    ("REQ-027 tracks only on F.Cu", "one segment on B.Cu", lambda t: re.sub(r'(\(segment\s+\(start [^)]*\)\s+\(end [^)]*\)\s+\(width [\d.]+\)\s+\(layer ")F\.Cu', r'\1B.Cu', t, count=1)),
    ("REQ-027 no copper object on B.Cu", "SW1 pad on B.Cu", lambda t: in_fp(t, "SW1", '(layers "F.Cu" "F.Mask" "F.Paste")', '(layers "B.Cu" "B.Mask" "B.Paste")')),
    ("REQ-027 no vias", "via added", lambda t: add_top(t, VIA)),
    ("REQ-027 no copper pour (only rule areas)", "copper zone added", lambda t: add_top(t, ZONE)),
    ("REQ-027 every copper pad is surface-mount on F.Cu with no drill", "J2 pad 2 through-hole", lambda t: in_fp(t, "J2", '(pad "2" smd oval\n\t\t\t(at 5.08 0)\n\t\t\t(size 3 4.5)', '(pad "2" thru_hole oval\n\t\t\t(at 5.08 0)\n\t\t\t(size 3 4.5)\n\t\t\t(drill 1.4)')),
    ("REQ-027 every part on the copper side", "A2 placed on B.Cu", lambda t: t[:fp_block("A2")[0]] + re.sub(r'\(layer "F\.Cu"\)', '(layer "B.Cu")', t[fp_block("A2")[0]:fp_block("A2")[1]], count=1) + t[fp_block("A2")[1]:]),
    ("REQ-027 exactly 4 holes, all M3 NPTH on H1..H4", "H4 removed (3 holes)", lambda t: t[:fp_block("H4")[0]] + t[fp_block("H4")[1]:]),
    ("REQ-027 exactly 4 holes, all M3 NPTH on H1..H4", "H1 drill 2.5 mm", lambda t: in_fp(t, "H1", "(drill 3.2)", "(drill 2.5)")),
    ("REQ-027 every multi-pad net is one F.Cu island (no extra wire bridge needed)", "one /BTN segment removed", lambda t: remove_first(t, r'\s*\(segment\s+\(start [^)]*\)\s+\(end [^)]*\)\s+\(width [\d.]+\)\s+\(layer "F\.Cu"\)\s+\(net "/BTN"\)\s+\(uuid "[^"]+"\)\s*\)')),
    ("REQ-027 wire links limited to the 2 I2C configuration links (J1 SCL/SDA to J3 S1..S7)", "J1 pad 2 net changed to SCL", lambda t: in_fp(t, "J1", '(net "/SDA")', '(net "/SCL")')),
    ("REQ-029 track width >= 0.8 mm everywhere", "all GND tracks 0.7 mm", lambda t: seg_nth(t, "GND", 0.7)),
    ("REQ-029 power tracks >= 1.2 mm", "all +3V3 tracks 1.0 mm", lambda t: seg_nth(t, "+3V3", 1.0)),
    ("REQ-029 signal tracks >= 1.0 mm except stubs <= 6.0 mm", "all /SDA tracks 0.8 mm", lambda t: seg_nth(t, "/SDA", 0.8)),
    ("REQ-029 copper clearance >= 0.6 mm between different nets (pads and tracks)", "all /SDA tracks 2.0 mm", lambda t: seg_nth(t, "/SDA", 2.0)),
    ("REQ-029 copper >= 0.5 mm from the board edge (min_copper_edge_clearance, hardware/frutamidi.kicad_pro)", "track 0.3 mm from the edge", lambda t: add_top(t, seg(60, 119.8, 65, 119.8, 0.8))),
    ("REQ-029 remaining holes: drill >= 0.8 mm, copper >= 0.5 mm from the hole edge (min_hole_clearance, frutamidi.kicad_pro)", "track next to H1", lambda t: add_top(t, seg(hx + 2.0, hy, hx + 4.0, hy, 0.8))),
    ("REQ-029 every SMD land >= 1.0 mm in both directions", "SW1 land 0.9 mm", lambda t: t.replace("(size 1.55 1.3)", "(size 1.55 0.9)")),
    ("REQ-029 land sizes match the v1.3 table (A1, A2, J1, J3, RV1, SW1, C1, R1..R16)", "A2 lands 1.8 x 2.0 mm", lambda t: in_fp(t, "A2", "(size 1.8 2.4)", "(size 1.8 2)")),
    ("REQ-029 no bare copper in the 2 Pico keep-out rule areas", "track through a keep-out", lambda t: add_top(t, seg(kx, ky, kx + 0.5, ky, 0.8))),
    ("REQ-023 R1-R12 land gap >= 3.5 mm (4 kV rule) and = 5.0 mm (ADR-023)", "R5 pad 2 moved 1 mm inward", None),
    ("ADR-021/ADR-023 JP1 is a 3-pad SMD bridge, pads 1.94 x 2.4 mm, pitch 3.81 mm, gap >= 1.8 mm", "JP1 pad 2 through-hole", lambda t: in_fp(t, "JP1", '(pad "2" smd rect', '(pad "2" thru_hole rect')),
    ("ADR-021/ADR-023 JP1 is a 3-pad SMD bridge, pads 1.94 x 2.4 mm, pitch 3.81 mm, gap >= 1.8 mm", "JP1 pad 3 moved 0.5 mm", None),
    ("ADR-023 J2 is 14 SMD solder-wire pads 3.0 x 4.5 mm at 5.08 mm pitch", "J2 pad 3 narrower", lambda t: in_fp(t, "J2", '(at 10.16 0)\n\t\t\t(size 3 4.5)', '(at 10.16 0)\n\t\t\t(size 2.5 4.5)')),
    ("ADR-020 Ex <-> GND edge-track spark gap 1.40 +/- 0.05 mm", "J2 pad 2 moved 0.2 mm towards the edge", lambda t: in_fp(t, "J2", "(at 5.08 0)", "(at 5.08 0.2)")),
    ("ADR-020 Ex <-> GND edge-track spark gap 1.40 +/- 0.05 mm", "J2 pad 2 moved 0.2 mm away from the edge", lambda t: in_fp(t, "J2", "(at 5.08 0)", "(at 5.08 -0.2)")),
]
# Pad-position mutations need the current footprint text.
def move_pad(ref, num, dx, dy):
    def f(t):
        s, e = fp_block(ref); blk = t[s:e]
        m = re.search(r'\(pad "%s" smd \w+\s*\(at ([-\d.]+) ([-\d.]+)' % num, blk)
        new = blk[:m.start(1)] + "%g %g" % (float(m.group(1)) + dx, float(m.group(2)) + dy) + blk[m.end(2):]
        return t[:s] + new + t[e:]
    return f
def inward(ref, num, step):
    """Move the pad towards the footprint origin along the axis on which it is offset."""
    s_, e_ = fp_block(ref); m = re.search(r'\(pad "%s" smd \w+\s*\(at ([-\d.]+) ([-\d.]+)' % num, BOARD[s_:e_])
    x, y = float(m.group(1)), float(m.group(2))
    return move_pad(ref, num, -step if x > 0 else step if x < 0 else 0, -step if (x == 0 and y > 0) else step if (x == 0 and y < 0) else 0)
PCB_MUT = [(n, d, f if f else (inward("R5", "2", 1.0) if n.startswith("REQ-023") else inward("JP1", "3", 0.5))) for n, d, f in PCB_MUT]
DRL_NAME = "REQ-027 drill file has the same 4 holes as the board"

IF_MUT = [
    ("pcb.label_v1.3", "label v1.2", lambda t: t.replace("FrutaMIDI v1.3", "FrutaMIDI v1.2", 1)),
    ("pcb.R1_R12_footprint", "R5 footprint renamed", lambda t: t[:fp_block("R5")[0]] + BOARD[fp_block("R5")[0]:fp_block("R5")[1]].replace("FrutaMIDI:R_2512_HPWC_G5.0mm", "FrutaMIDI:R_2512_Other", 1) + t[fp_block("R5")[1]:]),
    ("pcb.R1_R12_MPN", "R7 MPN changed", lambda t: in_fp(t, "R7", "HPWC2512-3K0JT18", "PWC2512-3K0JT18")),
    ("pcb.R1_R12_value", "R9 value 3k3", lambda t: in_fp(t, "R9", '"Value" "3k0"', '"Value" "3k3"')),
    ("pcb.AGND_membership", "SW1 pad 2 on AGND", lambda t: in_fp(t, "SW1", '(net "GND")', '(net "/AGND")')),
    ("pcb.RV1_offboard_3_pads", "RV1 MP tab added", lambda t: in_fp(t, "RV1", '(pad "3" smd', '(pad "MP" smd rect\n\t\t\t(at 9 0)\n\t\t\t(size 2 2)\n\t\t\t(layers "F.Cu" "F.Mask")\n\t\t\t(net "/AGND")\n\t\t\t(uuid "00000000-0000-0000-0000-000000000003")\n\t\t)\n\t\t(pad "3" smd')),
    ("pcb.JP1_smd_bridge", "JP1 pad through-hole", lambda t: in_fp(t, "JP1", '(pad "1" smd', '(pad "1" thru_hole')),
    ("pcb.J1_J3_smd", "J3 pad through-hole", lambda t: in_fp(t, "J3", '(pad "1" smd', '(pad "1" thru_hole')),
    ("pcb.J2_solder_pads", "J2 pad through-hole", lambda t: in_fp(t, "J2", '(pad "5" smd', '(pad "5" thru_hole')),
    ("pcb.JP1_legend", "ORIG not etched", lambda t: re.sub(r'(\(gr_text "ORIG"\s*\(at [^)]*\)\s*\(layer ")F\.Cu', r'\1F.Fab', t, count=1)),
    ("pcb.part.A1", "A1 footprint renamed", lambda t: t.replace("FrutaMIDI:RaspberryPi_Pico_Castellated_HomeEtch", "FrutaMIDI:RaspberryPi_Pico_THT", 1)),
    ("pcb.part.A2", "A2 MPN changed", lambda t: in_fp(t, "A2", '"MPN" "1982"', '"MPN" "1983"')),
    ("pcb.part.C1", "C1 MPN changed", lambda t: in_fp(t, "C1", "C1206C104K5RACTU", "C322C104K5R5TA")),
    ("pcb.part.SW1", "SW1 MPN changed", lambda t: in_fp(t, "SW1", '"MPN" "B3S-1000"', '"MPN" "B3F-1000"')),
    ("pcb.part.R15", "R15 MPN changed", lambda t: in_fp(t, "R15", "220R 1 % thick film, 1206", "220R 1 % thick film, 0805")),
    ("pcb.part.JP1", "JP1 footprint THT", lambda t: t.replace("FrutaMIDI:SolderJumper_3_SMD_P3.81mm", "FrutaMIDI:SolderJumper_3_THT_P3.81mm", 1)),
    ("pcb.part.J2", "J2 footprint terminal block", lambda t: t.replace("FrutaMIDI:WirePads_1x14_P5.08mm", "FrutaMIDI:TerminalBlock_5.08_1x14", 1)),
    ("pcb.part.H1_H4", "H4 footprint renamed", lambda t: in_fp(t, "H4", "FrutaMIDI:MountingHole_3.2mm_M3", "FrutaMIDI:MountingHole_2.2mm_M2")),
    ("pcb.no_extra_parts", "reference R16 renamed X9", lambda t: in_fp(t, "R16", '"Reference" "R16"', '"Reference" "X9"')),
]
DOC_MUT = [
    ("doc.hw_readme.version", "title v1.2", lambda t: t.replace("(version 1.3)", "(version 1.2)")),
    ("doc.hw_readme.R1_R12_part", "HPWC part removed", lambda t: t.replace("HPWC2512-3K0JT18", "HPWC2512")),
    ("doc.hw_readme.only_4_holes", "drill statement removed", lambda t: t.replace("Only the 4 M3 mounting holes", "The mounting holes")),
    ("doc.hw_readme.no_sockets", "socket instruction added", lambda t: t.replace("## 3. Drill", "Use a socket for the Pico.\n\n## 3. Drill")),
    ("doc.hw_readme.continuity_through_series_R", "line removed", lambda t: t.replace("Resistance between each electrode pad of J2", "Check each electrode pad of J2")),
    ("doc.hw_readme.RV1_insulated", "insulated-shaft text removed", lambda t: t.replace("insulated (plastic) shaft", "any shaft")),
    ("doc.hw_readme.JP1_smd", "JP1 text changed", lambda t: t.replace("3-pad solder bridge", "wire link")),
]

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT).stdout
def line_for(out, name):
    for l in out.splitlines():
        if l.startswith(("PASS  ", "FAIL  ")) and l[6:].split(" :: ")[0] == name:
            return l
    return None

def write(name, text):
    p = os.path.join(SCR, name)
    open(p, "w", encoding="utf-8").write(text)
    return p

BASE_PCB = write("board.kicad_pcb", BOARD)
BASE_DRL = write("board.drl", DRL)
BASE_HW = write("readme.md", HWR)
BASE_MAN = write("manual.md", MAN)
BASE_BOM = write("bom.csv", BOM)
PCHK = [PY, os.path.join(ROOT, "sim/systems/pcb_rules_check.py")]
ICHK = [PY, os.path.join(ROOT, "sim/systems/interface_check.py")]
base_p = run(PCHK + [BASE_PCB, BASE_DRL]); base_i = run(ICHK + [BASE_PCB, BASE_HW, BASE_MAN, BASE_BOM])
print("# Unmodified inputs:"); print([l for l in base_p.splitlines() if l.startswith("SUMMARY")]); print([l for l in base_i.splitlines() if l.startswith("SUMMARY")])
ok = bad = 0
def report(name, desc, out, base):
    global ok, bad
    l, b = line_for(out, name), line_for(base, name)
    good = l is not None and l.startswith("FAIL") and b is not None and b.startswith("PASS")
    ok += good; bad += not good
    print("%s  [%s] %s -> %s" % ("MUT-OK " if good else "MUT-BAD", name, desc, (l or "NO SUCH CHECK")[:210]))
for name, desc, f in PCB_MUT:
    report(name, desc, run(PCHK + [write("m.kicad_pcb", f(BOARD)), BASE_DRL]), base_p)
report(DRL_NAME, "drill file H hit moved 1 mm", run(PCHK + [BASE_PCB, write("m.drl", re.sub(r'^X([-\d.]+)Y', lambda m: "X%sY" % (float(m.group(1)) + 1.0), DRL, count=1, flags=re.M))]), base_p)
for name, desc, f in IF_MUT:
    report(name, desc, run(ICHK + [write("m.kicad_pcb", f(BOARD)), BASE_HW, BASE_MAN, BASE_BOM]), base_i)
for name, desc, f in DOC_MUT:
    report(name, desc, run(ICHK + [BASE_PCB, write("m.md", f(HWR)), BASE_MAN, BASE_BOM]), base_i)
report("fab.bom_matches_board", "BOM R1-R12 MPN changed", run(ICHK + [BASE_PCB, BASE_HW, BASE_MAN, write("m.csv", BOM.replace("HPWC2512-3K0JT18", "HPWC2512-3K3JT18"))]), base_i)
# The manual check fails on the stale manual today: prove it can pass on a corrected copy and fails on the current text.
fixed = MAN
for w in ("PCB v1.2", "MBE0414", "DIN0414", "screw terminals", "screw-terminal pads", "Drill R1", "S holes", "version 1.2"):
    fixed = fixed.replace(w, "x")
fixed += "\nPCB version 1.3.\n"
o = run(ICHK + [BASE_PCB, BASE_HW, write("fixed.md", fixed), BASE_BOM])
l, b = line_for(o, "doc.manual.matches_v1.3"), line_for(base_i, "doc.manual.matches_v1.3")
good = l and l.startswith("PASS") and b.startswith("FAIL")
ok += bool(good); bad += not good
print("%s  [doc.manual.matches_v1.3] corrected copy passes, current manual fails -> %s" % ("MUT-OK " if good else "MUT-BAD", (l or "")[:150]))
print("MUTATION SUMMARY: %d proved, %d not proved" % (ok, bad))
sys.exit(0 if bad == 0 else 1)
