# AE Scripting Pitfalls

- ExtendScript is not modern JavaScript. Use ES3-style syntax and `var`.
- AE scripting is not browser JavaScript. No DOM, `fetch`, `Promise`, or web APIs.
- AE scripting API is separate from expression runtime. Do not use expression-only globals in JSX.
- Many AE indexes are 1-based: project items, comp layers, properties, keyframes.
- `comp.selectedLayers` is a 0-based JavaScript array and may be empty.
- `app.project.activeItem` may be `null`, `FolderItem`, or `FootageItem`; check `instanceof CompItem`.
- Display names can be localized; prefer verified `matchName`.
- `layer.property(...)` can return `null`; null-check before chaining.
- `TextDocument` edits are not written until `sourceTextProperty.setValue(textDoc)`.
- 2D and 3D layer Position values have different dimensions.
- Separated Position uses `ADBE Position_0`, `_1`, `_2`; ordinary Position uses `ADBE Position`.
- Removing keyframes shifts indexes; remove from highest index to lowest.
- Adding properties to indexed groups can invalidate existing property references.
- `replaceSource(..., true)` can be expensive because it tries to fix expressions.
- Render queue and output module template names may differ by version, language, or user setup.
- `app.project.renderQueue.render()` blocks until rendering completes.
- Some source docs include officially undocumented fields; mark them `needs_verify` before use.

