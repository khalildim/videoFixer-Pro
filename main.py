from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.core.repair_engine import run_repair
from app.models.app_settings import AppSettings
from app.models.repair_result import RepairJob


def run_cli(args: argparse.Namespace) -> int:
    settings = AppSettings.load()
    job = RepairJob(
        input_file=str(Path(args.input).expanduser()),
        output_folder=str(Path(args.output).expanduser()),
        reference_file=str(Path(args.reference).expanduser()) if args.reference else None,
        mode=args.mode,
    )

    def log(message: str) -> None:
        print(message, flush=True)

    def progress(value: int) -> None:
        print(f"Progress: {value}%", flush=True)

    result = run_repair(job, settings=settings, log_callback=log, progress_callback=progress)
    print()
    print(result.message)
    if result.output_file:
        print(f"Output: {result.output_file}")
    if result.log_file:
        print(f"Log: {result.log_file}")
    return 0 if result.success else 1


def run_gui() -> int:
    try:
        from PySide6.QtWidgets import QApplication

        from app.gui.main_window import MainWindow
    except ImportError as exc:
        print("PySide6 is required for the desktop GUI. Install dependencies with:")
        print("  pip install -r requirements.txt")
        print(f"Import error: {exc}")
        return 1

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Video Fixer Pro MP4/MOV repair utility")
    parser.add_argument("--input", help="Damaged video file")
    parser.add_argument("--output", help="Output folder")
    parser.add_argument("--reference", help="Optional healthy reference video")
    parser.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "remux", "faststart", "reencode", "untrunc", "extract"],
        help="Repair mode",
    )
    parser.add_argument("--gui", action="store_true", help="Force GUI mode")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.gui or not args.input:
        return run_gui()
    if not args.output:
        parser.error("--output is required when --input is provided")
    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
