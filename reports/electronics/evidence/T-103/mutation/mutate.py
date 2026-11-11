"""T-103: mutation proofs for the new check_smd.py checks. Writes mutated scratch copies of the board (never the real
board) and runs check_smd.py on each. Usage: KiCad python3 mutate.py <out_dir>"""
import os, subprocess, sys
import pcbnew

ROOT = "/Users/rod/fruta-midi-controller"
SRC = os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")
OUT = sys.argv[1]
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))


def m1(b):   # A2 lands back to the T-090 1.8 x 2.4 mm pads under the strip
    for p in b.FindFootprintByReference("A2").Pads():
        n = int(p.GetNumber())
        rel = p.GetFPRelativePosition()
        p.SetSize(pcbnew.F_Cu, V(1.8, 2.4))
        p.SetFPRelativePosition(pcbnew.VECTOR2I(rel.x, mm(8.255 if n <= 13 else -6.985)))


def m2(b):   # Pico 1.0 mm further onto the board
    f = b.FindFootprintByReference("A1")
    f.Move(V(0, 1.0))


def m3(b):   # a 1.0 mm track through the Pico 2 TP7 position
    f = b.FindFootprintByReference("A1")
    c = f.GetPosition() + V(9.89, 19.13)
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(c - V(1.0, 0)); t.SetEnd(c + V(1.0, 0)); t.SetWidth(mm(1.0)); t.SetLayer(pcbnew.F_Cu)
    b.Add(t)


def m4(b):   # C1 lands back to the 1.15 mm IPC reflow length
    for p in b.FindFootprintByReference("C1").Pads():
        rel = p.GetFPRelativePosition()
        p.SetSize(pcbnew.F_Cu, V(1.15, 1.8))
        p.SetFPRelativePosition(pcbnew.VECTOR2I(0 if p.GetNumber() == "1" else mm(2.9), rel.y))


for name, fn in (("M1_A2_short_lands", m1), ("M2_A1_moved_in", m2), ("M3_track_on_TP7", m3), ("M4_C1_short_lands", m4)):
    b = pcbnew.LoadBoard(SRC)
    fn(b)
    path = os.path.join(OUT, name + ".kicad_pcb")
    pcbnew.SaveBoard(path, b)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "sim/electronics/calc/check_smd.py"), path],
                       capture_output=True, text=True)
    open(os.path.join(OUT, name + ".out"), "w").write(r.stdout)
    print("== %s exit %d" % (name, r.returncode))
    for line in r.stdout.splitlines():
        if line.startswith("FAIL") or line.startswith("SUMMARY"):
            print(line)
