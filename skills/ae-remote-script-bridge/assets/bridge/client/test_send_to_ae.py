import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import send_to_ae
from run_context import create_run_context


class BridgeClientTests(unittest.TestCase):
    def test_run_context_uses_unique_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first = create_run_context(temp_dir)
            second = create_run_context(temp_dir)

            self.assertNotEqual(first.run_id, second.run_id)
            self.assertNotEqual(first.run_dir, second.run_dir)
            self.assertTrue(first.temp_dir.is_dir())
            self.assertTrue(second.temp_dir.is_dir())

    def test_wait_for_result_rejects_mismatched_run_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            result_path.write_text('{"runId":"stale"}', encoding="utf-8")

            with patch("send_to_ae.time.sleep"):
                with self.assertRaisesRegex(RuntimeError, "did not match"):
                    send_to_ae.wait_for_result(
                        result_path,
                        time.monotonic() + 0.01,
                        "current",
                    )

    def test_subprocess_timeout_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            with patch(
                "send_to_ae.subprocess.run",
                side_effect=subprocess.TimeoutExpired(["AfterFX.com"], 1),
            ):
                with self.assertRaisesRegex(RuntimeError, "timed out during test"):
                    send_to_ae.run_afterfx_script(
                        Path("AfterFX.com"),
                        Path("test.jsx"),
                        result_path,
                        "test",
                        timeout_seconds=1,
                    )


if __name__ == "__main__":
    unittest.main()
