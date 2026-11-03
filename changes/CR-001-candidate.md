# CR-001 (candidate, not opened) — Pulse-rated electrode series resistor
Proposed by: electronics-engineer (T-054). Status: candidate; to be opened only through /engineering-change.
Reason: Yageo MFR-12 3k3 is rated 400 V max overload; IEC 4 kV contact puts ≈3.6 kV across it (CALCULATION, sim/electronics/calc/calc_pulse.out).
Candidate: Vishay MBB 0207 (Vishay doc 28766 pulse chart to be read; needs ≥ 3.64 kV at 3.3 kΩ). Impact: larger body (2.5 mm) → staggered resistor rows; BOM; hardware/README assembly.
