---
name: latex-workflow
description: LaTeX route for FrutaMIDI: build reports with the project-local TinyTeX. Use for any .tex task.
---

# LaTeX workflow

- Binaries: `tools/TinyTeX/bin/universal-darwin/` (pdflatex, tlmgr). TinyTeX-1 v2026.10.
- Build: MCP `eng-tools` → `latex_build {tex}` (two pdflatex passes, nonstopmode, halt on error), or `PATH=tools/TinyTeX/bin/universal-darwin:$PATH pdflatex ...`.
- Missing package → `tools/TinyTeX/bin/universal-darwin/tlmgr install <pkg>` (stays inside the project). Record it in management/TOOLCHAIN.md.
- Check the log for `Output written on` and zero `! ` errors; warnings about undefined references need a second pass.
