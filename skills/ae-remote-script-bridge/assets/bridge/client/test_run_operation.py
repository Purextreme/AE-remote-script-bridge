import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import operation_request
import run_operation


class OperationRequestTests(unittest.TestCase):
    def test_valid_batch_is_accepted(self):
        request = {
            "operations": [
                {
                    "operation": "create_text",
                    "args": {
                        "text": "Hello",
                        "name": "Title",
                        "position": [960, 540],
                    },
                },
                {
                    "operation": "inspect_comp",
                    "args": {"includeLayers": True},
                },
            ]
        }

        self.assertIs(request, operation_request.validate_request(request))

    def test_unknown_field_is_rejected(self):
        request = {
            "operation": "set_transform",
            "args": {"layerIndex": 1, "postion": [1, 2]},
        }

        with self.assertRaisesRegex(
            operation_request.OperationRequestError,
            "unsupported field.*postion",
        ):
            operation_request.validate_request(request)

    def test_layer_name_and_index_are_mutually_exclusive(self):
        request = {
            "operation": "set_text",
            "args": {"layerIndex": 1, "layerName": "Title", "text": "New"},
        }

        with self.assertRaisesRegex(
            operation_request.OperationRequestError,
            "provide exactly one",
        ):
            operation_request.validate_request(request)

    def test_invalid_opacity_is_rejected_before_ae(self):
        request = {
            "operation": "set_transform",
            "args": {"layerIndex": 1, "opacity": 101},
        }

        with self.assertRaisesRegex(
            operation_request.OperationRequestError,
            "between 0 and 100",
        ):
            operation_request.validate_request(request)

    def test_launcher_embeds_ascii_json_and_static_operations_path(self):
        launcher = operation_request.build_launcher_jsx(
            {"operation": "create_text", "args": {"text": "中文"}}
        )

        self.assertIn("\\u4e2d\\u6587", launcher)
        self.assertIn("/operations/ae_operations.jsx", launcher)

    def test_runner_forwards_bridge_options_and_removes_launcher(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            request_path = Path(temp_dir) / "request.json"
            request_path.write_text(
                json.dumps(
                    {
                        "operation": "inspect_comp",
                        "args": {"includeLayers": False},
                    }
                ),
                encoding="utf-8",
            )
            captured = {}

            def run_command(command):
                captured["command"] = command
                launcher_path = Path(command[2])
                captured["launcher_path"] = launcher_path
                self.assertTrue(launcher_path.is_file())
                self.assertIn(
                    "AE_BRIDGE_OPERATION_REQUEST",
                    launcher_path.read_text(encoding="utf-8"),
                )
                return SimpleNamespace(returncode=0)

            with patch("run_operation.subprocess.run", side_effect=run_command):
                exit_code = run_operation.main(
                    [str(request_path), "--no-protect", "--capture-frame"]
                )

            self.assertEqual(0, exit_code)
            self.assertEqual(
                ["--no-protect", "--capture-frame"],
                captured["command"][3:],
            )
            self.assertFalse(captured["launcher_path"].exists())


if __name__ == "__main__":
    unittest.main()
