import argparse
import sys
from pathlib import Path

import send_to_ae


def main():
    parser = argparse.ArgumentParser(
        description="Discover or save the AfterFX.com used by this Codex skill."
    )
    parser.add_argument(
        "--afterfx",
        help="AfterFX.com path selected by the user.",
    )
    args = parser.parse_args()

    try:
        if args.afterfx:
            saved_path = send_to_ae.save_config_afterfx_path(Path(args.afterfx))
            print("Saved AE Path: " + str(saved_path))
            return 0

        configured_path = send_to_ae.load_config_afterfx_path()
        if configured_path and configured_path.is_file():
            print("Configured AE Path: " + str(configured_path))
            return 0

        candidates = send_to_ae.find_afterfx_com_candidates()
        if len(candidates) == 1:
            saved_path = send_to_ae.save_config_afterfx_path(candidates[0])
            print("Saved AE Path: " + str(saved_path))
            return 0
        if len(candidates) > 1:
            print("Multiple After Effects installations found:")
            for index, path in enumerate(candidates, start=1):
                print(str(index) + ". " + str(path))
            print("Ask the user which version to use, then run:")
            print('python client\\configure_afterfx.py --afterfx "<path>"')
            return 2

        print("AfterFX.com not found under C:\\Program Files\\Adobe.", file=sys.stderr)
        return 1
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
