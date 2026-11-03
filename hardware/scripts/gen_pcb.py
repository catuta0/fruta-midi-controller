#!/usr/bin/env python3
"""Generates the footprint library (FrutaMIDI.pretty) and the single-sided PCB (frutamidi.kicad_pcb).

Runs with the KiCad Python (needs the pcbnew module), after gen_schematic.py:
    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
        hardware/scripts/gen_pcb.py

Rules chosen for home chemical etching (toner transfer or photoresist):
  tracks >= 1.0 mm, clearance >= 0.6 mm, large pads (annular ring >= 0.4 mm), no vias, copper on the bottom only.
"""
import os, re, shutil, subprocess, sys, uuid
import pcbnew

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
KICAD = os.environ.get("KICAD_SHARED", "/Applications/KiCad/KiCad.app/Contents/SharedSupport")
KICAD_CLI = os.environ.get("KICAD_CLI", "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
FP_LIB = os.path.join(HW, "FrutaMIDI.pretty")
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))


def det_uuid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "frutamidi/" + "/".join(parts)))


# =========================================================================== footprints

def lib_fp(lib, name):
    return pcbnew.FootprintLoad(os.path.join(KICAD, "footprints", lib + ".pretty"), name)


def set_pad(p, shape, w, h, drill=None):
    try:
        p.SetShape(shape)
    except TypeError:
        p.SetShape(pcbnew.F_Cu, shape)
    p.SetSize(V(w, h))
    if drill:
        p.SetDrillSize(V(drill, drill))


def new_fp(name, descr):
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", name))
    fp.SetLibDescription(descr)
    fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
    fp.Reference().SetLayer(pcbnew.F_SilkS)
    fp.Value().SetLayer(pcbnew.F_Fab)
    return fp


def add_pad(fp, num, x, y, shape, w, h, drill):
    p = pcbnew.PAD(fp)
    p.SetNumber(num)
    p.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    p.SetLayerSet(pcbnew.PAD.PTHMask())
    set_pad(p, shape, w, h, drill)
    p.SetPosition(V(x, y))
    fp.Add(p)
    return p


def add_line(fp, layer, x1, y1, x2, y2, w=0.15):
    s = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(layer)
    s.SetStart(V(x1, y1))
    s.SetEnd(V(x2, y2))
    s.SetWidth(mm(w))
    fp.Add(s)


def add_rect(fp, layer, x1, y1, x2, y2, w=0.15):
    for a, b, c, d in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)):
        add_line(fp, layer, a, b, c, d, w)


def add_text(fp, txt, x, y, layer=pcbnew.F_SilkS, size=1.0):
    t = pcbnew.PCB_TEXT(fp)
    t.SetText(txt)
    t.SetLayer(layer)
    t.SetPosition(V(x, y))
    t.SetTextSize(V(size, size))
    t.SetTextThickness(mm(size * 0.15))
    fp.Add(t)


def replace_layer(fp, layer):
    for item in list(fp.GraphicalItems()):
        if item.GetLayer() == layer and item.GetClass() != "PCB_FIELD":
            fp.Remove(item)


def replace_courtyard(fp, pts):
    for item in list(fp.GraphicalItems()):
        if item.GetLayer() == pcbnew.F_CrtYd:
            fp.Remove(item)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        add_line(fp, pcbnew.F_CrtYd, x1, y1, x2, y2, 0.05)


def add_model(fp, path, offset=(0, 0, 0), rot=(0, 0, 0)):
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = path
    m.m_Offset = pcbnew.VECTOR3D(*offset)
    m.m_Rotation = pcbnew.VECTOR3D(*rot)
    fp.Add3DModel(m)


def build_footprints():
    if os.path.isdir(FP_LIB):
        shutil.rmtree(FP_LIB)
    os.makedirs(FP_LIB)
    OVAL, CIRC, RECT, RRECT = pcbnew.PAD_SHAPE_OVAL, pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_RECTANGLE, pcbnew.PAD_SHAPE_ROUNDRECT
    out = {}

    # --- Raspberry Pi Pico on two 1x20 female headers (origin = pin 1, USB up)
    # T-052 / REQ-029: oval pads 2.4 x 1.8 mm, drill 1.0 -> ring 0.4 mm; pad gap on 2.54 mm pitch = 0.74 mm
    fp = new_fp("RaspberryPi_Pico_Socket", "Raspberry Pi Pico / Pico 2 / W on two 1x20 female headers, oval pads for home etching")
    for k in range(1, 21):
        add_pad(fp, str(k), 0, (k - 1) * 2.54, RECT if k == 1 else OVAL, 2.4, 1.8, 1.0)
        add_pad(fp, str(41 - k), 17.78, (k - 1) * 2.54, OVAL, 2.4, 1.8, 1.0)
    add_rect(fp, pcbnew.F_SilkS, -1.61, -1.37, 19.39, 49.63)
    add_rect(fp, pcbnew.F_SilkS, 5.39, -1.37, 12.39, 3.5)                 # USB connector
    add_text(fp, "USB", 8.89, 5.2, size=1.2)
    add_text(fp, "1", -2.6, 0, size=1.0)
    add_rect(fp, pcbnew.F_CrtYd, -2.0, -1.8, 19.8, 50.0, 0.05)
    add_rect(fp, pcbnew.F_Fab, -1.61, -1.37, 19.39, 49.63, 0.1)
    for model in lib_fp("Module", "RaspberryPi_Pico_Common_THT").Models():
        fp.Add3DModel(model)
    out["RaspberryPi_Pico_Socket"] = fp

    # --- Adafruit MPR121 (1982) on female headers: 1x13 (electrodes) + 1x7 (power/I2C)
    # Orientation: rotated 180 deg from the Adafruit Eagle files, electrodes at the bottom.
    # Pads 14-20 repeated higher up (Q row): holes for the configuration wires / jumper links.
    # T-052 / REQ-029: header pads 1.8 x 2.4 mm, drill 1.0 -> ring 0.4 mm; gap on 2.54 mm pitch = 0.74 mm
    fp = new_fp("Adafruit_MPR121_1982_Socket",
                "Adafruit MPR121 breakout (1982, original or STEMMA QT) on 1x13 + 1x7 female headers; Q row for configuration")
    for j in range(13):
        add_pad(fp, str(1 + j), -15.24 + 2.54 * j, 8.255, RECT if j == 0 else OVAL, 1.8, 2.4, 1.0)
    for k in range(7):
        x = -7.62 + 2.54 * k
        add_pad(fp, str(14 + k), x, -6.985, OVAL, 1.8, 2.4, 1.0)
        add_pad(fp, str(14 + k), x, -12.065, CIRC, 1.8, 1.8, 0.9)
        add_text(fp, "S%d" % (k + 1), x, -14.4, size=0.9)
    add_rect(fp, pcbnew.F_SilkS, -16.51, -9.525, 16.51, 10.0)
    add_text(fp, "MPR121 (Adafruit 1982)", 0, 0.6, size=1.2)
    add_text(fp, "GND E0 ... E11", 0, 3.4, size=0.9)
    replace_courtyard(fp, [(-17.0, -9.9), (-8.6, -9.9), (-8.6, -13.2), (8.6, -13.2), (8.6, -9.9),
                           (17.0, -9.9), (17.0, 10.0), (-17.0, 10.0)])
    add_rect(fp, pcbnew.F_Fab, -16.51, -9.525, 16.51, 9.525, 0.1)
    sock = "${KICAD10_3DMODEL_DIR}/Connector_PinSocket_2.54mm.3dshapes/PinSocket_1x%02d_P2.54mm_Vertical.wrl"
    add_model(fp, sock % 13, offset=(-15.24, -8.255, 0), rot=(0, 0, -90))
    add_model(fp, sock % 7, offset=(-7.62, 6.985, 0), rot=(0, 0, -90))
    out["Adafruit_MPR121_1982_Socket"] = fp

    # --- 2 holes for the I2C configuration wires (T-052: 3V3 moved to the JP1 solder jumper)
    fp = new_fp("Config_2pads", "2 holes for the configuration wires: SCL (pad 1), SDA (pad 2)")
    for k, lab in enumerate(("SCL", "SDA")):
        add_pad(fp, str(1 + k), 3.81 * k, 0, RECT if k == 0 else CIRC, 2.2, 2.2, 0.9)
        add_text(fp, lab, 3.81 * k, -2.3, size=0.9)
    add_rect(fp, pcbnew.F_CrtYd, -1.6, -3.2, 5.41, 1.6, 0.05)
    out["Config_2pads"] = fp

    # --- 3-way selector jumper, through-hole (T-052 / D-4): pad 1 = S1 (ORIG), 2 = 3V3 (centre), 3 = S7 (QT).
    # Close with a solder bridge or a lead off-cut across 1-2 or 2-3. Pads 1.94 x 2.4 mm, drill 0.8 (ring 0.57),
    # pad gap 0.60 mm (= clearance rule). Through-hole, so REQ-027 (no SMD pads) still holds.
    fp = new_fp("SolderJumper_3_THT_P2.54mm", "3-way selector jumper, THT pads 2.54 mm pitch, bridge 1-2 or 2-3")
    for k in range(3):
        add_pad(fp, str(1 + k), 2.54 * k, 0, RECT, 1.94, 2.4, 0.8)
    add_rect(fp, pcbnew.F_SilkS, -1.3, -1.55, 6.38, 1.55, 0.12)
    add_rect(fp, pcbnew.F_CrtYd, -1.22, -1.45, 6.30, 1.45, 0.05)
    add_rect(fp, pcbnew.F_Fab, -1.0, -1.2, 6.08, 1.2, 0.1)
    fp.SetExcludedFromBOM(True)                    # copper only, nothing to buy (matches the symbol)
    out["SolderJumper_3_THT_P2.54mm"] = fp

    # --- Screw terminal 5.08 mm (larger pads)
    fp = lib_fp("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "TerminalBlock_5.08_1x02"))
    for p in fp.Pads():
        set_pad(p, RECT if p.GetNumber() == "1" else CIRC, 3.0, 3.0, 1.3)
    # blocks butt against each other (continuous 5.08 pitch): courtyard = exact block width
    replace_courtyard(fp, [(-2.52, -5.7), (7.6, -5.7), (7.6, 5.0), (-2.52, 5.0)])
    replace_layer(fp, pcbnew.F_SilkS)
    add_rect(fp, pcbnew.F_SilkS, -2.3, -5.4, 7.38, 4.4)
    add_line(fp, pcbnew.F_SilkS, -2.3, 2.6, 7.38, 2.6)          # front (wire entry)
    out["TerminalBlock_5.08_1x02"] = fp

    # --- 14 ways = 7 interlocked 2-way blocks (pin 1 on the left)
    fp = new_fp("TerminalBlock_5.08_1x14", "7 interlocked 2-way screw terminal blocks, 5.08 mm pitch")
    for i in range(14):
        add_pad(fp, str(i + 1), 5.08 * i, 0, RECT if i == 0 else CIRC, 3.0, 3.0, 1.3)
    for b in range(7):
        x0 = 10.16 * b
        add_rect(fp, pcbnew.F_SilkS, x0 - 2.3, -5.4, x0 + 7.38, 4.4)
        add_line(fp, pcbnew.F_SilkS, x0 - 2.3, 2.6, x0 + 7.38, 2.6)
        add_model(fp, "${KICAD10_3DMODEL_DIR}/TerminalBlock_Phoenix.3dshapes/"
                      "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal.step", offset=(x0, 0, 0))
    add_rect(fp, pcbnew.F_CrtYd, -2.6, -5.7, 68.7, 5.0, 0.05)
    add_rect(fp, pcbnew.F_Fab, -2.54, -5.2, 68.58, 4.6, 0.1)
    out["TerminalBlock_5.08_1x14"] = fp

    # --- 6 mm push button
    fp = lib_fp("Button_Switch_THT", "SW_PUSH_6mm")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "SW_PUSH_6mm"))
    for p in fp.Pads():
        set_pad(p, CIRC, 2.4, 2.4, 1.1)
    fp.SetDuplicatePadNumbersAreJumpers(True)     # legs with the same number are joined inside the switch
    out["SW_PUSH_6mm"] = fp

    # --- 9 mm potentiometer (Alps RK09K and compatibles), vertical
    # T-052 / REQ-029: 2.6 x 1.8 mm pads, drill 1.0 -> ring 0.4 mm; gap on 2.5 mm pitch = 0.7 mm
    fp = lib_fp("Potentiometer_THT", "Potentiometer_Alps_RK09K_Single_Vertical")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "Potentiometer_RK09K_Vertical"))
    for p in fp.Pads():
        if p.GetNumber() in ("1", "2", "3"):
            set_pad(p, RECT if p.GetNumber() == "1" else OVAL, 2.6, 1.8, 1.0)
    out["Potentiometer_RK09K_Vertical"] = fp

    # --- Resistor 0204 mounted vertical, 2.54 mm pitch (T-050: electrode series R and I2C pull-ups)
    # Pads enlarged for home etching: 1.6 mm pad, 0.8 mm drill (annular ring 0.4 mm); lead 0.45-0.5 mm (Yageo MFR-12).
    fp = lib_fp("Resistor_THT", "R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "R_Axial_DIN0204_P2.54mm_Vertical_HomeEtch"))
    for p in fp.Pads():
        set_pad(p, CIRC, 1.6, 1.6, 0.8)
    out["R_Axial_DIN0204_P2.54mm_Vertical_HomeEtch"] = fp

    # --- M3 hole
    fp = lib_fp("MountingHole", "MountingHole_3.2mm_M3")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "MountingHole_3.2mm_M3"))
    out["MountingHole_3.2mm_M3"] = fp

    io = pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    for name, fp in out.items():
        io.FootprintSave(FP_LIB, fp)
    return out


# =========================================================================== netlist

def read_netlist():
    sch = os.path.join(HW, "frutamidi.kicad_sch")
    net_path = os.path.join(HW, "build", "frutamidi.net")
    os.makedirs(os.path.dirname(net_path), exist_ok=True)
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net_path, sch],
                   check=True, capture_output=True)
    t = open(net_path, encoding="utf-8").read()
    comps = {}
    for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)\s+\(value "([^"]*)"\)\s+\(footprint "([^"]*)"\)', t):
        comps[m.group(1)] = (m.group(2), m.group(3))
    # user fields (BOM data such as Manufacturer / MPN) to copy onto the footprints (schematic parity)
    comp_fields = {}
    for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)\(libsource', t, re.S):
        f = dict(re.findall(r'\(field\s+\(name "([^"]+)"\)\s+"([^"]*)"\)', m.group(2)))
        comp_fields[m.group(1)] = {k: v for k, v in f.items() if k not in ("Footprint", "Datasheet", "Description")}
    read_netlist.fields = comp_fields
    pin_net = {}
    for m in re.finditer(r'\(name "([^"]+)"\)\s*\(class', t):
        start = m.end()
        end = t.find("(net", start)
        seg = t[start:end if end > 0 else len(t)]
        for ref, pin in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', seg):
            pin_net[(ref, pin)] = m.group(1)
    return comps, pin_net


# =========================================================================== board

W, H = 100.0, 70.0
PICO = (4.5, 2.0)                 # pin 1
POT = (28.0, 12.16)               # potentiometer pin 1
BTN = (27.0, 29.94)               # pad 1 (top-left corner)
MOD_C = (57.48, 32.745)           # module centre
CFG = (44.0, 15.0)                # J1 pad 1 (SCL); pad 2 (SDA) at +3.81 mm
T0, TY = 27.0, 64.5               # first terminal (GND), terminal row
HOLES = [(8.0, 64.0), (95.0, 5.0), (95.0, 48.0), (70.0, 6.0)]

W_SIG, W_PWR, W_STUB = 1.0, 1.2, 0.8

# T-050 resistors (0204 vertical, pad 1 = footprint origin, pad 2 2.54 mm below after rotation)
R_Y1 = 44.6               # pad 1 row of the electrode series resistors (module e-row pads at y = 41.0)
R_STUB = 1.0              # straight drop below pad 2 before the 45° fan-out (keeps 0.6 mm to the next pad)
R_ROT_DOWN = -90          # orientation that puts pad 2 below pad 1 (checked by check_vertical)
PU_SCL = (44.0, 6.0)      # R13 pad 1 on the 3V3 track (y = 6); pad 2 drops onto the SCL hole of J1
PU_SDA = (47.81, 6.0)     # R14 pad 1 on the 3V3 track (y = 6); pad 2 drops onto the SDA hole of J1
SER_SDA = (27.0, None)    # T-055 R16 pad 1 x on the SDA row (pad 2 at +2.54 mm)
SER_SCL_Y = 21.0          # T-055 R15 pad 1 y on the SCL riser x = 44 (pad 2 2.54 mm above)
JP1 = (51.6, 15.5)        # T-052 selector jumper, pad 1 (ORIG -> S1); pad 2 = 3V3; pad 3 (QT -> S7)

# The board sits away from the sheet corner so a printer at 100 % does not clip anything.
OX, OY = 50.0, 50.0
VB = lambda x, y: V(OX + x, OY + y)


def pico_pin(n):
    x0, y0 = PICO
    if n <= 20:
        return x0, y0 + (n - 1) * 2.54
    return x0 + 17.78, y0 + (40 - n) * 2.54


def mod_e(j):           # j = 0 (GND) .. 12 (E11)
    return MOD_C[0] - 15.24 + 2.54 * j, MOD_C[1] + 8.255


def mod_s(k):           # k = 1 .. 7
    return MOD_C[0] - 7.62 + 2.54 * (k - 1), MOD_C[1] - 6.985


def mod_q(k):
    x, y = mod_s(k)
    return x, y - 5.08


def term(i):            # i = 0 .. 13
    return T0 + 5.08 * i, TY


class Board:
    def __init__(self, path):
        self.b = pcbnew.NewBoard(path)
        self.nets = {}

    def net(self, name):
        if name not in self.nets:
            n = pcbnew.NETINFO_ITEM(self.b, name)
            self.b.Add(n)
            self.nets[name] = n
        return self.nets[name]

    def track(self, pts, net, width=W_SIG):
        n = self.net(net)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            if abs(x1 - x2) < 1e-6 and abs(y1 - y2) < 1e-6:
                continue                                  # skip zero-length segments
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(VB(x1, y1))
            t.SetEnd(VB(x2, y2))
            t.SetWidth(mm(width))
            t.SetLayer(pcbnew.B_Cu)
            t.SetNet(n)
            self.b.Add(t)

    def text(self, s, x, y, layer, size=1.5, mirror=False):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetPosition(VB(x, y))
        t.SetLayer(layer)
        t.SetTextSize(V(size, size))
        t.SetTextThickness(mm(size * 0.18))
        t.SetMirrored(mirror)
        self.b.Add(t)

    def edge(self):
        for a, b, c, d in ((0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)):
            s = pcbnew.PCB_SHAPE(self.b, pcbnew.SHAPE_T_SEGMENT)
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetStart(VB(a, b))
            s.SetEnd(VB(c, d))
            s.SetWidth(mm(0.15))
            self.b.Add(s)


def place(bd, fps, comps, pin_net, ref, x, y, rot=0, ref_at=None):
    value, fpname = comps[ref]
    lib, name = fpname.split(":")
    fp = pcbnew.FootprintLoad(FP_LIB, name)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPath(pcbnew.KIID_PATH("/" + det_uuid("sym", ref)))
    for k, v in getattr(read_netlist, "fields", {}).get(ref, {}).items():
        fp.SetField(k, v)
        fp.GetField(k).SetVisible(False)
    fp.SetPosition(VB(x, y))
    if rot:
        fp.SetOrientationDegrees(rot)
    if ref_at == "hide":
        fp.Reference().SetVisible(False)
    elif ref_at:
        fp.Reference().SetPosition(VB(x + ref_at[0], y + ref_at[1]))
    for p in fp.Pads():
        key = (ref, p.GetNumber())
        if key in pin_net:
            p.SetNet(bd.net(pin_net[key]))
    bd.b.Add(fp)
    return fp


def check_vertical(fp, x, y):
    """Fail the build if pad 2 of a vertical resistor is not 2.54 mm directly below pad 1."""
    pos = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
    p1, p2 = pos["1"], pos["2"]
    want1, want2 = VB(x, y), VB(x, y + 2.54)
    if abs(p1.x - want1.x) > 1000 or abs(p1.y - want1.y) > 1000 or \
       abs(p2.x - want2.x) > 1000 or abs(p2.y - want2.y) > 1000:
        raise SystemExit("resistor %s pads at %s/%s, expected pad 2 below pad 1"
                         % (fp.GetReference(), (p1.x, p1.y), (p2.x, p2.y)))


def build_board():
    comps, pin_net = read_netlist()
    path = os.path.join(HW, "frutamidi.kicad_pcb")
    bd = Board(path)
    bd.edge()
    for n in sorted(set(pin_net.values())):
        bd.net(n)

    place(bd, None, comps, pin_net, "A1", *PICO, ref_at=(8.89, 24.0))
    place(bd, None, comps, pin_net, "A2", *MOD_C, ref_at=(-13.0, -2.5))
    place(bd, None, comps, pin_net, "J1", *CFG, ref_at=(3.81, -4.0))
    place(bd, None, comps, pin_net, "RV1", *POT)
    place(bd, None, comps, pin_net, "SW1", *BTN)
    place(bd, None, comps, pin_net, "J2", *term(0), ref_at="hide")
    for k, (x, y) in enumerate(HOLES):
        place(bd, None, comps, pin_net, "H%d" % (k + 1), x, y, ref_at="hide")

    N = lambda ref, pin: pin_net[(ref, pin)]
    GND, V33 = "GND", "+3V3"

    # --- GND: ladder under the Pico (joins all Pico GND pins) ---------------------------
    xb = PICO[0] + 8.89
    bd.track([(xb, pico_pin(3)[1]), (xb, pico_pin(18)[1])], GND, W_PWR)
    bd.track([pico_pin(3), pico_pin(38)], GND, W_PWR)
    bd.track([pico_pin(8), (xb, pico_pin(8)[1])], GND, W_PWR)
    bd.track([pico_pin(13), pico_pin(28)], GND, W_PWR)
    bd.track([pico_pin(18), pico_pin(23)], GND, W_PWR)

    # --- Potentiometer: 3V3 (pin 1), wiper (2), AGND (3) ----------------------------------
    px, py = POT
    bd.track([pico_pin(36), (25.0, py), (px, py)], V33, W_PWR)
    p34 = pico_pin(34)
    bd.track([p34, (24.0, p34[1]), (24.0 + (p34[1] - (py + 2.5)), py + 2.5), (px, py + 2.5)], N("A1", "34"))
    p33 = pico_pin(33)
    bd.track([p33, (24.6, p33[1]), (24.6 + (p33[1] - (py + 5.0)), py + 5.0), (px, py + 5.0)], N("A1", "33"))

    # --- 3V3 over the potentiometer to the pull-ups and the JP1 centre pad -------------------
    cx, cy = CFG
    jc = (JP1[0] + 2.54, JP1[1])                     # JP1 centre pad (3V3)
    bd.track([(25.0, pico_pin(36)[1]), (25.0, 6.0), (jc[0], 6.0), jc], V33, W_PWR)

    # --- I2C: both come up from below (T-052: J1 = SCL | SDA, so the tracks do not cross) --------
    # T-055: 220R in line, pad 1 = Pico side, pad 2 = bus side (J1 hole + pull-up).
    # R16 (SDA) lies on the SDA row between the Pico and SW1; R15 (SCL) stands on the SCL riser below J1
    # (both outside the module and potentiometer courtyards).
    p31, p32 = pico_pin(31), pico_pin(32)
    place(bd, None, comps, pin_net, "R16", SER_SDA[0], p31[1], ref_at=(1.27, 1.9))
    bd.track([p31, (SER_SDA[0], p31[1])], N("A1", "31"))
    bd.track([(SER_SDA[0] + 2.54, p31[1]), (cx + 3.81, p31[1]), (cx + 3.81, cy)], N("J1", "2"))
    fp = place(bd, None, comps, pin_net, "R15", cx, SER_SCL_Y, rot=90, ref_at=(2.2, -1.27))
    pads = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
    if abs(pads["2"].y - VB(cx, SER_SCL_Y - 2.54).y) > 1000 or abs(pads["2"].x - VB(cx, 0).x) > 1000:
        raise SystemExit("R15 pad 2 is not 2.54 mm above pad 1")
    bd.track([p32, (cx, p32[1]), (cx, SER_SCL_Y)], N("A1", "32"))
    bd.track([(cx, SER_SCL_Y - 2.54), (cx, cy)], N("J1", "1"))

    # --- JP1 3V3 selector: pad 1 -> S1 (original VIN), pad 3 -> S7 (STEMMA QT VCC) ----------------
    place(bd, None, comps, pin_net, "JP1", *JP1, ref_at="hide")
    bd.track([JP1, mod_q(1)], N("A2", "14"), W_PWR)
    s7 = mod_q(7)
    bd.track([(JP1[0] + 5.08, JP1[1]), (s7[0], JP1[1]), s7], N("A2", "20"), W_PWR)

    # --- Module S row joined to the Q row (wire holes) --------------------------------
    for k in range(1, 8):
        bd.track([mod_s(k), mod_q(k)], N("A2", str(13 + k)), W_STUB)

    # --- Button: GP22 (pin 29) and GND (pin 28) -----------------------------------------------
    bx, by = BTN
    bd.track([pico_pin(29), (bx, by)], N("A1", "29"))
    p28 = pico_pin(28)
    bd.track([p28, (24.5, p28[1]), (bx, by + 4.5)], GND, W_PWR)

    # --- Module GND and first terminal, from Pico pin 23 ---------------------------
    g = mod_e(0)
    p23 = pico_pin(23)
    k = g[0] - (p23[1] - g[1])                     # start of the 45 deg climb
    t1 = term(0)
    bd.track([p23, (t1[0], p23[1]), (k, p23[1]), g], GND, W_PWR)
    bd.track([(t1[0], p23[1]), t1], GND, W_PWR)

    # --- Electrodes: module pin -> series R (vertical, directly under the pin) -> 45° fan-out -> terminal
    # T-050. Rj sits in electrode E(j-1); pad 1 (module side, net ELEx) on top, pad 2 (terminal side, net Ex) below.
    for j in range(1, 13):
        ex, ey = mod_e(j)
        tx, ty = term(j)
        fp = place(bd, None, comps, pin_net, "R%d" % j, ex, R_Y1, rot=R_ROT_DOWN, ref_at="hide")
        check_vertical(fp, ex, R_Y1)
        bd.track([(ex, ey), (ex, R_Y1)], N("A2", str(1 + j)))
        y0 = R_Y1 + 2.54 + R_STUB
        bd.track([(ex, R_Y1 + 2.54), (ex, y0), (tx, y0 + abs(tx - ex)), (tx, ty)], N("J2", str(1 + j)))

    # --- I2C pull-ups 4.7k to 3V3 (T-050), Pico side of the module's level shifter
    for ref, (x, y), net in (("R13", PU_SCL, N("J1", "1")), ("R14", PU_SDA, N("J1", "2"))):
        fp = place(bd, None, comps, pin_net, ref, x, y, rot=R_ROT_DOWN, ref_at=(-2.2, 1.27))
        check_vertical(fp, x, y)
        bd.track([(x, y + 2.54), (x, cy)], net)

    # --- GND from the first to the last terminal, along the edge -------------------------------------
    a, z = term(0), term(13)
    bd.track([a, (a[0], H - 2.0), (z[0], H - 2.0), z], GND, W_PWR)

    # --- Texts ----------------------------------------------------------------------------------
    bd.text("FrutaMIDI v1.1", 82.0, 12.0, pcbnew.B_Cu, 2.0, mirror=True)
    bd.text("copper: bottom side", 82.0, 15.5, pcbnew.B_Cu, 1.2, mirror=True)
    bd.text("FrutaMIDI v1.1", 82.0, 12.0, pcbnew.F_SilkS, 2.0)
    bd.text("github.com/catuta0/fruta-midi-controller", 72.0, 2.2, pcbnew.F_SilkS, 1.0)
    labels = ["GND"] + [str(i) for i in range(12)] + ["GND"]
    for i, lab in enumerate(labels):
        x, _ = term(i)
        bd.text(lab, x, 57.6, pcbnew.F_SilkS, 1.1)
    bd.text("OCTAVE", POT[0] + 7.0, 24.0, pcbnew.F_SilkS, 1.0)
    bd.text("SCALE", BTN[0] + 3.25, BTN[1] + 7.6, pcbnew.F_SilkS, 1.0)
    bd.text("R1 ... R12 = 3k3 (E0 ... E11)", mod_e(6)[0], 50.6, pcbnew.F_SilkS, 1.0)
    bd.text("ORIG", JP1[0], JP1[1] - 3.1, pcbnew.F_SilkS, 0.8)
    bd.text("QT", JP1[0] + 5.08, JP1[1] - 3.1, pcbnew.F_SilkS, 0.8)
    # T-055 / ADR-009 D-10: how to pick the JP1 side (free area right of the module)
    for k, line in enumerate(("JP1 3V3 selector:", "ORIG = no white connectors", "QT = 2 white connectors")):
        bd.text(line, 86.0, 21.0 + 1.6 * k, pcbnew.F_SilkS, 0.8)

    ds = bd.b.GetDesignSettings()
    ds.SetAuxOrigin(VB(0, 0))          # Gerber/drill origin at the board corner
    ds.SetGridOrigin(VB(0, 0))
    pcbnew.SaveBoard(path, bd.b)
    return path


if __name__ == "__main__":
    build_footprints()
    print(build_board())
