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

## CR-002 / v1.2 (2026-11-07 → 2026-11-08)
| Item | Value |
| --- | --- |
| Tasks | T-060…T-083 (electronics T-060/073/076/080, systems T-070/074/077/081, documentation T-072/075/078/082, reviewer T-071/T-079, manager analisar-pcb reviews ×2) |
| Retries / failures worth noting | reviewer findings writes refused (manager wrote files); report build broke on U+222B; REQ-023 table row overflowed a page (fixed in csv_to_table.py); zsh `$B:u` modifier broke the firmware build loop (rerun with sh); agents interrupted by session restarts, resumed |
| Final checks | ERC 0, DRC 0/0/0, interface_check 85/85, pcb_rules_check 20/20, budgets 25 PASS / 5 FAIL, firmware 9/9 builds, 295 host tests, 102 host/sampler tests, report 42 pages 0 errors, SHA256SUMS 21/21 OK |

## CR-003 / v1.3 (2026-11-09 → 2026-11-11)
| Item | Value |
| --- | --- |
| Tasks | T-090…T-115 (electronics T-090..T-098/T-103/T-109, systems T-093/T-099/T-104/T-106/T-110/T-112, documentation T-101/T-105/T-107/T-111/T-113, reviewer T-102/T-108, resource-manager checks) |
| Retries / failures worth noting | LCSC could not supply the board, moved to Mouser; HPWC resistor rejected on cost; datasheet PDFs committed by mistake (amended, .gitignore); electronics agent died on a network error (resumed); reviewer writes refused (manager wrote findings); rule proofs had to be rebuilt after documents were fixed; a reviewer-identified label mix (MEASUREMENT vs CALCULATION) fixed across files |
| Final checks | ERC 0, DRC 0/0/0, check_smd 65/65, interface_check 125/125, pcb_rules_check 26/26, budgets 31 PASS / 4 FAIL, mutations 86 proved, firmware 9/9 builds, 295 host tests, 102 host/sampler tests, report 56 pages 0 errors, SHA256SUMS 20/20 OK |
