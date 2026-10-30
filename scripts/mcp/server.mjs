#!/usr/bin/env node
// eng-tools: local, deterministic MCP adapter for the FrutaMIDI project.
// Every tool runs a fixed command inside the project and returns its exit code and
// output verbatim. No tool accepts free-form shell input.
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import fs from "node:fs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const KICAD_BIN = process.env.KICAD_BIN || "/Applications/KiCad/KiCad.app/Contents/MacOS";
const KICAD_CLI = path.join(KICAD_BIN, "kicad-cli");
const ARDUINO_CFG = path.join(ROOT, "tools/arduino/cli.yaml");
const TEX_BIN = path.join(ROOT, "tools/TinyTeX/bin/universal-darwin");
const BOARDS = ["rpipico", "rpipicow", "rpipico2", "rpipico2w", "leonardo"];

function inside(rel) {
  const abs = path.resolve(ROOT, rel);
  if (abs !== ROOT && !abs.startsWith(ROOT + path.sep)) throw new Error(`path outside project: ${rel}`);
  return abs;
}

function run(cmd, args, opts = {}) {
  const t0 = Date.now();
  const r = spawnSync(cmd, args, { cwd: opts.cwd || ROOT, encoding: "utf8", timeout: opts.timeout || 600000,
                                   env: { ...process.env, ...(opts.env || {}) }, maxBuffer: 64 * 1024 * 1024 });
  const out = (r.stdout || "") + (r.stderr || "");
  const lines = out.split("\n").filter((l) => !l.includes("Fontconfig warning"));
  const text = [
    `command: ${cmd} ${args.join(" ")}`,
    `exit_code: ${r.status}${r.error ? " (error: " + r.error.message + ")" : ""}`,
    `duration_s: ${((Date.now() - t0) / 1000).toFixed(1)}`,
    "output:",
    lines.slice(-200).join("\n"),
  ].join("\n");
  return { content: [{ type: "text", text }] };
}

const server = new McpServer({ name: "eng-tools", version: "0.1.0" });

server.tool("env_info", "Report tool versions available to the project (no side effects).", {}, async () => {
  const parts = [];
  for (const [label, cmd, args] of [
    ["kicad-cli", KICAD_CLI, ["version"]],
    ["arduino-cli", "arduino-cli", ["version"]],
    ["python(.venv)", path.join(ROOT, ".venv/bin/python"), ["--version"]],
    ["pdflatex", path.join(TEX_BIN, "pdflatex"), ["--version"]],
    ["node", process.execPath, ["--version"]],
  ]) {
    const r = spawnSync(cmd, args, { encoding: "utf8" });
    parts.push(`${label}: ${r.status === 0 ? (r.stdout || r.stderr).split("\n")[0] : "NOT AVAILABLE (" + (r.error?.message || r.status) + ")"}`);
  }
  parts.push(`project_root: ${ROOT}`);
  return { content: [{ type: "text", text: parts.join("\n") }] };
});

server.tool("kicad_erc", "Run KiCad ERC on a schematic inside the project; report written next to it.",
  { schematic: z.string().describe("project-relative .kicad_sch path") }, async ({ schematic }) => {
    const sch = inside(schematic);
    const rpt = sch.replace(/\.kicad_sch$/, "") + ".erc.rpt";
    const res = run(KICAD_CLI, ["sch", "erc", "--severity-all", "-o", rpt, sch]);
    if (fs.existsSync(rpt)) res.content.push({ type: "text", text: "report:\n" + fs.readFileSync(rpt, "utf8").slice(-8000) });
    return res;
  });

server.tool("kicad_drc", "Run KiCad DRC (with schematic parity) on a board inside the project.",
  { board: z.string().describe("project-relative .kicad_pcb path") }, async ({ board }) => {
    const pcb = inside(board);
    const rpt = pcb.replace(/\.kicad_pcb$/, "") + ".drc.rpt";
    const res = run(KICAD_CLI, ["pcb", "drc", "--severity-all", "--schematic-parity", "-o", rpt, pcb]);
    if (fs.existsSync(rpt)) res.content.push({ type: "text", text: "report:\n" + fs.readFileSync(rpt, "utf8").slice(-8000) });
    return res;
  });

server.tool("firmware_compile", "Compile an Arduino sketch inside the project with the project-local cores.",
  { sketch_dir: z.string().describe("project-relative sketch folder"),
    board: z.enum(BOARDS), pcb_variant: z.boolean().default(false) },
  async ({ sketch_dir, board, pcb_variant }) => {
    const fqbn = board === "leonardo" ? "arduino:avr:leonardo" : `rp2040:rp2040:${board}:usbstack=tinyusb`;
    const args = ["--config-file", ARDUINO_CFG, "compile", "-b", fqbn];
    if (pcb_variant) args.push("--build-property", "compiler.cpp.extra_flags=-DFRUTAMIDI_PCB");
    args.push(inside(sketch_dir));
    return run("arduino-cli", args, { timeout: 900000 });
  });

server.tool("run_pytest", "Run pytest from the project .venv on a project-relative path.",
  { target: z.string().default("tests") }, async ({ target }) =>
    run(path.join(ROOT, ".venv/bin/python"), ["-m", "pytest", "-q", inside(target)]));

server.tool("latex_build", "Compile a .tex file with the project-local TinyTeX (pdflatex, two passes).",
  { tex: z.string().describe("project-relative .tex path") }, async ({ tex }) => {
    const abs = inside(tex);
    const opts = { cwd: path.dirname(abs), env: { PATH: `${TEX_BIN}:${process.env.PATH}` } };
    const a = ["-interaction=nonstopmode", "-halt-on-error", path.basename(abs)];
    run(path.join(TEX_BIN, "pdflatex"), a, opts);
    return run(path.join(TEX_BIN, "pdflatex"), a, opts);
  });

await server.connect(new StdioServerTransport());
