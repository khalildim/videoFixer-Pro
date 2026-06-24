from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoInfo:
    path: str
    readable: bool
    duration: float | None = None
    codec_video: str | None = None
    codec_audio: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    has_audio: bool = False
    has_video: bool = False
    error_message: str | None = None
    moov_atom_missing: bool = False
