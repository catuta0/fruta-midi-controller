# Smoke tests (G2 evidence)

| Route | Agent | Tool + version | Command | Known answer | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| LaTeX | manager | pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026, TinyTeX-1 v2026.10) | `pdflatex -interaction=nonstopmode -halt-on-error smoke.tex` | 1-page PDF, no `!` errors | PASS (`Output written on smoke.pdf (1 page, 28601 bytes)`) | reports/smoke/latex/ |
| MCP adapter eng-tools (stdio, outside Claude) | manager | node v26.4.0, @modelcontextprotocol/sdk 1.32.2 | initialize, tools/list, tools/call env_info | 6 tools listed; versions reported | PASS (handshake + 6 tools + env_info output) | scripts/mcp/server.mjs (test command in RESUME.md) |
| MCP access from each specialist | all 6 agents | eng-tools via Claude Code | `env_info` called by each agent | agent quotes versions | PASS (6/6 quoted identical versions) | management/handoffs/*/T-006-*.md |
| Electronics: small schematic + board, ERC/DRC clean | electronics-engineer | KiCad 10.0.4 | gen_smoke.py; reopen; kicad_erc; kicad_drc --schematic-parity | 0/0/0 | PASS (`Found 0 DRC violations`, `ERC messages: 0`; negative control found 1 unconnected) | sim/electronics/smoke/ |
| Firmware: build + host unit tests | firmware-engineer | arduino-cli 1.5.1, arduino-pico 6.3.1, pytest 8.4.2, Apple clang 21 | firmware_compile rpipico; run_pytest tests/firmware/smoke | 4 known answers | PASS (`Sketch uses 89436 bytes`, `4 passed`; forced failure `1 failed, 3 passed`) | management/handoffs/firmware-engineer/T-006-FW_logs/ |
| Software: host test route | software-engineer | Python 3.9.6, node v26.4.0 | run_pytest tests/host/smoke; node text check | 4 known parses; >=1 occurrence | PASS (`6 passed`, `requestMIDIAccess occurrences=2`) | tests/host/smoke/ |
| Systems: calculation with known answer | systems-engineer | Python 3.9.6 | sim/systems/smoke/ohm_power.py | 0.33 mA, 1.089 mW | PASS (`RESULT: PASS`, err 0) | sim/systems/smoke/ |
| Documentation: LaTeX build via MCP | documentation-engineer | eng-tools latex_build, pdfTeX 1.40.29 | latex_build doc_smoke.tex | 1-page PDF, 0 errors | PASS (`Output written on doc_smoke.pdf (1 page, 50998 bytes)`); package install PARTIAL (tlmgr self-update approved, in progress) | reports/smoke/doc/ |
| Independent reviewer: access | independent-reviewer | eng-tools env_info; awk read-only | pin count of RaspberryPi_Pico symbol | 40 | PASS (40 distinct pin numbers) | management/handoffs/independent-reviewer/T-006-REV.md |
