#!/usr/bin/env python3
"""T-006-EE smoke test: minimal KiCad 10 project (J1 Conn_01x02 + R1 in a loop, 2 nets).

Run with the KiCad Python (needs pcbnew):
    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
        sim/electronics/smoke/gen_smoke.py

Writes smoke.kicad_pro, smoke.kicad_sch, smoke.kicad_pcb next to this script, then reloads the
board and prints footprint/track counts. Patterns follow hardware/scripts/gen_*.py (read-only).
"""
import json, os, re, subprocess, uuid
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
PROJECT = "smoke"
ROOT_UUID = "0b7e5c1a-1d2f-4e3a-9b8c-7d6e5f4a3b21"
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
det = lambda *p: str(uuid.uuid5(uuid.NAMESPACE_URL, "frutamidi-smoke/" + "/".join(p)))

PARTS = {  # ref: (lib, symbol, value, footprint)
    "J1": ("Connector_Generic", "Conn_01x02", "Conn_01x02",
           "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"),
    "R1": ("Device", "R", "1k",
           "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"),
}
NETS = {("J1", "1"): "N1", ("R1", "1"): "N1", ("J1", "2"): "N2", ("R1", "2"): "N2"}


# ------------------------------------------------------------------ schematic
def lib_symbol(lib, name):
    t = open(os.path.join(KICAD, "symbols", lib + ".kicad_sym"), encoding="utf-8").read()
    i = t.index('(symbol "%s"' % name)
    d = 0
    for j in range(i, len(t)):
        d += {"(": 1, ")": -1}.get(t[j], 0)
        if d == 0:
            return t[i:j + 1]


PIN_RE = re.compile(r'\(pin (\w+) (\w+)\s+\(at ([-\d.]+) ([-\d.]+) (\d+)\)\s+\(length ([\d.]+)\).*?\(number "([^"]*)"', re.S)


def gen_schematic():
    libs, items = [], []
    pos = {"J1": (101.6, 101.6), "R1": (127.0, 101.6)}
    for ref, (lib, name, value, fp) in PARTS.items():
        raw = lib_symbol(lib, name)
        pins = {m.group(7): (float(m.group(3)), float(m.group(4)), int(m.group(5))) for m in PIN_RE.finditer(raw)}
        libs.append(raw.replace('(symbol "%s"' % name, '(symbol "%s:%s"' % (lib, name), 1))
        x, y = pos[ref]
        pin_uuids = "".join('\n\t\t(pin "%s" (uuid "%s"))' % (n, det("pin", ref, n)) for n in pins)
        items.append(f'''	(symbol (lib_id "{lib}:{name}") (at {x:.2f} {y:.2f} 0) (unit 1)
		(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)
		(uuid "{det('sym', ref)}")
		(property "Reference" "{ref}" (at {x + 2.54:.2f} {y - 5.08:.2f} 0) (effects (font (size 1.27 1.27))))
		(property "Value" "{value}" (at {x + 2.54:.2f} {y + 6.35:.2f} 0) (effects (font (size 1.27 1.27))))
		(property "Footprint" "{fp}" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Datasheet" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes)))
		(property "Description" "" (at {x:.2f} {y:.2f} 0) (effects (font (size 1.27 1.27)) (hide yes))){pin_uuids}
		(instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))
	)''')
        for num, (px, py, a) in pins.items():
            ex, ey = x + px, y - py                      # symbol Y is inverted on the sheet
            dx, dy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[a]
            sx, sy = ex + dx * 2.54, ey + dy * 2.54
            items.append('\t(wire (pts (xy %.2f %.2f) (xy %.2f %.2f)) (stroke (width 0) (type default)) (uuid "%s"))'
                         % (ex, ey, sx, sy, det("w", ref, num)))
            ang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[(dx, dy)]
            just = "right" if ang in (180, 270) else "left"
            items.append('\t(label "%s" (at %.2f %.2f %d) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'
                         % (NETS[(ref, num)], sx, sy, ang, just, det("l", ref, num)))
    lib_txt = "\n".join("\t\t" + s.replace("\n", "\n\t\t") for s in libs)
    body = "\n".join(items)
    out = f'''(kicad_sch
	(version 20250114)
	(generator "frutamidi_smoke")
	(generator_version "1.0")
	(uuid "{ROOT_UUID}")
	(paper "A4")
	(title_block (title "T-006-EE smoke test") (date "2026-10-30") (rev "0"))
	(lib_symbols
{lib_txt}
	)
{body}
	(sheet_instances (path "/" (page "1")))
	(embedded_fonts no)
)
'''
    open(os.path.join(HERE, PROJECT + ".kicad_sch"), "w", encoding="utf-8").write(out)


def gen_project():
    pro = {"meta": {"filename": PROJECT + ".kicad_pro", "version": 3}}
    json.dump(pro, open(os.path.join(HERE, PROJECT + ".kicad_pro"), "w"), indent=2)


# ------------------------------------------------------------------ board
def read_netlist():
    net_path = os.path.join(HERE, "build", PROJECT + ".net")
    os.makedirs(os.path.dirname(net_path), exist_ok=True)
    subprocess.run([KICAD_CLI, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net_path,
                    os.path.join(HERE, PROJECT + ".kicad_sch")], check=True, capture_output=True)
    t = open(net_path, encoding="utf-8").read()
    pin_net = {}
    for m in re.finditer(r'\(name "([^"]+)"\)\s*\(class', t):
        end = t.find("(net", m.end())
        for ref, pin in re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"\)', t[m.end():end if end > 0 else len(t)]):
            pin_net[(ref, pin)] = m.group(1)
    return pin_net


OX, OY, W, H, W_TRK = 100.0, 100.0, 30.0, 20.0, 1.0
B = lambda x, y: V(OX + x, OY + y)


def gen_board():
    pin_net = read_netlist()
    path = os.path.join(HERE, PROJECT + ".kicad_pcb")
    b = pcbnew.NewBoard(path)
    nets = {}
    for n in sorted(set(pin_net.values())):
        nets[n] = pcbnew.NETINFO_ITEM(b, n)
        b.Add(nets[n])
    for a, c, d, e in ((0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)):
        s = pcbnew.PCB_SHAPE(b, pcbnew.SHAPE_T_SEGMENT)
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(B(a, c))
        s.SetEnd(B(d, e))
        s.SetWidth(mm(0.15))
        b.Add(s)
    place = {"J1": (5.0, 7.0), "R1": (12.0, 7.0)}      # pad 1 positions (board-relative mm)
    for ref, (lib, name, value, fpid) in PARTS.items():
        flib, fname = fpid.split(":")
        fp = pcbnew.FootprintLoad(os.path.join(KICAD, "footprints", flib + ".pretty"), fname)
        fp.SetFPID(pcbnew.LIB_ID(flib, fname))
        fp.SetReference(ref)
        fp.SetValue(value)
        fp.SetPath(pcbnew.KIID_PATH("/" + det("sym", ref)))
        fp.SetPosition(B(*place[ref]))
        for p in fp.Pads():
            p.SetNet(nets[pin_net[(ref, p.GetNumber())]])
        b.Add(fp)

    def track(pts, net):
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(B(x1, y1))
            t.SetEnd(B(x2, y2))
            t.SetWidth(mm(W_TRK))
            t.SetLayer(pcbnew.B_Cu)
            t.SetNet(nets[net])
            b.Add(t)

    n1 = pin_net[("J1", "1")]
    n2 = pin_net[("J1", "2")]
    track([(5.0, 7.0), (12.0, 7.0)], n1)                                   # J1.1 -> R1.1
    track([(5.0, 9.54), (5.0, 14.0), (22.16, 14.0), (22.16, 7.0)], n2)    # J1.2 -> R1.2
    pcbnew.SaveBoard(path, b)
    return path


def reopen(path):
    b = pcbnew.LoadBoard(path)
    tracks = [t for t in b.GetTracks() if t.GetClass() == "PCB_TRACK"]
    widths = sorted({round(pcbnew.ToMM(t.GetWidth()), 3) for t in tracks})
    layers = sorted({b.GetLayerName(t.GetLayer()) for t in tracks})
    bbox = b.GetBoardEdgesBoundingBox()
    print("reopen: footprints=%d tracks=%d track_widths_mm=%s track_layers=%s nets=%s outline_mm=%.2fx%.2f"
          % (len(b.GetFootprints()), len(tracks), widths, layers,
             sorted(str(n) for n in b.GetNetsByName().keys() if str(n)),
             pcbnew.ToMM(bbox.GetWidth()), pcbnew.ToMM(bbox.GetHeight())))
    for fp in b.GetFootprints():
        print("  %s %s pads=%s" % (fp.GetReference(), str(fp.GetFPID().GetUniStringLibId()),
                                   [(p.GetNumber(), p.GetNetname()) for p in fp.Pads()]))


if __name__ == "__main__":
    gen_project()
    gen_schematic()
    reopen(gen_board())
