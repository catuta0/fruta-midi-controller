#!/usr/bin/env python3
"""Generates the footprint library (FrutaMIDI.pretty) and the single-sided SMD PCB (frutamidi.kicad_pcb).

Runs with the KiCad Python (needs the pcbnew module), after gen_schematic.py:
    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
        hardware/scripts/gen_pcb.py

Rules chosen for home chemical etching (CR-003 / ADR-023, REQ-029):
  copper on one layer, on the component side (F.Cu); SMD only; the only holes are the 4 M3 mounting holes; no vias,
  no copper pour; signal tracks >= 1.0 mm (>= 0.8 mm short stubs), power >= 1.2 mm, clearance >= 0.6 mm (DRC hard
  minimum 0.5 mm). No silkscreen is assumed: references and pin 1 live on F.Fab (assembly map).
Dimensions and their labels: reports/electronics/smd_feasibility.md (T-090).
"""
import os, re, shutil, subprocess, sys, uuid
import pcbnew

HW = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
KICAD = os.environ.get("KICAD_SHARED", "/Applications/KiCad/KiCad.app/Contents/SharedSupport")
KICAD_CLI = os.environ.get("KICAD_CLI", "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli")
FP_LIB = os.path.join(HW, "FrutaMIDI.pretty")
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
MODELS = "${KICAD10_3DMODEL_DIR}/"


def det_uuid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "frutamidi/" + "/".join(parts)))


# =========================================================================== footprints

def lib_fp(lib, name):
    return pcbnew.FootprintLoad(os.path.join(KICAD, "footprints", lib + ".pretty"), name)


def set_pad(p, shape, w, h):
    try:
        p.SetShape(shape)
    except TypeError:
        p.SetShape(pcbnew.F_Cu, shape)
    p.SetSize(V(w, h))


def new_fp(name, descr, attr=None):
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", name))
    fp.SetLibDescription(descr)
    fp.SetAttributes(pcbnew.FP_SMD if attr is None else attr)
    fp.Reference().SetLayer(pcbnew.F_Fab)
    fp.Value().SetLayer(pcbnew.F_Fab)
    fp.Value().SetVisible(False)
    return fp


def add_pad(fp, num, x, y, shape, w, h):
    """SMD pad on the component side (F.Cu + mask opening + paste, as a fab would expect)."""
    p = pcbnew.PAD(fp)
    p.SetNumber(num)
    p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    p.SetLayerSet(pcbnew.PAD.SMDMask())
    set_pad(p, shape, w, h)
    p.SetPosition(V(x, y))
    fp.Add(p)
    return p


def add_line(fp, layer, x1, y1, x2, y2, w=0.1):
    s = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
    s.SetLayer(layer)
    s.SetStart(V(x1, y1))
    s.SetEnd(V(x2, y2))
    s.SetWidth(mm(w))
    fp.Add(s)


def add_rect(fp, layer, x1, y1, x2, y2, w=0.1):
    for a, b, c, d in ((x1, y1, x2, y1), (x2, y1, x2, y2), (x2, y2, x1, y2), (x1, y2, x1, y1)):
        add_line(fp, layer, a, b, c, d, w)


def add_circle(fp, layer, r, w=0.1):
    s = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_CIRCLE)
    s.SetLayer(layer)
    s.SetCenter(V(0, 0))
    s.SetEnd(V(r, 0))
    s.SetWidth(mm(w))
    fp.Add(s)


def add_text(fp, txt, x, y, layer=pcbnew.F_Fab, size=1.0):
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


def add_model(fp, path, offset=(0, 0, 0), rot=(0, 0, 0)):
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = path
    m.m_Offset = pcbnew.VECTOR3D(*offset)
    m.m_Rotation = pcbnew.VECTOR3D(*rot)
    fp.Add3DModel(m)


def add_keepout(fp, x1, y1, x2, y2):
    """Copper keep-out on F.Cu, enforced by DRC (no tracks, vias, pads or pour inside)."""
    z = pcbnew.ZONE(fp)
    z.SetLayer(pcbnew.F_Cu)
    z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowVias(True)
    z.SetDoNotAllowPads(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        o.Append(mm(x), mm(y))
    fp.Add(z)
    return z


HOLE_R, WASHER_R = 1.6, 3.5   # M3 drill radius; ISO 7089 M3 washer radius (ASSUMPTION, largest hardware the layout keeps clear)
JP1_PITCH = 3.81           # T-076: JP1 pad pitch (pad gap 3.81 - 1.94 = 1.87 mm), kept in SMD
TERM_PAD = (3.0, 4.5)      # J2 solder-wire pad: width x, length y (mm); same copper as the V1.2 terminal pad

# A1 land (T-090 section 3, SOURCE RP-008307-DS-2): inner edge at the datasheet 16.18 mm width, outer edge 1.79 mm
# beyond the 21 mm module; pad 1.6 x 4.2 mm, centre 1.3 mm outboard of the pin column (CALCULATION).
PICO_PAD = (4.2, 1.6)
PICO_PAD_OFF = 1.3
# Bare-copper keep-outs on the carrier, relative to the footprint origin (pin 1 column). The union of the exposed
# underside features with 0.6 mm clearance. KO_TP = TP1-TP6 and the USB shell pads (T-090, board x 9.52-17.27,
# y 0.48-14.98 mm at the V1.2 Pico position 4.5, 2.0). KO_DBG = the three SWD pads at the far end (T-090 Figure 5,
# 6.68 mm across; centre (13.39, 50.03) in board coordinates, library footprint RaspberryPi_Pico_SMD): not part of the
# T-090 union, added in T-091 because those pads are exposed metal too.
KO_TP = (9.52 - 4.5, 0.48 - 2.0, 17.27 - 4.5, 14.98 - 2.0)
KO_DBG = (9.45 - 4.5, 47.83 - 2.0, 17.33 - 4.5, 52.23 - 2.0)


def build_footprints():
    if os.path.isdir(FP_LIB):
        shutil.rmtree(FP_LIB)
    os.makedirs(FP_LIB)
    OVAL, CIRC, RECT = pcbnew.PAD_SHAPE_OVAL, pcbnew.PAD_SHAPE_CIRCLE, pcbnew.PAD_SHAPE_RECTANGLE
    out = {}

    # --- Raspberry Pi Pico surface-soldered on its castellations (origin = pin 1 column, USB up). All 40 pads etched
    # as mechanical anchors, pad 1 is the only one with a square inner marking on the assembly map.
    name = "RaspberryPi_Pico_Castellated_HomeEtch"
    fp = new_fp(name, "Raspberry Pi Pico / Pico 2 surface-soldered on castellations, 1.6 x 4.2 mm home-etch land (CR-003, T-090)")
    w, h = PICO_PAD
    for k in range(1, 21):
        add_pad(fp, str(k), -PICO_PAD_OFF, (k - 1) * 2.54, RECT, w, h)
        add_pad(fp, str(41 - k), 17.78 + PICO_PAD_OFF, (k - 1) * 2.54, RECT, w, h)
    add_keepout(fp, *KO_TP)
    add_keepout(fp, *KO_DBG)
    add_rect(fp, pcbnew.F_Fab, -1.61, -1.37, 19.39, 49.63)
    add_rect(fp, pcbnew.F_Fab, 5.39, -2.67, 12.39, 3.5)                    # USB connector
    add_rect(fp, pcbnew.F_Fab, KO_TP[0], KO_TP[1], KO_TP[2], KO_TP[3], 0.05)
    add_text(fp, "no bare copper", 8.89, 3.2, size=1.0)
    add_rect(fp, pcbnew.F_Fab, KO_DBG[0], KO_DBG[1], KO_DBG[2], KO_DBG[3], 0.05)
    add_text(fp, "no copper", 8.89, 47.0, size=0.9)
    add_text(fp, "USB", 8.89, 1.0, size=1.2)
    add_text(fp, "1", -2.0, 2.0, size=1.2)
    add_rect(fp, pcbnew.F_CrtYd, -3.7, -2.9, 21.5, 50.3, 0.05)
    add_model(fp, MODELS + "Module.3dshapes/RaspberryPi_Pico.step", offset=(8.89, -24.13, 0))
    out[name] = fp

    # --- Adafruit MPR121 (1982): header pins butted on 1.8 x 2.4 mm surface pads, plastic strip as stand-off (T-090).
    # Orientation as in V1.2 (rotated 180 deg from the Adafruit Eagle files, electrodes at the bottom).
    name = "Adafruit_MPR121_1982_SMD"
    fp = new_fp(name, "Adafruit MPR121 breakout (1982, original or STEMMA QT) on 1x13 + 1x7 header pins butted on surface pads")
    for j in range(13):
        add_pad(fp, str(1 + j), -15.24 + 2.54 * j, 8.255, RECT, 1.8, 2.4)
    for k in range(7):
        add_pad(fp, str(14 + k), -7.62 + 2.54 * k, -6.985, RECT, 1.8, 2.4)
    add_rect(fp, pcbnew.F_Fab, -16.51, -9.525, 16.51, 9.525)
    add_text(fp, "MPR121 (Adafruit 1982)", 0, 0.6, size=1.2)
    add_text(fp, "GND E0 ... E11", 0, 3.4, size=0.9)
    add_text(fp, "1", -15.24, 5.9, size=1.2)                               # pin 1 mark (electrode row, GND)
    add_rect(fp, pcbnew.F_CrtYd, -17.0, -9.9, 17.0, 10.0, 0.05)
    hdr = MODELS + "Connector_PinHeader_2.54mm.3dshapes/PinHeader_1x%02d_P2.54mm_Vertical.step"
    add_model(fp, hdr % 13, offset=(-15.24, -8.255, 0), rot=(0, 0, -90))
    add_model(fp, hdr % 7, offset=(-7.62, 6.985, 0), rot=(0, 0, -90))
    out[name] = fp

    # --- Q-row surface wire pads S1..S7 (J3), each directly above a module S pin
    name = "WirePads_1x07_P2.54mm"
    fp = new_fp(name, "7 surface wire pads S1..S7 above the MPR121 power/I2C row")
    for k in range(7):
        add_pad(fp, str(k + 1), 2.54 * k, 0, CIRC, 1.8, 1.8)
        add_text(fp, "S%d" % (k + 1), 2.54 * k, -2.335, size=0.9)
    add_rect(fp, pcbnew.F_CrtYd, -1.2, -3.0, 16.44, 1.2, 0.05)
    fp.SetExcludedFromBOM(True)                    # copper only (matches the symbol)
    out[name] = fp

    # --- 2 surface pads for the two insulated configuration wires
    name = "Config_2pads_SMD"
    fp = new_fp(name, "2 surface pads for the I2C configuration wires: SCL (pad 1), SDA (pad 2)")
    for k, lab in enumerate(("SCL", "SDA")):
        add_pad(fp, str(1 + k), 3.81 * k, 0, RECT if k == 0 else CIRC, 2.2, 2.2)
        add_text(fp, lab, 3.81 * k, -2.3, size=0.9)
    add_rect(fp, pcbnew.F_CrtYd, -1.6, -3.2, 5.41, 1.6, 0.05)
    out[name] = fp

    # --- 3-way selector jumper (T-052 / D-4), surface pads: pad 1 = S1 (ORIG), 2 = 3V3 (centre), 3 = S7 (QT).
    # T-076: pitch 3.81 mm, pad gap 1.87 mm, so one blob cannot easily wet all three pads.
    name = "SolderJumper_3_SMD_P3.81mm"
    fp = new_fp(name, "3-way selector solder bridge, SMD pads 3.81 mm pitch (1.87 mm gap), bridge 1-2 or 2-3 with a wire link")
    for k in range(3):
        add_pad(fp, str(1 + k), JP1_PITCH * k, 0, RECT, 1.94, 2.4)
    xe = 2 * JP1_PITCH
    add_rect(fp, pcbnew.F_Fab, -1.0, -1.2, xe + 1.0, 1.2)
    add_rect(fp, pcbnew.F_CrtYd, -1.22, -1.45, xe + 1.22, 1.45, 0.05)
    fp.SetExcludedFromBOM(True)                    # copper only (matches the symbol)
    out[name] = fp

    # --- J2: 14 electrode solder-wire pads, 5.08 mm pitch (ADR-023 D-3). Same copper rectangle as the V1.2 terminal pad
    # shape (3.0 x 4.5 mm), so the 1.40 mm gap to the GND edge track (ADR-020 spark gap) is unchanged.
    name = "WirePads_1x14_P5.08mm"
    fp = new_fp(name, "14 solder-wire pads for electrode wires, 5.08 mm pitch, 3.0 x 4.5 mm (hot-melt strain relief)")
    w, h = TERM_PAD
    for i in range(14):
        add_pad(fp, str(i + 1), 5.08 * i, 0, RECT if i == 0 else OVAL, w, h)
    add_rect(fp, pcbnew.F_Fab, -1.5, -2.25, 67.54, 2.25)
    add_rect(fp, pcbnew.F_CrtYd, -1.75, -2.5, 67.79, 2.5, 0.05)
    fp.SetExcludedFromBOM(True)                    # copper only (matches the symbol)
    out[name] = fp

    # --- RV1: 3 surface wire pads for the off-board potentiometer (ADR-023 D-2)
    name = "WirePads_1x03_P5.08mm"
    fp = new_fp(name, "3 surface wire pads, 5.08 mm pitch, for an off-board potentiometer (pad 1 = 3V3, 2 = wiper, 3 = AGND)")
    for k in range(3):
        add_pad(fp, str(k + 1), 0, 5.08 * k, RECT if k == 0 else CIRC, 3.0, 3.0)
    add_rect(fp, pcbnew.F_CrtYd, -1.75, -1.75, 1.75, 11.91, 0.05)
    out[name] = fp

    # --- SW1 Omron B3S-1000 (library land: 4 pads 1.55 x 1.3 mm, SOURCE Omron catalogue; pads with the same number are
    # joined inside the switch), origin at the centre.
    name = "SW_SPST_B3S-1000_HomeEtch"
    fp = lib_fp("Button_Switch_SMD", "SW_SPST_B3S-1000")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", name))
    replace_layer(fp, pcbnew.F_SilkS)
    fp.SetDuplicatePadNumbersAreJumpers(True)
    fp.Reference().SetLayer(pcbnew.F_Fab)
    fp.Value().SetVisible(False)
    for item in fp.GraphicalItems():                    # library designator sits above the body, on R16 (T-092): move it right
        if item.GetClass() == "PCB_TEXT" and "REFERENCE" in item.GetText():
            item.SetPosition(V(7.0, 0.0))
    out[name] = fp

    # --- R1-R12: TT HPWC2512, hand-solder land: pad 1.9 x 3.35 mm, copper gap G = 5.0 mm (T-090, ADR-023 D-1).
    # Origin at pad 1 (ELE side); pad 2 at +6.9 mm along x (CALCULATION: 5.0 + 1.9).
    name = "R_2512_HPWC_G5.0mm"
    fp = new_fp(name, "TT Electronics HPWC2512 pulse-rated chip resistor, land 1.9 x 3.35 mm, copper gap 5.0 mm (flashover rule)")
    add_pad(fp, "1", 0, 0, RECT, 1.9, 3.35)
    add_pad(fp, "2", 6.9, 0, RECT, 1.9, 3.35)
    add_rect(fp, pcbnew.F_Fab, 0.2, -1.6, 6.7, 1.6)                        # body 6.5 x 3.2 mm nominal (SOURCE TT HPWC 09.23)
    add_rect(fp, pcbnew.F_CrtYd, -1.2, -1.925, 8.1, 1.925, 0.05)
    add_model(fp, MODELS + "Resistor_SMD.3dshapes/R_2512_6332Metric.step", offset=(3.45, 0, 0))
    out[name] = fp

    # --- R13-R16 / C1: 1206 land G 1.75, Y 1.15, X 1.80 mm (SOURCE Vishay 28950), origin at pad 1, pad 2 at +2.9 mm
    for name, descr, mdl in (("R_1206_HomeEtch", "1206 chip resistor, IPC-7351 reflow land usable by hand", "Resistor_SMD.3dshapes/R_1206_3216Metric.step"),
                             ("C_1206_HomeEtch", "1206 chip capacitor, IPC-7351 reflow land usable by hand", "Capacitor_SMD.3dshapes/C_1206_3216Metric.step")):
        fp = new_fp(name, descr)
        add_pad(fp, "1", 0, 0, RECT, 1.15, 1.8)
        add_pad(fp, "2", 2.9, 0, RECT, 1.15, 1.8)
        add_rect(fp, pcbnew.F_Fab, -0.15, -0.8, 3.05, 0.8)
        add_rect(fp, pcbnew.F_CrtYd, -0.85, -1.15, 3.75, 1.15, 0.05)
        add_model(fp, MODELS + mdl, offset=(1.45, 0, 0))
        out[name] = fp

    # --- M3 mounting hole (the only holes on the board)
    name = "MountingHole_3.2mm_M3"
    fp = lib_fp("MountingHole", name)
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", name))
    replace_layer(fp, pcbnew.F_SilkS)
    fp.Value().SetVisible(False)
    add_circle(fp, pcbnew.F_Fab, HOLE_R)                # drill
    add_circle(fp, pcbnew.F_Fab, WASHER_R, 0.05)        # largest screw head / washer the layout keeps clear (T-092)
    out[name] = fp

    # F.Fab gets every pad outline, so the assembly map (F.Fab + outline, no copper) is readable on its own.
    for fp in out.values():
        for p in list(fp.Pads()):
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                continue
            c, sz = p.GetPosition(), p.GetSize(pcbnew.F_Cu)
            cx, cy, hw, hh = pcbnew.ToMM(c.x), pcbnew.ToMM(c.y), pcbnew.ToMM(sz.x) / 2, pcbnew.ToMM(sz.y) / 2
            add_rect(fp, pcbnew.F_Fab, cx - hw, cy - hh, cx + hw, cy + hh, 0.08)

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
PICO = (4.5, 2.0)                 # pin 1 column; the land centres are 1.3 mm outboard (V1.2 position, T-090 keep-out)
MOD_C = (60.02, 17.645)           # module centre (electrode row at y = 25.9, power/I2C S row at y = 10.66)
CFG = (85.0, 12.5)                # J1 pad 1 (SCL); pad 2 (SDA) at +3.81 mm (right of the module)
T0, TY = 27.0, 63.75              # first J2 pad centre (GND), pad row; 1.40 mm above the GND edge track (ADR-020)
# T-092: well-spread support, one hole per board quadrant (check_smd.py). H4 is as close to the USB end of the Pico as the
# layout allows: it cannot go left of or above the module (Pico lands reach x 25.68, module end y 0.63), so it sits just
# right of the lands, x fixed by 0.6 mm from the 3.5 mm washer radius to the lands and to the 3V3 riser at x 34.5.
# H3 cannot go nearer its corner: J2 pad 14 and the spark-gap track fill the bottom edge up to x 94.54.
HOLES = [(5.0, 65.0), (96.0, 4.0), (96.5, 58.0), (29.8, 4.0)]

W_SIG, W_PWR, W_STUB = 1.0, 1.2, 0.8

# R1-R12: origin at pad 1 (ELEx), pad 2 (Ex) R_PITCH below, one lane per electrode at the J2 pitch 5.08 mm, offset R_DX
# to the right of the J2 pad (centres the 2.54 -> 5.08 mm fan-out, |dx| <= 13.97 mm).
R_PITCH = 6.9             # G 5.0 + pad 1.9 (CALCULATION)
R_Y1 = 49.0               # pad 1 row; pad 2 row at 55.9, 5.6 mm above the J2 pad top edge (61.5)
R_DX = 1.27               # resistor x = J2 x + R_DX
E_STUB_Y = 27.9           # module side: straight drop from the electrode pin (y = 25.9) before the 45 deg run
R_ROT_DOWN = -90          # orientation that puts pad 2 below pad 1 (checked by check_vertical)
R_ROT_UP = 90             # pad 2 above pad 1
GND_DIAG = 72.6           # module GND run x + y = const: >= 0.6 mm from SW1 and from the ch.1 fan-out track (CALCULATION)
PU_SCL = (85.0, 5.5)      # R13 pad 1 on 3V3; pad 2 2.9 mm below drops onto the SCL pad of J1
PU_SDA = (88.81, 5.5)     # R14 pad 1 on 3V3; pad 2 drops onto the SDA pad of J1
SER_SDA = (27.6, 24.86)   # R16 pad 1 on the Pico side (pin 31 row)
JP1 = (79.5, 15.74)       # selector upright: pad 1 (ORIG -> S1) bottom, pad 2 = 3V3, pad 3 (QT -> S7) top
TOP_3V3_Y = 2.0           # 3V3 run along the top edge (above the S1..S7 wire pads)
X_3V3_LEVEL = 31.5        # 3V3 leaves Pico pin 36 level to this x, then 45 deg up to RV1 pad 1 (keeps the area around H4 free)
Y_S1, Y_SCL, Y_SDA = 15.74, 21.05, 23.55     # runs under the module (between the S row and the electrode row)
SER_SCL = (85.0, Y_SCL)   # R15 pad 1 (Pico side) at the end of the SCL run; pad 2 2.9 mm above
XC, XD = 38.5, 40.5       # x where SCL and SDA leave the Pico rows and climb to the module runs
RV_PAD = (34.5, 8.42)     # RV1 pad 1 (3V3); pads 2 (wiper) and 3 (AGND) 5.08 mm apart below
C1_POS = (30.0, 17.24)    # C1 pad 1 on the wiper row (Pico pin 34); pad 2 (AGND) 2.9 mm below
SW_C = (31.5, 30.23)      # SW1 centre; pad rows at y = 27.98 (BTN) and 32.48 (GND = Pico pin 28 row)
GND_RAIL_L, GND_RAIL_R = 7.4, 19.4   # GND rails under the Pico, in the 3.61 mm channels beside the TP keep-out

# The board sits away from the sheet corner so a printer at 100 % does not clip anything.
OX, OY = 50.0, 50.0
VB = lambda x, y: V(OX + x, OY + y)


def pico_pin(n):
    """Land centre of Pico pin n (1.3 mm outboard of the castellation column)."""
    x0, y0 = PICO
    if n <= 20:
        return x0 - PICO_PAD_OFF, y0 + (n - 1) * 2.54
    return x0 + 17.78 + PICO_PAD_OFF, y0 + (40 - n) * 2.54


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
            t.SetLayer(pcbnew.F_Cu)
            t.SetNet(n)
            self.b.Add(t)

    def text(self, s, x, y, layer, size=1.5, thick=None):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetPosition(VB(x, y))
        t.SetLayer(layer)
        t.SetTextSize(V(size, size))
        t.SetTextThickness(mm(thick if thick else size * 0.18))
        self.b.Add(t)

    def edge(self):
        for a, b, c, d in ((0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)):
            s = pcbnew.PCB_SHAPE(self.b, pcbnew.SHAPE_T_SEGMENT)
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetStart(VB(a, b))
            s.SetEnd(VB(c, d))
            s.SetWidth(mm(0.15))
            self.b.Add(s)


def place(bd, comps, pin_net, ref, x, y, rot=0, ref_at=None):
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
    fp.Reference().SetLayer(pcbnew.F_Fab)
    fp.Reference().SetTextSize(V(1.1, 1.1))
    fp.Reference().SetTextThickness(mm(0.16))
    fp.Reference().SetKeepUpright(False)
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


def check_vertical(fp, x, y, pitch):
    """Fail the build if pad 2 of a part is not `pitch` mm directly below (pitch < 0: above) pad 1."""
    pos = {p.GetNumber(): p.GetPosition() for p in fp.Pads()}
    p1, p2 = pos["1"], pos["2"]
    want1, want2 = VB(x, y), VB(x, y + pitch)
    if abs(p1.x - want1.x) > 1000 or abs(p1.y - want1.y) > 1000 or \
       abs(p2.x - want2.x) > 1000 or abs(p2.y - want2.y) > 1000:
        raise SystemExit("part %s pads at %s/%s, expected pad 2 below pad 1"
                         % (fp.GetReference(), (p1.x, p1.y), (p2.x, p2.y)))


def build_board():
    comps, pin_net = read_netlist()
    path = os.path.join(HW, "frutamidi.kicad_pcb")
    bd = Board(path)
    bd.edge()
    for n in sorted(set(pin_net.values())):
        bd.net(n)

    place(bd, comps, pin_net, "A1", *PICO, ref_at=(8.89, 24.0))
    place(bd, comps, pin_net, "A2", *MOD_C, ref_at=(-13.0, -2.5))
    place(bd, comps, pin_net, "J1", *CFG, ref_at=(6.6, 0.0))
    place(bd, comps, pin_net, "J3", *mod_q(1), ref_at="hide")
    place(bd, comps, pin_net, "RV1", *RV_PAD, ref_at=(-3.2, 5.08))
    place(bd, comps, pin_net, "SW1", *SW_C, ref_at="hide")                 # the library land carries ${REFERENCE} on F.Fab
    place(bd, comps, pin_net, "J2", *term(0), ref_at=(0, 4.2))
    for k, (x, y) in enumerate(HOLES):
        place(bd, comps, pin_net, "H%d" % (k + 1), x, y, ref_at="hide")

    N = lambda ref, pin: pin_net[(ref, pin)]
    GND, V33 = "GND", "+3V3"

    # --- GND: rails under the Pico, in the channels beside the TP keep-out; rungs at pins 13/28 and 18/23 --------------
    xl, xr_ = GND_RAIL_L, GND_RAIL_R
    bd.track([(xl, pico_pin(3)[1]), (xl, pico_pin(18)[1])], GND, W_PWR)
    bd.track([(xr_, pico_pin(38)[1]), (xr_, pico_pin(23)[1])], GND, W_PWR)
    for n in (3, 8, 13, 18):
        bd.track([pico_pin(n), (xl, pico_pin(n)[1])], GND, W_PWR)
    for n in (38, 28, 23):
        bd.track([pico_pin(n), (xr_, pico_pin(n)[1])], GND, W_PWR)
    bd.track([(xl, pico_pin(13)[1]), (xr_, pico_pin(28)[1])], GND, W_PWR)
    bd.track([(xl, pico_pin(18)[1]), (xr_, pico_pin(23)[1])], GND, W_PWR)

    # --- RV1 wire pads, C1 and the 3V3 riser --------------------------------------------------------------------------
    p36, p34, p33 = pico_pin(36), pico_pin(34), pico_pin(33)
    rvx, rvy = RV_PAD
    x3, py3 = X_3V3_LEVEL, p36[1]
    # 3V3: pin 36 -> level -> 45 deg -> RV1 pad 1 -> straight up -> top run -> R14 (T-092: riser moved from x 27.2 to x 34.5 for H4)
    bd.track([p36, (x3, py3), (rvx, py3 - (rvx - x3)), (rvx, rvy), (rvx, TOP_3V3_Y), (PU_SDA[0], TOP_3V3_Y), PU_SDA], V33, W_PWR)

    cx1, cy1 = C1_POS
    fp = place(bd, comps, pin_net, "C1", cx1, cy1, rot=R_ROT_DOWN, ref_at=(-2.6, 1.45))
    check_vertical(fp, cx1, cy1, 2.9)
    bd.track([p34, C1_POS], N("A1", "34"))                                 # POT to C1 pad 1
    y2w = rvy + 5.08                                                       # RV1 pad 2 (wiper)
    bd.track([C1_POS, (cx1 + 1.0, cy1), (rvx, cy1 - (rvx - cx1 - 1.0)), (rvx, y2w)], N("A1", "34"))
    agnd = N("A1", "33")
    c2 = (cx1, cy1 + 2.9)
    bd.track([p33, (cx1, p33[1])], agnd)                                   # AGND to C1 pad 2
    bd.track([c2, (cx1 + 2.5, c2[1]), (rvx, rvy + 10.16)], agnd)           # C1 pad 2 to RV1 pad 3

    cx, cy = CFG
    jc = (JP1[0], JP1[1] - JP1_PITCH)                # JP1 centre pad (3V3), JP1 upright
    yt = TOP_3V3_Y
    bd.track([(PU_SCL[0], yt), PU_SCL], V33, W_PWR)
    xj = 82.5                                        # 3V3 drop to the JP1 centre pad, right of JP1
    bd.track([(xj, yt), (xj, jc[1]), jc], V33, W_PWR)

    # --- I2C: Pico -> under the module (between the S row and the electrode row) -> right side ------------------------
    # 220R in line, pad 1 = Pico side, pad 2 = bus side. R16 (SDA) stays on the SDA row by the Pico; R15 (SCL) below J1.
    p31, p32 = pico_pin(31), pico_pin(32)
    place(bd, comps, pin_net, "R16", SER_SDA[0], p31[1], ref_at=(1.45, -2.05))
    bd.track([p31, (SER_SDA[0], p31[1])], N("A1", "31"))
    bd.track([(SER_SDA[0] + 2.9, p31[1]), (XD, p31[1]), (XD + (p31[1] - Y_SDA), Y_SDA),
              (cx + 3.81, Y_SDA), (cx + 3.81, cy)], N("J1", "2"))
    sx, sy = SER_SCL
    bd.track([p32, (XC, p32[1]), (XC + (p32[1] - Y_SCL), Y_SCL), (sx, Y_SCL)], N("A1", "32"))
    fp = place(bd, comps, pin_net, "R15", sx, sy, rot=R_ROT_UP, ref_at=(2.6, -1.45))
    check_vertical(fp, sx, sy, -2.9)
    bd.track([(sx, sy - 2.9), (cx, cy)], N("J1", "1"))

    # --- JP1 3V3 selector (upright, right of the module): pad 1 -> S1 (original VIN), pad 3 -> S7 (QT VCC) ---------------
    fp = place(bd, comps, pin_net, "JP1", *JP1, rot=R_ROT_UP, ref_at=(3.0, -3.81))
    check_vertical(fp, JP1[0], JP1[1], -JP1_PITCH)
    s1, s7 = mod_s(1), mod_s(7)
    bd.track([s1, (s1[0], Y_S1), JP1], N("A2", "14"), W_PWR)
    j3y = JP1[1] - 2 * JP1_PITCH
    rise = s7[1] - j3y
    xr = JP1[0] - 4.0 - rise                         # 45 deg rise ends 4 mm left of the pad centre
    bd.track([s7, (xr, s7[1]), (xr + rise, j3y), (JP1[0], j3y)], N("A2", "20"), W_PWR)

    # --- Module S row joined to the Q row (surface wire pads) -----------------------------------------------------------
    for k in range(1, 8):
        # S1 and S7 can carry the module supply (JP1), so they keep the power width on the stub as well (REQ-029)
        bd.track([mod_s(k), mod_q(k)], N("A2", str(13 + k)), W_PWR if k in (1, 7) else W_STUB)

    # --- Button: GP22 (pin 29) and GND (pin 28); SW1 left-hand pads only (the right-hand pads are joined internally) ----
    sw_lx = SW_C[0] - 3.975
    sw_ty = SW_C[1] - 2.25
    sw_by = SW_C[1] + 2.25
    p29 = pico_pin(29)
    bd.track([p29, (sw_lx, p29[1]), (sw_lx, sw_ty)], N("A1", "29"))
    bd.track([pico_pin(28), (sw_lx, sw_by)], GND, W_PWR)

    # --- Module GND (electrode row pin 1) and first J2 pad, from Pico pin 23 ---------------------------------------------
    # 45 deg run x + y = GND_DIAG, outermost on the left of the electrode fan-out.
    g = mod_e(0)
    p23 = pico_pin(23)
    t1 = term(0)
    gy = GND_DIAG - g[0]                             # end of the straight drop below the GND pin
    dy27 = GND_DIAG - t1[0]                          # y where the run reaches the J2 column
    top = min(dy27, p23[1])
    bd.track([g, (g[0], gy), (t1[0], dy27)], GND, W_PWR)
    bd.track([(t1[0], top), (t1[0], max(dy27, p23[1])), t1], GND, W_PWR)    # shared vertices (calc_gnd_bounce.py graph)
    bd.track([p23, (t1[0], p23[1])], GND, W_PWR)

    # --- Electrodes: module pin -> 45 deg fan-out (ELEx) -> R (2512, 5.0 mm land gap, no track under the body) -> Ex ---
    # All ELE copper lies above y = R_Y1 + 1.0, all E copper below y = R_Y1 + R_PITCH - 1.0 (check_gap.py measures it).
    for j in range(1, 13):
        ex, ey = mod_e(j)
        tx, ty = term(j)
        rx = tx + R_DX
        fp = place(bd, comps, pin_net, "R%d" % j, rx, R_Y1, rot=R_ROT_DOWN, ref_at=(0, 3.45))
        check_vertical(fp, rx, R_Y1, R_PITCH)
        dx = rx - ex
        if E_STUB_Y + abs(dx) > R_Y1 + 1e-6:
            raise SystemExit("electrode %d: fan-out does not reach x before the resistor row" % j)
        bd.track([(ex, ey), (ex, E_STUB_Y), (rx, E_STUB_Y + abs(dx)), (rx, R_Y1)], N("A2", str(1 + j)))
        y2 = R_Y1 + R_PITCH
        bd.track([(rx, y2), (tx, y2 + R_DX), (tx, ty)], N("J2", str(1 + j)))

    # --- I2C pull-ups 4.7k to 3V3, above J1 (bus side of R15/R16) -------------------------------------------------------
    for ref, (x, y), net, rdx in (("R13", PU_SCL, N("J1", "1"), -2.2), ("R14", PU_SDA, N("J1", "2"), 2.2)):
        fp = place(bd, comps, pin_net, ref, x, y, rot=R_ROT_DOWN, ref_at=(rdx, 1.45))
        check_vertical(fp, x, y, 2.9)
        bd.track([(x, y + 2.9), (x, cy)], net)

    # --- GND from the first to the last J2 pad, along the edge (intentional spark gap, ADR-020) -------------------------
    a, z = term(0), term(13)
    bd.track([a, (a[0], H - 2.0), (z[0], H - 2.0), z], GND, W_PWR)

    # --- Copper text (ADR-023: no silkscreen assumed; stroke >= 0.5 mm, clearance >= 0.6 mm) ----------------------------
    bd.text("FrutaMIDI v1.3", 13.4, 55.0, pcbnew.F_Cu, 2.0, thick=0.5)
    bd.text("ORIG", 79.0, 18.75, pcbnew.F_Cu, 1.8, thick=0.5)    # selector legend (R-007): below JP1 pad 1
    bd.text("QT", 78.5, 5.0, pcbnew.F_Cu, 2.0, thick=0.5)       # above JP1 pad 3

    # --- Assembly-map texts (F.Fab only) --------------------------------------------------------------------------------
    labels = ["GND"] + ["E%d" % i for i in range(12)] + ["GND"]
    for i, lab in enumerate(labels):
        x, _ = term(i)
        bd.text(lab, x - (1.0 if i == 13 else 0.0), 60.0, pcbnew.F_Fab, 1.0 if lab == "GND" else 0.9)   # last label clear of the H3 washer circle
    bd.text("OCTAVE", 39.0, 6.0, pcbnew.F_Fab, 0.9)
    for k, lab in enumerate(("1 3V3", "2 WIPER", "3 AGND")):
        bd.text(lab, 39.6, RV_PAD[1] + 5.08 * k, pcbnew.F_Fab, 0.8)
    bd.text("SCALE", SW_C[0], SW_C[1] + 4.2, pcbnew.F_Fab, 1.0)
    bd.text("R1 ... R12 = 3k0 HPWC2512 (E0 ... E11), keep solder and flux off the 5 mm gap", 61.0, 46.4, pcbnew.F_Fab, 0.9)
    for k, line in enumerate(("JP1 3V3 selector:", "ORIG = no white connectors", "QT = 2 white connectors")):
        bd.text(line, 75.0, 29.5 + 1.55 * k, pcbnew.F_Fab, 0.8)
    bd.text("ORIG", JP1[0] - 3.9, JP1[1], pcbnew.F_Fab, 0.9)
    bd.text("QT", JP1[0] - 3.2, JP1[1] - 2 * JP1_PITCH, pcbnew.F_Fab, 0.9)
    bd.text("FrutaMIDI v1.3 assembly map, component side, pin 1 marked 1", 62.0, 67.0, pcbnew.F_Fab, 1.0)
    bd.text("github.com/catuta0/fruta-midi-controller", 60.0, 1.0, pcbnew.F_Fab, 0.8)

    ds = bd.b.GetDesignSettings()
    ds.SetAuxOrigin(VB(0, 0))          # Gerber/drill origin at the board corner
    ds.SetGridOrigin(VB(0, 0))
    pcbnew.SaveBoard(path, bd.b)
    return path


if __name__ == "__main__":
    build_footprints()
    print(build_board())
