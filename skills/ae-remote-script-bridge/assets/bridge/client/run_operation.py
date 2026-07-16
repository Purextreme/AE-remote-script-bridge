import subprocess
import sys
import tempfile
from pathlib import Path

from operation_request import (
    OperationRequestError,
    build_launcher_jsx,
    load_request,
)


CLIENT_DIR = Path(__file__).resolve().parent
SEND_TO_AE_PATH = CLIENT_DIR / "send_to_ae.py"


def fail(message):
    print(message, file=sys.stderr)
    return 1


def usage():
    return (
        "Usage: python client\\run_operation.py REQUEST.json "
        "[send_to_ae options]\n\n"
        "The request is validated before AE runs. All remaining options are passed "
        "to send_to_ae.py, including --operation-id, --no-protect, --capture-frame, "
        "and --timeout-seconds."
    )


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in {"-h", "--help"}:
        print(usage())
        return 0 if argv else 1

    request_path = Path(argv[0]).resolve()
    if not request_path.is_file():
        return fail("[INPUT ERROR]\nOperation request not found: " + str(request_path))

    try:
        request = load_request(request_path)
    except (OSError, OperationRequestError) as err:
        return fail("[INPUT ERROR]\n" + str(err))

    launcher_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".jsx",
            prefix="ae_bridge_operation_",
            delete=False,
        ) as launcher_file:
            launcher_file.write(build_launcher_jsx(request))
            launcher_path = Path(launcher_file.name)

        command = [
            sys.executable,
            str(SEND_TO_AE_PATH),
            str(launcher_path),
        ] + argv[1:]
        return subprocess.run(command).returncode
    finally:
        if launcher_path is not None:
            try:
                launcher_path.unlink()
            except FileNotFoundError:
                pass


if __name__ == "__main__":
    sys.exit(main())
