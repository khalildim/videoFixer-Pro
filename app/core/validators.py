from __future__ import annotations

from pathlib import Path

from app.core.file_utils import VIDEO_EXTENSIONS, ensure_output_folder, has_enough_space
from app.models.app_settings import AppSettings
from app.models.repair_result import RepairJob


class ValidationError(ValueError):
    pass


def validate_job(job: RepairJob, settings: AppSettings) -> None:
    input_path = Path(job.input_file).expanduser()
    if not input_path.exists():
        raise ValidationError("The damaged video file does not exist.")
    if not input_path.is_file():
        raise ValidationError("The damaged video path is not a file.")
    if input_path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise ValidationError("Supported input formats are .mp4, .mov, .m4v, and .3gp.")
    if input_path.stat().st_size <= 0:
        raise ValidationError("The damaged video file is empty.")

    output_folder = ensure_output_folder(job.output_folder)
    if not has_enough_space(input_path, output_folder):
        raise ValidationError("The output folder does not appear to have enough free disk space.")

    if job.reference_file:
        reference_path = Path(job.reference_file).expanduser()
        if not reference_path.exists():
            raise ValidationError("The reference video file does not exist.")
        if reference_path.suffix.lower() not in VIDEO_EXTENSIONS:
            raise ValidationError("The reference video must be .mp4, .mov, .m4v, or .3gp.")

    if job.mode not in {"auto", "remux", "faststart", "reencode", "untrunc", "extract"}:
        raise ValidationError(f"Unknown repair mode: {job.mode}")

    _require_tool(settings.resolve_ffmpeg(), "FFmpeg")
    _require_tool(settings.resolve_ffprobe(), "FFprobe")
    if job.mode == "untrunc":
        _require_tool(settings.resolve_untrunc(), "Untrunc")


def _require_tool(path: str, label: str) -> None:
    import shutil

    if Path(path).exists() or shutil.which(path):
        return
    raise ValidationError(f"{label} was not found. Configure its path in Settings.")
