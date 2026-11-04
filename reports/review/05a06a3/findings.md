# Re-review of 72f67f0..05a06a3 (T-061)

Reviewer: independent-reviewer (inputs: REQUIREMENTS draft-5, INTERFACES frozen-2, git diff 72f67f0..05a06a3 of design outputs; no handoffs). Saved by the manager (reviewer harness refuses report writes).
Checks by reviewer: run_pytest tests/firmware "295 passed in 1.93s"; kicad_erc "Found 0 violations" (single-pin-label ignore removed); kicad_drc 0/0/0; evidence-path existence via git cat-file (1 missing: reports/firmware/T-044/build/*.log, git-ignored); status counts 17/18/3/4 = 42 match.

## Disposition verification
| ID | Verdict |
|---|---|
| F-001 | CLOSED (hardware/README §5 abs-max + back-feed; §6 pre-insertion JP1 check) |
| F-002 | CLOSED (REQ-023 "estimate on ASSUMPTIONs, not a PASS"; τ/Q comparison; closure by ESD test) |
| F-003 | CLOSED (REQ-006 restated; A5 noise+DNL+quantisation+ripple 0.0364 V < 0.132 V) |
| F-004 | CLOSED (fm_notes.h reference counting hand-traced: octave change while held, releaseAll, sent[] bookkeeping, clamp) |
| F-005 | CLOSED (sensor health; real defect fixed: NACK → touched() 0x0FFF) — see N-001 |
| F-006 | CLOSED (AVR twi.c:94 TWI_FREQ reset confirmed; setClock after begin) |
| F-007 | NOT CLOSED at 05a06a3 (build logs git-ignored) → fixed after review (ADR-018) |
| F-008 | CLOSED (budgets.md generated; coverage.md 200) — residue N-002 |
| F-009 | CLOSED |
| F-010 | CLOSED (REQ-018 FAIL) |
| F-011 | CLOSED (REQ-014 first touch; lockout 25.72 ms separate) |
| F-012 | ACCEPTED (ASSUMPTION, plan P-2) |
| F-013 | CLOSED at root (J3 part; no ERC ignore; ERC 0) |
| F-014 | CLOSED (1.4 mm drill, 0.13 mm over diagonal, ring 0.80 mm; slot instruction) |
| F-015 | CLOSED (MPNs, headers J4–J7, 2 strips) |
| F-016 | CLOSED (cited S-01 §2.1 / S-02) |

## New findings
| ID | Sev | Finding | Disposition |
|---|---|---|---|
| N-001 | minor | Restart of a self-reset chip (ECR mismatch) runs full begin()+configure in loop(): 16.8–22.1 ms, pausing the other sensor beyond REQ-016's 10 ms. | ACCEPTED as specified exception in REQ-016 (ADR-018) |
| N-002 | minor | REQ-016 evidence stale (line ref; worst loop ≈1.72 ms incl. ECR poll). | FIXED (ADR-018) |
| N-003 | info | INTERFACES has no J3/J4–J7. | FIXED (frozen-3, IF-PCB-AUX) |
| N-004 | info | With 2 sensors configured and one absent the LED blinks fast permanently. | ACCEPTED (matches REQ-009 and manual) |
| N-005 | info | Second pad on an already sounding note is silent (no retrigger). | ACCEPTED (matches REQ-042 and manual) |

Not covered: compile runs (logs only); copper PDFs/silkscreen visual; report LaTeX; individual test cases of test_notes_health.py.
