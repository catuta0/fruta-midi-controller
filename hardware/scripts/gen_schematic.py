#!/usr/bin/env python3
"""Generates hardware/frutamidi.kicad_sch and the project symbol library.

Runs with any Python 3 that can read the KiCad libraries:
    python3 hardware/scripts/gen_schematic.py
"""
import os, re, uuid, sys

KICAD_SYMBOLS = os.environ.get(
    "KICAD_SYMBOL_DIR", "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT = "frutamidi"
U = lambda: str(uuid.uuid4())
ROOT_UUID = "6f3c2a52-6b1e-4d8e-9a43-3f6a0c1d2e01"   # fixed: the PCB footprint paths depend on it


def det_uuid(*parts):
    """Deterministic UUID, so regenerating does not break the links to the PCB."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "frutamidi/" + "/".join(parts)))


# --------------------------------------------------------------------------- libraries

def extract(text, name):
    i = text.index('(symbol "%s"' % name)
    d = 0
    for j in range(i, len(text)):
        if text[j] == "(":
            d += 1
        elif text[j] == ")":
            d -= 1
            if d == 0:
                return text[i:j + 1]
    raise ValueError(name)


def lib_symbol(lib, name):
    text = open(os.path.join(KICAD_SYMBOLS, lib + ".kicad_sym"), encoding="utf-8").read()
    return extract(text, name)


PIN_RE = re.compile(
    r'\(pin (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s+\(length ([\d.]+)\).*?\(number "([^"]*)"', re.S)


def pins_of(sym_text):
    out = {}
    for m in PIN_RE.finditer(sym_text):
        etype, _, x, y, a, length, num = m.groups()
        out.setdefault(num, (float(x), float(y), int(a), etype))
    return out


# Own symbol: Adafruit 1982 module (MPR121) seen as a socket.
# Electrode row (1-13) is the same on both revisions; the power/I2C row (14-20) depends on the revision.
MODULE_PINS = [
    # (number, name, x, y, angle) — S-row names: "original revision / STEMMA QT revision"
] + [(str(2 + i), "E%d" % i, 17.78, 15.24 - 2.54 * i, 180) for i in range(12)] + [
    ("1", "GND", 17.78, -17.78, 180),
    ("14", "S1:VIN/ADDR", -17.78, 7.62, 0),
    ("15", "S2:3V3o/INT", -17.78, 5.08, 0),
    ("16", "S3:GND/SDA", -17.78, 2.54, 0),
    ("17", "S4:ADDR/SCL", -17.78, 0.0, 0),
    ("18", "S5:SDA/GND", -17.78, -2.54, 0),
    ("19", "S6:SCL/3V3o", -17.78, -5.08, 0),
    ("20", "S7:IRQ/VCC", -17.78, -7.62, 0),
]


def module_symbol(full_name):
    pins = "".join(
        '\n\t\t\t(pin passive line (at %.2f %.2f %d) (length 2.54) (name "%s" (effects (font (size 1.27 1.27)))) (number "%s" (effects (font (size 1.27 1.27)))))'
        % (x, y, a, n, num) for num, n, x, y, a in MODULE_PINS)
    return f'''(symbol "{full_name}"
		(pin_names (offset 1.016))
		(exclude_from_sim no) (in_bom yes) (on_board yes)
		(property "Reference" "A" (at 0 21.59 0) (effects (font (size 1.27 1.27))))
		(property "Value" "Adafruit_MPR121_1982" (at 0 -22.86 0) (effects (font (size 1.27 1.27))))
		(property "Footprint" "FrutaMIDI:Adafruit_MPR121_1982_SMD" (at 0 -25.4 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Datasheet" "https://www.adafruit.com/product/1982" (at 0 -27.94 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Description" "Adafruit MPR121 breakout (1982), original or STEMMA QT, header pins butted on surface pads" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(symbol "Adafruit_MPR121_1982_0_1"
			(rectangle (start -15.24 17.78) (end 15.24 -20.32) (stroke (width 0.254) (type default)) (fill (type background)))
		)
		(symbol "Adafruit_MPR121_1982_1_1"{pins}
		)
	)'''


def rename_for_schematic(sym_text, lib, name):
    return sym_text.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (lib, name), 1)


# --------------------------------------------------------------------------- drawing

class Sheet:
    def __init__(self):
        self.items = []
        self.lib = {}
        self.pins = {}
        self.rot = {}            # (lib key, x, y) -> rotation in degrees (counter-clockwise)
        self.mirror = {}         # (lib key, x, y) -> mirrored about the horizontal axis

    def use(self, lib, name):
        key = "%s:%s" % (lib, name)
        if key not in self.lib:
            if lib == "FrutaMIDI":
                text = module_symbol(key)
                self.pins[key] = {num: (x, y, a, "passive") for num, _, x, y, a in MODULE_PINS}
            else:
                raw = lib_symbol(lib, name)
                self.pins[key] = pins_of(raw)
                text = rename_for_schematic(raw, lib, name)
            self.lib[key] = text
        return key

    def symbol(self, lib, name, ref, value, x, y, footprint, fields=None, hide_ref=False, in_bom=True, ref_at=(0, -3.0),
               on_board=True, rot=0, mirror_x=False):
        key = self.use(lib, name)
        self.rot[(key, x, y)] = rot
        self.mirror[(key, x, y)] = mirror_x
        mir = " (mirror x)" if mirror_x else ""
        sid = det_uuid("sym", ref)
        pin_uuids = "".join('\n\t\t(pin "%s" (uuid "%s"))' % (n, det_uuid("pin", ref, n)) for n in self.pins[key])
        ref_hide = " (hide yes)" if hide_ref else ""
        extra = ""
        for k, v in (fields or {}).items():
            extra += '\n\t\t(property "%s" "%s" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (hide yes)))' % (k, v, x, y)
        self.items.append(f'''	(symbol
		(lib_id "{key}")
		(at {x:.2f} {y:.2f} {rot}){mir}
		(unit 1)
		(exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) (on_board {"yes" if on_board else "no"}) (dnp no)
		(uuid "{sid}")
		(property "Reference" "{ref}" (at {x + ref_at[0]:.2f} {y + ref_at[1]:.2f} {rot}) (effects (font (size 1.27 1.27)){ref_hide}))
		(property "Value" "{value}" (at {x:.2f} {y + 3.0:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Footprint" "{footprint}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Datasheet" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Description" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes))){extra}{pin_uuids}
		(instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))
	)''')
        return key

    def pin_end(self, key, sx, sy, num):
        px, py, a, _ = self.pins[key][num]
        r = self.rot.get((key, sx, sy), 0)
        if self.mirror.get((key, sx, sy)):        # (mirror x): flip top and bottom
            py, a = -py, {90: 270, 270: 90}.get(a, a)
        for _ in range(r // 90):                 # rotate 90 deg counter-clockwise (library y axis points up)
            px, py, a = -py, px, (a + 90) % 360
        return sx + px, sy - py, a

    def wire(self, x1, y1, x2, y2):
        self.items.append('\t(wire (pts (xy %.2f %.2f) (xy %.2f %.2f)) (stroke (width 0) (type default)) (uuid "%s"))'
                          % (x1, y1, x2, y2, U()))

    def label(self, text, x, y, angle):
        just = "right" if angle in (180, 270) else "left"
        self.items.append('\t(label "%s" (at %.2f %.2f %d) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'
                          % (text, x, y, angle, just, U()))

    def no_connect(self, x, y):
        self.items.append('\t(no_connect (at %.2f %.2f) (uuid "%s"))' % (x, y, U()))

    def power(self, name, x, y, ref, rot=0):
        key = self.use("power", name)
        self.items.append(f'''	(symbol
		(lib_id "{key}") (at {x:.2f} {y:.2f} {rot}) (unit 1)
		(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
		(uuid "{det_uuid('pwr', ref)}")
		(property "Reference" "{ref}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Value" "{name}" (at {x:.2f} {y + (3.81 if name == 'GND' else -3.81) * (-1 if rot == 180 else 1):.2f} 0) (effects (font (size 1.27 1.27))))
		(property "Footprint" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Datasheet" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Description" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(pin "1" (uuid "{det_uuid('pwrpin', ref)}"))
		(instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))
	)''')

    def text(self, s, x, y, size=1.27):
        s = s.replace('"', "'").replace("\n", "\\n")
        self.items.append('\t(text "%s" (exclude_from_sim no) (at %.2f %.2f 0) (effects (font (size %.2f %.2f)) (justify left top)) (uuid "%s"))'
                          % (s, x, y, size, size, U()))

    def connect(self, key, sx, sy, num, net, stub=2.54):
        """Short wire out of the pin, with a label or power symbol at its end."""
        x, y, a = self.pin_end(key, sx, sy, num)
        # outward direction: the pin angle points towards the symbol body
        dx = {0: -1, 180: 1, 90: 0, 270: 0}[a]
        dy = {0: 0, 180: 0, 90: 1, 270: -1}[a]
        ex, ey = x + dx * stub, y + dy * stub
        self.wire(x, y, ex, ey)
        if net in ("GND", "+3V3"):
            # turn the symbol over when the stub points against its natural direction (GND down, +3V3 up)
            flip = (net == "+3V3" and dy == 1) or (net == "GND" and dy == -1)
            self.power(net, ex, ey, "#PWR%02d" % (len([i for i in self.items if "#PWR" in i]) + 1), 180 if flip else 0)
        else:
            angle = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[(dx, dy)]
            self.label(net, ex, ey, angle)

    def frame(self, title, x1, y1, x2, y2):
        """Dashed box around a functional block, with its title inside the top-left corner."""
        self.items.append('\t(rectangle (start %.2f %.2f) (end %.2f %.2f) (stroke (width 0.254) (type dash)) '
                          '(fill (type none)) (uuid "%s"))' % (x1, y1, x2, y2, U()))
        self.text(title, x1 + 1.27, y1 + 1.27, size=2.0)

    def nc(self, key, sx, sy, num):
        x, y, _ = self.pin_end(key, sx, sy, num)
        self.no_connect(x, y)

    def write(self, path, title):
        libs = "\n".join("\t\t" + v.replace("\n", "\n\t\t") for v in self.lib.values())
        body = "\n".join(self.items)
        out = f'''(kicad_sch
	(version 20250114)
	(generator "frutamidi_gen")
	(generator_version "1.0")
	(uuid "{ROOT_UUID}")
	(paper "A3")
	(title_block
		(title "{title}")
		(date "2026-11-09")
		(rev "1.3")
		(company "github.com/catuta0/fruta-midi-controller")
		(comment 1 "Pico + MPR121 (1982), single-sided SMD PCB, copper on component side")
	)
	(lib_symbols
{libs}
	)
{body}
	(sheet_instances (path "/" (page "1")))
	(embedded_fonts no)
)
'''
        open(path, "w", encoding="utf-8").write(out)


# --------------------------------------------------------------------------- circuit

def build():
    """A3 sheet, one dashed frame per functional block. Signal flow left to right:
    Pico -> I2C bus -> MPR121 module -> series resistors -> electrode wire pads."""
    s = Sheet()

    # ------------------------------------------------------------------ Raspberry Pi Pico
    s.frame("1. Microcontroller: Raspberry Pi Pico (castellated)", 30.48, 78.74, 124.46, 190.50)
    s.text("I2C1: SDA = GP26, SCL = GP27 (Wire1).  Button = GP22.\n"
           "Potentiometer = GP28 (ADC2).  Build the firmware with FRUTAMIDI_PCB.", 31.75, 83.82)
    PX, PY = 76.20, 139.70
    pico = s.symbol("MCU_Module", "RaspberryPi_Pico", "A1", "RaspberryPi_Pico", PX, PY,
                    "FrutaMIDI:RaspberryPi_Pico_Castellated_HomeEtch", ref_at=(-17.78, -40.64),
                    fields={"Manufacturer": "Raspberry Pi", "MPN": "SC0915", "Mouser": "358-SC0915"})
    used = {"31": "SDA_PICO", "32": "SCL_PICO", "34": "POT", "33": "AGND", "29": "BTN", "36": "+3V3", "3": "GND"}
    for num, net in used.items():
        s.connect(pico, PX, PY, num, net)
    gnd_pins = {"8", "13", "18", "23", "28", "38"}          # stacked with pin 3 in the symbol
    for num in s.pins[pico]:
        if num not in used and num not in gnd_pins:
            s.nc(pico, PX, PY, num)

    # ------------------------------------------------------------------ I2C bus
    s.frame("2. I2C bus", 132.08, 35.56, 208.28, 91.44)
    s.text("R13/R14: 4.7k pull-ups to 3V3 (rise time at 400 kHz, T-050).\n"
           "R15/R16: 220R between the Pico pins and the bus (wrong-wire current limit, T-055).", 133.35, 40.64)
    PU_FIELDS = {"Manufacturer": "YAGEO", "MPN": "RC1206FR-074K7L", "Mouser": "603-RC1206FR-074K7L"}   # T-096: 4k7 1 % 1206
    for k, net in enumerate(("SCL", "SDA")):
        rx, ry = 144.78 + 10.16 * k, 63.50
        r = s.symbol("Device", "R", "R%d" % (13 + k), "4k7", rx, ry,
                     "FrutaMIDI:R_1206_HomeEtch", fields=PU_FIELDS, ref_at=(2.54, -1.27))
        s.connect(r, rx, ry, "1", "+3V3")
        s.connect(r, rx, ry, "2", net)
    SR_FIELDS = {"Manufacturer": "YAGEO", "MPN": "RC1206FR-07220RL", "Mouser": "603-RC1206FR-07220RL"}   # T-096: 220R 1 % 1206
    for k, net in enumerate(("SCL", "SDA")):
        rx, ry = 180.34, 58.42 + 12.70 * k
        r = s.symbol("Device", "R", "R%d" % (15 + k), "220", rx, ry,
                     "FrutaMIDI:R_1206_HomeEtch", fields=SR_FIELDS, ref_at=(0, -2.54), rot=90)
        s.connect(r, rx, ry, "1", net + "_PICO")
        s.connect(r, rx, ry, "2", net)
    JX, JY = 200.66, 81.28
    j1 = s.symbol("Connector_Generic", "Conn_01x02", "J1", "CFG_SCL_SDA", JX, JY, "FrutaMIDI:Config_2pads_SMD",
                  ref_at=(0, -3.81))
    for num, net in (("1", "SCL"), ("2", "SDA")):
        s.connect(j1, JX, JY, num, net)
    s.text("J1: surface pads, 2 insulated wires", 165.10, 86.36)

    # ------------------------------------------------------------------ MPR121 module, electrodes, terminals
    s.frame("3. Touch sensing: MPR121 module, electrode resistors, electrode wire pads", 213.36, 93.98, 340.36, 187.96)
    MX, MY = 264.16, 139.70
    mod = s.symbol("FrutaMIDI", "Adafruit_MPR121_1982", "A2", "Adafruit_MPR121_1982", MX, MY,
                   "FrutaMIDI:Adafruit_MPR121_1982_SMD", ref_at=(0, -22.86),
                   fields={"Manufacturer": "Adafruit", "MPN": "1982", "Mouser": "485-1982"})
    s.connect(mod, MX, MY, "1", "GND")
    for k, num in enumerate(range(14, 21)):
        s.connect(mod, MX, MY, str(num), "S%d" % (k + 1))   # S1/S7 via JP1; SDA/SCL by hand wire from J1

    # T-050: series resistor per electrode (ESD current limit; 2.7 k <= R <= 3.3 k, sim/electronics/calc).
    # Drawn on the wire between the module pin (net ELEx) and the terminal (net Ex).
    # T-096 / ADR-026: YAGEO RC2512FK-073K3L 3k3 1 %, 1 W, 200 V thick film. Land G 5.0 mm kept. No sourced pulse capability for the
    # IEC or the 1.2/50 us case: NOT PROVEN against 3.6 kV across R at IEC 4 kV (calc_pulse_rated.out).
    R_FIELDS = {"Manufacturer": "YAGEO", "MPN": "RC2512FK-073K3L", "Mouser": "603-RC2512FK-073K3L"}
    TX, TY = 325.12, MY - 2.54                              # terminal pin 2 (E0) level with module pin 2 (E0)
    t = s.symbol("Connector_Generic", "Conn_01x14", "J2", "Electrode wire pads 5.08 mm", TX, TY,
                 "FrutaMIDI:WirePads_1x14_P5.08mm", ref_at=(0, -20.32), in_bom=False)
    for i in range(12):
        mx, my, _ = s.pin_end(mod, MX, MY, str(2 + i))
        rx = 297.18
        r = s.symbol("Device", "R", "R%d" % (i + 1), "3k3", rx, my,
                     "FrutaMIDI:R_2512_HPWC_G5.0mm", fields=R_FIELDS, hide_ref=True,
                     rot=90)              # rows are 2.54 mm apart: designators are given by the column title
        r1x, r1y, _ = s.pin_end(r, rx, my, "1")
        r2x, r2y, _ = s.pin_end(r, rx, my, "2")
        tx, ty, _ = s.pin_end(t, TX, TY, str(2 + i))
        assert abs(r1y - my) < 1e-6 and abs(ty - my) < 1e-6, "electrode row %d not aligned" % i
        s.wire(mx, my, r1x, r1y)
        s.label("ELE%d" % i, mx + 2.54, my, 0)
        s.wire(r2x, r2y, tx, ty)
        s.label("E%d" % i, r2x + 2.54, my, 0)
    s.text("R1 (E0) ... R12 (E11)\n3k3, top to bottom", 289.56, 113.03)
    # GND at both ends of the terminal strip. Pin 1 sits just above the E0 wire, so its GND symbol
    # goes up and is turned over instead of hanging over that wire.
    gx, gy, _ = s.pin_end(t, TX, TY, "1")
    s.wire(gx, gy, gx - 2.54, gy)
    s.wire(gx - 2.54, gy, gx - 2.54, gy - 2.54)
    s.power("GND", gx - 2.54, gy - 2.54, "#PWR91", 180)
    s.connect(t, TX, TY, "14", "GND")

    # Q-row surface wire pads (J3) and the 3V3 selector (JP1)
    QHX, QHY = 231.14, 139.70
    jq = s.symbol("Connector_Generic", "Conn_01x07", "J3", "WIRE_PADS_S1_S7", QHX, QHY,
                  "FrutaMIDI:WirePads_1x07_P2.54mm", in_bom=False, ref_at=(0, -11.43))
    for k in range(7):
        s.connect(jq, QHX, QHY, str(k + 1), "S%d" % (k + 1))
    QX, QY = 233.68, 114.30
    jp = s.symbol("Jumper", "SolderJumper_3_Open", "JP1", "3V3_ORIG_QT", QX, QY,          # turned over: 3V3 on top
                  "FrutaMIDI:SolderJumper_3_SMD_P3.81mm", in_bom=False, ref_at=(0, 3.81), mirror_x=True)
    s.connect(jp, QX, QY, "1", "S1")
    s.connect(jp, QX, QY, "2", "+3V3")
    s.connect(jp, QX, QY, "3", "S7")
    s.text("Module configuration (component side):\n"
           "  Original module (no STEMMA QT):  JP1 bridge 'ORIG' (3V3 -> S1)   wires SDA -> S5   SCL -> S6\n"
           "  STEMMA QT module (current):      JP1 bridge 'QT'   (3V3 -> S7)   wires SDA -> S3   SCL -> S4\n"
           "Module GND enters through the electrode row (pin 1), the same on both revisions.",
           215.90, 165.10)
    s.text("R1-R12: 3.3k in series with each electrode (ESD current limit, ADR-026);\nthick film 2512 1 %, pulse capability not proven, land gap 5.0 mm, no track under the body.", 215.90, 180.34)

    # ------------------------------------------------------------------ user controls and mounting holes
    s.frame("4. User controls and mounting holes", 30.48, 198.12, 124.46, 254.00)
    BX, BY = 50.80, 218.44
    sw = s.symbol("Switch", "SW_Push", "SW1", "B3S-1000", BX, BY, "FrutaMIDI:SW_SPST_B3S-1000_HomeEtch",
                  fields={"Manufacturer": "Omron", "MPN": "B3S-1000", "Mouser": "653-B3S-1000"})
    s.connect(sw, BX, BY, "1", "BTN")
    s.connect(sw, BX, BY, "2", "GND")
    s.text("SCALE button", 45.72, 226.06)
    RX, RY = 96.52, 218.44
    # T-091 / ADR-023 D-2: off-board potentiometer on 3 surface wire pads; no MP pin on the board, the frame is not
    # tied to AGND here (R-011, reports/electronics).
    rv = s.symbol("Device", "R_Potentiometer", "RV1", "10k lin (B10K)", RX, RY,
                  "FrutaMIDI:WirePads_1x03_P5.08mm", ref_at=(-5.08, -5.08),
                  fields={"Manufacturer": "Bourns", "MPN": "PTV09A-4015F-B103", "Mouser": "652-PTV09A-4015FB103"})   # T-096: 10k linear, insulated flat shaft, off-board on wires
    s.connect(rv, RX, RY, "1", "+3V3")
    s.connect(rv, RX, RY, "2", "POT")
    s.connect(rv, RX, RY, "3", "AGND")
    s.text("OCTAVE pot (off-board, 3 wires)", 101.60, 223.52)
    # T-091 / ADR-023: C1 100 nF 1206 X7R 50 V wiper filter, near the Pico (datasheet not opened)
    CX, CY = 111.76, 236.22
    c1 = s.symbol("Device", "C", "C1", "100n X7R 50V", CX, CY, "FrutaMIDI:C_1206_HomeEtch",
                  ref_at=(2.54, -1.27), fields={"Manufacturer": "Samsung", "MPN": "CL31B104KBCNNNC", "Mouser": "187-CL31B104KBCNNNC"})
    s.connect(c1, CX, CY, "1", "POT")
    s.connect(c1, CX, CY, "2", "AGND")
    s.text("C1: wiper to AGND, near Pico", 88.90, 243.84)
    for k in range(4):
        s.symbol("Mechanical", "MountingHole", "H%d" % (k + 1), "M3", 43.18 + 12.70 * k, 243.84,
                 "FrutaMIDI:MountingHole_3.2mm_M3", in_bom=False)

    s.write(os.path.join(HW, PROJECT + ".kicad_sch"), "FrutaMIDI — capacitive MIDI controller")

    # Project symbol library
    lib = '(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "frutamidi_gen")\n\t' + \
          module_symbol("Adafruit_MPR121_1982").replace("\n", "\n\t") + "\n)\n"
    open(os.path.join(HW, "FrutaMIDI.kicad_sym"), "w", encoding="utf-8").write(lib)


if __name__ == "__main__":
    build()
    print("ok")
