(function () {
    var queue = app.project.renderQueue;
    var items = [];
    var i;
    var item;
    var output;

    for (i = 1; i <= queue.numItems; i++) {
        item = queue.item(i);
        output = null;
        try {
            output = item.outputModule(1).file;
        } catch (error) {
        }
        items.push({
            index: i,
            status: String(item.status),
            render: item.render,
            compName: item.comp ? item.comp.name : null,
            outputPath: output ? output.fsName : null
        });
    }

    $.global.AE_BRIDGE_PAYLOAD_JSON = JSON.stringify({
        ok: true,
        numItems: queue.numItems,
        items: items
    });
})();
