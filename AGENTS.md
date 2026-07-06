# Repository Guidelines

## Project Structure & Module Organization

This repository packages a Codex skill for operating Adobe After Effects through a Windows `AfterFX.com` JSX bridge. The installable skill lives in `skills/ae-remote-script-bridge/`.

- `SKILL.md` is the skill entry point and workflow guide.
- `agents/openai.yaml` contains agent-facing configuration.
- `assets/bridge/` contains the reusable bridge client, test JSX scripts, logs, temp directory placeholders, and `config.example.json`.
- `assets/templates/` contains small reusable JSX examples.
- `references/ae-agent/` contains rules, API tables, matchName tables, pitfalls, and task cards.

Keep changes scoped to the relevant skill area. Do not edit generated `logs/` or `temp/` outputs except for tracked placeholder files.

## Build, Test, and Development Commands

There is no package build step for this repository. Validate changes by inspecting Markdown and, for bridge changes, running the bundled scripts from the bridge root:

```bat
cd skills\ae-remote-script-bridge\assets\bridge
python client\send_to_ae.py --no-protect scripts\ae_test_create_comp.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_modify_active_comp.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_error.jsx
python client\send_to_ae.py --no-protect scripts\ae_test_integration_ops.jsx
python client\send_to_ae.py --no-protect scripts\ae_inspect_project.jsx
```

Use `--afterfx`, `AFTERFX_COM_PATH`, or a local `config.json` when automatic `AfterFX.com` discovery is not enough.

## Coding Style & Naming Conventions

Python code uses standard library modules, four-space indentation, `snake_case` functions, and clear path handling with `pathlib`. JSX must remain ExtendScript-compatible: prefer `var`, avoid modern browser JavaScript features, and wrap project edits in `app.beginUndoGroup()` / `app.endUndoGroup()`.

Name task cards and scripts with lowercase descriptive names, using underscores where helpful, for example `ae_test_create_comp.jsx` or `transform_keyframes.md`.

## Testing Guidelines

No standalone test framework is configured. Treat the bridge scripts under `assets/bridge/scripts/` as integration checks that require Windows and After Effects. After meaningful AE operations, run `ae_inspect_project.jsx` and compare concrete output in `logs/project_structure.json`. For key visual changes, use `--capture-frame` and choose the inspected comp time deliberately. For multi-command mutating work, reuse one `--operation-id` for the current user request.

## Commit & Pull Request Guidelines

Recent commits use short imperative or scope-prefixed subjects, such as `docs: translate readme to Chinese` or `Improve AE ExtendScript skill guidance`. Keep commits focused and describe the user-visible change.

Pull requests should include a concise summary, changed paths, verification performed, and any AE version or Windows configuration used. Include screenshots or log excerpts only when they clarify behavior.

## Security & Configuration Tips

Do not commit local `config.json`, generated logs, temp files, `agent backups/` folders, backup `.aep` files, or machine-specific `AfterFX.com` paths. Use `config.example.json` as the template for local setup.
