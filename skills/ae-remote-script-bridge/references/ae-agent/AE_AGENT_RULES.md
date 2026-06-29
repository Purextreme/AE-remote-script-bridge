# AE Agent Rules

## Runtime

- Write After Effects scripts as ExtendScript-compatible `.jsx`.
- Prefer `var`.
- Do not use `let`, `const`, arrow functions, classes, template literals, destructuring, `Promise`, `async`, `await`, `fetch`, `XMLHttpRequest`, browser DOM APIs, `window`, or `document`.
- Use plain `for` loops; avoid relying on modern Array methods.
- Use ExtendScript `File` and `Folder` for filesystem work.

## Project Safety

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

## Expressions

- Scripting API and expression runtime are separate.
- `property.expression = "..."` is scripting code assigning an expression string; it does not mean expression APIs are available to JSX.
- Check `property.canSetExpression` before setting expressions.

