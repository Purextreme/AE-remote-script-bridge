# AE Remote Script Bridge Improvement Queue

This file is an append-only review queue for reusable experience discovered during real After Effects operations. Entries are candidates, not established skill rules. A maintainer must review them before moving anything into `SKILL.md`, a task card, a reference, or bridge code.

## Recording rules

- Record only behavior observed in a real run with concrete evidence such as an error, warning, run artifact, or reproducible command.
- Search this file first and do not add a duplicate entry.
- Keep user secrets, authentication data, private asset contents, and unnecessary machine identifiers out of entries.
- Append new entries; do not silently rewrite, delete, or promote existing entries.
- Set `Status` to `pending review`. The maintainer owns later acceptance, rejection, consolidation, and removal.

## Entry template

```markdown
### YYYY-MM-DD - Short title

- Status: pending review
- Context: What operation and environment exposed the issue.
- Observation: Exact behavior, error, or warning.
- Evidence: Relevant command, run artifact, or reproducible condition.
- Workaround: What safely unblocked the task.
- Candidate destination: Possible `SKILL.md`, reference, task card, or bridge-code location.
- Review notes: Leave blank for the maintainer.
```

## Pending review

### 2026-07-17 - Force UTF-8 console output for bridge runs under Chinese paths

- Status: pending review
- Context: Ran `client\send_to_ae.py` from a workspace path containing Chinese characters on Windows with Python 3.12.
- Observation: The bridge stopped before JSX execution while printing `Run Dir`; the console used `cp1252` and raised `UnicodeEncodeError: 'charmap' codec can't encode characters`.
- Evidence: Reproduced when the run directory contained `AINAS项目素材`; rerunning the same command with `PYTHONIOENCODING=utf-8` completed normally.
- Workaround: In PowerShell, set `$env:PYTHONIOENCODING='utf-8'` for the bridge process before invoking Python.
- Candidate destination: Bridge launcher code or the Windows command examples in `SKILL.md`.
- Review notes:

### 2026-07-17 - Preview capture can invalidate the clean-project precondition

- Status: pending review
- Context: Captured a read-only preview before the first protected mutation in a saved, clean working project.
- Observation: `--capture-frame` restored transient settings but reported that capture marked the project dirty. The following protected mutation was correctly rejected with `AE Bridge safety guard: the current project has unsaved changes`.
- Evidence: The capture emitted `[AE CAPTURE WARNING] Frame capture restored transient settings but marked the project dirty`; the next protected call failed before the target JSX ran.
- Workaround: Prefer combining the meaningful mutation and its preview in the same protected call. If an initial preview is necessary, inspect `dirtyChangedByCapture`; do not assume the project remains clean or bypass protection. Any recovery save requires confirming the dirty transition came only from capture and must remain explicit.
- Candidate destination: Preview guidance and project-protection workflow in `SKILL.md`, or a bridge change that avoids/treats the transient bit-depth dirty state safely.
- Review notes:

### 2026-07-17 - Reuse one protection operation ID throughout the same task

- Status: pending review
- Context: A single user request required an initial AE edit followed by a layout adjustment and repeated verification calls.
- Observation: Treating related mutations as separate protected operations repeats the saved/clean check and may create redundant project backups, adding avoidable latency. The bridge already supports protection-state reuse for this case.
- Evidence: Passing the same `--operation-id` to the follow-up mutation produced `[AE BACKUP REUSED]` and reused the first protected backup instead of creating another one.
- Workaround: Generate one stable `--operation-id` per user-request batch and reuse it for every related mutating bridge call, including corrective iterations. Start a new ID only for a genuinely new user request; read-only inspection continues to use `--no-protect` where permitted.
- Candidate destination: Make operation-ID reuse more prominent in the core mutation workflow and command templates; consider a client-side task/session helper if agents still generate new IDs accidentally.
- Review notes:
