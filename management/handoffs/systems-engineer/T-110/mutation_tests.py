#!/usr/bin/env python3
"""T-093, updated T-099, T-104 and T-106: prove each new or changed design-file check can fail. Each mutation edits a scratch copy of the board, drill file,
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
def ko_centres():
    out = []
    for m in re.finditer(r"\n\t+\(zone\b", BOARD):
        z = BOARD[m.start():]
        pts = [(float(a), float(b)) for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', z)[:4]]
        out.append((sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4))
    return out
def drop_zone(t, k):
    ms = list(re.finditer(r"\n(\t+)\(zone\b", t))
    a = ms[k].start(); e = t.index("\n" + ms[k].group(1) + ")", a + 1) + len(ms[k].group(1)) + 2
    return t[:a] + t[e:]
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
    ("REQ-029 land sizes match the v1.3 table after T-103 (A1, A2, J1, J3, RV1, SW1, C1, R1..R16)", "A2 electrode lands back to 1.8 x 2.4 mm", lambda t: in_fp(t, "A2", "(size 1.8 4.2)", "(size 1.8 2.4)")),
    ("REQ-029 land sizes match the v1.3 table after T-103 (A1, A2, J1, J3, RV1, SW1, C1, R1..R16)", "C1 lands back to 1.15 mm", lambda t: in_fp(t, "C1", "(size 1.875 1.8)", "(size 1.15 1.8)")),
    ("REQ-029 land sizes match the v1.3 table after T-103 (A1, A2, J1, J3, RV1, SW1, C1, R1..R16)", "R15 lands back to 1.15 mm", lambda t: in_fp(t, "R15", "(size 1.775 1.8)", "(size 1.15 1.8)")),
    ("REQ-029 no bare copper in the 3 Pico keep-out rule areas", "TP7 keep-out removed (2 left)", lambda t: drop_zone(t, 2)),
    ("REQ-029 no bare copper in the 3 Pico keep-out rule areas", "track through the TP7 keep-out", lambda t: add_top(t, seg(ko_centres()[2][0], ko_centres()[2][1], ko_centres()[2][0] + 0.5, ko_centres()[2][1], 0.8))),
    ("ADR-028 D-1 Pico end inside the board and USB face >= 1.0 mm beyond the edge", "A1 moved 1.0 mm inward (face 0.19 mm)", lambda t: in_fp(t, "A1", "(at 54.5 51.48)", "(at 54.5 52.48)")),
    ("ADR-028 D-1 Pico end inside the board and USB face >= 1.0 mm beyond the edge", "A1 moved 0.2 mm outward (Pico end beyond the edge)", lambda t: in_fp(t, "A1", "(at 54.5 51.48)", "(at 54.5 51.28)")),
    ("REQ-029 no bare copper in the 3 Pico keep-out rule areas", "track through a keep-out", lambda t: add_top(t, seg(kx, ky, kx + 0.5, ky, 0.8))),
    ("REQ-023 R1-R12 land gap >= 3.5 mm (4 kV rule) and = 5.0 mm (ADR-023)", "R5 pad 2 moved 1 mm inward", None),
    ("ADR-026 R1-R12 on footprint R_2512_HomeEtch_G5.0mm", "R3 on the old footprint name", lambda t: in_fp(t, "R3", "FrutaMIDI:R_2512_HomeEtch_G5.0mm", "FrutaMIDI:R_2512_HPWC_G5.0mm")),
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
    ("pcb.R1_R12_footprint", "R5 footprint renamed", lambda t: t[:fp_block("R5")[0]] + BOARD[fp_block("R5")[0]:fp_block("R5")[1]].replace("FrutaMIDI:R_2512_HomeEtch_G5.0mm", "FrutaMIDI:R_2512_HPWC_G5.0mm", 1) + t[fp_block("R5")[1]:]),
    ("pcb.R1_R12_MPN", "R7 MPN changed", lambda t: in_fp(t, "R7", '"MPN" "RC2512FK-073K3L"', '"MPN" "HPWC2512-3K3JT1"')),
    ("pcb.R1_R12_Mouser", "R8 Mouser number changed", lambda t: in_fp(t, "R8", '"Mouser" "603-RC2512FK-073K3L"', '"Mouser" "756-HPWC2512-3K3JT1"')),
    ("pcb.R1_R12_value", "R9 value 3k0", lambda t: in_fp(t, "R9", '"Value" "3k3"', '"Value" "3k0"')),
    ("pcb.part.RV1", "RV1 MPN changed to the Alps part", lambda t: in_fp(t, "RV1", '"MPN" "PTV09A-4015F-B103"', '"MPN" "RK09D1130C2P"')),
    ("fab.copper_only_excluded_from_bom", "J1 no longer excluded from the BOM", lambda t: in_fp(t, "J1", "(attr smd exclude_from_bom)", "(attr smd)")),
    ("fab.copper_only_excluded_from_bom", "R16 excluded from the BOM", lambda t: in_fp(t, "R16", "(attr smd)", "(attr smd exclude_from_bom)")),
    ("pcb.part.A1", "A1 Mouser number removed", lambda t: in_fp(t, "A1", '"Mouser" "358-SC0915"', '"Mouser" ""')),
    ("pcb.AGND_membership", "SW1 pad 2 on AGND", lambda t: in_fp(t, "SW1", '(net "GND")', '(net "/AGND")')),
    ("pcb.RV1_offboard_3_pads", "RV1 MP tab added", lambda t: in_fp(t, "RV1", '(pad "3" smd', '(pad "MP" smd rect\n\t\t\t(at 9 0)\n\t\t\t(size 2 2)\n\t\t\t(layers "F.Cu" "F.Mask")\n\t\t\t(net "/AGND")\n\t\t\t(uuid "00000000-0000-0000-0000-000000000003")\n\t\t)\n\t\t(pad "3" smd')),
    ("pcb.JP1_smd_bridge", "JP1 pad through-hole", lambda t: in_fp(t, "JP1", '(pad "1" smd', '(pad "1" thru_hole')),
    ("pcb.J1_J3_smd", "J3 pad through-hole", lambda t: in_fp(t, "J3", '(pad "1" smd', '(pad "1" thru_hole')),
    ("pcb.J2_solder_pads", "J2 pad through-hole", lambda t: in_fp(t, "J2", '(pad "5" smd', '(pad "5" thru_hole')),
    ("pcb.JP1_legend", "ORIG not etched", lambda t: re.sub(r'(\(gr_text "ORIG"\s*\(at [^)]*\)\s*\(layer ")F\.Cu', r'\1F.Fab', t, count=1)),
    ("pcb.part.A1", "A1 footprint renamed", lambda t: t.replace("FrutaMIDI:RaspberryPi_Pico_Castellated_HomeEtch", "FrutaMIDI:RaspberryPi_Pico_THT", 1)),
    ("pcb.part.A2", "A2 MPN changed", lambda t: in_fp(t, "A2", '"MPN" "1982"', '"MPN" "1983"')),
    ("pcb.part.C1", "C1 MPN changed", lambda t: in_fp(t, "C1", '"MPN" "CL31B104KBCNNNC"', '"MPN" "C1206C104K5RACTU"')),
    ("pcb.part.SW1", "SW1 MPN changed", lambda t: in_fp(t, "SW1", '"MPN" "B3S-1000"', '"MPN" "B3F-1000"')),
    ("pcb.part.R15", "R15 MPN changed", lambda t: in_fp(t, "R15", '"MPN" "RC1206FR-07220RL"', '"MPN" "RC0805FR-07220RL"')),
    ("pcb.part.JP1", "JP1 footprint THT", lambda t: t.replace("FrutaMIDI:SolderJumper_3_SMD_P3.81mm", "FrutaMIDI:SolderJumper_3_THT_P3.81mm", 1)),
    ("pcb.part.J2", "J2 footprint terminal block", lambda t: t.replace("FrutaMIDI:WirePads_1x14_P5.08mm", "FrutaMIDI:TerminalBlock_5.08_1x14", 1)),
    ("pcb.part.H1_H4", "H4 footprint renamed", lambda t: in_fp(t, "H4", "FrutaMIDI:MountingHole_3.2mm_M3", "FrutaMIDI:MountingHole_2.2mm_M2")),
    ("pcb.no_extra_parts", "reference R16 renamed X9", lambda t: in_fp(t, "R16", '"Reference" "R16"', '"Reference" "X9"')),
]
DOC_MUT = [
    ("doc.hw_readme.version", "title v1.2", lambda t: t.replace("(version 1.3)", "(version 1.2)")),
    ("doc.hw_readme.R1_R12_part", "YAGEO part replaced by HPWC", lambda t: t.replace("RC2512FK-073K3L", "HPWC2512-3K3JT1")),
    ("doc.hw_readme.mouser_numbers", "Mouser number of SW1 removed", lambda t: t.replace("653-B3S-1000", "B3S")),
    ("doc.hw_readme.only_4_holes", "drill statement removed", lambda t: t.replace("Only the 4 M3 mounting holes", "The mounting holes")),
    ("doc.hw_readme.no_sockets", "socket instruction added", lambda t: t.replace("## 3. Drill", "Use a socket for the Pico.\n\n## 3. Drill")),
    ("doc.hw_readme.continuity_through_series_R", "line removed", lambda t: t.replace("Resistance between each electrode pad of J2", "Check each electrode pad of J2")),
    ("doc.hw_readme.RV1_insulated", "insulated-shaft text removed", lambda t: t.replace("insulated flatted shaft", "flatted shaft")),
    ("doc.hw_readme.continuity_through_series_R", "continuity value 3.0 kOhm", lambda t: t.replace("about **3.3 kΩ** (3267", "about **3.0 kΩ** (3267")),
    ("doc.hw_readme.pico_variants", "Pico W exclusion removed from the A1 row", lambda t: t.replace("Pico W and Pico 2 W are not supported", "Pico W and Pico 2 W also fit")),
    ("doc.hw_readme.pico_variants", "Pico 2 W firmware row says it fits", lambda t: re.sub(r"(\| Raspberry Pi Pico 2 W \(breadboard only: )not supported on this PCB", r"\1fits this PCB", t)),
    ("doc.hw_readme.R016_alternative", "alternative Mouser number removed", lambda t: t.replace("71-CRCW25123K30FKEG", "CRCW")),
    ("doc.hw_readme.knob_and_sw1_notes", "SW1 maker note removed", lambda t: t.replace("ARATAS, formerly Omron", "Omron")),
    ("doc.hw_readme.knob_and_sw1_notes", "knob-not-in-BOM note removed", lambda t: t.replace("knob is also not in `bom-kicad.csv`", "knob is listed")),
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
report("fab.bom_matches_board", "BOM R1-R12 MPN changed", run(ICHK + [BASE_PCB, BASE_HW, BASE_MAN, write("m.csv", BOM.replace('"RC2512FK-073K3L"', '"RC2512FK-073K0L"'))]), base_i)
report("fab.bom_matches_board", "BOM C1 Mouser number changed", run(ICHK + [BASE_PCB, BASE_HW, BASE_MAN, write("m.csv", BOM.replace("187-CL31B104KBCNNNC", "187-CL31B104KBCNNNX"))]), base_i)
# T-104: the manual and root README now pass; prove both checks fail on a stale copy.
RREAD = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
BASE_RR = write("root_readme.md", RREAD)
base_i5 = run(ICHK + [BASE_PCB, BASE_HW, BASE_MAN, BASE_BOM, BASE_RR])
report("doc.manual.matches_v1.3", "manual says PCB v1.2 and screw terminals", run(ICHK + [BASE_PCB, BASE_HW, write("m_man.md", MAN + "\nPCB v1.2 with screw terminals.\n"), BASE_BOM, BASE_RR]), base_i5)
report("doc.root_readme.matches_v1.3", "root README names PCB v1.2 and DIN0414", run(ICHK + [BASE_PCB, BASE_HW, BASE_MAN, BASE_BOM, write("m_rr.md", RREAD + "\nPCB v1.2, DIN0414 resistors.\n")]), base_i5)
# T-104: checks that FAIL on today's text: prove each passes on a corrected copy (and fails on the current one)
def inverse(name, desc, out):
    global ok, bad
    l, b = line_for(out, name), line_for(base_i5, name)
    good = bool(l and l.startswith("PASS") and b and b.startswith("FAIL"))
    ok += good; bad += not good
    print("%s  [%s] %s -> %s" % ("MUT-OK " if good else "MUT-BAD", name, desc, (l or "NO SUCH CHECK")[:170]))
# T-106: the manual and root README now pass these checks (T-105); prove each fails on a stale copy.
report("doc.manual.JP1_label_position", "manual says ORIG etched below", run(ICHK + [BASE_PCB, BASE_HW, write("m_man4.md", MAN + "\n**ORIG** etched below JP1.\n"), BASE_BOM, BASE_RR]), base_i5)
report("doc.root_readme.pcb_variants", "root README Pico W PCB row without the note", run(ICHK + [BASE_PCB, BASE_HW, BASE_MAN, BASE_BOM, write("m_rr2.md", RREAD.replace("`FrutaMIDI-pcb-rpipicow.uf2` (not supported on the v1.3 PCB, see below)", "`FrutaMIDI-pcb-rpipicow.uf2`"))]), base_i5)
report("doc.root_readme.pcb_variants", "manual gains a Pico 2 W PCB row without the note", run(ICHK + [BASE_PCB, BASE_HW, write("m_man5.md", MAN + "\n| Pico 2 W | `FrutaMIDI-pcb-rpipico2w.uf2` |\n"), BASE_BOM, BASE_RR]), base_i5)
report("doc.manual.JP1_label_position", "hardware README says ORIG etched below", run(ICHK + [BASE_PCB, write("m_hw.md", HWR + "\n**ORIG** etched below JP1.\n"), write("fix_man2.md", MAN.replace("**ORIG** etched below", "**ORIG** etched to the left")), BASE_BOM, BASE_RR]),
       run(ICHK + [BASE_PCB, BASE_HW, write("fix_man3.md", MAN.replace("**ORIG** etched below", "**ORIG** etched to the left")), BASE_BOM, BASE_RR]))
# T-104: budgets.py (checks C2, D1-D3) on a scratch input tree (FM_BUDGETS_ROOT)
import shutil
BR = os.path.join(SCR, "broot")
def btree(mut=None):
    shutil.rmtree(BR, ignore_errors=True)
    files = {"hardware/fabrication/bom-kicad.csv": BOM, "hardware/README.md": HWR}
    for n in ("calc_gnd_bounce.out", "calc_i2c_coupling.out", "calc_usb_pry.out"):
        files["sim/electronics/calc/" + n] = open(os.path.join(ROOT, "sim/electronics/calc", n), encoding="utf-8").read()
    if mut: k, f = mut; files[k] = f(files[k])
    for k, v in files.items():
        if v is None: continue
        os.makedirs(os.path.dirname(os.path.join(BR, k)), exist_ok=True); open(os.path.join(BR, k), "w", encoding="utf-8").write(v)
    return subprocess.run([PY, os.path.join(ROOT, "sim/systems/budgets.py")], capture_output=True, text=True, cwd=ROOT, env=dict(os.environ, FM_BUDGETS_ROOT=BR)).stdout
base_b = btree()
print([l for l in base_b.splitlines() if l.startswith("SUMMARY")])
C2 = "C2 budget BOM = fabrication BOM (Mouser numbers and quantities); knob only in the README"
D1 = "D1 injected I2C current and charge within the RP2040 HBM 4 kV equivalent (FT-pin rating; GP26/GP27 NOT CONFIRMED)"
D2 = "D2 SDA coupling step <= 3 counts (half RELEASE_THRESHOLD, REQ-038 proposal)"
D3 = "D3 largest M3 screw force at a 30 N USB pull <= 100 N (ASSUMPTION limit, not sourced)"
def subl(a, b):
    def f(t):
        if a not in t: raise SystemExit("mutation text not found: " + a)
        i = t.rindex(a); return t[:i] + b + t[i + len(a):]
    return f
for name, desc, mut in [
    (C2, "BOM R1-R12 quantity 11", ("hardware/fabrication/bom-kicad.csv", subl('"603-RC2512FK-073K3L","12"', '"603-RC2512FK-073K3L","11"'))),
    (C2, "BOM gains a knob line", ("hardware/fabrication/bom-kicad.csv", lambda t: t + '"K1","knob","x","Same Sky","SPK-016A","179-SPK-016A","1"\n')),
    (C2, "knob Mouser number missing from the README", ("hardware/README.md", lambda t: t.replace("179-SPK-016A", "SPK"))),
    (D1, "injected current 2.90 A", ("sim/electronics/calc/calc_gnd_bounce.out", subl("<= 1.49 A", "<= 2.90 A"))),
    (D1, "calc_gnd_bounce.out missing", ("sim/electronics/calc/calc_gnd_bounce.out", lambda t: None)),
    (D2, "SDA step 3.50 counts", ("sim/electronics/calc/calc_i2c_coupling.out", subl("= 2.09 ADC counts", "= 3.50 ADC counts"))),
    (D3, "screw force 135.6 N", ("sim/electronics/calc/calc_usb_pry.out", subl("current 35.6 N", "current 135.6 N"))),
]:
    report(name, desc, btree(mut), base_b)
print("MUTATION SUMMARY: %d proved, %d not proved" % (ok, bad))
sys.exit(0 if bad == 0 else 1)
