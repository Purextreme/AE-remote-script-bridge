import argparse
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path


CLIENT_DIR = Path(__file__).resolve().parent
BRIDGE_ROOT = CLIENT_DIR.parent
RUN_OPERATION_PATH = CLIENT_DIR / "run_operation.py"
SEND_TO_AE_PATH = CLIENT_DIR / "send_to_ae.py"


class ProductionTestFailure(RuntimeError):
    pass


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the lightweight AE Bridge production acceptance suite."
    )
    parser.add_argument("--fixture-a", required=True, type=Path)
    parser.add_argument("--fixture-b", required=True, type=Path)
    parser.add_argument(
        "--render",
        action="store_true",
        help="Also run a short isolated H.264 Render Queue output test.",
    )
    return parser.parse_args(argv)


def require_file(path, label):
    path = path.resolve()
    if not path.is_file():
        raise ProductionTestFailure(label + " not found: " + str(path))
    return path


def read_result_from_output(output):
    for line in output.splitlines():
        if line.startswith("Run Dir: "):
            run_dir = Path(line[len("Run Dir: ") :].strip())
            result_path = run_dir / "result.json"
            if result_path.is_file():
                return run_dir, json.loads(result_path.read_text(encoding="utf-8-sig"))
            return run_dir, None
    return None, None


def run_command(command, expected_success, label):
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=BRIDGE_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    duration_ms = round((time.perf_counter() - started) * 1000)
    output = completed.stdout + completed.stderr
    bridge_run_dir, result = read_result_from_output(output)
    succeeded = completed.returncode == 0 and bool(result and result.get("ok"))
    if succeeded != expected_success:
        raise ProductionTestFailure(
            label
            + " expected "
            + ("success" if expected_success else "failure")
            + ", return code "
            + str(completed.returncode)
            + "\n"
            + output
        )
    return {
        "label": label,
        "status": "passed",
        "expectedSuccess": expected_success,
        "durationMs": duration_ms,
        "returnCode": completed.returncode,
        "bridgeRunDir": str(bridge_run_dir) if bridge_run_dir else None,
        "result": result,
        "output": output,
    }


def run_request(run_dir, operation_id, label, request, expected_success=True, extra=None):
    request_path = run_dir / "requests" / (label + ".json")
    request_path.write_text(
        json.dumps(request, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    command = [
        sys.executable,
        str(RUN_OPERATION_PATH),
        str(request_path),
        "--no-protect",
        "--operation-id",
        operation_id,
    ]
    if extra:
        command.extend(extra)
    return run_command(command, expected_success, label)


def run_script(label, script_path, expected_success=True):
    return run_command(
        [
            sys.executable,
            str(SEND_TO_AE_PATH),
            "--no-protect",
            str(script_path),
        ],
        expected_success,
        label,
    )


def payload(record):
    result = record.get("result") or {}
    return result.get("payload") or {}


def assert_equal(actual, expected, message):
    if actual != expected:
        raise ProductionTestFailure(
            message + ": expected " + repr(expected) + ", got " + repr(actual)
        )


def assert_close(actual, expected, message, tolerance=0.001):
    if abs(actual - expected) > tolerance:
        raise ProductionTestFailure(
            message + ": expected " + repr(expected) + ", got " + repr(actual)
        )


def find_result(record, operation, occurrence=0):
    matches = [
        item
        for item in payload(record).get("results", [])
        if item.get("operation") == operation
    ]
    if occurrence >= len(matches):
        raise ProductionTestFailure(
            record["label"] + " missing result for operation " + operation
        )
    return matches[occurrence]


def preserve_artifact(source, run_dir, name):
    if not source.is_file() or source.stat().st_size <= 0:
        raise ProductionTestFailure("artifact was not created: " + str(source))
    artifact_dir = run_dir / "artifacts"
    artifact_dir.mkdir(exist_ok=True)
    destination = artifact_dir / name
    shutil.copy2(source, destination)
    return destination


def write_cleanup_script(path, prefix, baseline_folder_names=None):
    prefix_json = json.dumps(prefix, ensure_ascii=True)
    folder_names_json = json.dumps(
        [] if baseline_folder_names is None else baseline_folder_names,
        ensure_ascii=True,
    )
    remove_new_folders = "false" if baseline_folder_names is None else "true"
    path.write_text(
        """(function () {
    var prefix = %s;
    var baselineFolderNames = %s;
    var removeNewFolders = %s;
    var removed = [];
    var i;
    var item;
    app.beginUndoGroup("Clean AE Bridge Production Test");
    try {
        for (i = app.project.numItems; i >= 1; i--) {
            item = app.project.item(i);
            if (item.name.indexOf(prefix) === 0) {
                removed.push({id: item.id, name: item.name});
                item.remove();
            }
        }
        if (removeNewFolders) {
            for (i = app.project.numItems; i >= 1; i--) {
                item = app.project.item(i);
                if (
                    item instanceof FolderItem &&
                    item.numItems === 0 &&
                    baselineFolderNames.indexOf(item.name) < 0
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
"""
        % (prefix_json, folder_names_json, remove_new_folders),
        encoding="utf-8",
    )


def write_report(run_dir, report):
    (run_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# AE Bridge Production Test Report",
        "",
        "- Run ID: `" + report["runId"] + "`",
        "- Status: **" + report["status"] + "**",
        "- Cases: " + str(len(report["cases"])),
        "- Fixture A: `" + report["fixtures"]["a"] + "`",
        "- Fixture B: `" + report["fixtures"]["b"] + "`",
        "",
        "| Case | Expected | Duration | Bridge Run |",
        "|---|---|---:|---|",
    ]
    for case in report["cases"]:
        lines.append(
            "| "
            + case["label"]
            + " | "
            + ("success" if case["expectedSuccess"] else "failure")
            + " | "
            + str(case["durationMs"])
            + " ms | `"
            + str(case["bridgeRunDir"])
            + "` |"
        )
    (run_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv=None):
    args = parse_args(argv)
    fixture_a_source = require_file(args.fixture_a, "Fixture A")
    fixture_b_source = require_file(args.fixture_b, "Fixture B")
    run_id = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    prefix = "AE_BRIDGE_PROD_" + run_id + "_"
    operation_id = "production-test-" + run_id
    run_dir = BRIDGE_ROOT / "temp" / "production_tests" / run_id
    fixture_dir = run_dir / "fixtures"
    request_dir = run_dir / "requests"
    output_dir = run_dir / "output"
    fixture_dir.mkdir(parents=True)
    request_dir.mkdir()
    output_dir.mkdir()
    fixture_a = fixture_dir / "source_a.png"
    fixture_b = fixture_dir / "source_b.png"
    shutil.copy2(fixture_a_source, fixture_a)
    shutil.copy2(fixture_b_source, fixture_b)

    report = {
        "runId": run_id,
        "status": "running",
        "prefix": prefix,
        "fixtures": {"a": str(fixture_a_source), "b": str(fixture_b_source)},
        "cases": [],
        "artifacts": {},
    }
    baseline_items = None
    baseline_folder_names = None
    baseline_queue = None
    comp_build = prefix + "BUILD"
    comp_name = prefix + "MAIN"
    solid_name = prefix + "BG"
    text_name = prefix + "TITLE"
    footage_name = prefix + "FOOTAGE"
    footage_layer_name = prefix + "ICON"

    try:
        baseline_project = run_script(
            "baseline_project",
            BRIDGE_ROOT / "scripts" / "ae_inspect_project.jsx",
        )
        report["cases"].append(baseline_project)
        baseline_project_path = (
            Path(baseline_project["bridgeRunDir"]) / "project_structure.json"
        )
        baseline_state = json.loads(
            baseline_project_path.read_text(encoding="utf-8-sig")
        )
        baseline_items = baseline_state.get("items", [])
        baseline_folder_names = [
            item["name"] for item in baseline_items if item.get("kind") == "folder"
        ]
        baseline_render_queue = run_script(
            "baseline_render_queue",
            BRIDGE_ROOT / "scripts" / "ae_inspect_render_queue.jsx",
        )
        report["cases"].append(baseline_render_queue)
        baseline_queue = payload(baseline_render_queue)
        report["cases"].append(
            run_script(
                "preflight",
                BRIDGE_ROOT / "scripts" / "ae_probe_production_capabilities.jsx",
            )
        )
        positive_request = {
            "operations": [
                {
                    "operation": "create_comp",
                    "args": {
                        "name": comp_build,
                        "width": 320,
                        "height": 180,
                        "duration": 2,
                        "frameRate": 24,
                        "pixelAspect": 1,
                        "bgColor": [0.02, 0.03, 0.06],
                    },
                },
                {
                    "operation": "set_comp",
                    "args": {
                        "compName": comp_build,
                        "name": comp_name,
                        "width": 384,
                        "height": 216,
                        "bgColor": [0.03, 0.05, 0.1],
                    },
                },
                {
                    "operation": "create_solid",
                    "args": {
                        "compName": comp_name,
                        "name": solid_name,
                        "color": [0.08, 0.1, 0.18],
                    },
                },
                {
                    "operation": "add_effect",
                    "args": {
                        "compName": comp_name,
                        "layerName": solid_name,
                        "effectMatchName": "ADBE Fill",
                        "name": "Bridge Fill",
                    },
                },
                {
                    "operation": "set_effect_property",
                    "args": {
                        "compName": comp_name,
                        "layerName": solid_name,
                        "effectName": "Bridge Fill",
                        "propertyMatchName": "ADBE Fill-0002",
                        "value": [0.04, 0.12, 0.34],
                    },
                },
                {
                    "operation": "add_effect",
                    "args": {
                        "compName": comp_name,
                        "layerName": solid_name,
                        "effectMatchName": "ADBE Tint",
                        "name": "Temporary Effect",
                    },
                },
                {
                    "operation": "remove_effect",
                    "args": {
                        "compName": comp_name,
                        "layerName": solid_name,
                        "effectName": "Temporary Effect",
                    },
                },
                {
                    "operation": "create_text",
                    "args": {
                        "compName": comp_name,
                        "text": "AE BRIDGE",
                        "name": text_name,
                        "position": [192, 72],
                        "fontSize": 30,
                        "fillColor": [1, 0.9, 0.2],
                        "alignment": "center",
                    },
                },
                {
                    "operation": "set_text",
                    "args": {
                        "compName": comp_name,
                        "layerName": text_name,
                        "text": "AE BRIDGE PRODUCTION",
                        "fontSize": 22,
                        "fillColor": [1, 0.9, 0.2],
                        "alignment": "center",
                    },
                },
                {
                    "operation": "set_transform",
                    "args": {
                        "compName": comp_name,
                        "layerName": text_name,
                        "position": [192, 62],
                        "scale": [90, 90],
                        "opacity": 100,
                    },
                },
                {
                    "operation": "set_keyframes",
                    "args": {
                        "compName": comp_name,
                        "layerName": text_name,
                        "property": "position",
                        "clearExisting": True,
                        "keyframes": [
                            {"time": 0, "value": [100, 62]},
                            {"time": 1, "value": [192, 62]},
                            {"time": 2, "value": [284, 62]},
                        ],
                    },
                },
                {
                    "operation": "import_footage",
                    "args": {"path": str(fixture_a), "name": footage_name},
                },
                {
                    "operation": "add_source_layer",
                    "args": {
                        "compName": comp_name,
                        "itemName": footage_name,
                        "name": footage_layer_name,
                        "position": [192, 164],
                        "duration": 2,
                    },
                },
                {
                    "operation": "set_transform",
                    "args": {
                        "compName": comp_name,
                        "layerName": footage_layer_name,
                        "scale": [42, 42],
                    },
                },
                {
                    "operation": "add_effect",
                    "args": {
                        "compName": comp_name,
                        "layerName": footage_layer_name,
                        "effectMatchName": "ADBE Tint",
                        "name": "Bridge Tint",
                    },
                },
                {
                    "operation": "set_effect_property",
                    "args": {
                        "compName": comp_name,
                        "layerName": footage_layer_name,
                        "effectName": "Bridge Tint",
                        "propertyMatchName": "ADBE Tint-0003",
                        "value": 35,
                    },
                },
                {"operation": "inspect_comp", "args": {"compName": comp_name}},
                {
                    "operation": "inspect_layer",
                    "args": {
                        "compName": comp_name,
                        "layerName": text_name,
                        "includeKeyframes": True,
                    },
                },
                {
                    "operation": "inspect_layer",
                    "args": {
                        "compName": comp_name,
                        "layerName": solid_name,
                        "includeEffectProperties": True,
                    },
                },
                {
                    "operation": "inspect_layer",
                    "args": {
                        "compName": comp_name,
                        "layerName": footage_layer_name,
                        "includeEffectProperties": True,
                    },
                },
                {
                    "operation": "inspect_footage",
                    "args": {"itemName": footage_name},
                },
                {"operation": "open_comp", "args": {"compName": comp_name}},
            ]
        }
        positive = run_request(
            run_dir,
            operation_id,
            "positive_batch",
            positive_request,
            extra=["--capture-frame", "--capture-time", "1"],
        )
        report["cases"].append(positive)
        comp_result = find_result(positive, "inspect_comp")
        assert_equal(comp_result["comp"]["name"], comp_name, "composition name")
        assert_equal(comp_result["comp"]["width"], 384, "composition width")
        assert_equal(comp_result["comp"]["height"], 216, "composition height")
        assert_close(comp_result["comp"]["frameRate"], 24, "composition frame rate")
        text_result = find_result(positive, "inspect_layer", 0)
        assert_equal(text_result["text"]["text"], "AE BRIDGE PRODUCTION", "text value")
        assert_equal(text_result["transform"]["position"]["numKeys"], 3, "position keys")
        fill_result = find_result(positive, "inspect_layer", 1)
        assert_equal(fill_result["effects"][0]["matchName"], "ADBE Fill", "Fill effect")
        tint_result = find_result(positive, "inspect_layer", 2)
        assert_equal(tint_result["effects"][0]["matchName"], "ADBE Tint", "Tint effect")
        preview_path = Path(positive["bridgeRunDir"]) / "frame_preview.png"
        positive_artifact = preserve_artifact(
            preview_path,
            run_dir,
            "positive_frame.png",
        )
        report["artifacts"]["positiveFrame"] = str(positive_artifact)

        report["cases"].append(
            run_request(
                run_dir,
                operation_id,
                "missing_target",
                {
                    "operation": "inspect_comp",
                    "args": {"compName": prefix + "DOES_NOT_EXIST"},
                },
                expected_success=False,
            )
        )
        report["cases"].append(
            run_request(
                run_dir,
                operation_id,
                "bad_effect_property",
                {
                    "operation": "set_effect_property",
                    "args": {
                        "compName": comp_name,
                        "layerName": solid_name,
                        "effectName": "Bridge Fill",
                        "propertyMatchName": "ADBE Missing Property",
                        "value": 1,
                    },
                },
                expected_success=False,
            )
        )
        report["cases"].append(
            run_request(
                run_dir,
                operation_id,
                "missing_relink_path",
                {
                    "operation": "relink_footage",
                    "args": {
                        "itemName": footage_name,
                        "path": str(fixture_dir / "not_found.png"),
                    },
                },
                expected_success=False,
            )
        )

        missing_copy = fixture_dir / "source_a.missing"
        fixture_a.rename(missing_copy)
        missing_state = run_request(
            run_dir,
            operation_id,
            "inspect_missing_footage",
            {"operation": "inspect_footage", "args": {"itemName": footage_name}},
        )
        report["cases"].append(missing_state)
        missing_footage = find_result(missing_state, "inspect_footage")["footage"]
        assert_equal(missing_footage["fileExists"], False, "moved fixture file state")
        assert_equal(missing_footage["missing"], True, "combined missing state")
        original_item_id = missing_footage["id"]
        relinked = run_request(
            run_dir,
            operation_id,
            "explicit_relink",
            {
                "operations": [
                    {
                        "operation": "relink_footage",
                        "args": {"itemName": footage_name, "path": str(fixture_b)},
                    },
                    {
                        "operation": "inspect_footage",
                        "args": {"itemName": footage_name},
                    },
                    {
                        "operation": "inspect_layer",
                        "args": {
                            "compName": comp_name,
                            "layerName": footage_layer_name,
                            "includeEffectProperties": True,
                        },
                    },
                    {"operation": "open_comp", "args": {"compName": comp_name}},
                ]
            },
            extra=[
                "--capture-frame",
                "--capture-method",
                "render-queue",
                "--capture-time",
                "1",
            ],
        )
        report["cases"].append(relinked)
        relink_result = find_result(relinked, "inspect_footage")["footage"]
        assert_equal(relink_result["id"], original_item_id, "relink item ID")
        assert_equal(relink_result["footageMissing"], False, "relink missing state")
        assert_equal(relink_result["fileExists"], True, "relink file state")
        assert_equal(relink_result["missing"], False, "combined relink state")
        relink_preview = Path(relinked["bridgeRunDir"]) / "frame_preview.png"
        relink_artifact = preserve_artifact(
            relink_preview,
            run_dir,
            "relink_frame.png",
        )
        report["artifacts"]["relinkFrame"] = str(relink_artifact)

        if args.render:
            output_path = output_dir / "production_test.mp4"
            rendered = run_request(
                run_dir,
                operation_id,
                "render_output",
                {
                    "operation": "render_comp",
                    "args": {
                        "compName": comp_name,
                        "outputPath": str(output_path),
                        "renderSettingsTemplate": "Best Settings",
                        "outputModuleTemplate": "H.264 - Match Render Settings -  5 Mbps",
                        "cleanupQueueItem": True,
                    },
                },
                extra=["--timeout-seconds", "120"],
            )
            report["cases"].append(rendered)
            if not output_path.is_file() or output_path.stat().st_size <= 0:
                raise ProductionTestFailure("render output is missing or empty")
            report["artifacts"]["renderOutput"] = str(output_path)

        video_preview = run_request(
            run_dir,
            operation_id,
            "animation_preview",
            {
                "operations": [
                    {"operation": "inspect_comp", "args": {"compName": comp_name}},
                    {"operation": "open_comp", "args": {"compName": comp_name}},
                ]
            },
            extra=["--capture-video"],
        )
        report["cases"].append(video_preview)
        video_dir = Path(video_preview["bridgeRunDir"]) / "temp" / "video_preview"
        contact_sheet = video_dir / "preview_contact_sheet.png"
        contact_sheet_artifact = preserve_artifact(
            contact_sheet,
            run_dir,
            "animation_contact_sheet.png",
        )
        report["artifacts"]["contactSheet"] = str(contact_sheet_artifact)
        video_path = video_dir / "preview" / "preview.mp4"
        if video_path.is_file():
            video_artifact = preserve_artifact(
                video_path,
                run_dir,
                "animation_preview.mp4",
            )
            report["artifacts"]["animationVideo"] = str(video_artifact)

        duplicate_name = prefix + "DUPLICATE"
        ambiguous = run_request(
            run_dir,
            operation_id,
            "ambiguous_layer_batch",
            {
                "operations": [
                    {
                        "operation": "create_solid",
                        "args": {
                            "compName": comp_name,
                            "name": duplicate_name,
                            "color": [0.2, 0.2, 0.2],
                        },
                    },
                    {
                        "operation": "create_solid",
                        "args": {
                            "compName": comp_name,
                            "name": duplicate_name,
                            "color": [0.3, 0.3, 0.3],
                        },
                    },
                    {
                        "operation": "inspect_layer",
                        "args": {
                            "compName": comp_name,
                            "layerName": duplicate_name,
                        },
                    },
                ]
            },
            expected_success=False,
        )
        report["cases"].append(ambiguous)
        assert_equal(payload(ambiguous).get("completedCount"), 2, "partial batch count")

        cleanup_script = run_dir / "cleanup.jsx"
        write_cleanup_script(cleanup_script, prefix, baseline_folder_names)
        report["cases"].append(run_script("cleanup", cleanup_script))
        final_inspect = run_script(
            "final_inspect",
            BRIDGE_ROOT / "scripts" / "ae_inspect_project.jsx",
        )
        report["cases"].append(final_inspect)
        project_report = Path(final_inspect["bridgeRunDir"]) / "project_structure.json"
        if project_report.is_file():
            project_state = json.loads(project_report.read_text(encoding="utf-8-sig"))
            leftovers = [
                item for item in project_state.get("items", []) if item["name"].startswith(prefix)
            ]
            assert_equal(leftovers, [], "production test item cleanup")
            assert_equal(project_state.get("items", []), baseline_items, "project item baseline")
        final_queue = run_script(
            "final_render_queue",
            BRIDGE_ROOT / "scripts" / "ae_inspect_render_queue.jsx",
        )
        report["cases"].append(final_queue)
        assert_equal(payload(final_queue), baseline_queue, "Render Queue baseline")
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
        cleanup_script = run_dir / "cleanup_after_failure.jsx"
        try:
            write_cleanup_script(cleanup_script, prefix, baseline_folder_names)
            cleanup = run_script("cleanup_after_failure", cleanup_script)
            report["cases"].append(cleanup)
        except Exception as cleanup_error:
            report["cleanupError"] = str(cleanup_error)
        write_report(run_dir, report)
        print("[PRODUCTION TEST FAILED]\n" + str(error), file=sys.stderr)
        print("Report Dir: " + str(run_dir))
        return 1

    write_report(run_dir, report)
    print("[PRODUCTION TEST PASSED]")
    print("Report Dir: " + str(run_dir))
    for name, path in report["artifacts"].items():
        print(name + ": " + path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
