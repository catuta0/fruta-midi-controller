# Sources

| ID | Source | Used for | Accessed |
| --- | --- | --- | --- |
| S-001 | https://code.claude.com/docs/en/sub-agents | agent frontmatter, restart rule | 2026-10-30 |
| S-002 | https://github.com/anthropics/skills (list) — no KiCad/Arduino/LaTeX skill; `mcp-builder`, `webapp-testing` noted | skills | 2026-10-30 |
| S-003 | https://github.com/adafruit/Adafruit-MPR121-PCB (Eagle .brd, both revisions) | module footprint geometry | 2026-10-30 |
| S-004 | https://github.com/rstudio/tinytex-releases v2026.10 | LaTeX toolchain | 2026-10-30 |
| S-005 | https://github.com/earlephilhower/arduino-pico | Pico Arduino core | 2026-10-30 |
| S-006 | NXP/Freescale MPR121 datasheet, Rev. 4 02/2013, https://www.nxp.com/docs/en/data-sheet/MPR121.pdf, sha256 a02ff161d01d9dc85e5eef30e676f855e6c46121319f99471a1a6c0be0e9e55c (read by manager via pypdf, 27 pages) | p7/p17 Table 2: AUTOCONFIG0 0x7B = FFI RETRY BVA ARE ACE; AUTOCONFIG1 0x7C = SCTS (D7) … OORIE ARFIE ACFIE; p19 Eqn 1–3: USL=(VDD−0.7)/VDD×256, TL=0.9·USL, LSL=0.65·USL; p22 §6.4 multiple-byte read format; p21 §6.1 "pullup resistor, typically 4.7 kΩ, is required on SDA" | 2026-11-03 |
| S-007 | Adafruit_MPR121 Arduino library 1.2.1 (tools/arduino/user/libraries/Adafruit_MPR121) | begin(): AUTOCONFIG0 = 0x0B, limits 200/180/130, never writes 0x7C | 2026-10-30 |
| S-008 | Raspberry Pi Pico / Pico 2 datasheets, sha256 in requirements/SOURCES_SYSTEMS.md (S-01, S-16) | pins, 3V3 load, VSYS/VBUS, ADC | 2026-11-03 |
| S-009 | Electronics sources EE-S01..S16 | see reports/electronics/SOURCES_EE.md | 2026-10-30 |
