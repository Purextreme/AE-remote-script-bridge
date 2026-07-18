# Preview capture can invalidate the clean-project precondition

- Status: pending review
- Date: 2026-07-17
- Context: Captured a read-only preview before the first protected mutation in a saved, clean working project.
- Observation: `--capture-frame` restored transient settings but reported that capture marked the project dirty. The following protected mutation was correctly rejected with `AE Bridge safety guard: the current project has unsaved changes`.
- Evidence: The capture emitted `[AE CAPTURE WARNING] Frame capture restored transient settings but marked the project dirty`; the next protected call failed before the target JSX ran.
- Workaround: Prefer combining the meaningful mutation and its preview in the same protected call. If an initial preview is necessary, inspect `dirtyChangedByCapture`; do not assume the project remains clean or bypass protection. Any recovery save requires confirming the dirty transition came only from capture and must remain explicit.
- Candidate destination: Preview guidance and project-protection workflow in `SKILL.md`, or a bridge change that avoids or treats the transient bit-depth dirty state safely.
- Review notes:
