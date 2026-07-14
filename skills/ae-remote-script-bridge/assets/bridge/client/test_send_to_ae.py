import datetime as dt
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import capture_preview
import send_to_ae
from run_context import create_run_context, prune_run_contexts


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

    def test_expired_operation_state_is_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "protection_state.json"
            project_path = Path(temp_dir) / "project.aep"
            backup_path = Path(temp_dir) / "backup.aep"
            project_path.write_bytes(b"project")
            backup_path.write_bytes(b"backup")
            state_path.write_text(
                json.dumps(
                    {
                        "expired": {
                            "createdAt": (
                                dt.datetime.now() - dt.timedelta(days=2)
                            ).isoformat(timespec="seconds"),
                            "projectFile": str(project_path),
                            "backupPath": str(backup_path),
                        },
                        "current": {
                            "createdAt": dt.datetime.now().isoformat(
                                timespec="seconds"
                            ),
                            "projectFile": str(project_path),
                            "backupPath": str(backup_path),
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(send_to_ae, "PROTECTION_STATE_PATH", state_path):
                state = send_to_ae.load_protection_state()

            self.assertNotIn("expired", state)
            self.assertIn("current", state)
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(["current"], list(persisted))

    def test_invalid_operation_state_is_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            state_path = temp_path / "protection_state.json"
            project_path = temp_path / "project.aep"
            backup_path = temp_path / "backup.aep"
            project_path.write_bytes(b"project")
            backup_path.write_bytes(b"backup")
            created_at = dt.datetime.now().isoformat(timespec="seconds")
            state_path.write_text(
                json.dumps(
                    {
                        "missing_backup": {
                            "createdAt": created_at,
                            "projectFile": str(project_path),
                        },
                        "directory_backup": {
                            "createdAt": created_at,
                            "projectFile": str(project_path),
                            "backupPath": str(temp_path),
                        },
                        "relative_backup": {
                            "createdAt": created_at,
                            "projectFile": str(project_path),
                            "backupPath": backup_path.name,
                        },
                        "valid": {
                            "createdAt": created_at,
                            "projectFile": str(project_path),
                            "backupPath": str(backup_path),
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(send_to_ae, "PROTECTION_STATE_PATH", state_path):
                state = send_to_ae.load_protection_state()

            self.assertEqual(["valid"], list(state))
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(["valid"], list(persisted))

    def test_non_object_operation_state_is_cleared(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "protection_state.json"
            state_path.write_text("[]", encoding="utf-8")

            with patch.object(send_to_ae, "PROTECTION_STATE_PATH", state_path):
                state = send_to_ae.load_protection_state()

            self.assertEqual({}, state)
            self.assertEqual({}, json.loads(state_path.read_text(encoding="utf-8")))

    def test_afterfx_resolution_precedence(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cli_path = temp_path / "cli" / "AfterFX.com"
            env_path = temp_path / "env" / "AfterFX.com"
            config_path = temp_path / "config" / "AfterFX.com"
            discovered_path = temp_path / "discovered" / "AfterFX.com"
            for path in [cli_path, env_path, config_path, discovered_path]:
                path.parent.mkdir()
                path.write_bytes(b"")

            with patch.dict(
                send_to_ae.os.environ,
                {"AFTERFX_COM_PATH": str(env_path)},
                clear=True,
            ):
                self.assertEqual(cli_path, send_to_ae.resolve_afterfx_path(cli_path))

                with patch.object(
                    send_to_ae,
                    "load_config_afterfx_path",
                    return_value=config_path,
                ) as load_config:
                    with patch.object(
                        send_to_ae,
                        "find_afterfx_com",
                        return_value=discovered_path,
                    ) as discover:
                        self.assertEqual(
                            env_path,
                            send_to_ae.resolve_afterfx_path(None),
                        )
                        load_config.assert_not_called()
                        discover.assert_not_called()

            with patch.dict(send_to_ae.os.environ, {}, clear=True):
                with patch.object(
                    send_to_ae,
                    "load_config_afterfx_path",
                    return_value=config_path,
                ):
                    with patch.object(
                        send_to_ae,
                        "find_afterfx_com",
                        return_value=discovered_path,
                    ) as discover:
                        self.assertEqual(
                            config_path,
                            send_to_ae.resolve_afterfx_path(None),
                        )
                        discover.assert_not_called()

    def test_backup_rotation_keeps_latest_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "project.aep"
            backup_paths = []
            with patch.object(send_to_ae, "MAX_BACKUPS", 2):
                for index in range(3):
                    project_path.write_text(str(index), encoding="utf-8")
                    backup_paths.append(send_to_ae.make_backup(project_path))
                    time.sleep(0.01)

            existing_backups = list(
                (Path(temp_dir) / send_to_ae.BACKUP_DIR_NAME).glob("*.aep")
            )
            self.assertEqual(2, len(existing_backups))
            self.assertFalse(backup_paths[0].exists())
            self.assertTrue(backup_paths[1].is_file())
            self.assertTrue(backup_paths[2].is_file())

    def test_prune_run_contexts_keeps_requested_count(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for _ in range(4):
                create_run_context(temp_dir)

            prune_run_contexts(temp_dir, keep_runs=2)

            runs_root = Path(temp_dir) / "logs" / "runs"
            self.assertEqual(2, len([path for path in runs_root.iterdir()]))

    def test_ffmpeg_timeout_becomes_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "preview.mp4"
            with patch("capture_preview.shutil.which", return_value="ffmpeg"):
                with patch(
                    "capture_preview.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(["ffmpeg"], 1),
                ):
                    warning = capture_preview.assemble_preview_video(
                        video_path,
                        4,
                        timeout_seconds=1,
                    )

            self.assertIn("timed out after 1 seconds", warning)

    def test_missing_ffmpeg_becomes_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "preview.mp4"
            with patch("capture_preview.shutil.which", return_value=None):
                warning = capture_preview.assemble_preview_video(video_path, 4)

            self.assertIn("ffmpeg was not found", warning)

    def test_capture_normalization_falls_back_without_pillow(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "capture.png"
            preview_path = temp_path / "preview.png"
            result_path = temp_path / "result.json"
            source_path.write_bytes(b"capture")
            original_import = __import__

            def import_without_pillow(name, *args, **kwargs):
                if name == "PIL":
                    raise ImportError("Pillow unavailable")
                return original_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=import_without_pillow):
                with patch("builtins.print"):
                    result = capture_preview.normalize_capture(
                        {"outputPath": str(source_path)},
                        1500,
                        result_path,
                        preview_path,
                    )

            self.assertEqual(b"capture", preview_path.read_bytes())
            self.assertEqual(str(preview_path), result["previewPath"])
            persisted = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(str(preview_path), persisted["previewPath"])

    def test_main_reuses_only_valid_operation_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            script_path = temp_path / "test.jsx"
            project_path = temp_path / "project.aep"
            backup_path = temp_path / "backup.aep"
            state_path = temp_path / "protection_state.json"
            script_path.write_text("(function () {})();", encoding="utf-8")
            project_path.write_bytes(b"project")
            backup_path.write_bytes(b"backup")
            state_path.write_text(
                json.dumps(
                    {
                        "operation": {
                            "createdAt": dt.datetime.now().isoformat(
                                timespec="seconds"
                            ),
                            "projectFile": str(project_path),
                            "backupPath": str(backup_path),
                        }
                    }
                ),
                encoding="utf-8",
            )
            results = [
                {
                    "ok": True,
                    "projectFile": str(project_path),
                    "dirty": True,
                },
                {"ok": True, "message": "done"},
            ]

            with patch.object(send_to_ae, "PROJECT_ROOT", temp_path):
                with patch.object(
                    send_to_ae,
                    "PROTECTION_STATE_PATH",
                    state_path,
                ):
                    with patch.object(
                        send_to_ae,
                        "resolve_afterfx_path",
                        return_value=Path("AfterFX.com"),
                    ):
                        with patch.object(
                            send_to_ae,
                            "run_afterfx_script",
                            side_effect=results,
                        ) as run_afterfx:
                            with patch.object(send_to_ae, "make_backup") as backup:
                                with patch(
                                    "send_to_ae.sys.argv",
                                    [
                                        "send_to_ae.py",
                                        str(script_path),
                                        "--operation-id",
                                        "operation",
                                    ],
                                ):
                                    with patch("builtins.print"):
                                        exit_code = send_to_ae.main()

            self.assertEqual(0, exit_code)
            self.assertEqual(2, run_afterfx.call_count)
            backup.assert_not_called()
            preflight_files = list(
                (temp_path / "logs" / "runs").glob("*/preflight.jsx")
            )
            self.assertEqual(1, len(preflight_files))
            self.assertIn(
                "var allowDirty = true;",
                preflight_files[0].read_text(encoding="utf-8"),
            )

    def test_render_queue_capture_restores_comp_time(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jsx = capture_preview.build_render_queue_capture_jsx(
                "capture",
                "middle",
                None,
                temp_path / "result.json",
                temp_path,
            )

            self.assertIn("originalTime = comp.time", jsx)
            self.assertGreaterEqual(jsx.count("comp.time = originalTime"), 2)

    def test_negative_preview_edges_are_rejected(self):
        arguments = [
            ["send_to_ae.py", "test.jsx", "--capture-max-edge", "-1"],
            ["send_to_ae.py", "test.jsx", "--capture-video-max-edge", "-1"],
        ]
        for argv in arguments:
            with self.subTest(option=argv[2]):
                with patch("send_to_ae.sys.argv", argv):
                    with patch("send_to_ae.resolve_afterfx_path") as resolve:
                        self.assertEqual(1, send_to_ae.main())
                        resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
