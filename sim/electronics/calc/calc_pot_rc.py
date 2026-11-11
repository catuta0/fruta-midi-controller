#!/usr/bin/env python3
"""T-076, updated T-092 for the SMD board (C1 1206 near the Pico, pot off-board on 3 wires, ADR-023 D-2): CALCULATION of the
octave-potentiometer ADC input settling with C1 = 100 nF from the wiper (POT) to AGND.

Source resistance seen by C1 = Thevenin resistance of the pot divider, R_th = Ra * Rb / (Ra + Rb), maximum R/4 at
mid travel (both ends tied to 3V3 / AGND, which are low impedance).
Inputs:
  R_pot 10 kOhm +-20 %          SOURCE Bourns PTV09 datasheet and Mouser page, PTV09A-4015F-B103 (T-096)
  Residual resistance 500 ohm max (the datasheet states "500 ohms or +-1 % max.", ends of travel)   SOURCE Bourns PTV09 datasheet
  RIN_ADC 100 kOhm              SOURCE RP2040 datasheet extract, sim/systems/datasheets/rp2040-datasheet-adc.txt
  C1 100 nF +-10 % X7R 1206     ASSUMPTION: code K = +-10 % on the 1206 example KEMET C1206C104K5RACTU; datasheet NOT opened (T-090)
  X7R capacitance change over temperature: +-15 %   ASSUMPTION: EIA X7R class figure, 1206 datasheet not opened (T-090)
  X7R DC bias at 3.3 V on a 50 V part ignored (ASSUMPTION; 6.6 % of rating, would lower C, which shortens tau)
  Wire to the off-board pot: 30-50 pF/m (ASSUMPTION), up to 0.30 m (ASSUMPTION): at most 15 pF, 0.015 % of C1, ignored
  POT_READ_MS = 30 ms           SOURCE firmware/FrutaMIDI/fm_pot.h (pot sample period)
  ADC: 10-bit analogRead (Arduino default), hysteresis 0.2 zone = ~41 counts   SOURCE fm_pot.h comments
  RP2040 ADC sampling capacitance: not given in the RP2040 datasheet ADC section (sim/systems/datasheets/
  rp2040-datasheet-adc.txt mentions only "tens of femto Farads" scaling capacitors); 10 pF used as an upper-bound
  ASSUMPTION for the charge-sharing error.
  Fastest user turn: full travel in 100 ms (ASSUMPTION, a quick flick of a 9 mm knob).
"""
import math

R_NOM, R_TOL = 10e3, 0.20
C_NOM, C_TOL, C_TEMP = 100e-9, 0.10, 0.15
T_READ = 30e-3
N_BITS = 10
C_SAMPLE = 10e-12
T_TURN = 0.100

print("# calc_pot_rc.py  T-076 / T-092 CALCULATION (inputs: SOURCE / ASSUMPTION, see header; C1 1206, off-board pot)")
r_th_nom = R_NOM / 4
r_th_max = R_NOM * (1 + R_TOL) / 4
c_max = C_NOM * (1 + C_TOL) * (1 + C_TEMP)
for name, r, c in (("nominal", r_th_nom, C_NOM), ("worst (R +20 %, C +10 % tol, +15 % temp)", r_th_max, c_max)):
    tau = r * c
    n_half_lsb = math.log(2 ** (N_BITS + 1))       # full-scale step settles to 1/2 LSB after n tau
    t_settle = n_half_lsb * tau
    fc = 1 / (2 * math.pi * tau)
    print("%-42s R_th %.0f ohm  C %.0f nF  tau %.3f ms  fc %.0f Hz" % (name, r, c * 1e9, tau * 1e3, fc))
    print("    full-scale step to 1/2 LSB (%d-bit): %.2f tau = %.2f ms; read period %.0f ms = %.0f tau; margin %.1fx"
          % (N_BITS, n_half_lsb, t_settle * 1e3, T_READ * 1e3, T_READ / tau, T_READ / t_settle))
    slope = (2 ** N_BITS - 1) / T_TURN                # counts per second during the fastest turn
    lag = slope * tau
    print("    ramp lag at a %.0f ms full turn: %.1f counts (zone width %.0f counts, hysteresis ~41 counts)"
          % (T_TURN * 1e3, lag, 2 ** N_BITS / 5))
share = C_SAMPLE / (C_SAMPLE + C_NOM) * 2 ** N_BITS
print("ADC sample-capacitor charge sharing (C_sample <= %.0f pF ASSUMPTION): <= %.3f LSB (%d-bit) per conversion"
      % (C_SAMPLE * 1e12, share, N_BITS))
tau_w = r_th_max * c_max
ok = T_READ / (math.log(2 ** (N_BITS + 1)) * tau_w) >= 5
# T-096: RV1 PTV09A-4015F-B103 against the ADC input and the firmware zones (fm_pot.h: 5 zones, 10-bit, hysteresis 0.7 zone from centre)
R_IN = 100e3
ZONE = 1024 / 5.0
r_th_load = (R_NOM * (1 + R_TOL)) / 4
err_frac = 0.5 * r_th_load / (r_th_load + R_IN)            # wiper at mid travel, resistive load to ground treated as a bound (ASSUMPTION)
err_cnt = err_frac * 1024
print("ADC loading: R_th max %.0f ohm vs RIN_ADC %.0f kohm -> error at mid travel <= %.2f %% of full scale = %.1f counts, 10-bit (zone width %.0f counts, hysteresis ~41 counts) %s"
      % (r_th_load, R_IN / 1e3, err_frac * 100, err_cnt, ZONE, "PASS" if err_cnt < 41 else "FAIL"))
r_low = R_NOM * (1 - R_TOL)
end = 500.0 / r_low
pos_low, pos_high = end * 5, 5 - end * 5
ok_end = pos_low < 0.8 and pos_high > 4.2
print("Residual resistance: 500 ohm of %.0f ohm = %.2f %% of travel at each end -> zone position reached %.2f / %.2f (needs < 0.80 and > 4.20 to reach the outer octaves) %s"
      % (r_low, end * 100, pos_low, pos_high, "PASS" if ok_end else "FAIL"))
print("%s worst-case settling %.2f ms vs read period %.0f ms (criterion: margin >= 5x, ASSUMPTION)"
      % ("PASS" if ok else "FAIL", math.log(2 ** (N_BITS + 1)) * tau_w * 1e3, T_READ * 1e3))
