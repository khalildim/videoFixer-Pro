from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

from app.core.ffmpeg_runner import run_capture
from app.models.app_settings import AppSettings
from app.models.video_info import VideoInfo


def analyze_video(path: str, settings: AppSettings | None = None) -> VideoInfo:
    settings = settings or AppSettings.load()
    file_path = Path(path)
    if not file_path.exists():
        return VideoInfo(path=path, readable=False, error_message="File does not exist.")
    if file_path.stat().st_size == 0:
        return VideoInfo(path=path, readable=False, error_message="File is empty.")

    cmd = [
        settings.resolve_ffprobe(),
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    result = run_capture(cmd)
    if not result.success:
        error = result.output.strip() or "FFprobe could not read the file."
        return VideoInfo(
            path=str(file_path),
            readable=False,
            error_message=error,
            moov_atom_missing=_looks_like_missing_moov(error) or not _contains_atom(file_path, b"moov"),
        )

    try:
        data = json.loads(result.output)
    except json.JSONDecodeError as exc:
        return VideoInfo(path=str(file_path), readable=False, error_message=f"Invalid FFprobe output: {exc}")

    streams = data.get("streams") or []
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio_stream = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    duration = _parse_float((data.get("format") or {}).get("duration"))

    return VideoInfo(
        path=str(file_path),
        readable=True,
        duration=duration,
        codec_video=video_stream.get("codec_name") if video_stream else None,
        codec_audio=audio_stream.get("codec_name") if audio_stream else None,
        width=_parse_int(video_stream.get("width")) if video_stream else None,
        height=_parse_int(video_stream.get("height")) if video_stream else None,
        fps=_parse_fps(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate")) if video_stream else None,
        has_audio=audio_stream is not None,
        has_video=video_stream is not None,
        error_message=None,
        moov_atom_missing=False,
    )


def _parse_float(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_int(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_fps(value: object) -> float | None:
    if not value:
        return None
    try:
        fps = float(Fraction(str(value)))
    except (ValueError, ZeroDivisionError):
        return None
    return fps if fps > 0 else None


def _looks_like_missing_moov(error: str) -> bool:
    lower = error.lower()
    return "moov atom not found" in lower or "moov" in lower and "not found" in lower


def _contains_atom(path: Path, atom: bytes, max_bytes: int = 32 * 1024 * 1024) -> bool:
    try:
        with path.open("rb") as handle:
            remaining = min(path.stat().st_size, max_bytes)
            while remaining > 0:
                chunk = handle.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                if atom in chunk:
                    return True
                remaining -= len(chunk)
    except OSError:
        return False
    return False
