#!/usr/bin/env python3
"""T-095: one-board quote totals, LCSC against Mouser Portugal. CALCULATION from the prices in distributor_pages.txt."""
USD_PER_EUR = 1.1193  # SOURCE: ECB euro reference rate, 9 November 2026

# name, quantity paid, unit price USD (minimums and multiples already applied)
LCSC = [
    ("R13-14 FRC1206F4701TS", 100, 0.0040),
    ("R15-16 FRC1206F2200TS", 100, 0.0046),
    ("C1 CL31B104KBCNNNC", 20, 0.0143),
    ("SW1 B3S-1000", 5, 0.365),
    ("RV1 RK09D1130C2P", 1, 0.7417),
]
LCSC_R = {"CRGP2512F3K3": (12, 0.3359), "CMB02070X3301GB200": (12, 0.9719)}
PICO2 = 9.3787
MODULE_NOT_ORDERABLE = 21.6846

MOUSER = [
    ("A1 SC0915", 1, 3.44),
    ("A2 Adafruit 1982", 1, 6.84),
    ("R13-14 RC1206FR-074K7L", 2, 0.086),
    ("R15-16 RC1206FR-07220RL", 2, 0.086),
    ("C1 CL31B104KBCNNNC", 1, 0.12),
    ("SW1 B3S-1000", 1, 0.697),
    ("RV1 PTV09A-4015F-B103", 1, 0.765),
    ("Knob SPK-016A", 1, 0.327),
]
MOUSER_R = {"HPWC2512-3K3JT1": (12, 1.25), "CMB02070X3301GB200": (12, 0.422)}


def main():
    print("# compute_quote.py T-095  CALCULATION; rate %.4f USD per EUR (SOURCE, ECB, 2026-11-09)" % USD_PER_EUR)
    usd = 0.0
    print("LCSC lines")
    for n, q, p in LCSC:
        print("  %-26s %4d x %.4f USD = %.3f USD = %.3f EUR" % (n, q, p, q * p, q * p / USD_PER_EUR))
        usd += q * p
    print("LCSC common lines: %.3f USD = %.2f EUR" % (usd, usd / USD_PER_EUR))
    for n, (q, p) in LCSC_R.items():
        r = q * p
        print("  R1-R12 %-20s %.3f USD = %.2f EUR; with common lines %.2f EUR; with Pico 2 %.2f EUR"
              % (n, r, r / USD_PER_EUR, (usd + r) / USD_PER_EUR, (usd + r + PICO2) / USD_PER_EUR))
    print("Pico 2 alternative: %.2f EUR" % (PICO2 / USD_PER_EUR))
    print("Adafruit 1982 listed price, stock 0, not orderable: %.2f EUR" % (MODULE_NOT_ORDERABLE / USD_PER_EUR))
    r = LCSC_R["CRGP2512F3K3"]
    print("Hypothetical if the module were in stock, CRGP and Pico 2, no knob: %.2f EUR"
          % ((usd + r[0] * r[1] + PICO2 + MODULE_NOT_ORDERABLE) / USD_PER_EUR))
    eur = 0.0
    print("Mouser lines")
    for n, q, p in MOUSER:
        print("  %-26s %4d x %.3f EUR = %.3f EUR" % (n, q, p, q * p))
        eur += q * p
    print("Mouser common lines: %.3f EUR" % eur)
    for n, (q, p) in MOUSER_R.items():
        print("  R1-R12 %-20s %.2f EUR; total %.2f EUR" % (n, q * p, eur + q * p))


if __name__ == "__main__":
    main()
