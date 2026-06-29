import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
RESULT_PATH = PROJECT_ROOT / "logs" / "latest_result.json"
TEMP_DIR = PROJECT_ROOT / "temp"
TIMEOUT_SECONDS = 20
DEFAULT_ADOBE_DIR = Path("C:/Program Files/Adobe")


def fail(message):
    print(message, file=sys.stderr)
    return 1


def to_extendscript_path(path):
    return str(path.resolve()).replace("\\", "/")


def escape_extendscript_string(value):
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def load_config_afterfx_path():
    if not CONFIG_PATH.exists():
        return None
    with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    afterfx_com_path = config.get("afterfx_com_path")
    if afterfx_com_path:
        return Path(afterfx_com_path)
    if config:
        raise ValueError("config.json must contain afterfx_com_path.")
    return None


def afterfx_version_key(path):
    app_dir = path.parent.parent.name
    parts = [int(part) for part in re.findall(r"\d+", app_dir)]
    return parts if parts else [0]


def find_afterfx_com():
    if not DEFAULT_ADOBE_DIR.exists():
        return None

    candidates = []
    for app_dir in DEFAULT_ADOBE_DIR.glob("Adobe After Effects *"):
        candidate = app_dir / "Support Files" / "AfterFX.com"
        if candidate.exists():
            candidates.append(candidate)

    if not candidates:
        return None

    candidates.sort(key=afterfx_version_key, reverse=True)
    return candidates[0]


def resolve_afterfx_path(cli_afterfx_path):
    if cli_afterfx_path:
        path = Path(cli_afterfx_path)
        if not path.exists():
            raise FileNotFoundError("--afterfx path not found: " + str(path))
        return path

    env_afterfx_path = os.environ.get("AFTERFX_COM_PATH")
    if env_afterfx_path:
        path = Path(env_afterfx_path)
        if not path.exists():
            raise FileNotFoundError(
                "AFTERFX_COM_PATH path not found: " + str(path)
            )
        return path

    config_afterfx_path = load_config_afterfx_path()
    if config_afterfx_path:
        if not config_afterfx_path.exists():
            raise FileNotFoundError(
                "config.json afterfx_com_path not found: "
                + str(config_afterfx_path)
            )
        return config_afterfx_path

    discovered_path = find_afterfx_com()
    if discovered_path:
        return discovered_path

    raise FileNotFoundError(
        "AfterFX.com not found. Provide one of:\n"
        + "1. --afterfx \"C:\\path\\to\\AfterFX.com\"\n"
        + "2. AFTERFX_COM_PATH environment variable\n"
        + "3. config.json with afterfx_com_path next to this bridge"
    )


def build_wrapper_jsx(target_jsx):
    target_path = escape_extendscript_string(to_extendscript_path(target_jsx))
    bridge_root = escape_extendscript_string(to_extendscript_path(PROJECT_ROOT))
    logs_dir = escape_extendscript_string(to_extendscript_path(RESULT_PATH.parent))
    temp_dir = escape_extendscript_string(to_extendscript_path(TEMP_DIR))
    result_path = escape_extendscript_string(to_extendscript_path(RESULT_PATH))

    return """(function () {
    var targetFile = new File("%s");
    var resultFile = new File("%s");
    $.global.AE_BRIDGE_ROOT = "%s";
    $.global.AE_BRIDGE_LOGS_DIR = "%s";
    $.global.AE_BRIDGE_TEMP_DIR = "%s";
    $.global.AE_BRIDGE_RESULT_PATH = "%s";

    function escapeJson(value) {
        var text = String(value);
        text = text.replace(/\\\\/g, "\\\\\\\\");
        text = text.replace(/"/g, '\\\\"');
        text = text.replace(/\\r/g, "\\\\r");
        text = text.replace(/\\n/g, "\\\\n");
        text = text.replace(/\\t/g, "\\\\t");
        return text;
    }

    function writeResult(ok, message, line) {
        resultFile.encoding = "UTF-8";
        resultFile.open("w");
        resultFile.write("{");
        resultFile.write('"ok":' + (ok ? "true" : "false"));
        resultFile.write(',"message":"' + escapeJson(message) + '"');
        if (line !== null && line !== undefined) {
            resultFile.write(',"line":' + line);
        }
        resultFile.write("}");
        resultFile.close();
    }

    try {
        $.evalFile(targetFile);
        writeResult(true, "Script executed successfully.", null);
    } catch (err) {
        writeResult(false, err.toString(), err.line);
    }
})();""" % (
        target_path,
        result_path,
        bridge_root,
        logs_dir,
        temp_dir,
        result_path,
    )


def wait_for_result():
    deadline = time.time() + TIMEOUT_SECONDS
    while time.time() < deadline:
        if RESULT_PATH.exists():
            with RESULT_PATH.open("r", encoding="utf-8-sig") as result_file:
                return json.load(result_file)
        time.sleep(0.2)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Send a JSX file to Adobe After Effects through AfterFX.com."
    )
    parser.add_argument("script", help="Path to the .jsx script to run.")
    parser.add_argument(
        "--afterfx",
        help="Optional explicit path to AfterFX.com. Overrides env/config/search.",
    )
    args = parser.parse_args()

    try:
        afterfx_com_path = resolve_afterfx_path(args.afterfx)
    except (OSError, ValueError, json.JSONDecodeError) as err:
        return fail("[CONFIG ERROR]\n" + str(err))

    jsx_path = Path(args.script)
    if not jsx_path.is_absolute():
        jsx_path = (Path.cwd() / jsx_path).resolve()
    else:
        jsx_path = jsx_path.resolve()

    if not jsx_path.exists():
        return fail("[INPUT ERROR]\nJSX file not found: " + str(jsx_path))

    if jsx_path.suffix.lower() != ".jsx":
        return fail("[INPUT ERROR]\nExpected a .jsx file: " + str(jsx_path))

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    if RESULT_PATH.exists():
        RESULT_PATH.unlink()

    wrapper_path = TEMP_DIR / "ae_bridge_wrapper.jsx"
    wrapper_path.write_text(build_wrapper_jsx(jsx_path), encoding="utf-8")

    print("AE Path: " + str(afterfx_com_path))
    print("JSX Path: " + str(jsx_path))

    subprocess.run([str(afterfx_com_path), "-r", str(wrapper_path)])

    try:
        result = wait_for_result()
    except (OSError, json.JSONDecodeError) as err:
        return fail("[AE ERROR]\nCould not read result file: " + str(err))

    if result is None:
        print("[AE TIMEOUT]")
        print("No result file generated.")
        return 1

    if result.get("ok"):
        print("[AE OK]")
        print(result.get("message", "Script executed successfully."))
        return 0

    print("[AE ERROR]")
    print(result.get("message", "Unknown AE script error."))
    if "line" in result:
        print("Line: " + str(result["line"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
