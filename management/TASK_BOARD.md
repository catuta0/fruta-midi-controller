# Task board

| ID | Task | Owner | Status | Evidence |
| --- | --- | --- | --- | --- |
| T-001 | Restore git from origin, inspect environment | manager | DONE | logs/setup-environment.md |
| T-002 | Install toolchain inside project (arduino cores, venv+pytest, TinyTeX) | manager | DONE | logs/setup-install.log |
| T-003 | Create agents, skills, management docs | manager | DONE | .claude/, management/ |
| T-004 | Local MCP adapter `eng-tools` | manager | DONE (verified outside Claude) | scripts/mcp/ |
| T-005 | Restart session to load agents and MCP | user | TODO | — |
| T-006 | Smoke test: tool + MCP access, per specialist | all specialists | TODO | management/handoffs/*/SMOKE.md |
| T-007 | Smoke test: LaTeX one page | manager | PASS | reports/smoke/latex/ |
| T-008 | Requirements with IDs, rationale, source, verification method | systems-engineer | TODO | management/REQUIREMENTS.md |
| T-009 | Architecture options (>=2) and ADR; freeze INTERFACES.json | systems-engineer + manager | TODO | management/DECISIONS.md |
| T-010 | G1 gate | manager | TODO | — |
| T-020 | Sampler browser tests | software-engineer | IN PROGRESS | tests/host/ |
| T-030 | Translate README + hardware/README to English | documentation-engineer | PASS (interim) | handoffs/documentation-engineer/T-030.md |
| T-040 | Firmware logic extraction + host unit tests + build matrix | firmware-engineer | IN PROGRESS | reports/firmware/ |
| T-050 | Electrical analysis, datasheet checks, electrode-protection variants | electronics-engineer | IN PROGRESS | reports/electronics/ |
| T-060…T-078 | CR-002 design, checks, documents, re-review T-071, manager PCB review fixes | electronics/systems/documentation/reviewer | DONE | management/handoffs/, changes/CR-002.md |
| T-079 | CR-002 final independent re-review | independent-reviewer | DONE (release-ready) | reports/review/CR-002-final/findings.md |
| T-080 | F2-001/004/005/007 fixes (C1 drill 0.9 mm, wording, knob limit) | electronics-engineer | PASS | handoffs/electronics-engineer-T-080.md |
| T-081 | F2-002/003/006 (R-011, REQ-032 text, spark-gap check), frozen-7 | systems-engineer | PASS | handoffs/systems-engineer-T-081.md |
| T-082 | Report v1.2 final, manual, README | documentation-engineer | PASS | handoffs/documentation-engineer-T-082.md |
| T-083 | releases/V1.2, merge, tag v1.2.0 | manager | DONE | releases/V1.2/ |
| T-084 | GitHub release v1.2.0 | manager | DONE (user approved 2026-11-08) | https://github.com/catuta0/fruta-midi-controller/releases/tag/v1.2.0 |
