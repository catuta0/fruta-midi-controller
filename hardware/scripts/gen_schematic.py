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
		(property "Footprint" "FrutaMIDI:Adafruit_MPR121_1982_Socket" (at 0 -25.4 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Datasheet" "https://www.adafruit.com/product/1982" (at 0 -27.94 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Description" "Adafruit MPR121 breakout (1982), original or STEMMA QT, socketed" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
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

    def symbol(self, lib, name, ref, value, x, y, footprint, fields=None, hide_ref=False, in_bom=True, ref_at=(0, -3.0)):
        key = self.use(lib, name)
        sid = det_uuid("sym", ref)
        pin_uuids = "".join('\n\t\t(pin "%s" (uuid "%s"))' % (n, det_uuid("pin", ref, n)) for n in self.pins[key])
        ref_hide = " (hide yes)" if hide_ref else ""
        extra = ""
        for k, v in (fields or {}).items():
            extra += '\n\t\t(property "%s" "%s" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (hide yes)))' % (k, v, x, y)
        self.items.append(f'''	(symbol
		(lib_id "{key}")
		(at {x:.2f} {y:.2f} 0)
		(unit 1)
		(exclude_from_sim no) (in_bom {"yes" if in_bom else "no"}) (on_board yes) (dnp no)
		(uuid "{sid}")
		(property "Reference" "{ref}" (at {x + ref_at[0]:.2f} {y + ref_at[1]:.2f} 0) (effects (font (size 1.27 1.27)){ref_hide}))
		(property "Value" "{value}" (at {x:.2f} {y + 3.0:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Footprint" "{footprint}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Datasheet" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Description" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes))){extra}{pin_uuids}
		(instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))
	)''')
        return key

    def pin_end(self, key, sx, sy, num):
        px, py, a, _ = self.pins[key][num]
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

    def power(self, name, x, y, ref):
        key = self.use("power", name)
        self.items.append(f'''	(symbol
		(lib_id "{key}") (at {x:.2f} {y:.2f} 0) (unit 1)
		(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
		(uuid "{det_uuid('pwr', ref)}")
		(property "Reference" "{ref}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Value" "{name}" (at {x:.2f} {y + (3.81 if name == 'GND' else -3.81):.2f} 0) (effects (font (size 1.27 1.27))))
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
            self.power(net, ex, ey, "#PWR%02d" % (len([i for i in self.items if "#PWR" in i]) + 1))
        else:
            angle = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[(dx, dy)]
            self.label(net, ex, ey, angle)

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
	(paper "A4")
	(title_block
		(title "{title}")
		(date "2026-10-30")
		(rev "1.1")
		(company "github.com/catuta0/fruta-midi-controller")
		(comment 1 "Raspberry Pi Pico + Adafruit MPR121 (1982), single-sided PCB")
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
    s = Sheet()

    # Raspberry Pi Pico (socketed)
    PX, PY = 101.6, 101.6
    pico = s.symbol("MCU_Module", "RaspberryPi_Pico", "A1", "RaspberryPi_Pico", PX, PY,
                    "FrutaMIDI:RaspberryPi_Pico_Socket", ref_at=(-12.7, -40.64))
    used = {"31": "SDA_PICO", "32": "SCL_PICO", "34": "POT", "33": "AGND", "29": "BTN", "36": "+3V3", "3": "GND"}
    for num, net in used.items():
        s.connect(pico, PX, PY, num, net)
    gnd_pins = {"8", "13", "18", "23", "28", "38"}          # stacked with pin 3 in the symbol
    for num in s.pins[pico]:
        if num not in used and num not in gnd_pins:
            s.nc(pico, PX, PY, num)

    # MPR121 module (socketed): electrodes on the right, power/I2C row on the left
    MX, MY = 190.5, 96.52
    mod = s.symbol("FrutaMIDI", "Adafruit_MPR121_1982", "A2", "Adafruit_MPR121_1982", MX, MY,
                   "FrutaMIDI:Adafruit_MPR121_1982_Socket", ref_at=(0, -22.86))
    s.connect(mod, MX, MY, "1", "GND")
    for i in range(12):
        s.connect(mod, MX, MY, str(2 + i), "ELE%d" % i)       # MPR121 side of the series resistor

    # T-050: series resistor per electrode (ESD current limit; value from sim/electronics/calc/sim_electrode.py
    # and calc_esd_variants.py: 2.7 k <= R <= 3.3 k). Terminal side keeps the net names E0..E11.
    R_FIELDS = {"Manufacturer": "Yageo", "MPN": "MFR-12FTF52-3K3"}
    for i in range(12):
        rx, ry = 165.10 + 7.62 * i, 40.64
        r = s.symbol("Device", "R", "R%d" % (i + 1), "3k3", rx, ry,
                     "FrutaMIDI:R_Axial_DIN0204_P2.54mm_Vertical_HomeEtch", fields=R_FIELDS, ref_at=(2.54, -1.27))
        s.connect(r, rx, ry, "1", "ELE%d" % i)
        s.connect(r, rx, ry, "2", "E%d" % i)

    # T-050: I2C pull-ups on the Pico side (in parallel with the module's 10k): rise time, calc_i2c.py
    PU_FIELDS = {"Manufacturer": "Yageo", "MPN": "MFR-12FTF52-4K7"}
    for k, net in enumerate(("SCL", "SDA")):
        rx, ry = 134.62 + 7.62 * k, 40.64
        r = s.symbol("Device", "R", "R%d" % (13 + k), "4k7", rx, ry,
                     "FrutaMIDI:R_Axial_DIN0204_P2.54mm_Vertical_HomeEtch", fields=PU_FIELDS, ref_at=(2.54, -1.27))
        s.connect(r, rx, ry, "1", "+3V3")
        s.connect(r, rx, ry, "2", net)

    # T-055 / ADR-009 D-9: 220R in series between each Pico I2C pin and the bus (J1 hole + pull-ups).
    # A hand wire misplaced onto a supply pin then limits the Pico pin current to <= 15.5 mA (calc_i2c_series.py);
    # the pull-ups stay on the bus side, so the module's low level reaches the Pico without an I*R drop.
    SR_FIELDS = {"Manufacturer": "Yageo", "MPN": "MFR-12FTF52-220R"}
    for k, net in enumerate(("SCL", "SDA")):
        rx, ry = 149.86 + 7.62 * k, 40.64
        r = s.symbol("Device", "R", "R%d" % (15 + k), "220", rx, ry,
                     "FrutaMIDI:R_Axial_DIN0204_P2.54mm_Vertical_HomeEtch", fields=SR_FIELDS, ref_at=(2.54, -1.27))
        s.connect(r, rx, ry, "1", net + "_PICO")
        s.connect(r, rx, ry, "2", net)
    for k, num in enumerate(range(14, 21)):
        s.connect(mod, MX, MY, str(num), "S%d" % (k + 1))   # S1/S7 via JP1; SDA/SCL by hand wire from J1 (see note)

    # Configuration holes for the two I2C wires (T-052 / D-4: 3V3 is no longer a free wire)
    JX, JY = 152.4, 63.5
    j1 = s.symbol("Connector_Generic", "Conn_01x02", "J1", "CFG_SCL_SDA", JX, JY, "FrutaMIDI:Config_2pads")
    for num, net in (("1", "SCL"), ("2", "SDA")):
        s.connect(j1, JX, JY, num, net)

    # 3V3 selector (T-052 / D-4): centre = +3V3, side A -> S1 (VIN, original), side B -> S7 (VCC, STEMMA QT).
    # A wrong choice lands on ADDR (QT) or IRQ (original): no short circuit.
    QX, QY = 165.1, 63.5
    jp = s.symbol("Jumper", "SolderJumper_3_Open", "JP1", "3V3_ORIG_QT", QX, QY,
                  "FrutaMIDI:SolderJumper_3_THT_P2.54mm", in_bom=False, ref_at=(0, -3.81))
    s.connect(jp, QX, QY, "1", "S1")
    s.connect(jp, QX, QY, "2", "+3V3")
    s.connect(jp, QX, QY, "3", "S7")

    # Screw terminals (7 interlocked 2-way blocks): GND, E0..E11, GND
    TX, TY = 262.89, 96.52
    t = s.symbol("Connector", "Screw_Terminal_01x14", "J2", "Screw terminals 5.08 mm (7x 2-way)", TX, TY,
                 "FrutaMIDI:TerminalBlock_5.08_1x14", ref_at=(0, -20.32))
    for i in range(12):
        s.connect(t, TX, TY, str(2 + i), "E%d" % i)
    (x1, y1, _), (x14, y14, _) = s.pin_end(t, TX, TY, "1"), s.pin_end(t, TX, TY, "14")
    bus = x1 - 12.7
    s.wire(x1, y1, bus, y1)
    s.wire(x14, y14, bus, y14)
    s.wire(bus, y1, bus, y14)
    s.wire(bus, y14, bus, y14 + 2.54)
    s.power("GND", bus, y14 + 2.54, "#PWR%02d" % 90)

    # Button (scale / recalibrate)
    BX, BY = 63.5, 160.02
    sw = s.symbol("Switch", "SW_Push", "SW1", "SW_Push_6mm", BX, BY, "FrutaMIDI:SW_PUSH_6mm")
    s.connect(sw, BX, BY, "1", "BTN")
    s.connect(sw, BX, BY, "2", "GND")

    # Octave potentiometer
    RX, RY = 101.6, 160.02
    rv = s.symbol("Device", "R_Potentiometer", "RV1", "10k lin (B10K)", RX, RY, "FrutaMIDI:Potentiometer_RK09K_Vertical", ref_at=(-5.08, -1.27))
    s.connect(rv, RX, RY, "1", "+3V3")
    s.connect(rv, RX, RY, "2", "POT")
    s.connect(rv, RX, RY, "3", "AGND")

    # M3 mounting holes
    for k in range(4):
        s.symbol("Mechanical", "MountingHole", "H%d" % (k + 1), "M3", 20.32 + 10.16 * k, 185.42,
                 "FrutaMIDI:MountingHole_3.2mm_M3", in_bom=False)

    s.text("Module configuration (component side):\n"
           "  Original module (no STEMMA QT):  JP1 bridge 'ORIG' (3V3 -> S1)   wires SDA -> S5   SCL -> S6\n"
           "  STEMMA QT module (current):      JP1 bridge 'QT'   (3V3 -> S7)   wires SDA -> S3   SCL -> S4\n"
           "Module GND enters through the electrode row (pin 1), the same on both revisions.",
           127.0, 135.0)
    s.text("R1-R12: 3.3k in series with each electrode (ESD current limit, T-050).\n"
           "R13/R14: 4.7k I2C pull-ups to 3V3 on the bus side (rise time at 400 kHz, T-050).\n"
           "R15/R16: 220R between the Pico I2C pins and the bus (wrong-wire current limit, T-055).",
           134.62, 50.8)
    s.text("I2C1: SDA = GP26, SCL = GP27 (Wire1).  Button = GP22.  Potentiometer = GP28 (ADC2).\n"
           "Firmware: build with FRUTAMIDI_PCB defined (see firmware/).", 20.32, 25.4)

    s.write(os.path.join(HW, PROJECT + ".kicad_sch"), "FrutaMIDI — capacitive MIDI controller")

    # Project symbol library
    lib = '(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "frutamidi_gen")\n\t' + \
          module_symbol("Adafruit_MPR121_1982").replace("\n", "\n\t") + "\n)\n"
    open(os.path.join(HW, "FrutaMIDI.kicad_sym"), "w", encoding="utf-8").write(lib)


if __name__ == "__main__":
    build()
    print("ok")
