"""T-008 interface consistency check (systems-engineer).

Cross-checks, by parsing the files (read-only):
  - firmware/FrutaMIDI/FrutaMIDI.ino pin constants (breadboard and FRUTAMIDI_PCB variants)
  - hardware/frutamidi.kicad_pcb pad-to-net assignments (A1 Pico, A2 MPR121, J1, J2, RV1, SW1)
  - hardware/scripts/gen_schematic.py module power-row labels
  - Adafruit 1982 header nets for both revisions (SOURCE: Adafruit Eagle files, see
    requirements/SOURCES_SYSTEMS.md S-06/S-07) and the 180-degree footprint rotation in gen_pcb.py
  - README.md / hardware/README.md pin tables
T-093 (CR-003, ADR-023): adapted to the v1.3 SMD board: footprints, MPNs, pad types, label, AGND without RV1 tabs, BOM file, manual.
Prints one line per check: PASS / FAIL, and a final summary line.
Usage: python3 sim/systems/interface_check.py [board.kicad_pcb [hardware_README.md [MANUAL.md [bom.csv [README.md]]]]]   (scratch copies for mutation tests)
"""
import csv
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = lambda *a: os.path.join(ROOT, *a)

# SOURCE S-03 (pico.pinout.xyz, cross-checked with raspberrypi.com documentation S-02):
PICO_PHYS = {}
left = ["GP0", "GP1", "GND", "GP2", "GP3", "GP4", "GP5", "GND", "GP6", "GP7", "GP8", "GP9", "GND",
        "GP10", "GP11", "GP12", "GP13", "GND", "GP14", "GP15"]
right = ["GP16", "GP17", "GND", "GP18", "GP19", "GP20", "GP21", "GND", "GP22", "RUN", "GP26", "GP27",
         "AGND", "GP28", "ADC_VREF", "3V3", "3V3_EN", "GND", "VSYS", "VBUS"]
for i, f in enumerate(left + right):
    PICO_PHYS[i + 1] = f
GP_TO_PHYS = {f: n for n, f in PICO_PHYS.items() if f.startswith("GP")}

# SOURCE S-07 (original, Eagle "Adafruit MPR121 Breakout.brd", JP2 pads 1..7) and
# S-06 (STEMMA QT, Eagle "Adafruit MPR121Q QT.brd", JP2 pads 1..7):
JP2 = {
    "original": ["VIN", "3V3", "GND", "ADDR", "SDA", "SCL", "IRQ"],
    "stemma_qt": ["VCC", "3V3", "GND", "SCL", "SDA", "INT", "ADDR"],
}
JP2_ROT = {"original": 180, "stemma_qt": 0}       # element rotation in the Eagle board
JP1 = ["E11", "E10", "E9", "E8", "E7", "E6", "E5", "E4", "E3", "E2", "E1", "E0", "GND"]  # pads 1..13, x ascending


def s_row(rev):
    """Module JP2 net seen at FrutaMIDI S1..S7 (S1 = lowest x on the FrutaMIDI board).

    gen_pcb.py places the module rotated 180 deg relative to the Adafruit Eagle files, so the
    FrutaMIDI left-to-right order is the Adafruit right-to-left (x descending) order.
    Eagle JP2 without rotation: pad 1 at lowest x. With R180: pad 1 at highest x.
    """
    pads = JP2[rev]
    x_ascending = pads if JP2_ROT[rev] == 0 else list(reversed(pads))
    return list(reversed(x_ascending))


def electrode_row():
    return list(reversed(JP1))     # FrutaMIDI pin 1..13 (x ascending after 180 deg rotation)


PAD_TYPES = {}   # ref -> pad number -> set of "type shape" strings


def footprints(pcb_text):
    out = {}
    i = 0
    while True:
        i = pcb_text.find("\n\t(footprint ", i)
        if i < 0:
            break
        d, j = 0, i + 1
        while True:
            c = pcb_text[j]
            if c == "(":
                d += 1
            elif c == ")":
                d -= 1
                if d == 0:
                    break
            j += 1
        blk = pcb_text[i:j + 1]
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        pads = {}
        for m in re.finditer(r'\(pad "([^"]*)"(.*?)\n\t\t\)', blk, re.S):
            n = re.search(r'\(net "([^"]*)"\)', m.group(2))
            pads.setdefault(m.group(1), set()).add(n.group(1).lstrip("/") if n else None)
            PAD_TYPES.setdefault(ref, {}).setdefault(m.group(1), set()).add(m.group(2).split()[0])
        out[ref] = pads
        i = j
    return out


def fw_pins(ino):
    blocks = re.split(r"#(?:if|elif|else|endif)", ino)
    # block order in the file: [pre, PCB, breadboard RP2040, ProMicro, ...]
    res = {}
    m = re.search(r"#if defined\(ARDUINO_ARCH_RP2040\) && defined\(FRUTAMIDI_PCB\)(.*?)#elif defined\(ARDUINO_ARCH_RP2040\)(.*?)#else(.*?)#endif", ino, re.S)
    for name, blk in (("pcb", m.group(1)), ("breadboard", m.group(2))):
        d = dict((k, int(v)) for k, v in re.findall(r"(PIN_\w+)\s*=\s*(\d+)", blk))
        d["I2C_BUS"] = re.search(r"#define I2C_BUS (\w+)", blk).group(1)
        res[name] = d
    return res


results = []
names = []


def check(name, ok, detail):
    results.append(ok)
    names.append(name)
    print("%s  %s :: %s" % ("PASS" if ok else "FAIL", name, detail))


ino = open(P("firmware", "FrutaMIDI", "FrutaMIDI.ino"), encoding="utf-8").read()
pcb = open(sys.argv[1] if len(sys.argv) > 1 else P("hardware", "frutamidi.kicad_pcb"), encoding="utf-8").read()
sch_py = open(P("hardware", "scripts", "gen_schematic.py"), encoding="utf-8").read()
readme = open(sys.argv[5] if len(sys.argv) > 5 else P("README.md"), encoding="utf-8").read()
hw_readme = open(sys.argv[2] if len(sys.argv) > 2 else P("hardware", "README.md"), encoding="utf-8").read()
manual = open(sys.argv[3] if len(sys.argv) > 3 else P("docs", "manual", "MANUAL.md"), encoding="utf-8").read()
BOM_PATH = sys.argv[4] if len(sys.argv) > 4 else P("hardware", "fabrication", "bom-kicad.csv")

fw = fw_pins(ino)
fps = footprints(pcb)
VALUES = {}
for _m in re.finditer(r'\(property "Reference" "([^"]+)".*?\(property "Value" "([^"]+)"', pcb, re.S):
    VALUES.setdefault(_m.group(1), _m.group(2))
print("firmware pins:", fw)
print("footprints:", sorted(fps))

# I2C instance validity (SOURCE S-09: arduino-pico 6.3.1 Wire.cpp valid SDA masks; Wire=i2c0, Wire1=i2c1)
I2C0_SDA, I2C1_SDA = {0, 4, 8, 12, 16, 20, 24, 28}, {2, 6, 10, 14, 18, 22, 26}
for v in ("pcb", "breadboard"):
    sda, scl, bus = fw[v]["PIN_SDA"], fw[v]["PIN_SCL"], fw[v]["I2C_BUS"]
    ok = (bus == "Wire" and sda in I2C0_SDA or bus == "Wire1" and sda in I2C1_SDA) and scl == sda + 1
    check("fw.%s.i2c_instance" % v, ok, "%s SDA=GP%d SCL=GP%d" % (bus, sda, scl))

# Firmware PCB pins vs PCB nets on the Pico socket A1
pcb_expect = {"PIN_SDA": "SDA", "PIN_SCL": "SCL", "PIN_BUTTON": "BTN", "PIN_POT": "POT"}
for const, net in pcb_expect.items():
    gp = "GP%d" % fw["pcb"][const]
    phys = GP_TO_PHYS[gp]
    got = fps["A1"].get(str(phys))
    if net in ("SDA", "SCL") and got == {net + "_PICO"}:
        # T-055 / ADR-012: Pico pad -> <net>_PICO -> 220 R series -> bus net <net>
        rs = [r for r, pads in fps.items() if r.startswith("R") and r != "RV1"
              and set().union(*pads.values()) == {net + "_PICO", net}]
        val = [VALUES.get(r) for r in rs]
        check("fw.pcb.%s_vs_pcb" % const, len(rs) == 1 and val == ["220"],
              "%s -> Pico pin %d net %s_PICO -> %s %s -> %s" % (gp, phys, net, rs, val, net))
    else:
        check("fw.pcb.%s_vs_pcb" % const, got == {net}, "%s -> Pico pin %d, PCB A1 pad %d net %s (expected %s)"
              % (gp, phys, phys, got, net))

# Power pins on A1
for phys, net in ((36, "+3V3"), (33, "AGND")):
    got = fps["A1"].get(str(phys))
    check("pcb.A1.pin%d" % phys, got == {net}, "pad %d net %s, Pico function %s" % (phys, got, PICO_PHYS[phys]))
gnd_pads = [n for n, f in PICO_PHYS.items() if f == "GND"]
check("pcb.A1.gnd_pins", all(fps["A1"].get(str(n)) == {"GND"} for n in gnd_pads),
      "pads %s -> %s" % (gnd_pads, [fps["A1"].get(str(n)) for n in gnd_pads]))
used = {str(GP_TO_PHYS["GP%d" % fw["pcb"][c]]) for c in pcb_expect} | {"36", "33"} | {str(n) for n in gnd_pads}
others = {p: n for p, n in fps["A1"].items() if p not in used and n != {None} and not any(x and x.startswith("unconnected") for x in n)}
check("pcb.A1.no_other_nets", not others, "other connected pads: %s" % others)
# AGND membership rule (T-077, ADR-021; ADR-023 removes the RV1 tabs): AGND joins exactly A1 pin 33, RV1 pin 3 (off-board
# pot wire pad) and C1 pin 2 (wiper filter to AGND); nothing else. The off-board pot has no board-side mounting tab. It relies on the Pico-internal AGND-GND link (S-02 'also a GND pin';
# S-01 sec. 2.1 'separate analog ground plane ... terminating at this pin'), so no other AGND-GND join may exist.
AGND_ALLOWED = {("A1", "33"), ("RV1", "3"), ("C1", "2")}
agnd_members = sorted({(r, p) for r, f in fps.items() for p, n in f.items() if "AGND" in n})
check("pcb.AGND_membership", set(agnd_members) == AGND_ALLOWED,
      "AGND pads %s (allowed exactly %s)" % (agnd_members, sorted(AGND_ALLOWED)))
mixed = sorted((r, p, sorted(x for x in n if x)) for r, f in fps.items() for p, n in f.items() if "AGND" in n and len(n) > 1)
check("pcb.AGND_no_shared_pad", not mixed, "AGND pads carrying a second net: %s" % mixed)
agnd_parts = {r for r, _ in agnd_members}
gnd_on_agnd_parts = sorted(r for r in agnd_parts - {"A1"} if any("GND" in n for n in fps[r].values()))
check("pcb.AGND_parts_not_on_GND", not gnd_on_agnd_parts,
      "parts with an AGND pad that also have a GND pad (would be a second AGND-GND link): %s" % gnd_on_agnd_parts)

# Controls: RV1 (octave pot) and SW1 (button)
check("pcb.RV1", [fps["RV1"].get(n) for n in "123"] == [{"+3V3"}, {"POT"}, {"AGND"}],
      "RV1 1/2/3 = %s" % [fps["RV1"].get(n) for n in "123"])
check("pcb.RV1_offboard_3_pads", sorted(fps["RV1"]) == ["1", "2", "3"] and all(PAD_TYPES["RV1"][n] == {"smd"} for n in "123"),
      "RV1 pads %s, types %s (ADR-023 D-2: off-board pot on 3 wire pads, no mounting tabs on the board)" % (sorted(fps["RV1"]), PAD_TYPES["RV1"]))
c1 = fps.get("C1", {})
check("pcb.C1_wiper_filter", [c1.get(n) for n in "12"] == [{"POT"}, {"AGND"}] and len(c1) == 2
      and VALUES.get("C1", "").startswith("100n"),
      "C1 1/2 = %s, value %r (ADR-021: 100 nF POT to AGND; ADR-023: 1206)" % ([c1.get(n) for n in "12"], VALUES.get("C1")))
pot_members = sorted((r, p) for r, f in fps.items() for p, n in f.items() if "POT" in n)
check("pcb.POT_membership", set(pot_members) == {("A1", str(GP_TO_PHYS["GP%d" % fw["pcb"]["PIN_POT"]])), ("RV1", "2"), ("C1", "1")},
      "POT pads %s" % pot_members)
sw = set().union(*fps["SW1"].values())
check("pcb.SW1", sw == {"BTN", "GND"}, "SW1 nets %s (active low, firmware INPUT_PULLUP)" % sorted(sw))
check("fw.button_pullup", "pinMode(PIN_BUTTON, INPUT_PULLUP)" in ino and "digitalRead(PIN_BUTTON) == LOW" in ino,
      "button read active-low with internal pull-up")

# Module A2 electrode row, series resistors and terminals J2.
# PCB from T-050 on: terminal net E<k> -> series resistor -> module net ELE<k> (ESD, ADR-007 D-2).
# Older boards: terminal and module share net E<k>. Both topologies are accepted; the chain must be 1:1.
def series_r_between(a, b):
    hits = []
    for ref, pads in fps.items():
        if ref.startswith("R") and ref != "RV1":
            nets = set().union(*pads.values())
            if nets == {a, b}:
                hits.append(ref)
    return hits

er = electrode_row()
term_expect = ["GND"] + ["E%d" % i for i in range(12)] + ["GND"]
for k in range(13):
    got = fps["A2"].get(str(k + 1))
    if er[k] == "GND":
        check("pcb.A2.pin%d" % (k + 1), got == {"GND"}, "module row pin %d = Adafruit GND, PCB net %s" % (k + 1, got))
        continue
    e = int(er[k][1:])
    mod_net = list(got)[0] if got and len(got) == 1 else None
    if mod_net == "E%d" % e:
        check("pcb.A2.pin%d" % (k + 1), True, "module pin %d = Adafruit %s, direct net E%d" % (k + 1, er[k], e))
    else:
        rs = series_r_between(mod_net, "E%d" % e)
        check("pcb.A2.pin%d" % (k + 1), mod_net == "ELE%d" % e and len(rs) == 1,
              "module pin %d = Adafruit %s, net %s -> series %s -> terminal net E%d" % (k + 1, er[k], mod_net, rs, e))
for i in range(14):
    got = fps["J2"].get(str(i + 1))
    check("pcb.J2.T%d" % (i + 1), got == {term_expect[i]}, "terminal %d net %s (expected %s)" % (i + 1, got, term_expect[i]))
check("pcb.J2_solder_pads", sorted(fps["J2"], key=int) == [str(k) for k in range(1, 15)] and all(v == {"smd"} for v in PAD_TYPES["J2"].values()),
      "J2 %d pads, types %s (ADR-023 D-3: solder-wire pads, no terminal blocks)" % (len(fps["J2"]), sorted({x for v in PAD_TYPES["J2"].values() for x in v})))
# I2C pull-ups placed on the PCB (if any)
pu = {n: series_r_between("+3V3", n) for n in ("SDA", "SCL")}
print("INFO  PCB I2C pull-ups to +3V3: %s" % pu)

# Config pads J1 and module S row
if "JP1" in fps:
    # T-052 topology (ADR-007 D-4): JP1 3-pad selector, centre +3V3, pad 1 -> S1 (original VIN), pad 3 -> S7 (QT VCC);
    # J1 carries only SCL (pad 1) and SDA (pad 2) for the hand wires.
    jp = [fps["JP1"].get(n) for n in "123"]
    check("pcb.JP1_selector", jp == [{"S1"}, {"+3V3"}, {"S7"}], "JP1 1/2/3 = %s (expected S1/+3V3/S7)" % jp)
    check("pcb.JP1_smd_bridge", sorted(PAD_TYPES["JP1"]) == ["1", "2", "3"] and all(v == {"smd"} for v in PAD_TYPES["JP1"].values()),
          "JP1 pad types %s (ADR-023: SMD solder bridge, no holes)" % PAD_TYPES["JP1"])
    so_, sq_ = s_row("original"), s_row("stemma_qt")
    check("pcb.JP1_targets", so_[0] == "VIN" and sq_[6] == "VCC",
          "ORIG side S1 = %s (original), QT side S7 = %s (STEMMA QT)" % (so_[0], sq_[6]))
    print("INFO  JP1 wrong choice: original+QT side -> 3V3 on S7 = %s ; QT+ORIG side -> 3V3 on S1 = %s (no GND reachable)"
          % (so_[6], sq_[0]))
    check("pcb.JP1_no_gnd_reachable", "GND" not in (so_[0], so_[6], sq_[0], sq_[6]), "S1/S7 are never GND in either revision")
    silk = set(re.findall(r'\(gr_text "([^"]*)"\s*\(at [^)]*\)\s*\(layer "F\.Cu"\)', pcb))    # etched copper text (no silkscreen on v1.3)
    fab = set(re.findall(r'\(gr_text "([^"]*)"\s*\(at [^)]*\)\s*\(layer "F\.Fab"\)', pcb))     # assembly map
    legend = {"ORIG = no white connectors", "QT = 2 white connectors"}
    check("pcb.JP1_legend", {"ORIG", "QT"} <= silk and legend <= fab,
          "etched F.Cu: %s; explanatory legend on the assembly map (F.Fab), not on the board: %s (ADR-009 D-10, ADR-023 no silkscreen)"
          % (sorted(w for w in silk if "ORIG" in w or "QT" in w), sorted(w for w in fab if "ORIG" in w or "QT" in w)))
    j1 = [fps["J1"].get(n) for n in "12"]
    check("pcb.J1", j1 == [{"SCL"}, {"SDA"}] and "3" not in fps["J1"], "J1 1/2 = %s" % j1)
    check("pcb.J1_J3_smd", all(v == {"smd"} for r in ("J1", "J3") for v in PAD_TYPES[r].values()) and sorted(fps["J3"], key=int) == [str(k) for k in range(1, 8)],
          "J1 types %s, J3 pads %s types %s" % (PAD_TYPES["J1"], sorted(fps["J3"], key=int), sorted({x for v in PAD_TYPES["J3"].values() for x in v})))
else:
    check("pcb.J1", fps["J1"].get("1") == {"+3V3"} and fps["J1"].get("2") == {"SCL"} and fps["J1"].get("3") == {"SDA"},
          "J1 1/2/3 = %s/%s/%s (pre-T-052 topology)" % (fps["J1"].get("1"), fps["J1"].get("2"), fps["J1"].get("3")))
for k in range(1, 8):
    got = fps["A2"].get(str(13 + k))
    check("pcb.A2.S%d_isolated_net" % k, got is not None and len(got) == 1 and list(got)[0] == "S%d" % k,
          "S%d net %s (only joined to J1 by a hand wire)" % (k, got))

# gen_schematic.py labels "S<k>:<orig>/<qt>" vs Adafruit Eagle-derived mapping
labels = dict(re.findall(r'\("(\d+)", "S\d:([^"]+)"', sch_py))
so, sq = s_row("original"), s_row("stemma_qt")
alias = {"3V3o": "3V3", "3Vo": "3V3", "INT": "INT", "IRQ": "IRQ"}
for k in range(1, 8):
    lab = labels.get(str(13 + k), "?/?")
    o, q = [alias.get(x, x) for x in lab.split("/")]
    check("sch.S%d_label" % k, o == so[k - 1] and q == sq[k - 1],
          "schematic '%s' vs Eagle-derived original=%s qt=%s" % (lab, so[k - 1], sq[k - 1]))

# Wiring rule in hardware/README.md (T-035 table: version | how to recognise | JP1 bridge | SDA -> | SCL ->).
# The 3V3 path is JP1: ORIG side = S1, QT side = S7 (derived from the S-row: VIN / VCC position).
for rev, row_name in (("original", "Original"), ("stemma_qt", "STEMMA QT")):
    row = s_row(rev)
    supply = row.index("VIN" if rev == "original" else "VCC") + 1
    jp_side = {1: "ORIG", 7: "QT"}.get(supply, "?")
    exp = (jp_side, "S%d" % (row.index("SDA") + 1), "S%d" % (row.index("SCL") + 1))
    m = re.search(r"\| %s[^|]*\|[^|]*\| \*\*(\w+)\*\* \| \*\*(S\d)\*\* \| \*\*(S\d)\*\* \|" % re.escape(row_name), hw_readme)
    got = m.groups() if m else None
    check("doc.hw_readme.jp1_and_wires.%s" % rev, got == exp, "README (JP1, SDA, SCL)=%s, derived=%s" % (got, exp))
    gnd_s = "S%d" % (row.index("GND") + 1)
    print("INFO  %s: S-row = %s ; module GND at %s (not reachable by JP1)" % (rev, row, gnd_s))
# Documentation of the 220 R I2C series resistors (ADR-012)
if any(VALUES.get(r) == "220" for r in fps):
    for name, txt in (("hardware/README.md", hw_readme),):
        check("doc.hw_readme.R15_R16", "R15" in txt and "R16" in txt and "220" in txt,
              "%s lists R15/R16 220 Ohm I2C series resistors" % name)

# Board revision label (ADR-019 D-2 set "FrutaMIDI v1.2"; CR-003 / ADR-023 moves to "FrutaMIDI v1.3"). Etched on F.Cu: there is no silkscreen.
BOARD_LABEL = "FrutaMIDI v1.3"
labels_cu = re.findall(r'\(gr_text "(FrutaMIDI v[^"]*)"\s*\(at [^)]*\)\s*\(layer "F\.Cu"\)', pcb)
labels_all = re.findall(r'\(gr_text "(FrutaMIDI v\d[^"]*)"', pcb)
check("pcb.label_v1.3", labels_cu == [BOARD_LABEL] and all(x.startswith(BOARD_LABEL) for x in labels_all),
      "F.Cu label texts %s; all revision texts %s (expected one '%s')" % (labels_cu, labels_all, BOARD_LABEL))

# Parts on the v1.3 board (ADR-023): footprint and MPN of every line. MPN None = no part number on this footprint.
fp_info = {}
for blk in re.split(r"\n\t\(footprint ", pcb)[1:]:
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk)
    mpn = re.search(r'\(property "MPN" "([^"]*)"', blk)
    fp_info[ref.group(1) if ref else None] = (blk.split('"')[1], mpn.group(1) if mpn else None)
R_EL_FP = "FrutaMIDI:R_2512_HPWC_G5.0mm"
R_EL_MPN = "HPWC2512-3K0JT18"
r_el = ["R%d" % i for i in range(1, 13)]
bad_fp = {r: fp_info.get(r, (None,))[0] for r in r_el if fp_info.get(r, (None,))[0] != R_EL_FP}
check("pcb.R1_R12_footprint", not bad_fp, "R1..R12 footprint %s (mismatches: %s)" % (R_EL_FP, bad_fp))
bad_mpn = {r: fp_info.get(r, (None, None))[1] for r in r_el if fp_info.get(r, (None, None))[1] != R_EL_MPN}
check("pcb.R1_R12_MPN", R_EL_MPN in sch_py and not bad_mpn,
      "R1..R12 MPN TT Electronics %s in gen_schematic.py and on the PCB (mismatches: %s)" % (R_EL_MPN, bad_mpn))
bad_val = {r: VALUES.get(r) for r in r_el if VALUES.get(r) != "3k0"}
check("pcb.R1_R12_value", not bad_val, "R1..R12 value 3k0 (ADR-023 D-1; mismatches: %s)" % bad_val)
PARTS = {
    "A1": ("FrutaMIDI:RaspberryPi_Pico_Castellated_HomeEtch", "SC0915"),
    "A2": ("FrutaMIDI:Adafruit_MPR121_1982_SMD", "1982"),
    "C1": ("FrutaMIDI:C_1206_HomeEtch", "C1206C104K5RACTU"),
    "SW1": ("FrutaMIDI:SW_SPST_B3S-1000_HomeEtch", "B3S-1000"),
    "R13": ("FrutaMIDI:R_1206_HomeEtch", "4k7 1 % thick film, 1206"),
    "R14": ("FrutaMIDI:R_1206_HomeEtch", "4k7 1 % thick film, 1206"),
    "R15": ("FrutaMIDI:R_1206_HomeEtch", "220R 1 % thick film, 1206"),
    "R16": ("FrutaMIDI:R_1206_HomeEtch", "220R 1 % thick film, 1206"),
    "RV1": ("FrutaMIDI:WirePads_1x03_P5.08mm", None),
    "J1": ("FrutaMIDI:Config_2pads_SMD", None),
    "J2": ("FrutaMIDI:WirePads_1x14_P5.08mm", None),
    "J3": ("FrutaMIDI:WirePads_1x07_P2.54mm", None),
    "JP1": ("FrutaMIDI:SolderJumper_3_SMD_P3.81mm", None),
}
for ref, (want_fp, want_mpn) in sorted(PARTS.items()):
    got_fp, got_mpn = fp_info.get(ref, (None, None))
    ok = got_fp == want_fp and (want_mpn is None or got_mpn == want_mpn)
    check("pcb.part.%s" % ref, ok, "footprint %s, MPN %r (expected %s, %r)" % (got_fp, got_mpn, want_fp, want_mpn))
holes_fp = sorted(r for r in fps if re.fullmatch(r"H\d+", r))
check("pcb.part.H1_H4", holes_fp == ["H1", "H2", "H3", "H4"] and all(fp_info[r][0] == "FrutaMIDI:MountingHole_3.2mm_M3" for r in holes_fp),
      "%s footprint %s" % (holes_fp, sorted({fp_info[r][0] for r in holes_fp})))
extra = sorted(set(fps) - set(PARTS) - set(r_el) - set(holes_fp))
check("pcb.no_extra_parts", not extra, "footprints outside the v1.3 parts list: %s" % extra)

# Fabrication BOM export against the board
bom_path = BOM_PATH
bom_bad = []
bom_refs = set()
for row in csv.DictReader(open(bom_path, encoding="utf-8")):
    refs = []
    for part in row["Ref"].split(","):
        m = re.fullmatch(r"([A-Z]+)(\d+)-[A-Z]+(\d+)", part.strip())
        refs += ["%s%d" % (m.group(1), k) for k in range(int(m.group(2)), int(m.group(3)) + 1)] if m else [part.strip()]
    bom_refs |= set(refs)
    for r in refs:
        got = fp_info.get(r, (None, None))
        if got[0] != row["Footprint"] or (row["MPN"] and got[1] != row["MPN"]):
            bom_bad.append((r, row["Footprint"], row["MPN"], got))
want_bom = set(PARTS) | set(r_el)
want_bom -= {"J2", "J3", "JP1"}                  # copper-only items, excluded from the BOM by the generator (T-091)
check("fab.bom_matches_board", not bom_bad and bom_refs == want_bom, "BOM refs %d; mismatches %s; missing %s; extra %s"
      % (len(bom_refs), bom_bad, sorted(want_bom - bom_refs), sorted(bom_refs - want_bom)))

# Documentation vs the current PCB topology (T-010)
if "JP1" in fps:
    check("doc.hw_readme.mentions_JP1", "JP1" in hw_readme, "hardware/README.md describes the JP1 3V3 selector")
    check("doc.hw_readme.no_J1_3V3_wire", "J1 **3V3**" not in hw_readme and "3V3** hole of J1" not in hw_readme,
          "hardware/README.md must not instruct a J1 3V3 wire / J1 3V3 hole")
series = [r for r in fps if r.startswith("R") and r != "RV1" and set().union(*fps[r].values()) & {"E0"}]
m_cont = re.search(r"Resistance between each electrode pad of J2[^\n]*", hw_readme)
check("doc.hw_readme.continuity_through_series_R", bool(series) and bool(m_cont) and "3.0 k" in m_cont.group(0) and "not beep" in m_cont.group(0),
      "electrode pad to module pin passes through %s; README line: %s" % (series, m_cont.group(0)[:140] if m_cont else None))
# v1.3 assembly guide content (ADR-023)
check("doc.hw_readme.version", "(version 1.3)" in hw_readme.split("\n")[0] and "v1.2" not in hw_readme,
      "title line %r; 'v1.2' present: %s" % (hw_readme.split("\n")[0], "v1.2" in hw_readme))
check("doc.hw_readme.R1_R12_part", "HPWC2512-3K0JT18" in hw_readme and "3.0 kΩ" in hw_readme and "MBE0414" not in hw_readme,
      "HPWC2512-3K0JT18 and 3.0 kOhm stated, no MBE0414")
check("doc.hw_readme.only_4_holes", "Only the 4 M3 mounting holes" in hw_readme and "**3.2 mm**" in hw_readme and not re.search(r"\b(0\.8|0\.9|1\.0|1\.1|1\.4) ?mm (bit|drill)", hw_readme),
      "rule table says only the 4 M3 holes; bit 3.2 mm; no other drill size named")
sock = [m.start() for m in re.finditer(r"socket", hw_readme, re.I)]
sock_bad = [hw_readme[max(0, i - 25):i + 8].replace("\n", " ") for i in sock if not re.search(r"\bno\s+$", hw_readme[max(0, i - 4):i], re.I)]
check("doc.hw_readme.no_sockets", not sock_bad and "female" not in hw_readme.lower() and "screw terminal" not in hw_readme.lower(),
      "%d mentions of sockets, not 'no sockets': %s; female headers or screw terminals mentioned: %s"
      % (len(sock), sock_bad, "female" in hw_readme.lower() or "screw terminal" in hw_readme.lower()))
check("doc.hw_readme.RV1_insulated", "insulated (plastic) shaft" in hw_readme and "metal shaft is not protected" in hw_readme,
      "RV1: insulated shaft required, metal shaft warning present (R-011)")
check("doc.hw_readme.JP1_smd", "3-pad solder bridge" in hw_readme and "1.87 mm" in hw_readme, "JP1 described as surface bridge with the 1.87 mm gap")
# The user manual and the root README must describe the same board (REQ-036). They are not owned by the systems engineer.
stale = lambda txt: sorted({w for w in ("PCB v1.2", "MBE0414", "DIN0414", "screw-terminal pads", "screw terminals", "Drill R1", "S holes") if w in txt})
check("doc.manual.matches_v1.3", "1.3" in manual and "version 1.2" not in manual and not stale(manual),
      "docs/manual/MANUAL.md: 'version 1.2' present: %s; stale v1.2 terms: %s" % ("version 1.2" in manual, stale(manual)))
root_stale = sorted({w for w in ("PCB v1.2", "MBE0414", "DIN0414") if w in readme})
check("doc.root_readme.matches_v1.3", not root_stale, "README.md stale PCB terms: %s" % root_stale)
for name, txt in (("README.md", readme), ("hardware/README.md", hw_readme)):
    base = ROOT if name == "README.md" else P("hardware")
    links = [l.split("#")[0] for l in re.findall(r"\]\(([^)#][^)]*)\)", txt) if not re.match(r"[a-z]+:", l)]
    broken = sorted({l for l in links if l and not os.path.exists(os.path.join(base, l))})
    check("doc.links.%s" % name, not broken, "broken relative links: %s" % broken)
pcb_silk = set(re.findall(r'\(gr_text "([^"]*)"', pcb))
for word in ("ESCALA", "OITAVA"):
    if word in hw_readme and word not in pcb_silk:
        check("doc.hw_readme.silk_%s" % word, False, "README quotes silkscreen '%s', PCB silkscreen has %s"
              % (word, sorted(w for w in pcb_silk if w.isalpha() and w.isupper())))

# README pin tables
for gp, phys, src, txt in (("GP4", 6, "README", readme), ("GP5", 7, "README", readme),
                           ("GP15", 20, "README", readme), ("GP26", 31, "README", readme)):
    ok = re.search(r"\| %s[^|]*\| %d \|" % (gp, phys), txt) is not None and GP_TO_PHYS[gp] == phys
    check("doc.%s.%s" % (src, gp), ok, "%s at physical pin %d" % (gp, phys))
bb = fw["breadboard"]
check("doc.README_vs_fw_breadboard", (bb["PIN_SDA"], bb["PIN_SCL"], bb["PIN_BUTTON"], bb["PIN_POT"]) == (4, 5, 15, 26),
      "firmware breadboard SDA/SCL/BTN/POT = GP%d/GP%d/GP%d/GP%d, README GP4/GP5/GP15/GP26"
      % (bb["PIN_SDA"], bb["PIN_SCL"], bb["PIN_BUTTON"], bb["PIN_POT"]))
for sig, phys, gp in (("SDA", 31, "GP26"), ("SCL", 32, "GP27"), ("Button", 29, "GP22"), ("Potentiometer", 34, "GP28")):
    ok = re.search(r"\| %s[^|]*\| %d \| %s" % (sig, phys, gp), hw_readme) is not None
    check("doc.hw_readme.%s" % sig, ok and GP_TO_PHYS[gp] == phys, "%s pin %d %s" % (sig, phys, gp))

hw = [ok for n, ok in zip(names, results) if not n.startswith("doc.")]
dc = [ok for n, ok in zip(names, results) if n.startswith("doc.")]
print("SUMMARY hardware/firmware: %d checks, %d PASS, %d FAIL" % (len(hw), hw.count(True), hw.count(False)))
print("SUMMARY documentation: %d checks, %d PASS, %d FAIL" % (len(dc), dc.count(True), dc.count(False)))
n_fail = results.count(False)
print("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(results), results.count(True), n_fail))
sys.exit(1 if n_fail else 0)
