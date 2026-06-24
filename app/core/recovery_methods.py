from __future__ import annotations

import threading
import time
from pathlib import Path

from app.core.ffmpeg_runner import LogCallback, ProgressCallback, run_command
from app.core.file_utils import ensure_output_folder, unique_output_path
from app.models.app_settings import AppSettings
from app.models.repair_result import RepairResult
from app.models.video_info import VideoInfo


def repair_remux(
    input_file: str,
    output_folder: str,
    settings: AppSettings,
    analysis: VideoInfo | None = None,
    log_callback: LogCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> RepairResult:
    output_file = unique_output_path(input_file, output_folder, "remux")
    cmd = [
        settings.resolve_ffmpeg(),
        "-y",
        "-err_detect",
        "ignore_err",
        "-i",
        input_file,
        "-c",
        "copy",
        str(output_file),
    ]
    result = run_command(cmd, log_callback=log_callback, progress_callback=progress_callback, duration=_duration(analysis), cancel_event=cancel_event)
    return _result_from_command(result.success, "remux", output_file, "Remux repair completed.", "Remux repair failed.", result.output)


def repair_faststart(
    input_file: str,
    output_folder: str,
    settings: AppSettings,
    analysis: VideoInfo | None = None,
    log_callback: LogCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> RepairResult:
    output_file = unique_output_path(input_file, output_folder, "faststart")
    cmd = [
        settings.resolve_ffmpeg(),
        "-y",
        "-i",
        input_file,
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(output_file),
    ]
    result = run_command(cmd, log_callback=log_callback, progress_callback=progress_callback, duration=_duration(analysis), cancel_event=cancel_event)
    return _result_from_command(result.success, "faststart", output_file, "Faststart repair completed.", "Faststart repair failed.", result.output)


def repair_reencode(
    input_file: str,
    output_folder: str,
    settings: AppSettings,
    analysis: VideoInfo | None = None,
    log_callback: LogCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> RepairResult:
    output_file = unique_output_path(input_file, output_folder, "reencode")
    cmd = [
        settings.resolve_ffmpeg(),
        "-y",
        "-err_detect",
        "ignore_err",
        "-i",
        input_file,
        "-c:v",
        "libx264",
        "-preset",
        settings.reencode_preset,
        "-crf",
        str(settings.crf_quality),
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        str(output_file),
    ]
    result = run_command(cmd, log_callback=log_callback, progress_callback=progress_callback, duration=_duration(analysis), cancel_event=cancel_event)
    return _result_from_command(result.success, "reencode", output_file, "Re-encode repair completed.", "Re-encode repair failed.", result.output)


def repair_with_untrunc(
    reference_file: str,
    damaged_file: str,
    output_folder: str,
    settings: AppSettings,
    log_callback: LogCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> RepairResult:
    folder = ensure_output_folder(output_folder)
    damaged_path = Path(damaged_file).expanduser().resolve()
    output_file = unique_output_path(damaged_path, folder, "untrunc", damaged_path.suffix or ".mp4")
    start_time = time.time()
    cmd = [
        settings.resolve_untrunc(),
        "-n",
        "-dst",
        str(output_file),
        str(Path(reference_file).expanduser().resolve()),
        str(damaged_path),
    ]
    result = run_command(cmd, cwd=folder, log_callback=log_callback, progress_callback=progress_callback, cancel_event=cancel_event)
    found_output = output_file if output_file.exists() and output_file.stat().st_size > 0 else _find_untrunc_output(damaged_path, folder, start_time)
    success = result.success and found_output is not None
    if log_callback and not found_output:
        expected = _expected_untrunc_outputs(damaged_path, folder)
        expected.insert(0, output_file)
        log_callback("No fixed file was found after untrunc finished.")
        log_callback("Checked: " + ", ".join(str(path) for path in expected))
    return RepairResult(
        success=success,
        method="untrunc",
        output_file=str(found_output) if found_output else None,
        message="Reference-video recovery completed." if success else "Reference-video recovery failed.",
        log=result.output,
    )


def extract_streams(
    input_file: str,
    output_folder: str,
    settings: AppSettings,
    analysis: VideoInfo | None = None,
    log_callback: LogCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> RepairResult:
    folder = ensure_output_folder(output_folder)
    stem = Path(input_file).stem or "video"
    video_track = folder / f"{stem}_video_track.h264"
    audio_track = folder / f"{stem}_audio_track.aac"
    rebuilt = unique_output_path(input_file, output_folder, "extracted")
    logs: list[str] = []

    video_cmd = [
        settings.resolve_ffmpeg(),
        "-y",
        "-err_detect",
        "ignore_err",
        "-i",
        input_file,
        "-map",
        "0:v:0",
        "-c",
        "copy",
        str(video_track),
    ]
    video_result = run_command(video_cmd, log_callback=log_callback, duration=_duration(analysis), cancel_event=cancel_event)
    logs.append(video_result.output)
    if not video_result.success:
        return RepairResult(False, "extract", None, "Video stream extraction failed.", "\n".join(logs))

    audio_result = None
    if analysis is None or analysis.has_audio:
        audio_cmd = [
            settings.resolve_ffmpeg(),
            "-y",
            "-err_detect",
            "ignore_err",
            "-i",
            input_file,
            "-map",
            "0:a:0",
            "-c",
            "copy",
            str(audio_track),
        ]
        audio_result = run_command(audio_cmd, log_callback=log_callback, cancel_event=cancel_event)
        logs.append(audio_result.output)

    rebuild_cmd = [
        settings.resolve_ffmpeg(),
        "-y",
        "-r",
        str(analysis.fps if analysis and analysis.fps else 30),
        "-i",
        str(video_track),
    ]
    if audio_result and audio_result.success and audio_track.exists():
        rebuild_cmd.extend(["-i", str(audio_track)])
    rebuild_cmd.extend(["-c", "copy", str(rebuilt)])
    rebuild_result = run_command(
        rebuild_cmd,
        log_callback=log_callback,
        progress_callback=progress_callback,
        duration=_duration(analysis),
        cancel_event=cancel_event,
    )
    logs.append(rebuild_result.output)
    return _result_from_command(
        rebuild_result.success,
        "extract",
        rebuilt,
        "Readable streams were extracted and rebuilt.",
        "Stream rebuild failed.",
        "\n".join(logs),
    )


def _result_from_command(success: bool, method: str, output_file: Path, success_message: str, failure_message: str, log: str) -> RepairResult:
    output = str(output_file) if success and output_file.exists() and output_file.stat().st_size > 0 else None
    return RepairResult(success=output is not None, method=method, output_file=output, message=success_message if output else failure_message, log=log)


def _duration(analysis: VideoInfo | None) -> float | None:
    return analysis.duration if analysis and analysis.duration and analysis.duration > 0 else None


def _find_recent_video(folder: Path, start_time: float) -> Path | None:
    candidates = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in {".mp4", ".mov", ".m4v", ".3gp"} and path.stat().st_mtime >= start_time
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _find_untrunc_output(damaged_file: Path, output_folder: Path, start_time: float) -> Path | None:
    expected = _expected_untrunc_outputs(damaged_file, output_folder)
    for path in expected:
        if path.exists() and path.is_file() and path.stat().st_size > 0:
            return path

    search_folders = {output_folder, damaged_file.parent}
    candidates: list[Path] = []
    for folder in search_folders:
        try:
            candidates.extend(
                path
                for path in folder.iterdir()
                if path.is_file()
                and path.suffix.lower() in {".mp4", ".mov", ".m4v", ".3gp"}
                and path.stat().st_mtime >= start_time
                and path.stat().st_size > 0
            )
        except OSError:
            continue
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _expected_untrunc_outputs(damaged_file: Path, output_folder: Path) -> list[Path]:
    names = [
        f"{damaged_file.stem}_fixed{damaged_file.suffix}",
        f"{damaged_file.stem}.fixed{damaged_file.suffix}",
        f"{damaged_file.stem}_repaired{damaged_file.suffix}",
    ]
    folders = [output_folder, damaged_file.parent]
    return [folder / name for folder in folders for name in names]
