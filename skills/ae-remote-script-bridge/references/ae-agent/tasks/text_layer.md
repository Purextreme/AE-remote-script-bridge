# Task: Text Layer

## Use When

Create text layers or edit text contents/style.

## Required Checks

- Active item is `CompItem`.
- Source Text property exists before reading/writing.
- Write modified `TextDocument` back with `setValue()`.

## Key APIs

- `comp.layers.addText(text)`
- `layer.property("ADBE Text Properties")`
- `textGroup.property("ADBE Text Document")`
- `sourceText.value`
- `sourceText.setValue(textDoc)`

## Minimal JSX Pattern

```javascript
var comp = app.project.activeItem;
if (!(comp instanceof CompItem)) {
    throw new Error("Select or open a composition first.");
}

app.beginUndoGroup("Add Text");
try {
    var textLayer = comp.layers.addText("Hello AE");
    var textProp = textLayer.property("ADBE Text Properties").property("ADBE Text Document");
    var textDoc = textProp.value;
    textDoc.fontSize = 64;
    textDoc.fillColor = [1, 1, 1];
    textProp.setValue(textDoc);
} finally {
    app.endUndoGroup();
}
```

## Common Failures

- Editing `textDoc` but not calling `setValue(textDoc)`.
- Assuming a selected layer is a `TextLayer`.
- Using newer TextDocument fields without version checks.

