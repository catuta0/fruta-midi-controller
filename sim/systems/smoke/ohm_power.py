"""T-006-SYS smoke test: known-answer Ohm's law calculation.

CALCULATION: I = V / R, P = V * I = V^2 / R
Inputs (ASSUMPTION, test case): V = 3.3 V, R = 10 kOhm.
Hand values: I = 0.33 mA, P = 1.089 mW.
"""
import math
import sys

V = 3.3          # V
R = 10_000.0     # Ohm
TOL = 1e-9

I_A = V / R
P_W = V * I_A

I_mA = I_A * 1e3
P_mW = P_W * 1e3

I_HAND_mA = 0.33
P_HAND_mW = 1.089

print(f"python: {sys.version.split()[0]}")
print(f"inputs: V = {V} V, R = {R} Ohm")
print(f"I = V/R = {I_mA:.12f} mA (hand {I_HAND_mA} mA, |err| = {abs(I_mA - I_HAND_mA):.3e})")
print(f"P = V*I = {P_mW:.12f} mW (hand {P_HAND_mW} mW, |err| = {abs(P_mW - P_HAND_mW):.3e})")

assert math.isclose(I_mA, I_HAND_mA, rel_tol=0.0, abs_tol=TOL), "current mismatch"
assert math.isclose(P_mW, P_HAND_mW, rel_tol=0.0, abs_tol=TOL), "power mismatch"
print(f"RESULT: PASS (both assertions within abs tol {TOL})")
