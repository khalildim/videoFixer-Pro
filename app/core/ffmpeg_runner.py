from __future__ import annotations

import re
import subprocess
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ProgressCallback = Callable[[int], None]
LogCallback = Callable[[str], None]


def _creation_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0


@dataclass(frozen=True)
class CommandResult:
    return_code: int
    output: str

    @property
    def success(self) -> bool:
        return self.return_code == 0


def run_command(
    cmd: list[str],
    cwd: str | Path | None = None,
    log_callback: LogCallback | None = None,
    progress_callback: ProgressCallback | None = None,
    duration: float | None = None,
    cancel_event: threading.Event | None = None,
) -> CommandResult:
    command_text = " ".join(_quote(part) for part in cmd)
    if log_callback:
        log_callback(f"$ {command_text}")

    process = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=_creation_flags(),
    )

    lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        stripped = line.rstrip()
        lines.append(stripped)
        if log_callback and stripped:
            log_callback(stripped)
        if progress_callback and duration:
            parsed = parse_ffmpeg_time(stripped)
            if parsed is not None:
                progress_callback(max(0, min(99, int(parsed / duration * 100))))
        if cancel_event and cancel_event.is_set():
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            lines.append("Cancelled by user.")
            return CommandResult(return_code=130, output="\n".join(lines))

    return_code = process.wait()
    if log_callback:
        log_callback(f"Process exited with code {return_code}.")
        if return_code != 0 and not any(line.strip() for line in lines):
            log_callback("The process did not print an error message.")
    if progress_callback and return_code == 0:
        progress_callback(100)
    return CommandResult(return_code=return_code, output="\n".join(lines))


def run_capture(cmd: list[str], timeout: int = 60) -> CommandResult:
    try:
        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            creationflags=_creation_flags(),
        )
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        return CommandResult(return_code=124, output=str(output))
    except OSError as exc:
        return CommandResult(return_code=127, output=str(exc))
    return CommandResult(return_code=completed.returncode, output=completed.stdout)


def parse_ffmpeg_time(line: str) -> float | None:
    match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", line)
    if not match:
        return None
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _quote(part: str) -> str:
    if " " in part or "\t" in part:
        return f'"{part}"'
    return part
