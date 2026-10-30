---
name: host-software-workflow
description: Host software route for FrutaMIDI: sampler in docs/index.html, Python/Node scripts and tests. Use for any host-side code task.
---

# Host software workflow

- Python: `.venv/bin/python` (3.9) with pytest; install extra packages only into `.venv`.
- Node: system `node` (v26); install packages only inside the project (`npm install` in a project subfolder; `node_modules` is git-ignored).
- Sampler testing without hardware: serve `docs/` with `python3 -m http.server`, stub `navigator.requestMIDIAccess` before page scripts run, drive notes through the stub (approach used and verified in an earlier session).
- MCP: `eng-tools` → `run_pytest {target}`.
