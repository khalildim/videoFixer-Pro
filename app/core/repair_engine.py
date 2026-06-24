from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from app.core.analyzer import analyze_video
from app.core.file_utils import repair_log_path
from app.core.recovery_methods import extract_streams, repair_faststart, repair_reencode, repair_remux, repair_with_untrunc
from app.core.validators import ValidationError, validate_job
from app.models.app_settings import AppSettings
from app.models.repair_result import RepairJob, RepairResult
from app.models.video_info import VideoInfo


LogCallback = Callable[[str], None]
ProgressCallback = Callable[[int], None]


def run_repair(
    job: RepairJob,
    settings: AppSettings | None = None,
    log_callback: LogCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    cancel_event: threading.Event | None = None,
) -> RepairResult:
    settings = settings or AppSettings.load()
    log_lines: list[str] = []

    def log(message: str) -> None:
        log_lines.append(message)
        if log_callback:
            log_callback(message)

    def progress(value: int) -> None:
        if progress_callback:
            progress_callback(value)

    try:
        validate_job(job, settings)
        progress(2)
        log("Analyzing damaged video with FFprobe...")
        analysis = analyze_video(job.input_file, settings)
        _log_analysis(analysis, log)
        progress(10)

        if job.mode == "auto":
            result = _auto_repair(job, settings, analysis, log, progress, cancel_event)
        else:
            result = _run_single_method(job, settings, analysis, log, progress, cancel_event)
            if result.success and not _verify_result(result, settings, log):
                result = RepairResult(
                    False,
                    result.method,
                    result.output_file,
                    "Repair output was created, but FFprobe could not verify a readable video stream.",
                    result.log,
                )

        final = _attach_log(result, job, log_lines)
        progress(100 if final.success else 0)
        return final
    except ValidationError as exc:
        result = RepairResult(False, "validation", None, str(exc), "\n".join(log_lines))
        return _attach_log(result, job, log_lines)
    except Exception as exc:
        log(f"Unexpected failure: {exc}")
        result = RepairResult(False, "error", None, "Repair failed because an unexpected error occurred.", "\n".join(log_lines))
        return _attach_log(result, job, log_lines)


def _auto_repair(
    job: RepairJob,
    settings: AppSettings,
    analysis: VideoInfo,
    log: LogCallback,
    progress: ProgressCallback,
    cancel_event: threading.Event | None,
) -> RepairResult:
    if analysis.readable:
        log("FFmpeg can read the file. Trying remux repair...")
        result = repair_remux(job.input_file, job.output_folder, settings, analysis, log, progress, cancel_event)
        if _verify_result(result, settings, log):
            return result

        log("Remux failed. Trying faststart repair...")
        result = repair_faststart(job.input_file, job.output_folder, settings, analysis, log, progress, cancel_event)
        if _verify_result(result, settings, log):
            return result

        log("Faststart failed. Trying full re-encode...")
        result = repair_reencode(job.input_file, job.output_folder, settings, analysis, log, progress, cancel_event)
        if _verify_result(result, settings, log):
            return result

    if analysis.moov_atom_missing:
        if job.reference_file:
            log("Moov atom appears to be missing. Trying reference-video recovery...")
            result = repair_with_untrunc(job.reference_file, job.input_file, job.output_folder, settings, log, progress, cancel_event)
            if _verify_result(result, settings, log):
                return result
            return RepairResult(
                False,
                "untrunc",
                None,
                "Reference-video recovery failed. FFmpeg cannot extract streams from this file because the moov atom is missing.",
                result.log,
            )
        else:
            return RepairResult(
                False,
                "reference_required",
                None,
                "This file likely needs a healthy reference video from the same device.",
            )

    log("Trying stream extraction mode...")
    result = extract_streams(job.input_file, job.output_folder, settings, analysis, log, progress, cancel_event)
    if _verify_result(result, settings, log):
        return result
    return RepairResult(False, "auto", None, "Repair failed. The media data may be missing or too damaged.", result.log)


def _run_single_method(
    job: RepairJob,
    settings: AppSettings,
    analysis: VideoInfo,
    log: LogCallback,
    progress: ProgressCallback,
    cancel_event: threading.Event | None,
) -> RepairResult:
    if job.mode == "remux":
        return repair_remux(job.input_file, job.output_folder, settings, analysis, log, progress, cancel_event)
    if job.mode == "faststart":
        return repair_faststart(job.input_file, job.output_folder, settings, analysis, log, progress, cancel_event)
    if job.mode == "reencode":
        return repair_reencode(job.input_file, job.output_folder, settings, analysis, log, progress, cancel_event)
    if job.mode == "untrunc":
        if not job.reference_file:
            return RepairResult(False, "untrunc", None, "Reference-video recovery requires a healthy reference video.")
        return repair_with_untrunc(job.reference_file, job.input_file, job.output_folder, settings, log, progress, cancel_event)
    if job.mode == "extract":
        return extract_streams(job.input_file, job.output_folder, settings, analysis, log, progress, cancel_event)
    return RepairResult(False, job.mode, None, f"Unknown repair mode: {job.mode}")


def _verify_result(result: RepairResult, settings: AppSettings, log: LogCallback) -> bool:
    if not result.success or not result.output_file:
        log(result.message)
        return False
    output_path = Path(result.output_file)
    if not output_path.exists() or output_path.stat().st_size == 0:
        log("Repair command completed but did not create a usable output file.")
        return False
    verification = analyze_video(str(output_path), settings)
    if not verification.readable or not verification.has_video:
        log("Output was created, but FFprobe could not verify a readable video stream.")
        return False
    log(f"Verified output: {output_path}")
    return True


def _attach_log(result: RepairResult, job: RepairJob, log_lines: list[str]) -> RepairResult:
    try:
        path = repair_log_path(job.input_file, job.output_folder)
        body = "\n".join(log_lines)
        if result.log and result.log not in body:
            body = f"{body}\n\n{result.log}".strip()
        path.write_text(body, encoding="utf-8")
        return RepairResult(result.success, result.method, result.output_file, result.message, body, str(path))
    except OSError:
        return result


def _log_analysis(analysis: VideoInfo, log: LogCallback) -> None:
    if not analysis.readable:
        log(f"FFprobe could not read the file: {analysis.error_message or 'unknown error'}")
        if analysis.moov_atom_missing:
            log("Moov atom missing. Please choose a healthy reference video from the same camera when available.")
        return
    log(
        "Readable video: "
        f"duration={analysis.duration or 'unknown'}s, "
        f"video={analysis.codec_video or 'none'}, "
        f"audio={analysis.codec_audio or 'none'}, "
        f"size={analysis.width or '?'}x{analysis.height or '?'}, "
        f"fps={analysis.fps or 'unknown'}"
    )
