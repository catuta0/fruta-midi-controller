---
name: engineering-evidence
description: Evidence rules for the FrutaMIDI engineering project: number labels, status words, revisions, checksums, locks and handoffs. Use whenever producing results, numbers or handoffs.
---

# Engineering evidence

## Labels (every number)
SOURCE (datasheet/standard, cite in management/SOURCES.md) · CALCULATION (show formula and inputs) · SIMULATION (tool, version, model, settings) · MEASUREMENT (instrument or command, raw output path) · ASSUMPTION (why, and how it will be checked).
Record numbers that others will reuse in `management/metrics.json`: name, value, unit, label, revision, evidence path.

## Status words
PASS, PARTIAL, FAIL, BLOCKED, NOT RUN — nothing else. Never relabel a FAIL. ERC/DRC/compile/lint passing is not hardware validation. Simulation is not test.

## Proof
Exit code 0 is not a pass. Open the output and quote the line that proves the claim (e.g. `Found 0 violations`, `3 passed`). Keep raw logs under `logs/<agent>/` or next to the report.

## Revisions and checksums
State the git revision (`git rev-parse --short HEAD`, plus `-dirty` if `git status --porcelain` is non-empty) of every input. For released files, record `shasum -a 256`.

## Locks
One writer per file. Shared file → create `management/locks/<slug>.lock` containing agent name + UTC time; delete when done. Existing lock → stop, report BLOCKED.

## Handoff template
```
# <task-id> — <agent>
Status: PASS | PARTIAL | FAIL | BLOCKED | NOT RUN
Requirements addressed:
Inputs (path @ revision):
Outputs:
Checks performed (command · version · result line):
Numerical findings (value unit LABEL):
Assumptions:
Errors:
Open decisions for manager:
Next actions:
```
