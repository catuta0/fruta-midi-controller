# RESUME — read this first when resuming

Last update: 2026-10-30 (UTC). Gate: pre-G1. Phase B setup complete; **session restart required** because `.claude/agents/` did not exist when the previous session started (per code.claude.com/docs/en/sub-agents) and `.mcp.json` is new.

## Done
- Phase A definition confirmed by user: management/PROJECT_DEFINITION.md.
- git restored from origin (`main` @ d85b330) — the app's folder copy omitted `.git`.
- Environment inspected (logs/setup-environment.md); toolchain installed inside project: tools/arduino (rp2040 6.3.1, avr 1.8.8, libs), .venv (pytest 8.4.2), tools/TinyTeX (v2026.10). See management/TOOLCHAIN.md.
- Agents: .claude/agents/{systems,electronics,firmware,software,documentation}-engineer.md, independent-reviewer.md (disallowedTools: [Agent], no tools allowlist → inherit MCP).
- Skills: .claude/skills/{engineering-evidence,kicad-workflow,firmware-workflow,host-software-workflow,latex-workflow,engineering-reporting,engineering-change}.
- Local MCP adapter: scripts/mcp/server.mjs registered in .mcp.json as `eng-tools` (tools: env_info, kicad_erc, kicad_drc, firmware_compile, run_pytest, latex_build). Verified outside Claude.
- Manager LaTeX smoke test PASS (management/SMOKE_TESTS.md).

## Next steps (in order)
1. Confirm agents are loaded (`/agents`) and approve the project MCP server `eng-tools` when prompted.
2. Invoke EVERY specialist once: call `eng-tools.env_info`, then its route smoke test with a known answer (see SMOKE_TESTS.md rows marked NOT RUN). Electronics: tiny schematic+board in `sim/electronics/smoke/`, ERC/DRC 0. Firmware: compile rpipico + a pytest on extracted logic with known answers. Software: pytest/node test with known answer. Systems: a budget hand calculation reproduced in Python. Documentation: `latex_build` of reports/smoke/latex/smoke.tex copy. Reviewer: env_info + read-only check.
3. systems-engineer: REQUIREMENTS.md (T-008); architecture options + manager ADR; freeze INTERFACES.json (T-009).
4. Stop at G1 with the gate summary (Portuguese chat, English files).

## Re-test MCP adapter outside Claude
`printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"t","version":"0"}}}' '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' | node scripts/mcp/server.mjs`
