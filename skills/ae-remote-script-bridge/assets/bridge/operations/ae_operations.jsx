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
        return {
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
            comp: {
                id: comp.id,
                name: comp.name,
                width: comp.width,
                height: comp.height,
                duration: comp.duration,
                frameRate: comp.frameRate,
                numLayers: comp.numLayers,
                time: comp.time,
                workAreaStart: comp.workAreaStart,
                workAreaDuration: comp.workAreaDuration
            }
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

    function inspectLayer(args) {
        var comp = resolveComp(args);
        var layer = resolveLayer(comp, args);
        var includeKeyframes = args.includeKeyframes !== false;
        var maxKeyframes = args.maxKeyframes === undefined ? 50 : args.maxKeyframes;
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
                output.effects.push({
                    index: i,
                    name: effect.name,
                    matchName: effect.matchName,
                    enabled: effect.enabled
                });
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
            case "inspect_layer":
                return inspectLayer(item.args);
            default:
                throw new Error("Unsupported operation: " + item.operation);
        }
    }

    function isMutation(operation) {
        return operation !== "inspect_comp" && operation !== "inspect_layer";
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
