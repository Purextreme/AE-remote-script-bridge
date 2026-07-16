(function () {
    var comp = null;
    var rqItem = null;
    var output = {
        version: app.version,
        buildName: app.buildName,
        buildNumber: app.buildNumber,
        isoLanguage: app.isoLanguage,
        effects: {},
        renderSettingsTemplates: [],
        outputModuleTemplates: []
    };

    function propertySummary(group) {
        var properties = [];
        var i;
        var property;
        for (i = 1; i <= group.numProperties; i++) {
            property = group.property(i);
            properties.push({
                index: i,
                name: property.name,
                matchName: property.matchName,
                propertyValueType: property.propertyValueType,
                canSetExpression: !!property.canSetExpression
            });
        }
        return properties;
    }

    app.beginUndoGroup("Probe AE Bridge Production Capabilities");
    try {
        comp = app.project.items.addComp(
            "AE_BRIDGE_CAPABILITY_PROBE",
            64,
            64,
            1,
            0.5,
            24
        );
        var probeLayer = comp.layers.addText("Probe");
        var effects = probeLayer.property("ADBE Effect Parade");
        var effectNames = ["ADBE Fill", "ADBE Tint"];
        var i;
        var effect;
        for (i = 0; i < effectNames.length; i++) {
            output.effects[effectNames[i]] = {available: false, properties: []};
            if (effects && effects.canAddProperty(effectNames[i])) {
                effect = effects.addProperty(effectNames[i]);
                output.effects[effectNames[i]] = {
                    available: true,
                    name: effect.name,
                    matchName: effect.matchName,
                    properties: propertySummary(effect)
                };
            }
        }

        rqItem = app.project.renderQueue.items.add(comp);
        output.renderSettingsTemplates = rqItem.templates;
        output.outputModuleTemplates = rqItem.outputModule(1).templates;
    } finally {
        if (rqItem !== null) {
            try {
                rqItem.remove();
            } catch (removeQueueError) {
            }
        }
        if (comp !== null) {
            try {
                comp.remove();
            } catch (removeCompError) {
            }
        }
        app.endUndoGroup();
    }

    $.global.AE_BRIDGE_PAYLOAD_JSON = JSON.stringify(output);
})();
