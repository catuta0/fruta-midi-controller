# Execution metrics

| Item | Value |
| --- | --- |
| Model / effort | Manager and all specialists: claude-opus-5-5 (inherit), session effort medium |
| Wall time | 2026-10-30 → 2026-11-04 (including pauses for usage limits) |
| Interruptions | 1 weekly limit (2026-10-30 → 11-03), 4 session/5-hour limits; every interrupted agent resumed from saved state; 1 duplicated session (fork) archived on user request |
| Specialists invoked | systems, electronics, firmware, software, documentation, independent-reviewer (all 6, real subagents) |
| Tasks | T-006 smoke ×6; systems T-008..T-013; electronics T-050..T-056; firmware T-040..T-044; software T-020..T-021; documentation T-030..T-041; review T-060, re-review T-061 |
| Tool versions | management/TOOLCHAIN.md (KiCad 10.0.4, arduino-cli 1.5.1, arduino-pico 6.3.1, avr 1.8.8, Python 3.9.6, pytest 8.4.2, pdfTeX 1.40.29 / TeX Live 2026, node 26.4.0, playwright-core 1.64.1, Chrome 156) |
| Retries / failures worth noting | install script zsh word-splitting (1 retry); tlmgr needed self-update; report writes refused for electronics/reviewer agents (manager wrote files); requirements.csv write failure restored from git; malformed REQ-015 CSV row found and fixed |
| Final checks | ERC 0, DRC 0/0/0, interface_check 78/78, pcb_rules_check 15/15, firmware host tests 295 passed, 9/9 builds, host/sampler tests 102 passed (T-021), report 22 pages 0 errors |
