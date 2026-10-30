#!/usr/bin/env python3
"""Gera hardware/frutamidi.kicad_sch e a biblioteca de símbolos do projeto.

Corre com qualquer Python 3 que veja as bibliotecas do KiCad:
    python3 hardware/scripts/gen_schematic.py
"""
import os, re, uuid, sys

KICAD_SYMBOLS = os.environ.get(
    "KICAD_SYMBOL_DIR", "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")
HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT = "frutamidi"
U = lambda: str(uuid.uuid4())
ROOT_UUID = "6f3c2a52-6b1e-4d8e-9a43-3f6a0c1d2e01"   # fixo: os caminhos da PCB dependem dele


def det_uuid(*parts):
    """UUID determinístico, para que regenerar não mude as ligações com a PCB."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "frutamidi/" + "/".join(parts)))


# --------------------------------------------------------------------------- bibliotecas

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


# Símbolo próprio: módulo Adafruit 1982 (MPR121) visto como socket.
# Fila de elétrodos (1-13) igual nas duas versões; fila de alimentação (14-20) depende da versão.
MODULE_PINS = [
    # (número, nome, x, y, ângulo) — nomes da fila S: "versão original / versão STEMMA QT"
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
		(property "Description" "Breakout Adafruit MPR121 (1982), original ou STEMMA QT, em socket" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(symbol "Adafruit_MPR121_1982_0_1"
			(rectangle (start -15.24 17.78) (end 15.24 -20.32) (stroke (width 0.254) (type default)) (fill (type background)))
		)
		(symbol "Adafruit_MPR121_1982_1_1"{pins}
		)
	)'''


def rename_for_schematic(sym_text, lib, name):
    return sym_text.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (lib, name), 1)


# --------------------------------------------------------------------------- desenho

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
        """Fio curto a sair do pino + etiqueta/alimentação na ponta."""
        x, y, a = self.pin_end(key, sx, sy, num)
        # direção para fora: ângulo do pino aponta para o corpo
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
		(rev "1.0")
		(company "github.com/catuta0/fruta-midi-controller")
		(comment 1 "Raspberry Pi Pico + Adafruit MPR121 (1982), PCB de uma face")
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


# --------------------------------------------------------------------------- circuito

def build():
    s = Sheet()

    # Raspberry Pi Pico (em socket)
    PX, PY = 101.6, 101.6
    pico = s.symbol("MCU_Module", "RaspberryPi_Pico", "A1", "RaspberryPi_Pico", PX, PY,
                    "FrutaMIDI:RaspberryPi_Pico_Socket", ref_at=(-12.7, -40.64))
    used = {"31": "SDA", "32": "SCL", "34": "POT", "33": "AGND", "29": "BTN", "36": "+3V3", "3": "GND"}
    for num, net in used.items():
        s.connect(pico, PX, PY, num, net)
    gnd_pins = {"8", "13", "18", "23", "28", "38"}          # empilhados com o 3 no símbolo
    for num in s.pins[pico]:
        if num not in used and num not in gnd_pins:
            s.nc(pico, PX, PY, num)

    # Módulo MPR121 (socket) — elétrodos à direita, fila de alimentação à esquerda
    MX, MY = 190.5, 96.52
    mod = s.symbol("FrutaMIDI", "Adafruit_MPR121_1982", "A2", "Adafruit_MPR121_1982", MX, MY,
                   "FrutaMIDI:Adafruit_MPR121_1982_Socket", ref_at=(0, -22.86))
    s.connect(mod, MX, MY, "1", "GND")
    for i in range(12):
        s.connect(mod, MX, MY, str(2 + i), "E%d" % i)
    for k, num in enumerate(range(14, 21)):
        s.connect(mod, MX, MY, str(num), "S%d" % (k + 1))   # ligados por fio a J1 conforme a versão (ver nota)

    # Pads de configuração (3 furos ligados ao Pico)
    JX, JY = 152.4, 63.5
    j1 = s.symbol("Connector_Generic", "Conn_01x03", "J1", "CFG_3V3_SCL_SDA", JX, JY, "FrutaMIDI:Config_3pads")
    for num, net in (("1", "+3V3"), ("2", "SCL"), ("3", "SDA")):
        s.connect(j1, JX, JY, num, net)

    # Terminais de parafuso (7 blocos de 2 vias encaixados): GND, E0…E11, GND
    TX, TY = 262.89, 96.52
    t = s.symbol("Connector", "Screw_Terminal_01x14", "J2", "Terminais 5,08 mm (7x 2 vias)", TX, TY,
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

    # Botão (escala / recalibrar)
    BX, BY = 63.5, 160.02
    sw = s.symbol("Switch", "SW_Push", "SW1", "SW_Push_6mm", BX, BY, "FrutaMIDI:SW_PUSH_6mm")
    s.connect(sw, BX, BY, "1", "BTN")
    s.connect(sw, BX, BY, "2", "GND")

    # Potenciómetro de oitava
    RX, RY = 101.6, 160.02
    rv = s.symbol("Device", "R_Potentiometer", "RV1", "10k lin (B10K)", RX, RY, "FrutaMIDI:Potentiometer_RK09K_Vertical", ref_at=(-5.08, -1.27))
    s.connect(rv, RX, RY, "1", "+3V3")
    s.connect(rv, RX, RY, "2", "POT")
    s.connect(rv, RX, RY, "3", "AGND")

    # Furos de fixação M3
    for k in range(4):
        s.symbol("Mechanical", "MountingHole", "H%d" % (k + 1), "M3", 20.32 + 10.16 * k, 185.42,
                 "FrutaMIDI:MountingHole_3.2mm_M3", in_bom=False)

    s.text("Fios de configuração (lado dos componentes), de J1 para a fila S do módulo:\n"
           "  Módulo original (sem STEMMA QT):  3V3 -> S1   SDA -> S5   SCL -> S6\n"
           "  Módulo STEMMA QT (atual):         3V3 -> S7   SDA -> S3   SCL -> S4\n"
           "O GND do módulo entra pela fila dos elétrodos (pino 1), igual nas duas versões.",
           127.0, 135.0)
    s.text("I2C1: SDA = GP26, SCL = GP27 (Wire1).  Botão = GP22.  Potenciómetro = GP28 (ADC2).\n"
           "Firmware: compilar com FRUTAMIDI_PCB definido (ver firmware/).", 20.32, 25.4)

    s.write(os.path.join(HW, PROJECT + ".kicad_sch"), "FrutaMIDI — controlador MIDI capacitivo")

    # Biblioteca de símbolos do projeto
    lib = '(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "frutamidi_gen")\n\t' + \
          module_symbol("Adafruit_MPR121_1982").replace("\n", "\n\t") + "\n)\n"
    open(os.path.join(HW, "FrutaMIDI.kicad_sym"), "w", encoding="utf-8").write(lib)


if __name__ == "__main__":
    build()
    print("ok")
