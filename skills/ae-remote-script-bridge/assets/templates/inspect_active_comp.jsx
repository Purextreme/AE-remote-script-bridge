(function () {
    var logsDir = $.global.AE_BRIDGE_LOGS_DIR || Folder.temp.fsName;
    var outputFile = new File(logsDir + "/inspect_active_comp.json");

    function escapeJson(value) {
        var text = String(value);
        text = text.replace(/\\/g, "\\\\");
        text = text.replace(/"/g, '\\"');
        text = text.replace(/\r/g, "\\r");
        text = text.replace(/\n/g, "\\n");
        text = text.replace(/\t/g, "\\t");
        return text;
    }

    function quoted(value) {
        return '"' + escapeJson(value) + '"';
    }

    var item = app.project.activeItem;
    outputFile.encoding = "UTF-8";
    outputFile.open("w");
    outputFile.write("{");

    if (!(item instanceof CompItem)) {
        outputFile.write('"ok":false');
        outputFile.write(',"message":"Active item is not a composition."');
    } else {
        outputFile.write('"ok":true');
        outputFile.write(',"name":' + quoted(item.name));
        outputFile.write(',"width":' + item.width);
        outputFile.write(',"height":' + item.height);
        outputFile.write(',"duration":' + item.duration);
        outputFile.write(',"frameRate":' + item.frameRate);
        outputFile.write(',"numLayers":' + item.numLayers);
        outputFile.write(',"selectedLayerCount":' + item.selectedLayers.length);
    }

    outputFile.write("}");
    outputFile.close();
})();

