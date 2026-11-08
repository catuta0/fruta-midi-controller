# RESUME
Last update: 2026-11-08. CR-002 complete: releases/V1.2 (tag v1.2.0) on main, pushed. Earlier: V1_BASELINE (v1.1.0-baseline).
Only open action: publish the GitHub release v1.2.0 from releases/V1.2/ (needs explicit user "yes"; assets: 8 UF2, Leonardo hex, fabrication zip, report PDF, SHA256SUMS; verify SHA256SUMS first).
Next work (if any) goes through /engineering-change (candidate CR-001: pulse-rated electrode resistor), and the physical validation plan V-01..V-22 in the report.

## GitHub release (2026-11-04)
Published with explicit user approval: https://github.com/catuta0/fruta-midi-controller/releases/tag/v1.1.0 (tag v1.1.0 = 048023c, same commit as v1.1.0-baseline). 12 assets: 8 UF2, Leonardo hex, fabrication zip, report PDF, SHA256SUMS (verified 20/20 OK before upload).

## CR-002 / v1.2 (2026-11-07)
Branch change/CR-002. changes/CR-002.md opened (flashover across R1–R12 + pulse-rated part; supersedes CR-001 candidate).
Next: delegate T-060 to electronics-engineer (assignment text = CR-002 acceptance criteria), then documentation/systems updates, independent re-review, then the user's requested /anthropic-skills:analisar-pcb on the v1.2 board, then release V1.2 folder (GitHub release only on explicit yes).

## CR-002 closed (2026-11-08)
T-060…T-082 done; final re-review T-079 release-ready, F2-001…F2-007 dispositioned (ADR-022); INTERFACES frozen-7; report 42 pages (sha256 8600c847…bc1bc6). releases/V1.2 with SHA256SUMS 21/21 OK. Merged change/CR-002 into main, tag v1.2.0.
Next: user "yes" → `gh release create v1.2.0` with the assets above. Then only the physical validation plan V-01…V-29 remains (out of scope here).
