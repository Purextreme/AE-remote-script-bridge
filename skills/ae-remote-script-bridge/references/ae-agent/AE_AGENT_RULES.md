# AE Agent Rules

## Runtime

- Write After Effects scripts as ExtendScript-compatible `.jsx`.
- Prefer `var`.
- Do not use `let`, `const`, arrow functions, classes, template literals, destructuring, `Promise`, `async`, `await`, `fetch`, `XMLHttpRequest`, browser DOM APIs, `window`, or `document`.
- Use plain `for` loops; avoid relying on modern Array methods.
- Use ExtendScript `File` and `Folder` for filesystem work.

## Project Safety

- Run mutating scripts through the bridge's default protection. It requires a saved, clean project and creates a rolling `.aep` backup next to the project file before executing the target JSX.
- Reuse one `--operation-id` across all bridge calls in the same user request. The first call backs up the project; later calls with the same id reuse that backup and may run after the project becomes dirty.
- Use `--no-protect` only for read-only checks, disposable bridge tests, or explicitly approved recovery workflows.
- Wrap project edits with `app.beginUndoGroup("name")` and `app.endUndoGroup()`.
- Use `try/finally` so `endUndoGroup()` runs after failures.
- Before active comp work, check `app.project.activeItem instanceof CompItem`.
- Before selected layer work, check `comp.selectedLayers.length`.
- Remember AE collection indexes are often 1-based: `app.project.item(1)`, `comp.layer(1)`, `property.keyTime(1)`.
- Remember `comp.selectedLayers` is a 0-based JavaScript array.

## Property Access

- Prefer stable `matchName` values where known, for example `ADBE Transform Group`, `ADBE Position`, `ADBE Opacity`, `ADBE Effect Parade`.
- Do not invent match names. If a matchName is not verified, mark it `needs_verify`.
- Display names can be localized; use them only when no verified matchName is known or when the API requires a template/display string.
- Always null-check property lookups before using returned objects.
- Adding properties to indexed groups can invalidate existing references. Reacquire properties after `addProperty()` when continuing work.

## Text

- `Source Text` is a `TextDocument` property.
- Read it with `.value`, edit the `TextDocument`, then write it back with `.setValue(textDoc)`.

## Output

- Avoid `alert()` in normal workflows.
- Prefer `$.writeln()` or writing a small report file.
- With this bridge, prefer `$.global.AE_BRIDGE_LOGS_DIR` for reports.
- After key visual edits or a long batch of changes, use `--capture-frame` so the agent can inspect a rendered PNG. Choose `current`, `middle`, `two-thirds`, `end`, or an exact `--capture-time` based on the comp and task. Avoid capture for routine read-only checks because AE may mark the project dirty after temporary Render Queue use.

## Expressions

- Scripting API and expression runtime are separate.
- `property.expression = "..."` is scripting code assigning an expression string; it does not mean expression APIs are available to JSX.
- Check `property.canSetExpression` before setting expressions.
