#!/usr/bin/env python3
"""T-050: drill vs component pin, read from the generated board. Run with the KiCad Python (pcbnew).

Drill and pad sizes are MEASUREMENT of the design file (hardware/frutamidi.kicad_pcb).
Pin sizes are SOURCE where a datasheet was read, otherwise ASSUMPTION (stated per row).
Rule of thumb used (ASSUMPTION, common THT practice): drill >= pin max diagonal (square) or diameter + 0.2 mm
(the "gap" column is diametral, drill - pin; the radial clearance is half of it; T-073 / C2-008),
and annular ring (pad - drill)/2 >= 0.4 mm (home-etch rule, management/TOOLCHAIN / kicad-workflow skill).
"""
import math, os, sys
import pcbnew

BOARD = os.path.join(os.path.dirname(__file__), "..", "..", "..", "hardware", "frutamidi.kicad_pcb")

PINS = {  # footprint name -> (pin description, max pin cross-dimension mm, label)
    "RaspberryPi_Pico_Socket": ("female header tail 0.64 mm square (diag 0.91)", 0.64 * math.sqrt(2),
                                "ASSUMPTION: generic 2.54 mm female header, datasheet not read"),
    "Adafruit_MPR121_1982_Socket": ("female header tail 0.64 mm square (diag 0.91); Q-row: AWG24 wire 0.51 mm",
                                    0.64 * math.sqrt(2), "ASSUMPTION"),
    "WireHoles_1x07_P2.54mm": ("Q-row wire hole, AWG24 solid wire 0.51 mm", 0.51, "ASSUMPTION (wire gauge chosen by builder)"),
    "Config_2pads": ("AWG24 solid wire 0.51 mm", 0.51, "ASSUMPTION (wire gauge chosen by builder)"),
    "SolderJumper_3_THT_P3.81mm": ("resistor lead off-cut 0.45-0.50 mm as link (or solder bridge); T-076 pitch 3.81", 0.50,
                                   "SOURCE Yageo MFR lead (EE-S14)"),
    "C_Radial_KEMET_C322_P5.08mm_HomeEtch": ("KEMET C322 radial MLCC lead 0.51 mm (.020 in), T-076", 0.51,
                                             "SOURCE KEMET Golden Max dimension table (EE-S29)"),
    "TerminalBlock_5.08_1x14": ("Phoenix MKDS 1,5/2-5,08 pin 0.9 x 0.9 mm (diag 1.27); maker hole 1.3 mm",
                                0.9 * math.sqrt(2), "SOURCE Phoenix Contact 1715721 data (via search)"),
    "SW_PUSH_6mm": ("6x6 mm tact switch leg ~0.7 x 0.3 mm (diag 0.76)", 0.76, "ASSUMPTION"),
    "Potentiometer_RK09K_Vertical": ("Alps RK09K terminal ~0.8 x 0.5 mm (diag 0.94)", 0.94,
                                     "ASSUMPTION (Alps drawing is an image, not read)"),
    "R_Axial_DIN0204_P2.54mm_Vertical_HomeEtch": ("Yageo MFR-12 lead 0.45..0.50 mm", 0.50,
                                                  "SOURCE Yageo MFR datasheet (via search)"),
    "R_Axial_DIN0414_P15.24mm_Horizontal_HomeEtch": ("Vishay MBE/SMA 0414 lead 0.8 mm nominal (LSR37 alternative 0.7 mm)", 0.80,
                                                     "SOURCE Vishay doc. 28766 dimensions table (EE-S17), T-060"),
    "MountingHole_3.2mm_M3": ("M3 screw 3.0 mm", 3.0, "SOURCE ISO 273 fine clearance 3.2 mm"),
}

b = pcbnew.LoadBoard(BOARD)
rows = {}
for fp in b.GetFootprints():
    name = fp.GetFPID().GetLibItemName().wx_str() if hasattr(fp.GetFPID().GetLibItemName(), "wx_str") else str(fp.GetFPID().GetLibItemName())
    for p in fp.Pads():
        d = pcbnew.ToMM(p.GetDrillSize().x)
        s = pcbnew.ToMM(min(p.GetSize(pcbnew.F_Cu).x, p.GetSize(pcbnew.F_Cu).y)) if d else 0
        if not d:
            continue
        key = (name, round(d, 3), round(s, 3), p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH)
        rows[key] = rows.get(key, 0) + 1

print("# calc_mechanical.py  drill (MEASUREMENT of design file) vs pin (SOURCE/ASSUMPTION)")
print("%-42s %6s %7s %6s %7s %8s %7s  %s" % ("footprint", "drill", "pad_min", "count", "ring", "pin_max", "gap", "verdict / pin data"))
fails = 0
for (name, d, s, npth), n in sorted(rows.items()):
    desc, pin, lab = PINS.get(name, ("?", float("nan"), "unknown"))
    if name == "Adafruit_MPR121_1982_Socket" and d < 0.95:
        desc, pin, lab = "Q-row wire hole, AWG24 solid wire 0.51 mm", 0.51, "ASSUMPTION (wire gauge chosen by builder)"
    ring = (s - d) / 2 if not npth else float("nan")
    gap = d - pin
    # fit: PASS gap >= 0.2 mm (or the maker's own hole for the terminal block); PARTIAL 0 <= gap < 0.2 (fits, tight);
    # FAIL gap < 0. Ring: FAIL if < 0.4 mm (home-etch rule).
    maker_hole = False   # T-056: 1.4 mm drill judged on the gap like every other hole
    fit = "PASS" if (gap >= 0.2 - 1e-9 or maker_hole) else ("PARTIAL" if gap >= 0 else "FAIL")
    ok_ring = npth or ring >= 0.4 - 1e-9
    verdict = fit if ok_ring else "FAIL(ring)"
    fails += verdict.startswith("FAIL")
    print("%-42s %6.2f %7.2f %6d %7.2f %8.2f %7.2f  %s: %s [%s]" %
          (name, d, s, n, ring, pin, gap, verdict, desc, lab))
print("# rows FAIL: %d" % fails)
