from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".3gp"}


def ensure_output_folder(path: str | Path) -> Path:
    folder = Path(path).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def unique_output_path(input_file: str | Path, output_folder: str | Path, suffix: str, extension: str = ".mp4") -> Path:
    source = Path(input_file)
    folder = ensure_output_folder(output_folder)
    base = source.stem or "video"
    candidate = folder / f"{base}_repaired_{suffix}{extension}"
    index = 2
    while candidate.exists():
        candidate = folder / f"{base}_repaired_{suffix}_{index}{extension}"
        index += 1
    return candidate


def repair_log_path(input_file: str | Path, output_folder: str | Path) -> Path:
    folder = ensure_output_folder(output_folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return folder / f"{Path(input_file).stem}_repair_log_{timestamp}.txt"


def has_enough_space(input_file: str | Path, output_folder: str | Path, multiplier: float = 2.0) -> bool:
    try:
        needed = int(Path(input_file).stat().st_size * multiplier)
        free = shutil.disk_usage(str(output_folder)).free
        return free > needed
    except OSError:
        return False


def open_folder(path: str | Path) -> None:
    folder = Path(path)
    if not folder.is_dir():
        folder = folder.parent
    if os.name == "nt":
        os.startfile(str(folder))  # type: ignore[attr-defined]
    elif sys_platform() == "darwin":
        subprocess.Popen(["open", str(folder)])
    else:
        subprocess.Popen(["xdg-open", str(folder)])


def sys_platform() -> str:
    import sys

    return sys.platform
