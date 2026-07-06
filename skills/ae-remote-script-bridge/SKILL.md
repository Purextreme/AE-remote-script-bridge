---
name: ae-remote-script-bridge
description: Operate Adobe After Effects from Codex through a Windows AfterFX.com JSX bridge and a lightweight AE scripting reference. Use when Codex needs to inspect, create, modify, organize, render, save, or verify an open After Effects project with ExtendScript/JSX; when an agent needs AE scripting rules, common APIs, match names, pitfalls, task cards, or runnable JSX templates; or when AE version compatibility, match names, or app.project state must be checked from inside After Effects.
---

# AE Remote Script Bridge

Use this skill for After Effects scripting with ExtendScript JSX, not the C++ SDK and not browser JavaScript.

## Reference Workflow

Start with `references/ae-agent/AE_INDEX.md`.

Read only the needed reference file:

- Core JSX rules: `references/ae-agent/AE_AGENT_RULES.md`
- Frequent scripting APIs: `references/ae-agent/AE_API_TABLE.md`
- Common match names: `references/ae-agent/AE_MATCHNAME_TABLE.md`
- Common failure modes: `references/ae-agent/AE_PITFALLS.md`
- Task-specific cards: `references/ae-agent/tasks/`
- Older bridge operation examples: `references/ae-operations.md`

Use bundled templates from `assets/templates/` when they fit the task:

- `inspect_active_comp.jsx`
- `add_text_layer.jsx`
- `add_position_keyframes.jsx`

Do not load long external docs unless the local reference marks an area `needs_verify`, the API is version-sensitive, or AE returns repeated errors.

## Bridge Setup

Prefer an existing workspace bridge when it contains:

```text
client/send_to_ae.py
scripts/
logs/
temp/
```

If the workspace does not contain a bridge, copy `assets/bridge/` from this skill into the workspace. The copied bridge is self-contained.

The bridge uses `AfterFX.com -r`, not `AfterFX.exe -r`.

`client/send_to_ae.py` resolves `AfterFX.com` in this order:

1. `--afterfx "C:\path\to\AfterFX.com"`
2. `AFTERFX_COM_PATH`
3. optional bridge-local `config.json` with `afterfx_com_path`
4. automatic search under `C:\Program Files\Adobe\Adobe After Effects *\Support Files\AfterFX.com`

If automatic discovery fails, create a bridge-local `config.json` based on `config.example.json` or pass `--afterfx`.

## Running JSX

From the bridge root:

```bat
python client\send_to_ae.py scripts\your_script.jsx
```

or with an explicit AE path:

```bat
python client\send_to_ae.py --afterfx "C:\path\to\AfterFX.com" scripts\your_script.jsx
```

By default, `send_to_ae.py` protects the user's project before running a target script:

- AE must have an open project.
- The project must already be saved to an `.aep` file.
- The project must not have unsaved changes.
- The bridge copies the current `.aep` into an `agent backups/` folder next to the project file with an `agent backup` prefix and keeps the latest 10 backups.

If the project is unsaved or dirty, the bridge writes an `[AE ERROR]` result for the agent and shows an AE alert for the user before the target JSX runs. Use `--no-protect` only for read-only checks, disposable bridge tests, or explicitly approved recovery workflows.

For multi-command agent work, generate one stable `--operation-id` for the user request and pass it to every mutating bridge call in that request. The first call performs the saved/clean check and creates the backup; later calls with the same `--operation-id` reuse that backup and do not block on dirty state created by earlier calls. Use a new `--operation-id` for the next user request.

The bridge injects these ExtendScript globals:

```javascript
$.global.AE_BRIDGE_ROOT
$.global.AE_BRIDGE_LOGS_DIR
$.global.AE_BRIDGE_TEMP_DIR
$.global.AE_BRIDGE_RESULT_PATH
```

Use them for reports and temporary outputs instead of hardcoded paths.

Treat `[AE OK]` as proof that JSX finished without throwing. For meaningful changes, verify AE state from inside AE.

For key visual operations or after a batch of changes, request a frame capture in the same command:

```bat
python client\send_to_ae.py scripts\your_script.jsx --capture-frame --capture-time-mode two-thirds
```

Use `--capture-time-mode current`, `middle`, `two-thirds`, or `end`, or pass `--capture-time <seconds>`. For animated comps, choose a middle or middle-late frame when it better represents the result. The bridge captures the active composition through an isolated Render Queue item, restores existing queued items, then writes a resized preview PNG with a long edge of at most 1500 px. AE may still mark the project dirty because Render Queue was touched; the capture report includes `dirtyChangedByCapture` and the client prints a warning when this happens.

## Verification Workflow

After any meaningful AE operation, run:

```bat
python client\send_to_ae.py --no-protect scripts\ae_inspect_project.jsx
```

Then read `logs/project_structure.json` and compare concrete facts: comp names, dimensions, duration, layer names, text, source names, effect counts, keyframe counts, output files, and saved project paths.

When visual appearance matters, also capture a frame after the operation or batch. Do not capture after every tiny change. Prefer `--capture-time-mode middle` or `--capture-time-mode two-thirds` for animated comps unless the user's request points to a specific time.

For version-sensitive work, write a tiny probe script that reports `app.version`, `app.buildName`, `app.buildNumber`, `app.isoLanguage`, and feature availability checks.

## JSX Authoring Rules

Use ExtendScript-compatible JavaScript:

- prefer `var`
- avoid `let`, `const`, arrow functions, template literals, destructuring, classes, `Promise`, `async`, `await`, `fetch`, DOM APIs, and browser globals
- wrap project edits with `app.beginUndoGroup()` / `app.endUndoGroup()`
- check `app.project.activeItem instanceof CompItem` before comp work
- check `comp.selectedLayers.length` before selected-layer work
- prefer verified match names such as `ADBE Effect Parade`, `ADBE Transform Group`, `ADBE Position`, `ADBE Opacity`
- do not invent match names; mark uncertain areas `needs_verify`
- avoid `alert()` in normal workflows; write reports or use `$.writeln()`

Read `references/ae-agent/AE_AGENT_RULES.md` for the full rule list before writing non-trivial JSX.

## Built-In Bridge Checks

Use these from the bridge root:

```bat
python client\send_to_ae.py --no-protect scripts\ae_test_create_comp.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_modify_active_comp.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_error.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_integration_ops.jsx
python client\send_to_ae.py --no-protect scripts\ae_inspect_project.jsx
```
