"""Independent reviewer T-102: geometry checks on hardware/frutamidi.kicad_pcb @ 9505245 (board coordinates = KiCad - (50, 50)).
Inputs are copied from canon_committed.txt (pcbnew dump) and gen_pcb.py constants; labels in comments."""
OX = OY = 50.0
# A2 module: centre (60.02, 17.645), F.Fab outline +-16.51 x +-9.525 (gen_pcb.py, from Adafruit Eagle per T-090)
mod_y0, mod_y1 = 17.645 - 9.525, 17.645 + 9.525
STRIP_W = 2.54     # ASSUMPTION: standard 2.54 mm header plastic strip width (not measured)
for row, yc in (("power/I2C row S1..S7", 10.66), ("electrode row GND,E0..E11", 25.90)):
    p0, p1 = yc - 1.2, yc + 1.2               # pad 2.4 mm long in y (SOURCE design file)
    s0, s1 = yc - STRIP_W / 2, yc + STRIP_W / 2
    print("%s: pad y %.2f..%.2f; strip y %.2f..%.2f; module outline y %.2f..%.2f; pad length outside strip %.2f mm, outside module %.2f mm"
          % (row, p0, p1, s0, s1, mod_y0, mod_y1, max(0, s0 - p0) + max(0, p1 - s1), max(0, mod_y0 - p0) + max(0, p1 - mod_y1)))
# USB: Pico pin-1 hole at y 2.0, pin 1 is 1.37 mm from the Pico edge (SOURCE 51 mm length, 20 x 2.54 pitch), USB 1.3 mm overhang (SOURCE RP-008307 via T-090)
pico_edge = 2.0 - (51 - 19 * 2.54) / 2
print("Pico USB-end edge y %.2f mm; receptacle face y %.2f mm -> %.2f mm beyond the board edge (CALCULATION)" % (pico_edge, pico_edge - 1.3, 1.3 - pico_edge))
# Pico 2 TP7 (SOURCE Pico 2 datasheet Fig. 5: (11.5, 30.5) from bottom-left, 1.5 x 1.5 mm) in board coordinates
px0 = 4.5 - (21 - 17.78) / 2
tx, ty = px0 + 11.5, pico_edge + (51 - 30.5)
print("Pico 2 TP7 centre (%.2f, %.2f), x %.2f..%.2f; right GND rail edge x 18.80 -> gap %.2f mm; outside both keep-out rule areas (TP area y<=14.98, SWD y>=47.83)"
      % (tx, ty, tx - 0.75, tx + 0.75, 18.80 - (tx + 0.75)))
# SW1 pad 1L (BTN) vs A1 pin 30 (RUN) anchor pad (design file)
a30 = (23.58 + 2.1, 27.40)       # right edge x of pin 30 land
sw = 27.525 - 0.775
print("A1 pin 30 (RUN) land right edge x %.2f, SW1 pad 1L (BTN) left edge x %.2f -> gap %.2f mm; y overlap 27.33..28.20" % (a30[0], sw, sw - a30[0]))
# JP1 etched legend vs pads (design file, rotated 90 deg: pads 2.4 wide in x, 1.94 tall in y)
for n, y in (("pad1 S1/ORIG", 15.74), ("pad2 3V3", 11.93), ("pad3 S7/QT", 8.12)):
    print("JP1 %s y %.2f..%.2f" % (n, y - 0.97, y + 0.97))
print("etched ORIG text centre (74.0, 13.2), height 1.8 -> y 12.30..14.10 (between pad 2 and pad 1, left of JP1); etched QT centre (78.5, 5.0) -> y 4.0..6.0 (above pad 3)")
# ESD charge comparison (CALCULATION)
print("IEC 150 pF x 4 kV = %.0f nC; HBM 100 pF x 2 kV = %.0f nC; ratio %.1f; tau IEC (3300+330) x 150 pF = %.2f us, HBM 1500 x 100 pF = %.2f us"
      % (150e-12 * 4000 * 1e9, 100e-12 * 2000 * 1e9, 600 / 200, 3630 * 150e-12 * 1e6, 1500 * 100e-12 * 1e6))
