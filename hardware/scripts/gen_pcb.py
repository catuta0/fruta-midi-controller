#!/usr/bin/env python3
"""Gera a biblioteca de footprints (FrutaMIDI.pretty) e a PCB de uma face (frutamidi.kicad_pcb).

Corre com o Python do KiCad (precisa do módulo pcbnew), depois de gen_schematic.py:
    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
        hardware/scripts/gen_pcb.py

Regras pensadas para gravação química caseira (toner ou fotossensível):
  pistas >= 1,0 mm, isolamento >= 0,6 mm, pads largos (anel >= 0,4 mm), sem vias, cobre só em baixo.
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

    # --- Raspberry Pi Pico em 2 barras fêmea 1x20 (origem = pino 1, USB para cima)
    fp = new_fp("RaspberryPi_Pico_Socket", "Raspberry Pi Pico / Pico 2 / W em 2 barras fêmea 1x20, pads ovais para gravação caseira")
    for k in range(1, 21):
        add_pad(fp, str(k), 0, (k - 1) * 2.54, RECT if k == 1 else OVAL, 2.4, 1.6, 1.0)
        add_pad(fp, str(41 - k), 17.78, (k - 1) * 2.54, OVAL, 2.4, 1.6, 1.0)
    add_rect(fp, pcbnew.F_SilkS, -1.61, -1.37, 19.39, 49.63)
    add_rect(fp, pcbnew.F_SilkS, 5.39, -1.37, 12.39, 3.5)                 # conector USB
    add_text(fp, "USB", 8.89, 5.2, size=1.2)
    add_text(fp, "1", -2.6, 0, size=1.0)
    add_rect(fp, pcbnew.F_CrtYd, -2.0, -1.8, 19.8, 50.0, 0.05)
    add_rect(fp, pcbnew.F_Fab, -1.61, -1.37, 19.39, 49.63, 0.1)
    for model in lib_fp("Module", "RaspberryPi_Pico_Common_THT").Models():
        fp.Add3DModel(model)
    out["RaspberryPi_Pico_Socket"] = fp

    # --- Adafruit MPR121 (1982) em barras fêmea: 1x13 (elétrodos) + 1x7 (alimentação/I2C)
    # Orientação: rodado 180° em relação aos ficheiros Eagle da Adafruit, elétrodos em baixo.
    # Pads 14-20 repetidos mais acima (fila Q): furos para os fios de configuração.
    fp = new_fp("Adafruit_MPR121_1982_Socket",
                "Adafruit MPR121 breakout (1982, original ou STEMMA QT) em barras fêmea 1x13 + 1x7; fila Q para fios de configuração")
    for j in range(13):
        add_pad(fp, str(1 + j), -15.24 + 2.54 * j, 8.255, RECT if j == 0 else OVAL, 1.6, 2.4, 1.0)
    for k in range(7):
        x = -7.62 + 2.54 * k
        add_pad(fp, str(14 + k), x, -6.985, OVAL, 1.6, 2.4, 1.0)
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

    # --- 3 furos de configuração (SDA, SCL, 3V3)
    fp = new_fp("Config_3pads", "3 furos para fios de configuração: SDA, SCL, 3V3")
    for k, lab in enumerate(("SDA", "SCL", "3V3")):                    # pad 1 = 3V3 (à direita)
        add_pad(fp, str(3 - k), 3.81 * k, 0, RECT if k == 2 else CIRC, 2.2, 2.2, 0.9)
        add_text(fp, lab, 3.81 * k, -2.3, size=0.9)
    add_rect(fp, pcbnew.F_CrtYd, -1.6, -3.2, 9.2, 1.6, 0.05)
    out["Config_3pads"] = fp

    # --- Terminal de parafuso 5,08 mm (pads maiores)
    fp = lib_fp("TerminalBlock_Phoenix", "TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "TerminalBlock_5.08_1x02"))
    for p in fp.Pads():
        set_pad(p, RECT if p.GetNumber() == "1" else CIRC, 3.0, 3.0, 1.3)
    # blocos encostados uns aos outros (passo 5,08 contínuo): pátio = largura exata do bloco
    replace_courtyard(fp, [(-2.52, -5.7), (7.6, -5.7), (7.6, 5.0), (-2.52, 5.0)])
    replace_layer(fp, pcbnew.F_SilkS)
    add_rect(fp, pcbnew.F_SilkS, -2.3, -5.4, 7.38, 4.4)
    add_line(fp, pcbnew.F_SilkS, -2.3, 2.6, 7.38, 2.6)          # frente (entrada dos fios)
    out["TerminalBlock_5.08_1x02"] = fp

    # --- 14 vias = 7 blocos de 2 vias encaixados (pino 1 à esquerda)
    fp = new_fp("TerminalBlock_5.08_1x14", "7 blocos de terminais de parafuso 2 vias, passo 5,08 mm, encaixados")
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

    # --- Botão 6 mm
    fp = lib_fp("Button_Switch_THT", "SW_PUSH_6mm")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "SW_PUSH_6mm"))
    for p in fp.Pads():
        set_pad(p, CIRC, 2.4, 2.4, 1.1)
    fp.SetDuplicatePadNumbersAreJumpers(True)     # as pernas iguais estão ligadas dentro do botão
    out["SW_PUSH_6mm"] = fp

    # --- Potenciómetro 9 mm (Alps RK09K e compatíveis), vertical
    fp = lib_fp("Potentiometer_THT", "Potentiometer_Alps_RK09K_Single_Vertical")
    fp.SetFPID(pcbnew.LIB_ID("FrutaMIDI", "Potentiometer_RK09K_Vertical"))
    for p in fp.Pads():
        if p.GetNumber() in ("1", "2", "3"):
            set_pad(p, RECT if p.GetNumber() == "1" else OVAL, 2.6, 1.7, 1.0)
    out["Potentiometer_RK09K_Vertical"] = fp

    # --- Furo M3
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
    pin_net = {}
    for m in re.finditer(r'\(name "([^"]+)"\)\s*\(class', t):
        start = m.end()
        end = t.find("(net", start)
        seg = t[start:end if end > 0 else len(t)]
        for ref, pin in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', seg):
            pin_net[(ref, pin)] = m.group(1)
    return comps, pin_net


# =========================================================================== placa

W, H = 100.0, 70.0
PICO = (4.5, 2.0)                 # pino 1
POT = (28.0, 12.16)               # pino 1 do potenciómetro
BTN = (27.0, 29.94)               # pad 1 (canto sup. esquerdo)
MOD_C = (57.48, 32.745)           # centro do módulo
CFG = (44.0, 15.0)                # pad SDA da configuração
T0, TY = 27.0, 64.5               # primeiro terminal (GND), linha dos terminais
HOLES = [(8.0, 64.0), (95.0, 5.0), (95.0, 48.0), (70.0, 6.0)]

W_SIG, W_PWR, W_STUB = 1.0, 1.2, 0.8

# A placa fica afastada do canto da folha, para a impressora não cortar nada a 100 %.
OX, OY = 50.0, 50.0
VB = lambda x, y: V(OX + x, OY + y)


def pico_pin(n):
    x0, y0 = PICO
    if n <= 20:
        return x0, y0 + (n - 1) * 2.54
    return x0 + 17.78, y0 + (40 - n) * 2.54


def mod_e(j):           # j = 0 (GND) … 12 (E11)
    return MOD_C[0] - 15.24 + 2.54 * j, MOD_C[1] + 8.255


def mod_s(k):           # k = 1 … 7
    return MOD_C[0] - 7.62 + 2.54 * (k - 1), MOD_C[1] - 6.985


def mod_q(k):
    x, y = mod_s(k)
    return x, y - 5.08


def term(i):            # i = 0 … 13
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

    # --- GND: escada debaixo do Pico (une todos os GND do Pico) ---------------------------
    xb = PICO[0] + 8.89
    bd.track([(xb, pico_pin(3)[1]), (xb, pico_pin(18)[1])], GND, W_PWR)
    bd.track([pico_pin(3), pico_pin(38)], GND, W_PWR)
    bd.track([pico_pin(8), (xb, pico_pin(8)[1])], GND, W_PWR)
    bd.track([pico_pin(13), pico_pin(28)], GND, W_PWR)
    bd.track([pico_pin(18), pico_pin(23)], GND, W_PWR)

    # --- Potenciómetro: 3V3 (pino 1), cursor (2), AGND (3) ----------------------------------
    px, py = POT
    bd.track([pico_pin(36), (25.0, py), (px, py)], V33, W_PWR)
    p34 = pico_pin(34)
    bd.track([p34, (24.0, p34[1]), (24.0 + (p34[1] - (py + 2.5)), py + 2.5), (px, py + 2.5)], N("A1", "34"))
    p33 = pico_pin(33)
    bd.track([p33, (24.6, p33[1]), (24.6 + (p33[1] - (py + 5.0)), py + 5.0), (px, py + 5.0)], N("A1", "33"))

    # --- 3V3 por cima do potenciómetro até ao furo de configuração ---------------------------
    cx, cy = CFG
    c3v3 = (cx + 2 * 3.81, cy)
    bd.track([(25.0, pico_pin(36)[1]), (25.0, 6.0), (c3v3[0], 6.0), c3v3], V33, W_PWR)

    # --- I2C: SCL (GP27, pino 32) e SDA (GP26, pino 31) ---------------------------------------
    p32 = pico_pin(32)
    bd.track([p32, (41.0, p32[1]), (41.0, 11.0), (cx + 3.81, 11.0), (cx + 3.81, cy)], N("A1", "32"))
    p31 = pico_pin(31)
    bd.track([p31, (cx, p31[1]), (cx, cy)], N("A1", "31"))

    # --- Fila S do módulo ligada à fila Q (furos para os fios) --------------------------------
    for k in range(1, 8):
        bd.track([mod_s(k), mod_q(k)], N("A2", str(13 + k)), W_STUB)

    # --- Botão: GP22 (pino 29) e GND (pino 28) -----------------------------------------------
    bx, by = BTN
    bd.track([pico_pin(29), (bx, by)], N("A1", "29"))
    p28 = pico_pin(28)
    bd.track([p28, (24.5, p28[1]), (bx, by + 4.5)], GND, W_PWR)

    # --- GND do módulo e do 1.º terminal, a partir do pino 23 do Pico ---------------------------
    g = mod_e(0)
    p23 = pico_pin(23)
    k = g[0] - (p23[1] - g[1])                     # início da subida a 45°
    t1 = term(0)
    bd.track([p23, (t1[0], p23[1]), (k, p23[1]), g], GND, W_PWR)
    bd.track([(t1[0], p23[1]), t1], GND, W_PWR)

    # --- Leque: elétrodos (GND, E0…E11) até aos terminais ---------------------------------------
    for j in range(1, 13):
        ex, ey = mod_e(j)
        tx, ty = term(j)
        bd.track([(ex, ey), (ex, ey + 3.0), (tx, ty - 3.0), (tx, ty)], N("A2", str(1 + j)))

    # --- GND do primeiro ao último terminal, junto à borda -------------------------------------
    a, z = term(0), term(13)
    bd.track([a, (a[0], H - 2.0), (z[0], H - 2.0), z], GND, W_PWR)

    # --- Textos ----------------------------------------------------------------------------------
    bd.text("FrutaMIDI v1.0", 82.0, 12.0, pcbnew.B_Cu, 2.0, mirror=True)
    bd.text("cobre: face de baixo", 82.0, 15.5, pcbnew.B_Cu, 1.2, mirror=True)
    bd.text("FrutaMIDI v1.0", 82.0, 12.0, pcbnew.F_SilkS, 2.0)
    bd.text("github.com/catuta0/fruta-midi-controller", 72.0, 2.2, pcbnew.F_SilkS, 1.0)
    labels = ["GND"] + [str(i) for i in range(12)] + ["GND"]
    for i, lab in enumerate(labels):
        x, _ = term(i)
        bd.text(lab, x, 57.6, pcbnew.F_SilkS, 1.1)
    bd.text("OITAVA", POT[0] + 7.0, 24.0, pcbnew.F_SilkS, 1.0)
    bd.text("ESCALA", BTN[0] + 3.25, BTN[1] + 7.6, pcbnew.F_SilkS, 1.0)

    ds = bd.b.GetDesignSettings()
    ds.SetAuxOrigin(VB(0, 0))          # origem dos Gerbers/furação no canto da placa
    ds.SetGridOrigin(VB(0, 0))
    pcbnew.SaveBoard(path, bd.b)
    return path


if __name__ == "__main__":
    build_footprints()
    print(build_board())
