#!/usr/bin/env python3
"""T-050 critical block: user-touched electrode path (screw terminal -> track -> R_series -> MPR121 ELEx).

SIMULATION (closed-form, piecewise-linear circuit; pure Python 3, no dependencies):
  MPR121 constant-current measurement (datasheet: "constant DC current capacitance sensing",
  sampled by a 10-bit ADC "at the end of each charge cycle"; Cin = I*T/V, Eqn. 4).
  Two-node model:
      current source I (CDC) -> node P (C_pin = MPR121 ELE self-capacitance 15 pF SOURCE
      + module trace/header ASSUMPTION 2 pF) -> R_series -> node E (C_ext: our track + terminal +
      wire + object).
  Charge phase: I for T (CDT). ADC samples V_P at t = T.
  Discharge phase: ASSUMPTION electrode pin switched to VSS for the same time T
      (the datasheet scan-time example counts "32 us + 32 us" per sample = charge + discharge).
  FFI = 6 consecutive samples per electrode (Adafruit library: CONFIG1 0x10 -> FFI = 6);
      residual charge carries from one sample to the next; reported value = mean of the 6.
  AUTOCONFIG (Adafruit_MPR121::setAutoconfig): USL = 200, TL = 180, LSL = 130 (8-bit, ADC >> 2),
      SCTS = 0 (AUTOCONFIG1 not written -> reset value) so the chip searches CDC (1..63 uA) and
      CDT (0.5..32 us). The chip's exact search order is not published: we report the set of
      valid (CDC, CDT) pairs and three choices: closest-to-TL (nominal), best and worst
      sensitivity inside the valid window.

Outputs: printed tables (saved as sim_electrode.out by run_all.sh).
"""
import math

VDD = 3.29            # V, MPR121 supply = Pico 3V3 (3.30 V nominal) - LDO dropout (CALCULATION, see calc_supply.py)
C_PIN = 15e-12 + 2e-12
USL, TL, LSL = 200, 180, 130
CDT_SET = [0.5e-6 * 2 ** k for k in range(7)]          # 0.5 .. 32 us (SOURCE MPR121 CDT encodings 1..7)
CDC_SET = [k * 1e-6 for k in range(1, 64)]              # 1 .. 63 uA (SOURCE MPR121 CDC encodings 1..63)
FFI = 6
TOUCH_THRESHOLD = 12                                    # counts, firmware TOUCH_THRESHOLD (SOURCE FrutaMIDI.ino)


def charge(vp0, ve0, I, T, R, Ce):
    """Constant current I into node P for time T. Returns (vp, ve) at T."""
    ct = C_PIN + Ce
    q0 = C_PIN * vp0 + Ce * ve0
    q = q0 + I * T
    if R == 0:
        v = q / ct
        return v, v
    tau = R * C_PIN * Ce / ct
    u_inf = I * R * Ce / ct                 # steady-state drop across R (u = vp - ve)
    u0 = vp0 - ve0
    u = u_inf + (u0 - u_inf) * math.exp(-T / tau)
    vp = (q + Ce * u) / ct
    return vp, vp - u


def discharge(ve0, T, R, Ce):
    """Pin P held at VSS for time T; C_ext discharges through R."""
    if R == 0:
        return 0.0, 0.0
    return 0.0, ve0 * math.exp(-T / (R * Ce))


def measure(I, T, R, Ce):
    """Mean ADC counts (10-bit) over FFI consecutive charge/discharge cycles."""
    vp = ve = 0.0
    acc = 0.0
    for _ in range(FFI):
        vp, ve = charge(0.0, ve, I, T, R, Ce)
        acc += min(vp, VDD) / VDD * 1024
        vp, ve = discharge(ve, T, R, Ce)
    return acc / FFI


def valid_pairs(R, Ce):
    out = []
    for T in CDT_SET:
        for I in CDC_SET:
            c = measure(I, T, R, Ce)
            if LSL <= c / 4 <= USL:
                out.append((I, T, c))
    return out


def sens(I, T, R, Ce, dC=1e-12):
    """Counts lost per +1 pF on the electrode (touch makes counts fall)."""
    return measure(I, T, R, Ce) - measure(I, T, R, Ce + dC)


def analyse(R, Ce):
    pairs = valid_pairs(R, Ce)
    if not pairs:
        return None
    nominal = min(pairs, key=lambda p: (abs(p[2] / 4 - TL), -p[1]))
    s = [(sens(I, T, R, Ce), I, T) for I, T, _ in pairs]
    best, worst = max(s), min(s)
    sn = sens(nominal[0], nominal[1], R, Ce)
    return dict(n=len(pairs), nominal=nominal, s_nom=sn, best=best, worst=worst)


# T-092: 2.85k / 3k / 3.15k = HPWC2512 3k0 +-5 % (ADR-023, superseded); 3.135k / 3.465k = 3k3 +-5 % (ADR-025, superseded); T-096 / ADR-026: 3.267k / 3.3k / 3.333k = RC2512 3k3 +-1 %
# T-094: 2.565k = 2k7 -5 %, 2.673k/2.727k = 2k7 +-1 %, 3.267k/3.333k = 3k3 +-1 %, 3.366k/3.399k = 3k3 +2 %/+3 %
R_SWEEP = [0, 1e3, 2.2e3, 2.565e3, 2.673e3, 2.727e3, 2.85e3, 3e3, 3.135e3, 3.15e3, 3.267e3, 3.3e3, 3.333e3, 3.366e3, 3.399e3, 3.465e3, 4.7e3, 6.8e3, 10e3, 22e3, 47e3, 100e3]
C_SWEEP = [10e-12, 20e-12, 50e-12, 100e-12, 200e-12, 500e-12, 1000e-12, 2000e-12]


WORST_LIMIT = 0.90                                      # ADR-019 acceptance limit on the worst-case ratio
R_LOW, R_NOM, R_HIGH = 3267.0, 3300.0, 3333.0           # RC2512FK-073K3L 3k3 +-1 % (SOURCE Mouser / YAGEO RC_L)


def fmt_r(R):
    return "%gk" % (R / 1e3) if R else "0"


def main():
    print("# sim_electrode.py  VDD=%.2f V  C_pin=%.0f pF  USL/TL/LSL=%d/%d/%d  FFI=%d" %
          (VDD, C_PIN * 1e12, USL, TL, LSL, FFI))
    print("# SIMULATION. Values: counts per +1 pF at the autoconfig 'nominal' (closest to TL) pair,")
    print("# ratio = sensitivity relative to R=0 at the same C_ext; dCmin = pF needed for TOUCH_THRESHOLD=%d counts" % TOUCH_THRESHOLD)
    ref = {}
    print()
    print("%-6s %-8s %5s %8s %8s %9s %9s %9s %8s %8s" %
          ("R", "C_ext", "pairs", "CDC_uA", "CDT_us", "cnt/pF", "ratio", "worst/pF", "worstrat", "dCmin"))
    rows = []
    for R in R_SWEEP:
        for Ce in C_SWEEP:
            a = analyse(R, Ce)
            if a is None:
                print("%-6s %6.0fpF %5d  -- no valid CDC/CDT pair (OOR) --" % (fmt_r(R), Ce * 1e12, 0))
                rows.append((R, Ce, None))
                continue
            I, T, _ = a["nominal"]
            if R == 0:
                ref[Ce] = a
            r0 = ref.get(Ce)
            ratio = a["s_nom"] / r0["s_nom"] if r0 else float("nan")
            wratio = a["worst"][0] / r0["worst"][0] if r0 else float("nan")
            dcmin = TOUCH_THRESHOLD / a["s_nom"] if a["s_nom"] > 0 else float("inf")
            rows.append((R, Ce, a, ratio, wratio))
            print("%-6s %6.0fpF %5d %8.0f %8.1f %9.3f %9.3f %9.3f %8.3f %7.1fpF" %
                  (fmt_r(R), Ce * 1e12, a["n"], I * 1e6, T * 1e6, a["s_nom"], ratio,
                   a["worst"][0], wratio, dcmin))
    # design rule: largest R with nominal ratio >= 0.9 and worst-case ratio >= 0.8 for every C <= 1000 pF
    print()
    print("# Design-rule search (C_ext 10..1000 pF):")
    for R in R_SWEEP:
        sub = [r for r in rows if r[0] == R and r[1] <= 1000e-12]
        ok_valid = all(r[2] is not None for r in sub)
        if not ok_valid:
            print("R=%-6s some C out of range (no valid pair)" % fmt_r(R))
            continue
        mn = min(r[3] for r in sub)
        mw = min(r[4] for r in sub)
        print("R=%-6s min nominal ratio=%.3f  min worst-case ratio=%.3f  %s" %
              (fmt_r(R), mn, mw, "MEETS (>=0.90 nominal, >=0.80 worst)" if mn >= 0.9 and mw >= 0.8 else "does not meet"))
    # T-096 / ADR-026: acceptance of R1-R12 on the 0.90 worst-case limit (the MEETS text above uses the older 0.80 worst criterion)
    print()
    print("# T-096 / ADR-026 R1-R12 = RC2512FK-073K3L 3k3 +-1 %%, limit: worst-case ratio >= %.2f, C_ext 10..1000 pF. SIMULATION" % WORST_LIMIT)
    for R, name in ((R_LOW, "-1 % corner"), (R_NOM, "nominal"), (R_HIGH, "+1 % corner")):
        sub = [r for r in rows if r[0] == R and r[1] <= 1000e-12]
        w = min(r[4] for r in sub)
        print("%s %s %.0f ohm: worst %.3f vs %.2f (SIMULATION)" % ("PASS" if w >= WORST_LIMIT else "FAIL", name, R, w, WORST_LIMIT))
    # simple IR-drop bound, independent of the simulation (CALCULATION)
    v_tl = TL / 256 * VDD
    print()
    print("# CALCULATION cross-check: V_TL = TL/256*VDD = %.3f V; I*R <= 10%% of V_TL gives R <= %.0f ohm at CDC=63 uA, "
          "R <= %.0f ohm at 20 uA" % (v_tl, 0.1 * v_tl / 63e-6, 0.1 * v_tl / 20e-6))


if __name__ == "__main__":
    main()
