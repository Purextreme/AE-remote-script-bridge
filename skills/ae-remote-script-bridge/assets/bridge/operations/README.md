# Stable Operations

This directory contains a small, MCP-independent operation layer for common AE
edits. It runs through the existing `AfterFX.com` bridge, so project protection,
operation IDs, per-run logs, timeouts, frame capture, and the raw JSX escape
hatch remain unchanged.

Run a JSON request from the bridge root:

```bat
python client\run_operation.py examples\operations\create_text.json --operation-id my-task
python client\run_operation.py examples\operations\inspect_active_comp.json --no-protect
python client\run_operation.py examples\operations\text_batch.json --no-protect --capture-frame --capture-time 1
```

`run_operation.py` validates the request before launching AE and forwards all
remaining options to `send_to_ae.py`. Mutating requests should normally use a
stable `--operation-id`; `--no-protect` is only for read-only work or an
explicitly disposable test project.

## Request shape

One operation:

```json
{
  "operation": "set_transform",
  "args": {
    "compName": "Main",
    "layerName": "Title",
    "position": [960, 540],
    "opacity": 100
  }
}
```

A batch of at most 50 operations:

```json
{
  "operations": [
    {"operation": "create_text", "args": {"text": "Hello", "name": "Title"}},
    {"operation": "inspect_comp", "args": {"includeLayers": true}}
  ]
}
```

A mutating batch uses one AE undo group and one bridge round trip. It is
fail-fast. If a later operation fails, `result.json.payload` reports
`completedCount` and the completed results; it does not automatically undo
earlier operations. After a client timeout or interruption, treat AE state as
unknown and inspect before continuing.

`render_comp` must be a standalone request and does not run inside an Undo
Group. `app.project.renderQueue.render()` is blocking and can make AE show an
Undo Group mismatch warning if it is wrapped by one.

## Target selectors

Composition selectors are optional and mutually exclusive:

- `compId`: AE item ID.
- `compName`: exact, unique composition name.
- Omit both to use the active composition.

Layer operations require exactly one selector:

- `layerId`: AE layer ID when the installed AE version exposes it.
- `layerIndex`: current 1-based layer index.
- `layerName`: exact, unique layer name.

An ambiguous name is an error; the operation never silently selects the first
match.

Footage/source item operations require exactly one `itemId` or unique exact
`itemName`. Effect operations require an effect index, unique effect name, or
unique effect matchName. Effect properties use an index or exact matchName.

## Supported operations

### Composition and layers

- `create_comp`: requires `name`, `width`, `height`, `duration`, and
  `frameRate`; accepts `pixelAspect` and `bgColor` (0..1 RGB).
- `set_comp`: changes only supplied composition fields: name, dimensions,
  duration, frame rate, pixel aspect, or background color.
- `open_comp`: opens the exact target comp in a viewer so preview capture does
  not rely on implicit active-item state.
- `create_solid`: creates a Solid in a target comp; accepts dimensions,
  duration, pixel aspect, and position.
- `add_source_layer`: adds an exact project item as a layer and accepts layer
  name, position, start time, and duration.
- `create_text` / `set_text`: create or replace text with bounded font, size,
  fill color, alignment, timing, and position options.
- `set_transform`: sets one or more of position, anchor point, scale, rotation,
  and opacity.
- `set_keyframes`: sets Transform keyframes as `{time, value}` objects;
  `clearExisting` is optional.

### Footage

- `import_footage`: imports one explicit existing path and returns the item ID.
- `inspect_footage`: returns path, dimensions, AE `footageMissing`, real-time
  `fileExists`, and combined `missing` state. AE can cache `footageMissing`
  after the host moves a file, so do not rely on that field alone.
- `relink_footage`: replaces one exact FootageItem with one caller-provided
  file path while preserving item identity and layer references.

Relinking is never automatic. The operation does not search folders, choose a
candidate, or retry a different file.

### Effects, inspection, and output

- `add_effect` / `remove_effect`: add by verified effect matchName and remove by
  an exact selector.
- `set_effect_property`: sets one scalar or numeric-array property selected by
  property index or matchName. Fill Color (`ADBE Fill-0002`) and Tint Amount
  (`ADBE Tint-0003`) were probed in AE 2024.
- `inspect_comp`: returns composition configuration and bounded layer summaries.
- `inspect_layer`: returns text, Transform values/keyframes, effects, and masks;
  `includeEffectProperties`, `maxEffectProperties`, `includeKeyframes`, and
  `maxKeyframes` bound the response.
- `render_comp`: performs a standalone blocking render, temporarily disables
  pre-existing queued items, restores their render flags, and normally removes
  its test item afterward. Template names must exist on the current AE install.

Use raw JSX through `client/send_to_ae.py` for masks, shape construction,
special interpolation, expressions, advanced effect paths, advanced render
configuration, or any operation outside this intentionally bounded surface.

## Module boundary

- `client/operation_request.py`: stdlib-only request validation and launcher
  generation.
- `client/run_operation.py`: thin CLI adapter to the existing bridge.
- `client/run_production_tests.py`: stdlib-only production suite orchestration,
  artifact preservation, assertions, and exact-prefix cleanup.
- `operations/ae_operations.jsx`: AE-side handlers only.
- `scripts/ae_probe_production_capabilities.jsx`: temporary, self-cleaning
  effect/template capability probe.
- `tests/production/`: suite usage and fixture policy.
- MCP adapters, if added later, should translate MCP arguments into this JSON
  contract rather than owning AE logic.

See `THIRD_PARTY_NOTICES.md` for upstream lineage and licenses.
