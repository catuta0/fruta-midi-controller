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


JP1_PITCH = 3.81           # T-076: JP1 pad pitch (pad gap 3.81 - 1.94 = 1.87 mm)
# T-076: screw-terminal pads 3.0 x 4.5 mm (long axis along y) for peel strength under screw torque on a single-sided
# board. The copper is offset 0.75 mm towards the back of the block (away from the board edge): the pad still ends
# 1.5 mm below the hole centre, as the old 3.0 mm round pad did, so the gap to the GND edge track (intentional spark
# gap, ADR-020) stays 1.40 mm, and the extra copper goes where there is room (towards the resistor row).
TERM_PAD = (3.0, 4.5, 1.4)        # width x, length y, drill (mm)
TERM_PAD_OFFSET = -0.75           # mm, shape centre relative to the hole (negative = towards the back, -y)


def set_term_pad(p, first):
    w, h, drill = TERM_PAD
    set_pad(p, pcbnew.PAD_SHAPE_RECTANGLE if first else pcbnew.PAD_SHAPE_OVAL, w, h, drill)
    off = V(0, TERM_PAD_OFFSET)
    try:
        p.SetOffset(pcbnew.F_Cu, off)
    except TypeError:
        p.SetOffset(off)
    return p


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

    add_rect(fp, pcbnew.F_SilkS, -16.51, -9.525, 16.51, 10.0)
    add_text(fp, "MPR121 (Adafruit 1982)", 0, 0.6, size=1.2)
    add_text(fp, "GND E0 ... E11", 0, 3.4, size=0.9)
    replace_courtyard(fp, [(-17.0, -9.9), (17.0, -9.9), (17.0, 10.0), (-17.0, 10.0)])
    add_rect(fp, pcbnew.F_Fab, -16.51, -9.525, 16.51, 9.525, 0.1)
    sock = "${KICAD10_3DMODEL_DIR}/Connector_PinSocket_2.54mm.3dshapes/PinSocket_1x%02d_P2.54mm_Vertical.wrl"
    add_model(fp, sock % 13, offset=(-15.24, -8.255, 0), rot=(0, 0, -90))
    add_model(fp, sock % 7, offset=(-7.62, 6.985, 0), rot=(0, 0, -90))
    out["Adafruit_MPR121_1982_Socket"] = fp

    # --- Q-row wire holes S1..S7 (T-056 / F-013: separate part J3, formerly duplicate pads 14-20 of the module)
    fp = new_fp("WireHoles_1x07_P2.54mm", "7 wire holes S1..S7 above the MPR121 power/I2C row")
    for k in range(7):
        add_pad(fp, str(k + 1), 2.54 * k, 0, CIRC, 1.8, 1.8, 0.9)
        add_text(fp, "S%d" % (k + 1), 2.54 * k, -2.335, size=0.9)
    add_rect(fp, pcbnew.F_CrtYd, -1.2, -3.0, 16.44, 1.2, 0.05)
    fp.SetExcludedFromBOM(True)                    # holes only (matches the symbol)
    out["WireHoles_1x07_P2.54mm"] = fp

    # --- 2 holes for the I2C configuration wires (T-052: 3V3 moved to the JP1 solder jumper)
    fp = new_fp("Config_2pads", "2 holes for the configuration wires: SCL (pad 1), SDA (pad 2)")
    for k, lab in enumerate(("SCL", "SDA")):
        add_pad(fp, str(1 + k), 3.81 * k, 0, RECT if k == 0 else CIRC, 2.2, 2.2, 0.9)
        add_text(fp, lab, 3.81 * k, -2.3, size=0.9)
    add_rect(fp, pcbnew.F_CrtYd, -1.6, -3.2, 5.41, 1.6, 0.05)
    out["Config_2pads"] = fp

    # --- 3-way selector jumper, through-hole (T-052 / D-4): pad 1 = S1 (ORIG), 2 = 3V3 (centre), 3 = S7 (QT).
    # Close with a solder bridge or a lead off-cut across 1-2 or 2-3. Pads 1.94 x 2.4 mm, drill 0.8 (ring 0.57).
    # T-076: pitch 2.54 -> 3.81 mm, pad gap 0.60 -> 1.87 mm (>= 1.8 mm), so one blob cannot easily wet all three pads
    # (an accidental 1-2-3 bridge would join S1 and S7 = VIN/VCC and IRQ/ADDR of the module). A 0.5 mm R13-R16
    # off-cut (3.81 + 2.4 = 6.2 mm long) or a deliberate solder bridge over 1.87 mm still closes one side.
    fp = new_fp("SolderJumper_3_THT_P3.81mm", "3-way selector jumper, THT pads 3.81 mm pitch (1.87 mm gap), bridge 1-2 or 2-3")
    for k in range(3):
        add_pad(fp, str(1 + k), JP1_PITCH * k, 0, RECT, 1.94, 2.4, 0.8)
    xe = 2 * JP1_PITCH
    add_rect(fp, pcbnew.F_SilkS, -1.3, -1.55, xe + 1.3, 1.55, 0.12)
    add_rect(fp, pcbnew.F_CrtYd, -1.22, -1.45, xe + 1.22, 1.45, 0.05)
    add_rect(fp, pcbnew.F_Fab, -1.0, -1.2, xe + 1.0, 1.2, 0.1)
    fp.SetExcludedFromBOM(True)                    # copper only, nothing to buy (matches the symbol)
    out["SolderJumper_3_THT_P3.81mm"] = fp

    # --- Screw terminal 5.08 mm (larger pads)
    fp = lib_fp("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "TerminalBlock_5.08_1x02"))
    for p in fp.Pads():
        set_term_pad(p, p.GetNumber() == "1")                                # T-056 / F-014: 1.4 mm drill; T-076 oval
    # blocks butt against each other (continuous 5.08 pitch): courtyard = exact block width
    replace_courtyard(fp, [(-2.52, -5.7), (7.6, -5.7), (7.6, 5.0), (-2.52, 5.0)])
    replace_layer(fp, pcbnew.F_SilkS)
    add_rect(fp, pcbnew.F_SilkS, -2.3, -5.4, 7.38, 4.4)
    add_line(fp, pcbnew.F_SilkS, -2.3, 2.6, 7.38, 2.6)          # front (wire entry)
    out["TerminalBlock_5.08_1x02"] = fp

    # --- 14 ways = 7 interlocked 2-way blocks (pin 1 on the left)
    fp = new_fp("TerminalBlock_5.08_1x14", "7 interlocked 2-way screw terminal blocks, 5.08 mm pitch")
    for i in range(14):
        set_term_pad(add_pad(fp, str(i + 1), 5.08 * i, 0, OVAL, 3.0, 3.0, 1.4), i == 0)   # F-014: pin diag 1.27 mm
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

    # --- T-076: C1, KEMET Golden Max C322 radial MLCC: L 5.08, H 6.60, T 3.18 mm max, lead spacing 5.08 mm, lead
    # 0.51 mm (SOURCE EE-S29, dimension table). Drill 0.8 mm (hole - lead = 0.29 mm diametral, as the 0204 resistors),
    # round pad 2.0 mm (ring 0.6 mm). Silkscreen only above and below the body, clear of the pads.
    fp = new_fp("C_Radial_KEMET_C322_P5.08mm_HomeEtch",
                "KEMET Golden Max C322 radial MLCC, 5.08 x 3.18 mm body, 5.08 mm lead spacing, home-etch pads")
    for k in range(2):
        add_pad(fp, str(k + 1), 5.08 * k, 0, CIRC, 2.0, 2.0, 0.8)
    for yy in (-1.75, 1.75):
        add_line(fp, pcbnew.F_SilkS, 1.2, yy, 3.88, yy, 0.12)
    add_rect(fp, pcbnew.F_Fab, 0.0, -1.59, 5.08, 1.59, 0.1)
    add_rect(fp, pcbnew.F_CrtYd, -1.25, -1.85, 6.33, 1.85, 0.05)
    for model in lib_fp("Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm").Models():
        fp.Add3DModel(model)
    out["C_Radial_KEMET_C322_P5.08mm_HomeEtch"] = fp

    # --- Resistor 0204 mounted vertical, 2.54 mm pitch (T-050: electrode series R and I2C pull-ups)
    # Pads enlarged for home etching: 1.6 mm pad, 0.8 mm drill (annular ring 0.4 mm); lead 0.45-0.5 mm (Yageo MFR-12).
    fp = lib_fp("Resistor_THT", "R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "R_Axial_DIN0204_P2.54mm_Vertical_HomeEtch"))
    for p in fp.Pads():
        set_pad(p, CIRC, 1.6, 1.6, 0.8)
    out["R_Axial_DIN0204_P2.54mm_Vertical_HomeEtch"] = fp

    # --- Resistor DIN0414 lying flat, 15.24 mm pitch (T-060 / CR-002: electrode series R1-R12, pulse-rated).
    # Vishay MBE/SMA 0414: D <= 4.2 mm, L <= 11.9 mm, lead 0.8 mm, min. pitch 15.0 mm (SOURCE EE-S17).
    # Pads 2.2 mm, drill 1.1 mm (T-073 / C2-008: ring (2.2 - 1.1)/2 = 0.55 mm; hole - lead = 0.3 mm diametral,
    # 0.15 mm radial, above the 0.2 mm diametral fit rule of calc_mechanical.py). Copper gap pad-to-pad 13.04 mm
    # >= flashover rule 3.5 mm (sim/electronics/calc/calc_flashover.py). Courtyard = body 4.2 mm + 0.05 mm
    # each side (the 4.5 mm library outline is the generic DIN size; the real part is 4.2 mm max).
    fp = lib_fp("Resistor_THT", "R_Axial_DIN0414_L11.9mm_D4.5mm_P15.24mm_Horizontal")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "R_Axial_DIN0414_P15.24mm_Horizontal_HomeEtch"))
    for p in fp.Pads():
        set_pad(p, CIRC, 2.2, 2.2, 1.1)
    replace_courtyard(fp, [(-1.35, -2.15), (16.59, -2.15), (16.59, 2.15), (-1.35, 2.15)])
    out["R_Axial_DIN0414_P15.24mm_Horizontal_HomeEtch"] = fp

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
# T-060 / CR-002: module moved 15.1 mm up and 2.54 mm right so that the pulse-rated DIN0414 resistors
# (15.24 mm pitch, lying flat) and the 2.54 -> 5.08 mm fan-out fit between the module and J2.
MOD_C = (60.02, 17.645)           # module centre (electrode row at y = 25.9, power/I2C S row at y = 10.66)
CFG = (85.0, 12.5)                # J1 pad 1 (SCL); pad 2 (SDA) at +3.81 mm (right of the module)
T0, TY = 27.0, 64.5               # first terminal (GND), terminal row
# T-060: H4 moved from (70, 6) (module row). T-073 / C2-009: H3 moved from (95, 48) to (96, 38): at (95, 48) a metal
# screw head or washer (ASSUMED 5.6-7.0 mm) lay 0.2-0.9 mm from the R12 body and level with both of its end caps, a
# floating-metal bypass of R12 (check_gap.py section (e)); at (96, 38) it faces only the ELE11 end cap.
HOLES = [(8.0, 64.0), (95.0, 5.0), (96.0, 38.0), (88.5, 30.5)]

W_SIG, W_PWR, W_STUB = 1.0, 1.2, 0.8

# T-060 electrode resistors R1-R12: DIN0414 lying flat, axis along y, pad 1 (ELEx) on top, pad 2 (Ex) 15.24 mm
# below. One row at the terminal pitch 5.08 mm, offset R_DX to the right of the terminals (centres the
# 2.54 -> 5.08 mm fan-out: |dx| <= 13.97 mm on the module side, 1.27 mm on the terminal side).
R_PITCH = 15.24
R_Y1 = 42.15              # pad 1 row (courtyard 40.8 .. 58.74 stays above the J2 courtyard at 58.8)
R_DX = 1.27               # resistor x = terminal x + R_DX
E_STUB_Y = 27.9           # module side: straight drop from the electrode pin (y = 25.9) before the 45° run
R_ROT_DOWN = -90          # orientation that puts pad 2 below pad 1 (checked by check_vertical)
GND_DIAG = 71.8           # module GND run x + y = const: >= 0.6 mm from SW1, ch.1 track and R1 (CALCULATION)
R_ROT_UP = 90             # 0204 vertical part with pad 2 above pad 1
PU_SCL = (85.0, 5.5)      # R13 pad 1 on 3V3; pad 2 (2.54 mm below) drops onto the SCL hole of J1
PU_SDA = (88.81, 5.5)     # R14 pad 1 on 3V3; pad 2 drops onto the SDA hole of J1
SER_SDA = (27.0, None)    # T-055 R16 pad 1 x on the SDA row (pad 2 at +2.54 mm)
SER_SCL = (85.0, 18.5)    # T-055 R15 pad 1 (Pico side) at the end of the SCL run; pad 2 2.54 mm above
JP1 = (79.5, 15.74)       # T-052 selector jumper turned upright: pad 1 (ORIG -> S1) bottom, pad 2 = 3V3, pad 3 (QT -> S7) top
C1_POS = (31.2, 5.3)      # T-076: C1 pad 1 (POT); pad 2 (AGND) 5.08 mm to the right, between the 3V3 top run and RV1
TOP_3V3_Y = 2.0           # 3V3 run along the top edge (above the S1..S7 wire holes)
Y_S1, Y_SCL, Y_SDA = 15.74, 18.5, 21.0   # runs under the module (between the S row and the electrode row)

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


def check_vertical(fp, x, y, pitch=2.54):
    """Fail the build if pad 2 of a resistor is not `pitch` mm directly below (pitch < 0: above) pad 1."""
    pos = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
    p1, p2 = pos["1"], pos["2"]
    want1, want2 = VB(x, y), VB(x, y + pitch)
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
    place(bd, None, comps, pin_net, "J1", *CFG, ref_at=(6.6, 0.0))
    place(bd, None, comps, pin_net, "J3", *mod_q(1), ref_at="hide")
    place(bd, None, comps, pin_net, "RV1", *POT, ref_at=(10.0, 2.5))     # T-076: inside the body outline (C1 above)
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
    # T-076: C1 100 nF wiper -> AGND above RV1 (outside its courtyard). POT leaves pad 2 to the right, climbs at
    # x = C1 pad 1 between pad 1 (3V3) and the upper mounting tab; AGND joins C1 pad 2, both tabs (pad "MP") and pad 3.
    cx1, cy1 = C1_POS
    place(bd, None, comps, pin_net, "C1", cx1, cy1, ref_at=(2.54, -2.75))
    bd.track([(px, py + 2.5), (cx1, py + 2.5), (cx1, cy1)], N("A1", "34"))
    mp = sorted((p.GetPosition().y, p.GetPosition().x) for p in
                [q for f in bd.b.GetFootprints() if f.GetReference() == "RV1" for q in f.Pads() if q.GetNumber() == "MP"])
    (mty, mtx), (mby, mbx) = [((y - mm(OY)) / 1e6, (x - mm(OX)) / 1e6) for y, x in mp]
    agnd = N("A1", "33")
    c2x = cx1 + 5.08
    bd.track([(c2x, cy1), (c2x, mty - 1.28), (mtx, mty)], agnd)          # C1 pad 2 -> upper tab
    bd.track([(mtx, mty), (mbx, mby)], agnd)                             # upper tab -> lower tab
    bd.track([(px, py + 5.0), (mbx - 1.9, py + 5.0), (mbx, mby)], agnd)  # pad 3 -> lower tab

    # --- 3V3 up past the potentiometer and along the top edge (above the S1..S7 wire holes) -------
    # T-060: the module moved up, so 3V3 runs over the J3 wire holes to the pull-ups and JP1 on the right.
    cx, cy = CFG
    jc = (JP1[0], JP1[1] - JP1_PITCH)                # JP1 centre pad (3V3), JP1 upright
    yt = TOP_3V3_Y
    bd.track([(25.0, pico_pin(36)[1]), (25.0, yt), (PU_SDA[0], yt), PU_SDA], V33, W_PWR)
    bd.track([(PU_SCL[0], yt), PU_SCL], V33, W_PWR)
    xj = 82.5                                        # 3V3 drop to the JP1 centre pad, right of JP1
    bd.track([(xj, yt), (xj, jc[1]), jc], V33, W_PWR)

    # --- I2C: Pico -> under the module (between the S row and the electrode row) -> right side -----
    # T-055: 220R in line, pad 1 = Pico side, pad 2 = bus side (J1 hole + pull-up). R16 (SDA) stays on the SDA
    # row left of SW1; R15 (SCL) stands at the end of the SCL run, below J1.
    p31, p32 = pico_pin(31), pico_pin(32)
    place(bd, None, comps, pin_net, "R16", SER_SDA[0], p31[1], ref_at=(1.27, -2.05))   # T-076: above, clear of SW1 (check_silk)
    bd.track([p31, (SER_SDA[0], p31[1])], N("A1", "31"))
    xd = 40.5                                        # SDA climbs after SW1 / below the potentiometer pad
    bd.track([(SER_SDA[0] + 2.54, p31[1]), (xd, p31[1]), (xd + (p31[1] - Y_SDA), Y_SDA),
              (cx + 3.81, Y_SDA), (cx + 3.81, cy)], N("J1", "2"))
    xc = 38.5                                        # SCL climbs right of the potentiometer mounting pad
    sx, sy = SER_SCL
    bd.track([p32, (xc, p32[1]), (xc + (p32[1] - Y_SCL), Y_SCL), (sx, Y_SCL)], N("A1", "32"))
    fp = place(bd, None, comps, pin_net, "R15", sx, sy, rot=R_ROT_UP, ref_at=(2.2, -1.27))
    check_vertical(fp, sx, sy, -2.54)
    bd.track([(sx, sy - 2.54), (cx, cy)], N("J1", "1"))

    # --- JP1 3V3 selector (upright, right of the module): pad 1 -> S1 (original VIN), pad 3 -> S7 (QT VCC)
    fp = place(bd, None, comps, pin_net, "JP1", *JP1, rot=R_ROT_UP, ref_at="hide")
    check_vertical(fp, JP1[0], JP1[1], -JP1_PITCH)
    s1, s7 = mod_s(1), mod_s(7)
    bd.track([s1, (s1[0], Y_S1), JP1], N("A2", "14"), W_PWR)
    # T-076: pad 3 now sits 2.54 mm above the S row: S7 runs level, then 45 deg up, then level into pad 3
    j3y = JP1[1] - 2 * JP1_PITCH
    rise = s7[1] - j3y
    xr = JP1[0] - 4.0 - rise                         # 45 deg rise ends 4 mm left of the pad centre
    bd.track([s7, (xr, s7[1]), (xr + rise, j3y), (JP1[0], j3y)], N("A2", "20"), W_PWR)

    # --- Module S row joined to the Q row (wire holes) --------------------------------
    for k in range(1, 8):
        bd.track([mod_s(k), mod_q(k)], N("A2", str(13 + k)), W_STUB)

    # --- Button: GP22 (pin 29) and GND (pin 28) -----------------------------------------------
    bx, by = BTN
    bd.track([pico_pin(29), (bx, by)], N("A1", "29"))
    p28 = pico_pin(28)
    bd.track([p28, (24.5, p28[1]), (bx, by + 4.5)], GND, W_PWR)

    # --- Module GND (electrode row pin 1) and first terminal, from Pico pin 23 ---------------------
    # T-060: 45° run x + y = GND_DIAG, outermost on the left of the electrode fan-out.
    g = mod_e(0)
    p23 = pico_pin(23)
    t1 = term(0)
    gy = GND_DIAG - g[0]                             # end of the straight drop below the GND pin
    bd.track([g, (g[0], gy), (t1[0], GND_DIAG - t1[0]), (t1[0], p23[1]), t1], GND, W_PWR)
    bd.track([p23, (t1[0], p23[1])], GND, W_PWR)

    # --- Electrodes: module pin -> 45° fan-out (ELEx, low voltage) -> R lying flat -> short 45° -> terminal (Ex)
    # T-060 / CR-002: every ELE copper lies above y = R_Y1 + 1.1, every E copper below y = R_Y1 + R_PITCH - 1.1,
    # so the ELE/E gap (same channel and cross-channel) is set by the resistor pitch (check_gap.py measures it).
    for j in range(1, 13):
        ex, ey = mod_e(j)
        tx, ty = term(j)
        rx = tx + R_DX
        fp = place(bd, None, comps, pin_net, "R%d" % j, rx, R_Y1, rot=R_ROT_DOWN, ref_at="hide")
        check_vertical(fp, rx, R_Y1, R_PITCH)
        dx = rx - ex
        if E_STUB_Y + abs(dx) > R_Y1 + 1e-6:
            raise SystemExit("electrode %d: fan-out does not reach x before the resistor row" % j)
        bd.track([(ex, ey), (ex, E_STUB_Y), (rx, E_STUB_Y + abs(dx)), (rx, R_Y1)], N("A2", str(1 + j)))
        y2 = R_Y1 + R_PITCH
        bd.track([(rx, y2), (tx, y2 + R_DX), (tx, ty)], N("J2", str(1 + j)))

    # --- I2C pull-ups 4.7k to 3V3 (T-050), above J1 (bus side of R15/R16)
    for ref, (x, y), net, rdx in (("R13", PU_SCL, N("J1", "1"), -2.0), ("R14", PU_SDA, N("J1", "2"), 2.0)):
        # T-076: R14 designator moved to the right of R14 (it was 0.16 mm from R13 pad 1, check_silk.py)
        fp = place(bd, None, comps, pin_net, ref, x, y, rot=R_ROT_DOWN, ref_at=(rdx, 1.27))
        check_vertical(fp, x, y)
        bd.track([(x, y + 2.54), (x, cy)], net)

    # --- GND from the first to the last terminal, along the edge -------------------------------------
    a, z = term(0), term(13)
    bd.track([a, (a[0], H - 2.0), (z[0], H - 2.0), z], GND, W_PWR)

    # --- Texts ----------------------------------------------------------------------------------
    bd.text("FrutaMIDI v1.2", 13.4, 55.0, pcbnew.B_Cu, 2.0, mirror=True)
    bd.text("copper: bottom side", 13.4, 58.4, pcbnew.B_Cu, 1.2, mirror=True)
    bd.text("FrutaMIDI v1.2", 13.4, 55.0, pcbnew.F_SilkS, 2.0)
    bd.text("github.com/catuta0/fruta-midi-controller", 60.0, 1.0, pcbnew.F_SilkS, 0.8)
    labels = ["GND"] + [str(i) for i in range(12)] + ["GND"]
    for i, lab in enumerate(labels):
        x, _ = term(i)
        # numbers sit midway between pad 2 of the previous resistor (x - 5.08 + R_DX) and of their own (x + R_DX),
        # i.e. at x + R_DX - 2.54; two-digit labels are smaller so they keep >= 0.2 mm from both pads (T-073 / C2-010,
        # measured by check_silk.py)
        if lab == "GND":
            bd.text(lab, x, 57.6, pcbnew.F_SilkS, 1.1)
        else:
            bd.text(lab, x + R_DX - 2.54, 57.6, pcbnew.F_SilkS, 1.1 if len(lab) == 1 else 0.9)
    bd.text("OCTAVE", POT[0] + 7.0, 24.0, pcbnew.F_SilkS, 1.0)
    bd.text("SCALE", BTN[0] + 3.25, BTN[1] + 7.6, pcbnew.F_SilkS, 1.0)
    bd.text("R1 ... R12 = 3k3 pulse-rated, lying flat (E0 ... E11)", 61.0, 39.0, pcbnew.F_SilkS, 1.0)
    bd.text("ORIG", JP1[0], JP1[1] + 2.15, pcbnew.F_SilkS, 0.8)          # below pad 1
    bd.text("QT", JP1[0], JP1[1] - 2 * JP1_PITCH - 2.15, pcbnew.F_SilkS, 0.8)   # above pad 3
    # T-055 / ADR-009 D-10: how to pick the JP1 side (free area right of the module)
    for k, line in enumerate(("JP1 3V3 selector:", "ORIG = no white connectors", "QT = 2 white connectors")):
        bd.text(line, 88.0, 22.9 + 1.55 * k, pcbnew.F_SilkS, 0.8)    # T-076: 1.55 mm pitch, boxes do not touch

    ds = bd.b.GetDesignSettings()
    ds.SetAuxOrigin(VB(0, 0))          # Gerber/drill origin at the board corner
    ds.SetGridOrigin(VB(0, 0))
    pcbnew.SaveBoard(path, bd.b)
    return path


if __name__ == "__main__":
    build_footprints()
    print(build_board())
