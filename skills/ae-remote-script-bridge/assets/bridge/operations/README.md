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

## Supported operations

- `create_text`: requires `text`; accepts `name`, `position`, `font`,
  `fontSize`, `fillColor` (0..1 RGB), `alignment`, `startTime`, and `duration`.
- `set_text`: requires a layer selector and `text`; accepts the same font,
  color, and alignment fields.
- `set_transform`: accepts one or more of `position`, `anchorPoint`, `scale`,
  `rotation`, and `opacity`.
- `set_keyframes`: requires `property` (one of the transform names above) and
  `keyframes` as `{time, value}` objects; `clearExisting` is optional.
- `inspect_comp`: returns composition facts and, by default, layer summaries.
- `inspect_layer`: returns text, transform values/keyframes, effects, and masks;
  `includeKeyframes` and `maxKeyframes` bound the response.

Use raw JSX through `client/send_to_ae.py` for effects, masks, shape construction,
special interpolation, expressions, rendering, or any operation not covered by
this intentionally small surface.

## Module boundary

- `client/operation_request.py`: stdlib-only request validation and launcher
  generation.
- `client/run_operation.py`: thin CLI adapter to the existing bridge.
- `operations/ae_operations.jsx`: AE-side handlers only.
- MCP adapters, if added later, should translate MCP arguments into this JSON
  contract rather than owning AE logic.

See `THIRD_PARTY_NOTICES.md` for upstream lineage and licenses.
