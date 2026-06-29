# Task: Transform Keyframes

## Use When

Animate Position, Scale, Rotation, Opacity, or Anchor Point.

## Required Checks

- Active item is `CompItem`.
- At least one layer is selected.
- Transform group and target property exist.
- Value shape matches 2D or 3D layer state.

## Key APIs

- `layer.property("ADBE Transform Group")`
- `transform.property("ADBE Position")`
- `property.setValueAtTime(time, value)`
- `property.numKeys`
- `property.removeKey(index)`

## Minimal JSX Pattern

```javascript
var comp = app.project.activeItem;
if (!(comp instanceof CompItem) || comp.selectedLayers.length < 1) {
    throw new Error("Select one layer in a composition.");
}

var layer = comp.selectedLayers[0];
var transform = layer.property("ADBE Transform Group");
var position = transform.property("ADBE Position");
var startValue = position.value;
var endValue = startValue.slice(0);
endValue[0] += 200;

app.beginUndoGroup("Position Keyframes");
try {
    position.setValueAtTime(comp.time, startValue);
    position.setValueAtTime(comp.time + 1, endValue);
} finally {
    app.endUndoGroup();
}
```

## Common Failures

- Supplying `[x,y]` to a 3D Position property that expects `[x,y,z]`.
- Removing keyframes from low to high indexes.
- Using display names in localized AE installations.

