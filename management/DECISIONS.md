# Decisions (ADR style)

## ADR-000 — Project setup
- Date: 2026-10-30. Status: accepted (user, Phase A).
- Context: project continues the FrutaMIDI repository (v1.0.0 released, v1.1 on main).
- Decision: project folder `/Users/rod/fruta-midi-controller`; all project files in English (user choice, includes converting the existing Portuguese README/guide); existing paths `hardware/`, `firmware/`, `docs/` kept to avoid breaking released links; commits without Co-Authored-By lines (skill rule, supersedes earlier commits).
- Consequences: the existing Portuguese user documentation must be translated before the next release.

## ADR-001 — End-to-end run without stopping at intermediate gates
- Date: 2026-10-30. Status: accepted (user, chat: "sim, faz tudo, do inicio ao fim").
- Decision: the manager runs G1–G4 without waiting; each gate summary is written to `management/gates/G<n>.md` at the moment it is passed. Publishing a GitHub release (G5 public step) still requires an explicit user "yes" at that moment (CLAUDE.md rule). Pushing commits to `origin/main` is authorized.
- Consequences: user decisions normally taken at gates are taken by the manager and recorded as ADRs, flagged for later user review.

## ADR-002 — Documentation follows firmware for long-press time
- Date: 2026-10-30. Status: accepted (manager, ADR-001 authority; flagged for user review).
- Context: docs said "hold 1 s" to recalibrate; firmware uses `now - downAt > 800` (800 ms). Evidence: T-030 handoff.
- Decision: firmware is the source of truth; docs state 0.8 s. No firmware change.

## ADR-003 — Safety statement on touchable electrodes
- Status: accepted. The README must not claim "safe to touch" without evidence. Wording waits for the electronics analysis T-050 (ESD/current limiting); until then it is qualified as an ASSUMPTION.

## ADR-004 — English file and folder names
- Status: accepted. `hardware/fabrico/` → `hardware/fabrication/`, `imagens/` → `images/`, Portuguese PDF names → English, done by electronics in build_all.sh after T-050 (task T-051), docs links updated afterwards by documentation.

## ADR-005 — Sampler fixes and language
- Status: accepted (manager under ADR-001; flagged for user review). Evidence: T-020 handoff.
- FINDING-SW-2: learning a note already used by another pad SWAPS the two pads' notes (both stay reachable; no silent shadowing).
- FINDING-SW-1: before audio is enabled, incoming notes still flash pads and the page shows a visible "click to enable sound" hint.
- MIDI channels: the sampler stays omni (accepts all 16 channels); the firmware channel is configurable, so filtering would add a failure mode for no benefit.
- Language: ADR-000 (all English) extends to user-visible strings: sampler UI text and PCB silkscreen ("ESCALA"→"SCALE", "OITAVA"→"OCTAVE", T-051).
