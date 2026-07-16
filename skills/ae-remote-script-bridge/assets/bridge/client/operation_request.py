import json


SUPPORTED_OPERATIONS = {
    "create_text",
    "inspect_comp",
    "inspect_layer",
    "set_keyframes",
    "set_text",
    "set_transform",
}
COMP_SELECTOR_KEYS = {"compId", "compName"}
LAYER_SELECTOR_KEYS = {"layerId", "layerIndex", "layerName"}
TRANSFORM_KEYS = {"anchorPoint", "opacity", "position", "rotation", "scale"}
TEXT_STYLE_KEYS = {"alignment", "fillColor", "font", "fontSize"}


class OperationRequestError(ValueError):
    pass


def _error(path, message):
    raise OperationRequestError(path + ": " + message)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_number(value, path):
    if not _is_number(value):
        _error(path, "expected a number")


def _reject_unknown(args, allowed, path):
    unknown = sorted(set(args).difference(allowed))
    if unknown:
        _error(path, "unsupported field(s): " + ", ".join(unknown))


def _validate_vector(value, path, lengths, minimum=None, maximum=None):
    if not isinstance(value, list) or len(value) not in lengths:
        _error(path, "expected an array with length " + " or ".join(map(str, lengths)))
    for index, item in enumerate(value):
        _require_number(item, path + "[" + str(index) + "]")
        if minimum is not None and item < minimum:
            _error(path + "[" + str(index) + "]", "must be >= " + str(minimum))
        if maximum is not None and item > maximum:
            _error(path + "[" + str(index) + "]", "must be <= " + str(maximum))


def _validate_comp_selector(args, path):
    present = [key for key in COMP_SELECTOR_KEYS if key in args]
    if len(present) > 1:
        _error(path, "provide at most one of compId or compName")
    if "compId" in args and (
        not isinstance(args["compId"], int) or isinstance(args["compId"], bool)
    ):
        _error(path + ".compId", "expected an integer")
    if "compName" in args and (
        not isinstance(args["compName"], str) or not args["compName"]
    ):
        _error(path + ".compName", "expected a non-empty string")


def _validate_layer_selector(args, path):
    present = [key for key in LAYER_SELECTOR_KEYS if key in args]
    if len(present) != 1:
        _error(path, "provide exactly one of layerId, layerIndex, or layerName")
    key = present[0]
    value = args[key]
    if key in {"layerId", "layerIndex"}:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            _error(path + "." + key, "expected a positive integer")
    elif not isinstance(value, str) or not value:
        _error(path + ".layerName", "expected a non-empty string")


def _validate_text_style(args, path):
    if "fontSize" in args:
        _require_number(args["fontSize"], path + ".fontSize")
        if args["fontSize"] <= 0:
            _error(path + ".fontSize", "must be > 0")
    if "fillColor" in args:
        _validate_vector(args["fillColor"], path + ".fillColor", (3,), 0, 1)
    if "alignment" in args and args["alignment"] not in {"left", "center", "right"}:
        _error(path + ".alignment", "expected left, center, or right")
    if "font" in args and not isinstance(args["font"], str):
        _error(path + ".font", "expected a string")


def _validate_create_text(args, path):
    _reject_unknown(
        args,
        COMP_SELECTOR_KEYS
        | TEXT_STYLE_KEYS
        | {"duration", "name", "position", "startTime", "text"},
        path,
    )
    _validate_comp_selector(args, path)
    if "text" not in args or not isinstance(args["text"], str):
        _error(path + ".text", "expected a string")
    if "name" in args and (not isinstance(args["name"], str) or not args["name"]):
        _error(path + ".name", "expected a non-empty string")
    if "position" in args:
        _validate_vector(args["position"], path + ".position", (2, 3))
    if "startTime" in args:
        _require_number(args["startTime"], path + ".startTime")
    if "duration" in args:
        _require_number(args["duration"], path + ".duration")
        if args["duration"] <= 0:
            _error(path + ".duration", "must be > 0")
    _validate_text_style(args, path)


def _validate_set_text(args, path):
    _reject_unknown(
        args,
        COMP_SELECTOR_KEYS | LAYER_SELECTOR_KEYS | TEXT_STYLE_KEYS | {"text"},
        path,
    )
    _validate_comp_selector(args, path)
    _validate_layer_selector(args, path)
    if "text" not in args or not isinstance(args["text"], str):
        _error(path + ".text", "expected a string")
    _validate_text_style(args, path)


def _validate_set_transform(args, path):
    _reject_unknown(
        args,
        COMP_SELECTOR_KEYS | LAYER_SELECTOR_KEYS | TRANSFORM_KEYS,
        path,
    )
    _validate_comp_selector(args, path)
    _validate_layer_selector(args, path)
    changed = TRANSFORM_KEYS.intersection(args)
    if not changed:
        _error(path, "provide at least one transform property")
    for key in {"position", "anchorPoint", "scale"}.intersection(changed):
        minimum = 0 if key == "scale" else None
        _validate_vector(args[key], path + "." + key, (2, 3), minimum)
    if "rotation" in args:
        _require_number(args["rotation"], path + ".rotation")
    if "opacity" in args:
        _require_number(args["opacity"], path + ".opacity")
        if args["opacity"] < 0 or args["opacity"] > 100:
            _error(path + ".opacity", "must be between 0 and 100")


def _validate_set_keyframes(args, path):
    _reject_unknown(
        args,
        COMP_SELECTOR_KEYS
        | LAYER_SELECTOR_KEYS
        | {"clearExisting", "keyframes", "property"},
        path,
    )
    _validate_comp_selector(args, path)
    _validate_layer_selector(args, path)
    if args.get("property") not in TRANSFORM_KEYS:
        _error(path + ".property", "expected a supported transform property")
    keyframes = args.get("keyframes")
    if not isinstance(keyframes, list) or not keyframes:
        _error(path + ".keyframes", "expected a non-empty array")
    for index, keyframe in enumerate(keyframes):
        key_path = path + ".keyframes[" + str(index) + "]"
        if not isinstance(keyframe, dict):
            _error(key_path, "expected an object")
        if set(keyframe) != {"time", "value"}:
            _error(key_path, "expected exactly time and value")
        _require_number(keyframe["time"], key_path + ".time")
        value = keyframe["value"]
        if args["property"] in {"position", "anchorPoint", "scale"}:
            _validate_vector(value, key_path + ".value", (2, 3))
        else:
            _require_number(value, key_path + ".value")
    if "clearExisting" in args and not isinstance(args["clearExisting"], bool):
        _error(path + ".clearExisting", "expected a boolean")


def _validate_inspect_comp(args, path):
    _reject_unknown(args, COMP_SELECTOR_KEYS | {"includeLayers"}, path)
    _validate_comp_selector(args, path)
    if "includeLayers" in args and not isinstance(args["includeLayers"], bool):
        _error(path + ".includeLayers", "expected a boolean")


def _validate_inspect_layer(args, path):
    _reject_unknown(
        args,
        COMP_SELECTOR_KEYS
        | LAYER_SELECTOR_KEYS
        | {"includeKeyframes", "maxKeyframes"},
        path,
    )
    _validate_comp_selector(args, path)
    _validate_layer_selector(args, path)
    if "includeKeyframes" in args and not isinstance(args["includeKeyframes"], bool):
        _error(path + ".includeKeyframes", "expected a boolean")
    if "maxKeyframes" in args:
        value = args["maxKeyframes"]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 200:
            _error(path + ".maxKeyframes", "expected an integer from 0 to 200")


VALIDATORS = {
    "create_text": _validate_create_text,
    "inspect_comp": _validate_inspect_comp,
    "inspect_layer": _validate_inspect_layer,
    "set_keyframes": _validate_set_keyframes,
    "set_text": _validate_set_text,
    "set_transform": _validate_set_transform,
}


def validate_request(request):
    if not isinstance(request, dict):
        _error("request", "expected an object")
    if set(request) == {"operation", "args"}:
        operations = [request]
    elif set(request) == {"operations"}:
        operations = request["operations"]
        if not isinstance(operations, list) or not operations:
            _error("request.operations", "expected a non-empty array")
        if len(operations) > 50:
            _error("request.operations", "at most 50 operations are allowed")
    else:
        _error(
            "request",
            "expected operation+args for one call, or operations for a batch",
        )

    for index, item in enumerate(operations):
        path = "request.operations[" + str(index) + "]"
        if not isinstance(item, dict) or set(item) != {"operation", "args"}:
            _error(path, "expected exactly operation and args")
        operation = item["operation"]
        if operation not in SUPPORTED_OPERATIONS:
            _error(path + ".operation", "unsupported operation: " + str(operation))
        if not isinstance(item["args"], dict):
            _error(path + ".args", "expected an object")
        VALIDATORS[operation](item["args"], path + ".args")

    return request


def load_request(path):
    try:
        with path.open("r", encoding="utf-8-sig") as request_file:
            request = json.load(request_file)
    except json.JSONDecodeError as err:
        raise OperationRequestError("invalid JSON: " + str(err)) from err
    return validate_request(request)


def build_launcher_jsx(request):
    request_json = json.dumps(request, ensure_ascii=True, separators=(",", ":"))
    return """(function () {
    $.global.AE_BRIDGE_OPERATION_REQUEST = %s;
    var operationsFile = new File(
        $.global.AE_BRIDGE_ROOT + "/operations/ae_operations.jsx"
    );
    if (!operationsFile.exists) {
        throw new Error("AE Bridge operations file not found: " + operationsFile.fsName);
    }
    $.evalFile(operationsFile);
})();
""" % request_json
