(function () {
    var compName = "AE_Bridge_Create_Comp_Test";
    var solidName = "AE Bridge Solid";

    function removeExistingTestItems() {
        var i;
        var item;

        for (i = app.project.numItems; i >= 1; i -= 1) {
            item = app.project.item(i);
            if (item instanceof CompItem && item.name === compName) {
                item.remove();
            }
        }
        for (i = app.project.numItems; i >= 1; i -= 1) {
            item = app.project.item(i);
            if (item instanceof FootageItem && item.name === solidName) {
                item.remove();
            }
        }
    }

    app.beginUndoGroup("AE Bridge Create Comp Test");

    try {
        removeExistingTestItems();
        var comp = app.project.items.addComp(
            compName,
            1920,
            1080,
            1,
            5,
            30
        );

        comp.layers.addSolid(
            [1, 0, 0],
            solidName,
            1920,
            1080,
            1,
            5
        );

        var textLayer = comp.layers.addText("AE Bridge OK");
        textLayer.property("Position").setValue([960, 540]);

        comp.openInViewer();
    } finally {
        app.endUndoGroup();
    }
})();
