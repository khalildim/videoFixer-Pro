# Video Fixer Pro

Video Fixer Pro is a Python/PySide6 desktop utility for repairing or recovering damaged MP4, MOV, M4V, and 3GP files. It keeps the original file untouched and writes repaired files to a selected output folder.

Download: https://github.com/khalildim/videoFixer-Pro/releases/latest

[![Buy Me a Coffee](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://buymeacoffee.com/khalil_dim)

## Current Features

- PySide6 desktop GUI with repair, analysis, and settings pages
- English and German interface language support
- Optional CLI mode for backend testing
- FFprobe analysis for duration, streams, codecs, resolution, FPS, and missing `moov` detection
- Repair modes:
  - Auto repair
  - Remux
  - Faststart / `moov` relocation
  - Re-encode
  - Reference-video recovery with `untrunc`
  - Stream extraction and rebuild
- Worker-thread execution so long FFmpeg jobs do not freeze the UI
- Settings for FFmpeg, FFprobe, Untrunc, output folder, default mode, CRF, and preset
- On-screen repair log without saving extra log files beside the videos

## Requirements

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install or configure these external tools:

- `ffmpeg`
- `ffprobe`
- `untrunc` for reference-video repair

The app checks configured paths first, then bundled binaries under `app/assets/ffmpeg/`, then the system `PATH`.

## Run The GUI

```bash
python main.py
```

or:

```bash
python main.py --gui
```

## Run From CLI

```bash
python main.py --input damaged.mp4 --output output --mode auto
```

Optional reference-video recovery:

```bash
python main.py --input damaged.mp4 --output output --reference healthy_reference.mp4 --mode untrunc
```

Available modes are:

```text
auto
remux
faststart
reencode
untrunc
extract
```

## Safety Notes

Video Fixer Pro never modifies the source video. Repair attempts create new output files such as:

```text
video_repaired_remux.mp4
video_repaired_faststart.mp4
video_repaired_reencode.mp4
video_repaired_extracted.mp4
```

MP4 recovery cannot be guaranteed. If media data is missing, no tool can recreate it perfectly. Files missing the `moov` atom often need a healthy reference video recorded with the same device and settings.

## License

Video Fixer Pro is freeware for personal and non-commercial use only. Commercial use, redistribution, republishing, resale, modified builds, or inclusion in another product requires prior written permission. See `LICENSE`.

Bundled third-party binaries have their own licenses. See `THIRD_PARTY_NOTICES.md`.

## Privacy

Video Fixer Pro processes selected videos locally and does not intentionally upload files, collect analytics, show ads, or require an account. See `PRIVACY.md`.
