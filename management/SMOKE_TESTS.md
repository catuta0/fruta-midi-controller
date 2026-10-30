# Smoke tests (G2 evidence)

| Route | Agent | Tool + version | Command | Known answer | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| LaTeX | manager | pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026, TinyTeX-1 v2026.10) | `pdflatex -interaction=nonstopmode -halt-on-error smoke.tex` | 1-page PDF, no `!` errors | PASS (`Output written on smoke.pdf (1 page, 28601 bytes)`) | reports/smoke/latex/ |
| MCP adapter eng-tools (stdio, outside Claude) | manager | node v26.4.0, @modelcontextprotocol/sdk 1.32.2 | initialize, tools/list, tools/call env_info | 6 tools listed; versions reported | PASS (handshake + 6 tools + env_info output) | scripts/mcp/server.mjs (test command in RESUME.md) |
| MCP access from each specialist | each agent | eng-tools via Claude Code | `env_info` called by the agent | agent quotes versions | NOT RUN (needs session restart) | — |
| Electronics: small schematic + board, ERC/DRC clean | electronics-engineer | KiCad 10.0.4 | — | 0 violations | NOT RUN | — |
| Firmware: build + host unit tests | firmware-engineer | arduino-cli 1.5.1, arduino-pico 6.3.1, pytest 8.4.2 | — | build OK, tests pass | NOT RUN | — |
| Software: host test of sampler logic | software-engineer | Python 3.9.6 / node | — | tests pass | NOT RUN | — |
| Systems: budget calculation with known answer | systems-engineer | Python | — | hand calc matches | NOT RUN | — |
| Documentation: LaTeX build via MCP | documentation-engineer | eng-tools latex_build | — | PDF produced | NOT RUN | — |
| Independent reviewer: read-only access, MCP access | independent-reviewer | eng-tools env_info | — | — | NOT RUN | — |
