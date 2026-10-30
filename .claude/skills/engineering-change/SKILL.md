---
name: engineering-change
description: Change process for a released FrutaMIDI baseline. Only run when the user explicitly types /engineering-change <description>.
disable-model-invocation: true
argument-hint: <description of the change>
---

# Engineering change

Run only on an explicit `/engineering-change <description>` from the user.

1. Preserve the baseline: never edit files under `releases/<baseline>/`; work on a new branch `change/CR-<nnn>`.
2. Open `changes/CR-<nnn>.md` (next free number): description, requester, date, reason.
3. Impact analysis: affected requirements (IDs), parts/BOM lines, interfaces in `management/INTERFACES.json`, firmware pins/flags, documents. Write it in the CR before any design work.
4. Delegate to the affected specialists through the manager with assignments (goal, input revisions, paths, acceptance criteria, handoff contract).
5. Compare old vs new: ERC/DRC/compile/test results and metrics side by side, with labels.
6. Re-review: `independent-reviewer` on the changed outputs only, with requirements and interfaces.
7. Publish a new release folder `releases/V<n>_.../` with SHA-256 manifest and updated report; update PROJECT_STATE and the requirement status matrix. Publishing to GitHub needs explicit user approval.
