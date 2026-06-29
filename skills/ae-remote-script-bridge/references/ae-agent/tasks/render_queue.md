# Task: Render Queue

## Use When

Add a comp to the render queue and set an output path.

## Required Checks

- Active item is `CompItem`.
- Output folder exists.
- Avoid assuming template names are available.

## Key APIs

- `app.project.renderQueue.items.add(comp)`
- `rqItem.outputModule(1)`
- `outputModule.file = new File(path)`
- `rqItem.applyTemplate(name)`
- `outputModule.applyTemplate(name)`
- `app.project.renderQueue.render()`

## Minimal JSX Pattern

```javascript
var comp = app.project.activeItem;
if (!(comp instanceof CompItem)) {
    throw new Error("Select or open a composition first.");
}

var outputFile = new File("C:/renders/output.mov");

app.beginUndoGroup("Queue Render");
try {
    var rqItem = app.project.renderQueue.items.add(comp);
    var outputModule = rqItem.outputModule(1);
    outputModule.file = outputFile;
} finally {
    app.endUndoGroup();
}
```

## Common Failures

- Output folder does not exist.
- Template names differ across AE installs.
- Calling `render()` blocks until complete.
- Queueing the wrong active item.

