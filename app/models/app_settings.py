from __future__ import annotations

import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


CONFIG_DIR = Path.home() / ".videofixer_pro"
CONFIG_FILE = CONFIG_DIR / "settings.json"


@dataclass
class AppSettings:
    ffmpeg_path: str = ""
    ffprobe_path: str = ""
    untrunc_path: str = ""
    default_output_folder: str = ""
    default_repair_mode: str = "auto"
    overwrite_existing: bool = False
    keep_temp_files: bool = False
    language: str = "en"
    hardware_acceleration: bool = False
    crf_quality: int = 23
    reencode_preset: str = "medium"

    @classmethod
    def load(cls) -> "AppSettings":
        if not CONFIG_FILE.exists():
            return cls()
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        defaults = asdict(cls())
        defaults.update({key: value for key, value in data.items() if key in defaults})
        return cls(**defaults)

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    def resolve_ffmpeg(self) -> str:
        return self._resolve_tool(self.ffmpeg_path, "ffmpeg.exe" if _is_windows() else "ffmpeg")

    def resolve_ffprobe(self) -> str:
        return self._resolve_tool(self.ffprobe_path, "ffprobe.exe" if _is_windows() else "ffprobe")

    def resolve_untrunc(self) -> str:
        return self._resolve_tool(self.untrunc_path, "untrunc.exe" if _is_windows() else "untrunc")

    @staticmethod
    def _resolve_tool(configured_path: str, binary_name: str) -> str:
        bundled = AppSettings._bundled_tool(binary_name)
        if _is_frozen() and bundled.exists():
            return str(bundled)

        if configured_path and Path(configured_path).exists():
            return configured_path

        if bundled.exists():
            return str(bundled)

        found = shutil.which(binary_name)
        if found:
            return found

        fallback_name = binary_name[:-4] if binary_name.lower().endswith(".exe") else binary_name
        return shutil.which(fallback_name) or fallback_name

    @staticmethod
    def _bundled_tool(binary_name: str) -> Path:
        return Path(__file__).resolve().parents[1] / "assets" / "ffmpeg" / binary_name


def _is_windows() -> bool:
    import os

    return os.name == "nt"


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))
