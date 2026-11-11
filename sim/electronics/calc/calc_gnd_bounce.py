#!/usr/bin/env python3
"""T-073 / C2-005, inductances updated T-092 for the SMD board (no sockets): ESD strike on a terminal that arcs across the
1.40 mm E-pad <-> GND edge-track gap.

Every J2 electrode pad is 1.40 mm (MEASUREMENT, check_gap.out (c)) from the GND track along the bottom edge. That
is below the breakdown distance of every model in calc_flashover.out at 3.6 kV, so a 4 kV contact strike most
likely arcs to GND instead of driving 1.1 A through Rx into the MPR121 pin. This script estimates what the arc
current does on the way out (to the host through the Pico USB GND), in particular the voltage between the MPR121
module GND and the Pico GND (the only difference that reaches IC pins; a common rise of the whole board is not).

Runs with the KiCad Python (pcbnew): GND track lengths are MEASUREMENT on hardware/frutamidi.kicad_pcb.
Labels: SOURCE (EE-S16 IEC 61000-4-2 values from memory, not re-read; EE-S28 RP2040 ESD; EE-S01 MPR121 ESD),
ASSUMPTION (inductances, stated with a sweep), CALCULATION (everything else).
"""
import heapq
import math
import os
import sys

import pcbnew

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "hardware", "frutamidi.kicad_pcb")
TOMM = 1e-6

# SOURCE EE-S16 (IEC 61000-4-2, from memory): contact discharge first peak 3.75 A/kV +-15 %, rise time 0.8 ns +-25 %;
# current at 30 ns 2 A/kV, at 60 ns 1 A/kV.
KV = 4.0
I_PK = 3.75 * KV * 1.15           # A, upper tolerance
TR = (0.6e-9, 1.0e-9)             # s, rise time range
I30 = 2.0 * KV
# ASSUMPTION: 1.2 mm track without a ground plane 0.7 ... 1.0 nH/mm (thin-strip partial inductance, order of
# magnitude 1 nH/mm). To be checked only by the ESD test.
L_MM = (0.7e-9, 1.0e-9)
# T-092, board without sockets (ADR-023). Series elements between the board trunk and the two IC grounds (ASSUMPTION):
#   Pico castellation joint: 0.5 ... 1.5 nH (short solder fillet + module edge plating, about 1 mm at 0.5 ... 1.5 nH/mm)
#   MPR121 module header pin on the pad (T-103, F3-001 option a): exposed leg 3.0 mm + strip 2.5 mm (ASSUMPTION, standard
#     2.54 mm header) + through the 1.6 mm module board (ASSUMPTION) = 7.1 mm at 0.7 ... 1.2 nH/mm = 5.0 ... 8.5 nH
#     (T-092 had 4.1 mm, 2.9 ... 4.9 nH, with the strip butted on the pad)
# V1.2 used 3 ... 10 nH for female socket + male header pin.
L_CAST = (0.5e-9, 1.5e-9)
L_MODPIN = (5.0e-9, 8.5e-9)
L_PIN = (L_CAST[0] + L_MODPIN[0], L_CAST[1] + L_MODPIN[1])
R_SER, V_CLAMP = 220.0, 1.5       # R15/R16 (SOURCE schematic); two diode drops in the path (ASSUMPTION)
HBM_RP2040_KV = 4.0               # SOURCE EE-S28: RP2040 HBM 4 kV (JEDEC JS-001, "Digital (FT) pins only"), CDM 500 V
HBM_C, HBM_R = 100e-12, 1500.0    # HBM network (JEDEC JS-001, SOURCE from memory)


def gnd_graph(board, ox, oy):
    g = {}
    for t in board.GetTracks():
        if t.GetNetname() != "GND":
            continue
        a = (round(t.GetStart().x * TOMM - ox, 3), round(t.GetStart().y * TOMM - oy, 3))
        b = (round(t.GetEnd().x * TOMM - ox, 3), round(t.GetEnd().y * TOMM - oy, 3))
        d = math.hypot(a[0] - b[0], a[1] - b[1])
        g.setdefault(a, []).append((b, d))
        g.setdefault(b, []).append((a, d))
    return g


def shortest(g, src, dst):
    dist, q, prev = {src: 0.0}, [(0.0, src)], {}
    while q:
        d, u = heapq.heappop(q)
        if u == dst:
            break
        if d > dist.get(u, 1e9):
            continue
        for v, w in g.get(u, []):
            if d + w < dist.get(v, 1e9):
                dist[v], prev[v] = d + w, u
                heapq.heappush(q, (d + w, v))
    path, u = [dst], dst
    while u != src:
        u = prev[u]
        path.append(u)
    return dist[dst], path[::-1]


def main():
    board = pcbnew.LoadBoard(PCB)
    o = board.GetDesignSettings().GetAuxOrigin()
    ox, oy = o.x * TOMM, o.y * TOMM
    g = gnd_graph(board, ox, oy)
    pads = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pads[(fp.GetReference(), p.GetNumber())] = (round(p.GetPosition().x * TOMM - ox, 3),
                                                        round(p.GetPosition().y * TOMM - oy, 3))
    p23 = pads[("A1", "23")]
    # T-103: the A2 land now runs outward past the pin, so take the header pin position (module centre - 15.24, + 8.255 mm,
    # SOURCE Adafruit 1982 via T-090), where the GND track starts, instead of the land centre
    fa2 = board.FindFootprintByReference("A2")
    mod_gnd = (round(fa2.GetPosition().x * TOMM - ox - 15.24, 3), round(fa2.GetPosition().y * TOMM - oy + 8.255, 3))
    print("# calc_gnd_bounce.py  CALCULATION (T-073, C2-005; T-092 no sockets) on %s (KiCad %s)" % (os.path.relpath(PCB, ROOT), pcbnew.Version()))
    print("# series elements (ASSUMPTION): castellation %.1f-%.1f nH + module header pin %.1f-%.1f nH = %.1f-%.1f nH (V1.2: 3-10 nH socket + header)"
          % (L_CAST[0] * 1e9, L_CAST[1] * 1e9, L_MODPIN[0] * 1e9, L_MODPIN[1] * 1e9, L_PIN[0] * 1e9, L_PIN[1] * 1e9))
    # node where the module GND branch joins the terminal trunk: the vertex shared by the module->Pico and
    # terminal->Pico shortest paths that is farthest from the Pico
    l_mod, path_mod = shortest(g, mod_gnd, p23)
    t0 = pads[("J2", "1")]
    l_t0, path_t0 = shortest(g, t0, p23)
    shared = [v for v in path_t0 if v in set(path_mod)]
    n = shared[0]
    l_np23, _ = shortest(g, n, p23)
    print("GND path lengths (MEASUREMENT, design file): J2 pad 1 (GND terminal) -> Pico pin 23 %.2f mm; module GND pin ->"
          " Pico pin 23 %.2f mm; shared section from node (%.2f,%.2f) to pin 23 %.2f mm" % (l_t0, l_mod, n[0], n[1], l_np23))
    # longest arc path: farthest electrode pad along the edge track to J2 pad 1
    edge_y = max(v[1] for v in g)
    far = max((pads[("J2", str(k))] for k in range(2, 14)), key=lambda p: abs(p[0] - t0[0]))
    l_far = abs(far[0] - t0[0]) + (edge_y - t0[1])
    print("Arc entry: E pad -> edge track (y = %.2f) -> J2 pad 1: up to %.1f mm (E11); this section and the trunk to the"
          " node are common to module and Pico (whole-board rise, no differential at IC pins)" % (edge_y, l_far))
    print()
    print("IEC 61000-4-2 %.0f kV contact (SOURCE EE-S16 from memory, upper tolerance): Ipk %.1f A, tr %.1f-%.1f ns, I(30 ns) %.0f A"
          % (KV, I_PK, TR[0] * 1e9, TR[1] * 1e9, I30))
    print("%-34s %10s %10s %10s %12s %12s" % ("case (ASSUMPTION)", "L_diff nH", "di/dt A/ns", "Vb peak V", "I2C peak A",
                                               "I2C Q nC"))
    worst = None
    for lmm in L_MM:
        for lp in L_PIN:
            for tr in TR:
                L = l_np23 * lmm + lp
                didt = 0.8 * I_PK / tr                      # 10-90 % slope
                vb = L * didt
                i2c = max(0.0, vb - V_CLAMP) / R_SER
                q = i2c * tr                                # pulse lasts about one rise time
                name = "%.1f nH/mm, pin %.0f nH, tr %.1f ns" % (lmm * 1e9, lp * 1e9, tr * 1e9)
                print("%-34s %10.1f %10.1f %10.0f %12.2f %12.2f" % (name, L * 1e9, didt * 1e-9, vb, i2c, q * 1e9))
                if worst is None or vb > worst[0]:
                    worst = (vb, i2c, q, L)
    vb, i2c, q, L = worst
    v30 = L * (I_PK - I30) / 30e-9
    q_hbm = HBM_C * HBM_RP2040_KV * 1e3
    i_hbm = HBM_RP2040_KV * 1e3 / HBM_R
    print()
    print("Worst case: module GND - Pico GND bounce %.0f V for ~1 ns; after the first peak (slope to I(30 ns)) %.1f V"
          % (vb, v30))
    print("  through R15/R16 (220 ohm, then the BSS138 level shifters on the module): <= %.2f A, <= %.2f nC per line"
          % (i2c, q * 1e9))
    print("  RP2040 HBM %.0f kV (SOURCE EE-S28, stated for digital FT pins only) = %.2f A peak, %.0f nC -> injected charge"
          " %.1f %% of the HBM charge, peak %.2fx the HBM peak" % (HBM_RP2040_KV, i_hbm, q_hbm * 1e9, 100 * q / q_hbm,
                                                              i2c / i_hbm))
    print("  NOT CONFIRMED: GP26/GP27 (I2C1 on the PCB) are ADC-capable pins; the extracted RP2040 table gives HBM 4 kV for"
          " FT pins and CDM 500 V, no separate HBM value for these pins was found (EE-S28)")
    print("  without the arc (strike through Rx into the MPR121 pin): pin current %.2f A (R 3k3 + 330 ohm source, CALCULATION), bounce"
          " scaled by %.2f -> %.0f V" % (KV * 1e3 / 3630, KV * 1e3 / 3630 / I_PK, vb * KV * 1e3 / 3630 / I_PK))
    print("DECISION INPUT: the 1.40 mm gap acts as a spark gap to GND at every terminal; it keeps the strike off the"
          " MPR121 pin; residual risk = %.0f V / ~1 ns GND bounce between module and Pico (ASSUMPTION-based), not measured"
          % vb)
    return 0


if __name__ == "__main__":
    sys.exit(main())
