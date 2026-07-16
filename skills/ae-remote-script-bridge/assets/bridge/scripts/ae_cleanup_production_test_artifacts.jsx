(function () {
    var removed = [];
    var i;
    var item;
    var removedProbeSolid = false;
    app.beginUndoGroup("Clean AE Bridge Production Test Artifacts");
    try {
        for (i = app.project.numItems; i >= 1; i--) {
            item = app.project.item(i);
            if (
                item.name.indexOf("AE_BRIDGE_PROD_") === 0 ||
                item.name === "AE_BRIDGE_CAPABILITY_PROBE" ||
                item.name === "Probe Solid"
            ) {
                removed.push({id: item.id, name: item.name});
                if (item.name === "Probe Solid") {
                    removedProbeSolid = true;
                }
                item.remove();
            }
        }
        if (removedProbeSolid) {
            for (i = app.project.numItems; i >= 1; i--) {
                item = app.project.item(i);
                if (
                    item instanceof FolderItem &&
                    item.numItems === 0 &&
                    item.name === "Solids"
                ) {
                    removed.push({id: item.id, name: item.name});
                    item.remove();
                }
            }
        }
    } finally {
        app.endUndoGroup();
    }
    $.global.AE_BRIDGE_PAYLOAD_JSON = JSON.stringify({removed: removed});
})();
