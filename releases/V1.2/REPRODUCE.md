# Reproduce V1.2

Measured on macOS 26.5 (arm64, Apple M4). Tool versions: management/TOOLCHAIN.md (KiCad 10.0.4, arduino-cli 1.5.1, arduino-pico 6.3.1, avr 1.8.8, Python 3.9.6, pytest 8.4.2, TeX Live 2026).

1. Clone at tag `v1.2.0` and install the project-local toolchain as in releases/V1_BASELINE/REPRODUCE.md step 1.
2. Hardware: `sh hardware/scripts/build_all.sh` regenerates schematic and PCB, fails on any ERC/DRC/parity violation and exports hardware/fabrication/. Regeneration changes UUIDs, timestamps and Gerber aperture order, so compare geometry, not bytes: `<KiCad python> reports/electronics/evidence/T-080/geo_dump.py hardware/frutamidi.kicad_pcb` gives 316 lines identical to the tagged board (MEASUREMENT, 2026-11-08).
3. Checks: `.venv/bin/python sim/systems/interface_check.py` (expect `85 checks, 85 PASS, 0 FAIL`), `sim/systems/pcb_rules_check.py` (`20 checks, 20 PASS, 0 FAIL`), `sim/systems/budgets.py` (`30 checks, 25 PASS, 5 FAIL`), `sh sim/electronics/calc/run_all.sh`.
4. Firmware tests: `.venv/bin/python -m pytest -q tests/firmware` (expect 295 passed). Host/sampler tests: `cd tests/host/browser && npm ci`, then `.venv/bin/python -m pytest -q tests/host` (expect 102 passed; needs Google Chrome).
5. Firmware binaries: for B in rpipico rpipicow rpipico2 rpipico2w: `arduino-cli --config-file tools/arduino/cli.yaml compile -b "rp2040:rp2040:${B}:usbstack=tinyusb" [--build-property "compiler.cpp.extra_flags=-DFRUTAMIDI_PCB"] --output-dir <dir> firmware/FrutaMIDI`; Leonardo: `-b arduino:avr:leonardo`. Use `${B}` braces (in zsh `$B:u` is a modifier). Expected sizes: firmware/build.log. Compare sizes, not hashes.
6. Report: `sh reports/report/build.sh` (expect 42 pages, 0 LaTeX errors).
7. Verify this folder: `shasum -a 256 -c SHA256SUMS`.

Nothing in this release has been tested on real hardware. See the physical validation plan (report §10).
