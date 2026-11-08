"""C2 review: independent reading of Vishay doc 28766 p.10 '1.2/50 Pulse' chart (vector paths). CALCULATION."""
import math
# axis gridlines read from the content stream (PDF pt): x 10 ohm = 156.03, 100 ohm = 205.13, 1k = 254.23, 10k = 303.33
# y 10 V = 563.36, 100 V = 603.42, 1 kV = 643.49, 10 kV = 683.55
X10, XDEC = 156.03, (303.33 - 156.03) / 3
Y100, YDEC = 603.42, (683.55 - 603.42) / 2
curves = {"0414 (2 pt)": [(156.03, 617.9), (156.03 + 132.81, 617.9 + 53.784), (156.03 + 309.34, 617.9 + 53.637)],
          "0207 (1 pt)": [(156.03, 603.42), (156.03 + 147.48, 603.42 + 59.282), (156.03 + 309.34, 603.42 + 59.325)],
          "0204 (0.5 pt)": [(156.03, 595.79), (156.03 + 136.4, 595.79 + 59.992), (156.03 + 294.54, 595.79 + 59.912)]}
x = X10 + XDEC * math.log10(3300 / 10)
for n, c in curves.items():
    (x0, y0), (x1, y1), (x2, y2) = c
    y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    v = 100 * 10 ** ((y - Y100) / YDEC)
    slope = ((y1 - y0) / YDEC) / ((x1 - x0) / XDEC)
    rk = 10 * 10 ** ((x1 - X10) / XDEC)
    vp = 100 * 10 ** ((y1 - Y100) / YDEC)
    print("%-14s U(3k3) = %5.0f V  low-R slope dlogU/dlogR = %.3f  knee R = %5.0f ohm  plateau U = %5.0f V" % (n, v, slope, rk, vp))
# energy of a 1.2/50 us voltage pulse into R: integral V^2 dt ~ Vp^2 * tau2/2 * k, tau2 = 68.2 us, k=(1.037)^2
for vp in (4083.0,):
    e = (1.037 * vp) ** 2 / 3300 * 68.2e-6 / 2
    print("1.2/50 us energy at %.0f V into 3k3: %.0f mJ (script value: %.0f mJ)" % (vp, e * 1e3, vp ** 2 / 3300 * 1.44 * 50e-6 * 1e3))
# bend geometry
L, d, M = 11.9, 0.8, 15.24
print("lead-centre distance from body end at 15.24 mm pitch, L = 11.9 mm: %.2f mm" % ((M - L) / 2))
for r in (0.0, 0.8):
    print("bend start 1.5 mm, inner radius %.1f mm -> required pitch %.2f mm" % (r, L + 2 * (1.5 + r + d / 2)))
