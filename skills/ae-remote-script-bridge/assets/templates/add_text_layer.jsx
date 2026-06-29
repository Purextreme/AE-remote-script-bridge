(function () {
    var comp = app.project.activeItem;
    if (!(comp instanceof CompItem)) {
        throw new Error("Select or open a composition first.");
    }

    app.beginUndoGroup("Add Text Layer");
    try {
        var textLayer = comp.layers.addText("Agent Text");
        textLayer.name = "Agent Text";

        var textGroup = textLayer.property("ADBE Text Properties");
        var sourceText = textGroup.property("ADBE Text Document");
        var textDoc = sourceText.value;
        textDoc.fontSize = 72;
        textDoc.fillColor = [1, 1, 1];
        sourceText.setValue(textDoc);

        var transform = textLayer.property("ADBE Transform Group");
        var position = transform.property("ADBE Position");
        position.setValue([comp.width / 2, comp.height / 2]);
    } finally {
        app.endUndoGroup();
    }
})();

