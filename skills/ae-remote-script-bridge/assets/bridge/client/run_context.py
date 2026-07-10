import datetime as dt
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path


MAX_RUNS = 10


@dataclass(frozen=True)
class RunContext:
    run_id: str
    run_dir: Path
    temp_dir: Path
    result_path: Path
    preflight_jsx_path: Path
    preflight_result_path: Path
    wrapper_jsx_path: Path
    frame_capture_jsx_path: Path
    frame_capture_result_path: Path
    frame_preview_path: Path
    video_capture_jsx_path: Path
    video_capture_result_path: Path
    video_capture_dir: Path


def create_run_context(project_root):
    runs_root = Path(project_root) / "logs" / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_id = timestamp + "_" + uuid.uuid4().hex[:8]
    run_dir = runs_root / run_id
    temp_dir = run_dir / "temp"
    temp_dir.mkdir(parents=True, exist_ok=False)

    return RunContext(
        run_id=run_id,
        run_dir=run_dir,
        temp_dir=temp_dir,
        result_path=run_dir / "result.json",
        preflight_jsx_path=run_dir / "preflight.jsx",
        preflight_result_path=run_dir / "preflight_result.json",
        wrapper_jsx_path=run_dir / "wrapper.jsx",
        frame_capture_jsx_path=run_dir / "frame_capture.jsx",
        frame_capture_result_path=run_dir / "frame_capture_result.json",
        frame_preview_path=run_dir / "frame_preview.png",
        video_capture_jsx_path=run_dir / "video_capture.jsx",
        video_capture_result_path=run_dir / "video_capture_result.json",
        video_capture_dir=temp_dir / "video_preview",
    )


def prune_run_contexts(project_root, keep_runs=MAX_RUNS):
    runs_root = Path(project_root) / "logs" / "runs"
    if not runs_root.exists():
        return

    runs = [path for path in runs_root.iterdir() if path.is_dir()]
    runs.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    for stale_run in runs[max(1, keep_runs):]:
        shutil.rmtree(stale_run)
