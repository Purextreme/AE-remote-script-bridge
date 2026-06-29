# Task: Comp Basics

## Use When

Read or create compositions; inspect active comp; iterate comp layers.

## Required Checks

- `app.project` exists.
- For active comp work: `app.project.activeItem instanceof CompItem`.
- For layer iteration: use `1 <= i <= comp.numLayers`.

## Key APIs

- `app.project.activeItem`
- `app.project.items.addComp(name, width, height, pixelAspect, duration, frameRate)`
- `comp.numLayers`
- `comp.layer(index)`
- `comp.selectedLayers`

## Minimal JSX Pattern

```javascript
var comp = app.project.activeItem;
if (!(comp instanceof CompItem)) {
    throw new Error("Select or open a composition first.");
}

for (var i = 1; i <= comp.numLayers; i += 1) {
    var layer = comp.layer(i);
    $.writeln(i + ": " + layer.name);
}
```

## Common Failures

- Treating `activeItem` as a comp without checking.
- Using 0-based indexes with `comp.layer(index)`.
- Assuming `selectedLayers[0]` exists.

