# Reproduce V1.3

Measured on macOS 26.5 (arm64). Tool versions: management/TOOLCHAIN.md (KiCad 10.0.4, arduino-cli 1.5.1, arduino-pico 6.3.1, avr 1.8.8, Python 3.9.6, pytest 8.4.2, TeX Live 2026). On a shared machine run heavy steps through the job gate used by the project (pcgate).

1. Clone at tag `v1.3.0` and install the project-local toolchain as in releases/V1_BASELINE/REPRODUCE.md step 1.
2. Hardware: `sh hardware/scripts/build_all.sh` regenerates schematic and PCB, fails on any ERC/DRC/parity violation and exports hardware/fabrication/. Regeneration changes UUIDs and timestamps, so compare copper, not bytes: `python3 reports/electronics/evidence/T-096/compare_copper.py <rev>` against the tagged board (T-109: 657 operations identical).
3. Checks: `python3 sim/electronics/calc/check_smd.py` (expect `65 checks, 65 PASS, 0 FAIL`), `sh sim/electronics/calc/run_all.sh`, `python3 sim/systems/interface_check.py` (`125 checks, 125 PASS, 0 FAIL`), `python3 sim/systems/pcb_rules_check.py` (`26 checks, 26 PASS, 0 FAIL`), `python3 sim/systems/budgets.py` (`35 checks, 31 PASS, 4 FAIL`).
4. Firmware tests: `.venv/bin/python -m pytest -q tests/firmware` (expect 295 passed). Host/sampler tests: `cd tests/host/browser && npm ci`, then `.venv/bin/python -m pytest -q tests/host` (expect 102 passed; needs Google Chrome).
5. Firmware binaries: for B in rpipico rpipicow rpipico2 rpipico2w: `arduino-cli --config-file tools/arduino/cli.yaml compile -j 3 -b "rp2040:rp2040:${B}:usbstack=tinyusb" [--build-property "compiler.cpp.extra_flags=-DFRUTAMIDI_PCB"] --output-dir <dir> firmware/FrutaMIDI`; Leonardo: `-b arduino:avr:leonardo`. Expected sizes: firmware/build.log. Compare sizes, not hashes.
6. Report: `sh reports/report/build.sh` (expect 56 pages, 0 LaTeX errors).
7. Verify this folder: `shasum -a 256 -c SHA256SUMS`.

Nothing in this release has been tested on real hardware. See the first-build measurement list (report section 3) and the physical validation plan.
