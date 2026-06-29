# Task: Layer Basics

## Use When

Add, select, duplicate, remove, reorder, or inspect layers.

## Required Checks

- Active item is `CompItem`.
- Selected layer count is non-zero for selected-layer operations.
- For source replacement, selected layer is an `AVLayer`.

## Key APIs

- `comp.layers.addSolid(color, name, width, height, pixelAspect, duration)`
- `comp.layers.addText(text)`
- `comp.layers.addNull(duration)`
- `layer.duplicate()`
- `layer.remove()`
- `layer.moveTo(index)`

## Minimal JSX Pattern

```javascript
var comp = app.project.activeItem;
if (!(comp instanceof CompItem)) {
    throw new Error("Select or open a composition first.");
}

app.beginUndoGroup("Add Null");
try {
    var nullLayer = comp.layers.addNull(comp.duration);
    nullLayer.name = "CTRL";
} finally {
    app.endUndoGroup();
}
```

## Common Failures

- Editing locked layers.
- Removing layers while iterating forward.
- Assuming all layers have `source`.

