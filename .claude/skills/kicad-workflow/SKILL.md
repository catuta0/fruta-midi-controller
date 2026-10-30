---
name: kicad-workflow
description: KiCad 10 route for FrutaMIDI: regenerate schematic/PCB from scripts, run ERC/DRC with parity, export fabrication files. Use for any hardware/ task.
---

# KiCad workflow

- Source of truth: `hardware/scripts/gen_schematic.py` (any Python 3) and `hardware/scripts/gen_pcb.py` (KiCad Python: `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`). Do not hand-edit generated `.kicad_sch`/`.kicad_pcb`.
- Full build + checks + exports: `sh hardware/scripts/build_all.sh` (fails on any ERC/DRC violation).
- Checks via MCP: `eng-tools` → `kicad_erc {schematic}`, `kicad_drc {board}`. CLI: `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.
- Home-etch rules: single layer B.Cu, no vias, track >= 0.8 mm (1.0 signals, 1.2 power), clearance >= 0.6 mm (netclass), pads >= 1.6 mm with >= 0.4 mm annular ring.
- Fix violations at the root cause; no rule relaxations or exclusions to silence them.
- Lesson (earlier session): an empty `.pretty` dir makes `pcbnew.FootprintSave` fail; use `PCB_IO_MGR.FindPlugin(KICAD_SEXP)`. zsh does not word-split `$VAR` holding a command; and `$B:u` is a zsh modifier — write `${B}`.
