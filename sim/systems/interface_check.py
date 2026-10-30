"""T-008 interface consistency check (systems-engineer).

Cross-checks, by parsing the files (read-only):
  - firmware/FrutaMIDI/FrutaMIDI.ino pin constants (breadboard and FRUTAMIDI_PCB variants)
  - hardware/frutamidi.kicad_pcb pad-to-net assignments (A1 Pico, A2 MPR121, J1, J2, RV1, SW1)
  - hardware/scripts/gen_schematic.py module power-row labels
  - Adafruit 1982 header nets for both revisions (SOURCE: Adafruit Eagle files, see
    requirements/SOURCES_SYSTEMS.md S-06/S-07) and the 180-degree footprint rotation in gen_pcb.py
  - README.md / hardware/README.md pin tables
Prints one line per check: PASS / FAIL, and a final summary line.
"""
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
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


def check(name, ok, detail):
    results.append(ok)
    print("%s  %s :: %s" % ("PASS" if ok else "FAIL", name, detail))


ino = open(P("firmware", "FrutaMIDI", "FrutaMIDI.ino"), encoding="utf-8").read()
pcb = open(P("hardware", "frutamidi.kicad_pcb"), encoding="utf-8").read()
sch_py = open(P("hardware", "scripts", "gen_schematic.py"), encoding="utf-8").read()
readme = open(P("README.md"), encoding="utf-8").read()
hw_readme = open(P("hardware", "README.md"), encoding="utf-8").read()

fw = fw_pins(ino)
fps = footprints(pcb)
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
check("pcb.A1.AGND_isolated", "AGND" not in set().union(*[n for r, f in fps.items() for p, n in f.items() if r != "A1" and r != "RV1"]),
      "AGND net only on A1 pin 33 and RV1 (relies on the Pico module's internal AGND-GND link, SOURCE S-02 'also a GND pin')")

# Controls: RV1 (octave pot) and SW1 (button)
check("pcb.RV1", [fps["RV1"].get(n) for n in "123"] == [{"+3V3"}, {"POT"}, {"AGND"}],
      "RV1 1/2/3 = %s" % [fps["RV1"].get(n) for n in "123"])
sw = set().union(*fps["SW1"].values())
check("pcb.SW1", sw == {"BTN", "GND"}, "SW1 nets %s (active low, firmware INPUT_PULLUP)" % sorted(sw))
check("fw.button_pullup", "pinMode(PIN_BUTTON, INPUT_PULLUP)" in ino and "digitalRead(PIN_BUTTON) == LOW" in ino,
      "button read active-low with internal pull-up")

# Module A2 electrode row and terminals J2
er = electrode_row()
for k in range(13):
    got = fps["A2"].get(str(k + 1))
    exp = "GND" if er[k] == "GND" else er[k]
    check("pcb.A2.pin%d" % (k + 1), got == {exp}, "module row pin %d = Adafruit %s, PCB net %s" % (k + 1, er[k], got))
term_expect = ["GND"] + ["E%d" % i for i in range(12)] + ["GND"]
for i in range(14):
    got = fps["J2"].get(str(i + 1))
    check("pcb.J2.T%d" % (i + 1), got == {term_expect[i]}, "terminal %d net %s (expected %s)" % (i + 1, got, term_expect[i]))

# Config pads J1 and module S row
check("pcb.J1", fps["J1"].get("1") == {"+3V3"} and fps["J1"].get("2") == {"SCL"} and fps["J1"].get("3") == {"SDA"},
      "J1 1/2/3 = %s/%s/%s" % (fps["J1"].get("1"), fps["J1"].get("2"), fps["J1"].get("3")))
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

# Wiring rule in hardware/README.md: 3V3 -> VIN/VCC, SDA -> SDA, SCL -> SCL
for rev, row_name in (("original", "Original"), ("stemma_qt", "STEMMA QT")):
    row = s_row(rev)
    exp = ("S%d" % (row.index("VIN" if rev == "original" else "VCC") + 1),
           "S%d" % (row.index("SDA") + 1), "S%d" % (row.index("SCL") + 1))
    m = re.search(r"\| %s[^|]*\|[^|]*\| \*\*(S\d)\*\* \| \*\*(S\d)\*\* \| \*\*(S\d)\*\* \|" % re.escape(row_name), hw_readme)
    got = m.groups() if m else None
    check("doc.hw_readme.config_wires.%s" % rev, got == exp, "README (3V3,SDA,SCL)=%s, derived=%s" % (got, exp))
    gnd_s = "S%d" % (row.index("GND") + 1)
    print("INFO  %s: S-row = %s ; module GND at %s (3V3 wire there = short circuit)" % (rev, row, gnd_s))

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

n_fail = results.count(False)
print("SUMMARY: %d checks, %d PASS, %d FAIL" % (len(results), results.count(True), n_fail))
sys.exit(1 if n_fail else 0)
