(function () {
    var comp = app.project.activeItem;
    if (!(comp instanceof CompItem)) {
        throw new Error("Select or open a composition first.");
    }
    if (comp.selectedLayers.length < 1) {
        throw new Error("Select one layer before running this script.");
    }

    var layer = comp.selectedLayers[0];
    var transform = layer.property("ADBE Transform Group");
    if (transform === null) {
        throw new Error("Selected layer has no Transform group.");
    }

    var position = transform.property("ADBE Position");
    if (position === null) {
        throw new Error("Selected layer has no Position property.");
    }

    var startValue = position.value;
    var endValue = startValue.slice(0);
    endValue[0] = endValue[0] + 200;

    app.beginUndoGroup("Add Position Keyframes");
    try {
        position.setValueAtTime(comp.time, startValue);
        position.setValueAtTime(comp.time + 1, endValue);
    } finally {
        app.endUndoGroup();
    }
})();

