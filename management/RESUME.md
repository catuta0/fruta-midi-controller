# RESUME
Last update: 2026-11-11. CR-003 (SMD board for home etching) complete: releases/V1.3 (tag v1.3.0) on main. Earlier: V1.2 (v1.2.0), V1_BASELINE (v1.1.0-baseline).
G5 (v1.3) closed. GitHub release v1.3.0 published with the user's explicit "sim" (2026-11-11): https://github.com/catuta0/fruta-midi-controller/releases/tag/v1.3.0 (10 assets; 9 binaries downloaded back, all match SHA256SUMS).
Also open for the user: the pcgate edits in CLAUDE.md and .claude/agents/ (incl. resource-manager.md) are uncommitted; resource-manager.md still says BLOCKED at swap >= 10 GB (user said pcgate runs one job at a time at 10-14 GB).

## GitHub release (2026-11-04)
Published with explicit user approval: https://github.com/catuta0/fruta-midi-controller/releases/tag/v1.1.0 (tag v1.1.0 = 048023c, same commit as v1.1.0-baseline). 12 assets: 8 UF2, Leonardo hex, fabrication zip, report PDF, SHA256SUMS (verified 20/20 OK before upload).

## CR-002 / v1.2 (2026-11-07)
Branch change/CR-002. changes/CR-002.md opened (flashover across R1–R12 + pulse-rated part; supersedes CR-001 candidate).
Next: delegate T-060 to electronics-engineer (assignment text = CR-002 acceptance criteria), then documentation/systems updates, independent re-review, then the user's requested /anthropic-skills:analisar-pcb on the v1.2 board, then release V1.2 folder (GitHub release only on explicit yes).

## CR-002 closed (2026-11-08)
T-060…T-082 done; final re-review T-079 release-ready, F2-001…F2-007 dispositioned (ADR-022); INTERFACES frozen-7; report 42 pages (sha256 8600c847…bc1bc6). releases/V1.2 with SHA256SUMS 21/21 OK. Merged change/CR-002 into main, tag v1.2.0.
Published with explicit user approval (2026-11-08): https://github.com/catuta0/fruta-midi-controller/releases/tag/v1.2.0 (tag v1.2.0 = 193d6ae). 12 assets: 8 UF2, Leonardo hex, fabrication zip, report PDF, SHA256SUMS; 11 binary assets downloaded back and matched against SHA256SUMS.
Next: only the physical validation plan V-01…V-29 remains (out of scope here).

## CR-003 / v1.3 (2026-11-09 → 2026-11-11)
Branch change/CR-003. SMD conversion (ADR-023), Mouser BOM (ADR-024), R1-R12 YAGEO RC2512FK-073K3L (ADR-026, pulse NOT PROVEN), rulings ADR-027, review T-102 → fixes T-103..T-107 (ADR-028), re-review T-108 (ready after fixes) → fixes T-109..T-113 (ADR-029). INTERFACES frozen-9 frozen; requirements draft-16 (18 PASS, 18 PARTIAL, 2 FAIL, 4 NOT RUN). Report 56 pages. releases/V1.3 with SHA256SUMS 20/20 OK; firmware rebuilt via pcgate (9/9, sizes equal to V1.2; pcb- Pico W/2 W not shipped). Purchase list: management/PURCHASE_LIST_v1.3.md (user orders; R1-R12 stock 13).
Resource-manager before the release batch: PASS (swap 8 GB, disk 45 GB, queue empty).
Next: only the physical first build (FB-1..FB-12) remains, out of scope.
