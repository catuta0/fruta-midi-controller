# Toolchain

Measured on 2026-10-30 (MEASUREMENT by command, see logs/setup-environment.md).

| Tool | Version | Location | Route | Status |
| --- | --- | --- | --- | --- |
| macOS | 26.5.2, arm64, Apple M4, 10 cores, 16 GiB RAM | host | — | — |
| Claude Code | 2.1.270 | host | agents | — |
| KiCad (kicad-cli + pcbnew Python 3.9.13) | 10.0.4 | /Applications/KiCad | electronics | smoke NOT RUN |
| arduino-cli | 1.5.1 | Homebrew | firmware | smoke NOT RUN |
| arduino-pico core / AVR core / libs | rp2040 6.3.1 / avr 1.8.8 / Adafruit MPR121 1.2.1, BusIO 1.17.4, MIDI Library 5.0.2, MIDIUSB 1.0.5 | tools/arduino (project) | firmware | installed |
| Python + pytest | 3.9.6 + pytest 8.4.2 | .venv (project) | host tests | installed |
| Node.js + MCP SDK | v26.4.0 + @modelcontextprotocol/sdk 1.32.2 | Homebrew / scripts/mcp/node_modules | MCP adapter | installed |
| TinyTeX (TeX Live 2026) | TinyTeX-1 v2026.10, sha256 e40c294e…d40f, pdfTeX 1.40.29 | tools/TinyTeX (project) | report | smoke PASS |
| gh | 2.102.0 | Homebrew | releases | authenticated as catuta0 |
| MCP | no user/project servers existed; local adapter `eng-tools` in `.mcp.json` | scripts/mcp | all | stdio handshake PASS outside Claude; access from agents NOT RUN |

Not used: PlatformIO (not installed; arduino-cli covers the route), FreeCAD, OpenFOAM, Yosys (out of scope).

Disk after installs: tools/ 2.2 GiB, .venv 17 MiB (MEASUREMENT, du).
