# Retired calculations

Kept for traceability only. Nothing here describes the current board and none of it is run by `run_all.sh`.

| File | Why retired | Task |
| --- | --- | --- |
| check_silk.py, check_silk.out | Text and silkscreen check of the through-hole board. The SMD board has no silkscreen (ADR-023); its assembly-map reference check is in `check_smd.py`. The .out is from the V1.2 board | T-092 |
| calc_pulse.py, calc_pulse.out | Yageo MFR-12 3k3 pulse check (T-053). The part was replaced in T-060; the current part is in `calc_pulse_rated.py` | T-092 |
