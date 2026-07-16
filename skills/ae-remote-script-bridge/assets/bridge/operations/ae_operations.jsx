/*
 * Stable AE Bridge operations.
 *
 * Adapted from typed JSX operation patterns in JUNKDOGE-JOE/after-effects-mcp
 * and matchName/text/inspect patterns in a-y-ibrahim/after-effects-mcp.
 * Both upstream projects are MIT licensed. See THIRD_PARTY_NOTICES.md.
 */
(function () {
    var request = $.global.AE_BRIDGE_OPERATION_REQUEST;
    var results = [];
    var undoStarted = false;

    var PROPERTY_MATCH_NAMES = {
        anchorPoint: "ADBE Anchor Point",
        opacity: "ADBE Opacity",
        position: "ADBE Position",
        rotation: "ADBE Rotate Z",
        scale: "ADBE Scale"
    };

    function errorLine(error) {
        return error && error.line !== undefined ? error.line : null;
    }

    function setPayload(value) {
        $.global.AE_BRIDGE_PAYLOAD_JSON = JSON.stringify(value);
    }

    function layerId(layer) {
        try {
            return layer.id;
        } catch (error) {
            return null;
        }
    }

    function resolveComp(args) {
        var matches = [];
        var i;
        var item;

        if (args.compId !== undefined && args.compId !== null) {
            for (i = 1; i <= app.project.numItems; i++) {
                item = app.project.item(i);
                if (item instanceof CompItem && item.id === args.compId) {
                    matches.push(item);
                }
            }
        } else if (args.compName !== undefined && args.compName !== null) {
            for (i = 1; i <= app.project.numItems; i++) {
                item = app.project.item(i);
                if (item instanceof CompItem && item.name === args.compName) {
                    matches.push(item);
                }
            }
        } else if (app.project.activeItem instanceof CompItem) {
            matches.push(app.project.activeItem);
        }

        if (matches.length === 0) {
            throw new Error("Composition not found. Provide compId/compName or open an active comp.");
        }
        if (matches.length > 1) {
            throw new Error("Composition target is ambiguous: " + matches.length + " exact matches.");
        }
        return matches[0];
    }

    function resolveItem(args, requireFootage) {
        var matches = [];
        var i;
        var item;
        for (i = 1; i <= app.project.numItems; i++) {
            item = app.project.item(i);
            if (
                (args.itemId !== undefined && item.id === args.itemId) ||
                (args.itemName !== undefined && item.name === args.itemName)
            ) {
                matches.push(item);
            }
        }
        if (matches.length === 0) {
            throw new Error("Project item not found.");
        }
        if (matches.length > 1) {
            throw new Error(
                "Project item target is ambiguous: " + matches.length +
                " exact matches. Use itemId."
            );
        }
        if (requireFootage && !(matches[0] instanceof FootageItem)) {
            throw new Error("Project item '" + matches[0].name + "' is not footage.");
        }
        return matches[0];
    }

    function resolveLayer(comp, args) {
        var matches = [];
        var i;
        var layer;

        if (args.layerId !== undefined && args.layerId !== null) {
            for (i = 1; i <= comp.numLayers; i++) {
                layer = comp.layer(i);
                if (layerId(layer) === args.layerId) {
                    matches.push(layer);
                }
            }
        } else if (args.layerIndex !== undefined && args.layerIndex !== null) {
            if (args.layerIndex >= 1 && args.layerIndex <= comp.numLayers) {
                matches.push(comp.layer(args.layerIndex));
            }
        } else if (args.layerName !== undefined && args.layerName !== null) {
            for (i = 1; i <= comp.numLayers; i++) {
                layer = comp.layer(i);
                if (layer.name === args.layerName) {
                    matches.push(layer);
                }
            }
        }

        if (matches.length === 0) {
            throw new Error("Layer not found in composition '" + comp.name + "'.");
        }
        if (matches.length > 1) {
            throw new Error(
                "Layer target is ambiguous in composition '" + comp.name +
                "': " + matches.length + " exact matches. Use layerId or layerIndex."
            );
        }
        return matches[0];
    }

    function resolveEffect(layer, args) {
        var effects = layer.property("ADBE Effect Parade");
        var matches = [];
        var i;
        var effect;
        if (!effects) {
            throw new Error("Effects group not found on layer '" + layer.name + "'.");
        }
        if (args.effectIndex !== undefined && args.effectIndex !== null) {
            if (args.effectIndex >= 1 && args.effectIndex <= effects.numProperties) {
                matches.push(effects.property(args.effectIndex));
            }
        } else {
            for (i = 1; i <= effects.numProperties; i++) {
                effect = effects.property(i);
                if (
                    (args.effectName !== undefined && effect.name === args.effectName) ||
                    (
                        args.effectMatchName !== undefined &&
                        effect.matchName === args.effectMatchName
                    )
                ) {
                    matches.push(effect);
                }
            }
        }
        if (matches.length === 0) {
            throw new Error("Effect not found on layer '" + layer.name + "'.");
        }
        if (matches.length > 1) {
            throw new Error(
                "Effect target is ambiguous on layer '" + layer.name +
                "': " + matches.length + " exact matches. Use effectIndex."
            );
        }
        return matches[0];
    }

    function resolveEffectProperty(effect, args) {
        var matches = [];
        var i;
        var property;
        if (args.propertyIndex !== undefined && args.propertyIndex !== null) {
            if (args.propertyIndex >= 1 && args.propertyIndex <= effect.numProperties) {
                matches.push(effect.property(args.propertyIndex));
            }
        } else {
            for (i = 1; i <= effect.numProperties; i++) {
                property = effect.property(i);
                if (property.matchName === args.propertyMatchName) {
                    matches.push(property);
                }
            }
        }
        if (matches.length === 0) {
            throw new Error("Effect property not found on effect '" + effect.name + "'.");
        }
        if (matches.length > 1) {
            throw new Error(
                "Effect property target is ambiguous on effect '" + effect.name + "'."
            );
        }
        return matches[0];
    }

    function transformProperty(layer, alias) {
        var transform = layer.property("ADBE Transform Group");
        var matchName = PROPERTY_MATCH_NAMES[alias];
        var property = transform && matchName ? transform.property(matchName) : null;
        if (!property) {
            throw new Error("Transform property not found: " + alias);
        }
        return property;
    }

    function sourceTextProperty(layer) {
        var textGroup;
        var property;
        if (!(layer instanceof TextLayer)) {
            throw new Error("Layer '" + layer.name + "' is not a text layer.");
        }
        textGroup = layer.property("ADBE Text Properties");
        property = textGroup && textGroup.property("ADBE Text Document");
        if (!property) {
            throw new Error("Source Text property not found on layer '" + layer.name + "'.");
        }
        return property;
    }

    function applyTextStyle(textDocument, args) {
        if (args.font !== undefined && args.font !== null) {
            textDocument.font = args.font;
        }
        if (args.fontSize !== undefined && args.fontSize !== null) {
            textDocument.fontSize = args.fontSize;
        }
        if (args.fillColor !== undefined && args.fillColor !== null) {
            textDocument.applyFill = true;
            textDocument.fillColor = args.fillColor;
        }
        if (args.alignment === "left") {
            textDocument.justification = ParagraphJustification.LEFT_JUSTIFY;
        } else if (args.alignment === "center") {
            textDocument.justification = ParagraphJustification.CENTER_JUSTIFY;
        } else if (args.alignment === "right") {
            textDocument.justification = ParagraphJustification.RIGHT_JUSTIFY;
        }
    }

    function safeValue(value) {
        var output;
        var i;
        if (value === null || value === undefined) {
            return null;
        }
        if (value instanceof Array) {
            output = [];
            for (i = 0; i < value.length; i++) {
                output.push(safeValue(value[i]));
            }
            return output;
        }
        if (
            typeof value === "number" ||
            typeof value === "string" ||
            typeof value === "boolean"
        ) {
            return value;
        }
        return "[object]";
    }

    function layerType(layer) {
        if (layer instanceof TextLayer) {
            return "text";
        }
        if (layer instanceof ShapeLayer) {
            return "shape";
        }
        if (layer instanceof CameraLayer) {
            return "camera";
        }
        if (layer instanceof LightLayer) {
            return "light";
        }
        if (layer.nullLayer) {
            return "null";
        }
        if (layer.adjustmentLayer) {
            return "adjustment";
        }
        return "av";
    }

    function interpolationName(value) {
        if (value === KeyframeInterpolationType.LINEAR) {
            return "LINEAR";
        }
        if (value === KeyframeInterpolationType.BEZIER) {
            return "BEZIER";
        }
        if (value === KeyframeInterpolationType.HOLD) {
            return "HOLD";
        }
        return String(value);
    }

    function layerSummary(layer) {
        var output = {
            id: layerId(layer),
            index: layer.index,
            name: layer.name,
            type: layerType(layer),
            enabled: layer.enabled,
            locked: layer.locked,
            inPoint: layer.inPoint,
            outPoint: layer.outPoint,
            startTime: layer.startTime,
            threeDLayer: !!layer.threeDLayer,
            parent: layer.parent ? layer.parent.name : null
        };
        if (layer instanceof AVLayer && layer.source) {
            output.source = {id: layer.source.id, name: layer.source.name};
        }
        return output;
    }

    function compSummary(comp) {
        return {
            id: comp.id,
            name: comp.name,
            width: comp.width,
            height: comp.height,
            pixelAspect: comp.pixelAspect,
            duration: comp.duration,
            frameRate: comp.frameRate,
            bgColor: safeValue(comp.bgColor),
            numLayers: comp.numLayers,
            time: comp.time,
            workAreaStart: comp.workAreaStart,
            workAreaDuration: comp.workAreaDuration
        };
    }

    function footageSummary(item) {
        var output = {
            id: item.id,
            name: item.name,
            width: item.width,
            height: item.height,
            duration: item.duration,
            frameRate: item.frameRate,
            footageMissing: !!item.footageMissing,
            fileExists: false,
            path: null
        };
        try {
            output.path = item.file ? item.file.fsName : null;
            output.fileExists = item.file ? item.file.exists : false;
        } catch (fileError) {
            output.path = null;
            output.fileExists = false;
        }
        output.missing = output.footageMissing || !output.fileExists;
        return output;
    }

    function effectPropertySummary(property) {
        var output = {
            index: property.propertyIndex,
            name: property.name,
            matchName: property.matchName,
            value: null
        };
        try {
            output.value = safeValue(property.value);
        } catch (valueError) {
            output.value = null;
        }
        return output;
    }

    function keyframeSummary(property, includeKeyframes, maxKeyframes) {
        var output = {
            matchName: property.matchName,
            value: safeValue(property.value),
            numKeys: property.numKeys
        };
        var keys;
        var count;
        var i;
        var key;

        if (includeKeyframes && maxKeyframes > 0 && property.numKeys > 0) {
            keys = [];
            count = Math.min(property.numKeys, maxKeyframes);
            for (i = 1; i <= count; i++) {
                key = {
                    index: i,
                    time: property.keyTime(i),
                    value: safeValue(property.keyValue(i))
                };
                try {
                    key.inInterpolation = interpolationName(
                        property.keyInInterpolationType(i)
                    );
                    key.outInterpolation = interpolationName(
                        property.keyOutInterpolationType(i)
                    );
                } catch (error) {
                }
                keys.push(key);
            }
            output.keyframes = keys;
            output.keyframesTruncated = property.numKeys > count;
        }
        return output;
    }

    function createComp(args) {
        var comp = app.project.items.addComp(
            args.name,
            args.width,
            args.height,
            args.pixelAspect === undefined ? 1 : args.pixelAspect,
            args.duration,
            args.frameRate
        );
        if (args.bgColor !== undefined && args.bgColor !== null) {
            comp.bgColor = args.bgColor;
        }
        return {operation: "create_comp", comp: compSummary(comp)};
    }

    function setComp(args) {
        var comp = resolveComp(args);
        var changed = [];
        if (args.name !== undefined && args.name !== null) {
            comp.name = args.name;
            changed.push("name");
        }
        if (args.width !== undefined && args.width !== null) {
            comp.width = args.width;
            changed.push("width");
        }
        if (args.height !== undefined && args.height !== null) {
            comp.height = args.height;
            changed.push("height");
        }
        if (args.pixelAspect !== undefined && args.pixelAspect !== null) {
            comp.pixelAspect = args.pixelAspect;
            changed.push("pixelAspect");
        }
        if (args.duration !== undefined && args.duration !== null) {
            comp.duration = args.duration;
            changed.push("duration");
        }
        if (args.frameRate !== undefined && args.frameRate !== null) {
            comp.frameDuration = 1 / args.frameRate;
            changed.push("frameRate");
        }
        if (args.bgColor !== undefined && args.bgColor !== null) {
            comp.bgColor = args.bgColor;
            changed.push("bgColor");
        }
        return {
            operation: "set_comp",
            changed: changed,
            comp: compSummary(comp)
        };
    }

    function createSolid(args) {
        var comp = resolveComp(args);
        var layer = comp.layers.addSolid(
            args.color,
            args.name,
            args.width === undefined ? comp.width : args.width,
            args.height === undefined ? comp.height : args.height,
            args.pixelAspect === undefined ? comp.pixelAspect : args.pixelAspect,
            args.duration === undefined ? comp.duration : args.duration
        );
        if (args.position !== undefined && args.position !== null) {
            transformProperty(layer, "position").setValue(args.position);
        }
        return {
            operation: "create_solid",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer)
        };
    }

    function importFootage(args) {
        var file = new File(args.path);
        var options;
        var item;
        if (!file.exists) {
            throw new Error("Footage file does not exist: " + file.fsName);
        }
        options = new ImportOptions(file);
        item = app.project.importFile(options);
        if (!(item instanceof FootageItem)) {
            try {
                item.remove();
            } catch (removeError) {
            }
            throw new Error("Imported item is not footage: " + file.fsName);
        }
        if (args.name !== undefined && args.name !== null) {
            item.name = args.name;
        }
        return {operation: "import_footage", footage: footageSummary(item)};
    }

    function addSourceLayer(args) {
        var comp = resolveComp(args);
        var item = resolveItem(args, false);
        var layer;
        if (!(item instanceof CompItem) && !(item instanceof FootageItem)) {
            throw new Error("Project item '" + item.name + "' cannot be added as an AV layer.");
        }
        layer = comp.layers.add(item);
        if (args.name !== undefined && args.name !== null) {
            layer.name = args.name;
        }
        if (args.startTime !== undefined && args.startTime !== null) {
            layer.startTime = args.startTime;
        }
        if (args.duration !== undefined && args.duration !== null) {
            layer.outPoint = layer.startTime + args.duration;
        }
        if (args.position !== undefined && args.position !== null) {
            transformProperty(layer, "position").setValue(args.position);
        }
        return {
            operation: "add_source_layer",
            comp: {id: comp.id, name: comp.name},
            item: {id: item.id, name: item.name},
            layer: layerSummary(layer)
        };
    }

    function inspectFootage(args) {
        return {
            operation: "inspect_footage",
            footage: footageSummary(resolveItem(args, true))
        };
    }

    function relinkFootage(args) {
        var item = resolveItem(args, true);
        var previous = footageSummary(item);
        var file = new File(args.path);
        if (!file.exists) {
            throw new Error("Replacement footage file does not exist: " + file.fsName);
        }
        item.replace(file);
        return {
            operation: "relink_footage",
            previous: previous,
            footage: footageSummary(item)
        };
    }

    function addEffect(args) {
        var comp = resolveComp(args);
        var layer = resolveLayer(comp, args);
        var effects = layer.property("ADBE Effect Parade");
        var effect;
        if (!effects || !effects.canAddProperty(args.effectMatchName)) {
            throw new Error("Effect cannot be added: " + args.effectMatchName);
        }
        effect = effects.addProperty(args.effectMatchName);
        if (!effect) {
            throw new Error("Effect add returned no property: " + args.effectMatchName);
        }
        if (args.name !== undefined && args.name !== null) {
            effect.name = args.name;
        }
        return {
            operation: "add_effect",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer),
            effect: {
                index: effect.propertyIndex,
                name: effect.name,
                matchName: effect.matchName,
                enabled: effect.enabled
            }
        };
    }

    function setEffectProperty(args) {
        var comp = resolveComp(args);
        var layer = resolveLayer(comp, args);
        var effect = resolveEffect(layer, args);
        var property = resolveEffectProperty(effect, args);
        try {
            property.setValue(args.value);
        } catch (error) {
            throw new Error(
                "Failed to set effect property '" + property.matchName +
                "' on '" + effect.name + "': " + error.toString()
            );
        }
        return {
            operation: "set_effect_property",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer),
            effect: {
                index: effect.propertyIndex,
                name: effect.name,
                matchName: effect.matchName
            },
            property: effectPropertySummary(property)
        };
    }

    function removeEffect(args) {
        var comp = resolveComp(args);
        var layer = resolveLayer(comp, args);
        var effect = resolveEffect(layer, args);
        var removed = {
            index: effect.propertyIndex,
            name: effect.name,
            matchName: effect.matchName
        };
        effect.remove();
        return {
            operation: "remove_effect",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer),
            effect: removed
        };
    }

    function renderComp(args) {
        var comp = resolveComp(args);
        var outputFile = new File(args.outputPath);
        var queue = app.project.renderQueue;
        var existing = [];
        var rqItem = null;
        var i;
        var record;
        var outputModule;
        var output = null;
        if (!outputFile.parent.exists) {
            throw new Error("Output folder does not exist: " + outputFile.parent.fsName);
        }
        for (i = 1; i <= queue.numItems; i++) {
            record = {item: queue.item(i), render: null};
            try {
                record.render = record.item.render;
                record.item.render = false;
            } catch (snapshotError) {
                record.render = null;
            }
            existing.push(record);
        }
        try {
            rqItem = queue.items.add(comp);
            if (args.renderSettingsTemplate !== undefined) {
                rqItem.applyTemplate(args.renderSettingsTemplate);
            }
            outputModule = rqItem.outputModule(1);
            if (args.outputModuleTemplate !== undefined) {
                outputModule.applyTemplate(args.outputModuleTemplate);
            }
            outputModule.file = outputFile;
            rqItem.render = true;
            queue.render();
            output = {
                path: outputFile.fsName,
                exists: outputFile.exists,
                length: outputFile.exists ? outputFile.length : 0,
                status: String(rqItem.status)
            };
        } finally {
            if (rqItem !== null && args.cleanupQueueItem !== false) {
                try {
                    rqItem.remove();
                } catch (removeQueueError) {
                }
            }
            for (i = 0; i < existing.length; i++) {
                if (existing[i].render !== null) {
                    try {
                        existing[i].item.render = existing[i].render;
                    } catch (restoreError) {
                    }
                }
            }
        }
        if (!output || !output.exists || output.length <= 0) {
            throw new Error("Render output was not created: " + outputFile.fsName);
        }
        return {
            operation: "render_comp",
            comp: {id: comp.id, name: comp.name},
            output: output,
            queueItemCleaned: args.cleanupQueueItem !== false
        };
    }

    function createText(args) {
        var comp = resolveComp(args);
        var layer = comp.layers.addText(args.text);
        var sourceText = sourceTextProperty(layer);
        var textDocument = sourceText.value;

        textDocument.text = args.text;
        applyTextStyle(textDocument, args);
        sourceText.setValue(textDocument);

        if (args.name !== undefined && args.name !== null) {
            layer.name = args.name;
        }
        if (args.position !== undefined && args.position !== null) {
            transformProperty(layer, "position").setValue(args.position);
        }
        if (args.startTime !== undefined && args.startTime !== null) {
            layer.startTime = args.startTime;
        }
        if (args.duration !== undefined && args.duration !== null) {
            layer.outPoint = layer.startTime + args.duration;
        }

        return {
            operation: "create_text",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer),
            text: textDocument.text
        };
    }

    function setText(args) {
        var comp = resolveComp(args);
        var layer = resolveLayer(comp, args);
        var sourceText = sourceTextProperty(layer);
        var textDocument = sourceText.value;

        textDocument.text = args.text;
        applyTextStyle(textDocument, args);
        sourceText.setValue(textDocument);

        return {
            operation: "set_text",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer),
            text: textDocument.text
        };
    }

    function setTransform(args) {
        var comp = resolveComp(args);
        var layer = resolveLayer(comp, args);
        var changed = [];
        var alias;
        var property;

        for (alias in PROPERTY_MATCH_NAMES) {
            if (args[alias] !== undefined && args[alias] !== null) {
                property = transformProperty(layer, alias);
                property.setValue(args[alias]);
                changed.push(alias);
            }
        }

        return {
            operation: "set_transform",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer),
            changed: changed
        };
    }

    function setKeyframes(args) {
        var comp = resolveComp(args);
        var layer = resolveLayer(comp, args);
        var property = transformProperty(layer, args.property);
        var i;
        var keyframe;

        if (!property.canVaryOverTime) {
            throw new Error("Property cannot be keyframed: " + args.property);
        }
        if (args.clearExisting === true) {
            for (i = property.numKeys; i >= 1; i--) {
                property.removeKey(i);
            }
        }
        for (i = 0; i < args.keyframes.length; i++) {
            keyframe = args.keyframes[i];
            try {
                property.setValueAtTime(keyframe.time, keyframe.value);
            } catch (error) {
                throw new Error(
                    "Failed to set keyframes[" + i + "] on " + args.property +
                    ": " + error.toString()
                );
            }
        }

        return {
            operation: "set_keyframes",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer),
            property: args.property,
            keyframes: keyframeSummary(property, true, property.numKeys)
        };
    }

    function inspectComp(args) {
        var comp = resolveComp(args);
        var output = {
            operation: "inspect_comp",
            comp: compSummary(comp)
        };
        var layers;
        var i;

        if (args.includeLayers !== false) {
            layers = [];
            for (i = 1; i <= comp.numLayers; i++) {
                layers.push(layerSummary(comp.layer(i)));
            }
            output.layers = layers;
        }
        return output;
    }

    function openComp(args) {
        var comp = resolveComp(args);
        comp.openInViewer();
        return {operation: "open_comp", comp: compSummary(comp)};
    }

    function inspectLayer(args) {
        var comp = resolveComp(args);
        var layer = resolveLayer(comp, args);
        var includeKeyframes = args.includeKeyframes !== false;
        var maxKeyframes = args.maxKeyframes === undefined ? 50 : args.maxKeyframes;
        var includeEffectProperties = args.includeEffectProperties === true;
        var maxEffectProperties = args.maxEffectProperties === undefined ? 50 : args.maxEffectProperties;
        var output = {
            operation: "inspect_layer",
            comp: {id: comp.id, name: comp.name},
            layer: layerSummary(layer),
            transform: {},
            effects: [],
            masks: []
        };
        var alias;
        var property;
        var sourceText;
        var textDocument;
        var effects;
        var effect;
        var masks;
        var mask;
        var i;
        var j;
        var effectOutput;
        var propertyCount;

        for (alias in PROPERTY_MATCH_NAMES) {
            try {
                property = transformProperty(layer, alias);
                output.transform[alias] = keyframeSummary(
                    property,
                    includeKeyframes,
                    maxKeyframes
                );
            } catch (error) {
            }
        }

        if (layer instanceof TextLayer) {
            sourceText = sourceTextProperty(layer);
            textDocument = sourceText.value;
            output.text = {
                text: textDocument.text,
                font: textDocument.font,
                fontSize: textDocument.fontSize,
                fillColor: textDocument.applyFill ? safeValue(textDocument.fillColor) : null,
                sourceTextKeys: sourceText.numKeys
            };
        }

        effects = layer.property("ADBE Effect Parade");
        if (effects) {
            for (i = 1; i <= effects.numProperties; i++) {
                effect = effects.property(i);
                effectOutput = {
                    index: i,
                    name: effect.name,
                    matchName: effect.matchName,
                    enabled: effect.enabled
                };
                if (includeEffectProperties && maxEffectProperties > 0) {
                    effectOutput.properties = [];
                    propertyCount = Math.min(effect.numProperties, maxEffectProperties);
                    for (j = 1; j <= propertyCount; j++) {
                        effectOutput.properties.push(
                            effectPropertySummary(effect.property(j))
                        );
                    }
                    effectOutput.propertiesTruncated = effect.numProperties > propertyCount;
                }
                output.effects.push(effectOutput);
            }
        }

        masks = layer.property("ADBE Mask Parade");
        if (masks) {
            for (i = 1; i <= masks.numProperties; i++) {
                mask = masks.property(i);
                output.masks.push({index: i, name: mask.name});
            }
        }

        return output;
    }

    function runOperation(item) {
        switch (item.operation) {
            case "create_comp":
                return createComp(item.args);
            case "set_comp":
                return setComp(item.args);
            case "create_solid":
                return createSolid(item.args);
            case "import_footage":
                return importFootage(item.args);
            case "add_source_layer":
                return addSourceLayer(item.args);
            case "inspect_footage":
                return inspectFootage(item.args);
            case "relink_footage":
                return relinkFootage(item.args);
            case "add_effect":
                return addEffect(item.args);
            case "set_effect_property":
                return setEffectProperty(item.args);
            case "remove_effect":
                return removeEffect(item.args);
            case "render_comp":
                return renderComp(item.args);
            case "create_text":
                return createText(item.args);
            case "set_text":
                return setText(item.args);
            case "set_transform":
                return setTransform(item.args);
            case "set_keyframes":
                return setKeyframes(item.args);
            case "inspect_comp":
                return inspectComp(item.args);
            case "open_comp":
                return openComp(item.args);
            case "inspect_layer":
                return inspectLayer(item.args);
            default:
                throw new Error("Unsupported operation: " + item.operation);
        }
    }

    function isMutation(operation) {
        return (
            operation !== "inspect_comp" &&
            operation !== "inspect_footage" &&
            operation !== "inspect_layer" &&
            operation !== "open_comp" &&
            operation !== "render_comp"
        );
    }

    function normalizeOperations(value) {
        if (value.operations instanceof Array) {
            return value.operations;
        }
        return [value];
    }

    try {
        if (!request) {
            throw new Error("AE Bridge operation request is missing.");
        }

        var operations = normalizeOperations(request);
        var mutating = false;
        var index;
        for (index = 0; index < operations.length; index++) {
            if (isMutation(operations[index].operation)) {
                mutating = true;
                break;
            }
        }

        if (mutating) {
            app.beginUndoGroup("AE Bridge Operations");
            undoStarted = true;
        }

        for (index = 0; index < operations.length; index++) {
            results.push(runOperation(operations[index]));
        }

        setPayload({
            ok: true,
            operationCount: operations.length,
            results: results
        });
    } catch (error) {
        setPayload({
            ok: false,
            completedCount: results.length,
            results: results,
            error: error.toString(),
            line: errorLine(error)
        });
        throw error;
    } finally {
        if (undoStarted) {
            app.endUndoGroup();
        }
    }
})();
