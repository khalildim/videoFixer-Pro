from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepairResult:
    success: bool
    method: str
    output_file: str | None
    message: str
    log: str = ""
    log_file: str | None = None


@dataclass(frozen=True)
class RepairJob:
    input_file: str
    output_folder: str
    reference_file: str | None = None
    mode: str = "auto"
