# Video Fixer Pro — Python MP4 Repair/Recovery App Plan

## 1. Main Idea

The goal is to build a Python desktop application with a **PySide6 GUI** that can repair or recover corrupted MP4/MOV video files.

The app should support several recovery strategies:

1. **Simple remux repair**  
   For videos that are playable but not accepted by editors or some players.

2. **Moov atom relocation / faststart fix**  
   For MP4 files where metadata exists but is placed incorrectly.

3. **Re-encode repair**  
   For videos with broken timestamps, decoding errors, audio/video sync issues, or damaged stream structure.

4. **Truncated MP4 repair using reference video**  
   For damaged MP4/MOV files where the `moov atom` is missing. This often needs a healthy reference video recorded with the same camera/app/settings.

5. **Stream extraction mode**  
   Try to extract readable audio/video streams even if the container is broken.

> Important: MP4 repair cannot be guaranteed 100% for every damaged file. If the actual video data is missing, no software can perfectly recreate it. The goal is to build a robust app that tries multiple recovery methods automatically.

---

## 2. Required Tools and Dependencies

### Python Packages

```bash
pip install PySide6 pymediainfo ffmpeg-python send2trash rich pydantic
```

Optional but useful:

```bash
pip install opencv-python
```

For packaging:

```bash
pip install pyinstaller
```

### External Binaries

The app should either bundle or require these executables:

```text
ffmpeg.exe
ffprobe.exe
untrunc.exe
```

Required tools:

- **FFmpeg**: for remuxing, re-encoding, stream extraction, and rebuilding.
- **FFprobe**: for analyzing video metadata and streams.
- **Untrunc**: for truncated MP4/MOV recovery using a reference video.

---

## 3. Recommended Project Folder Structure

```text
video_repair_app/
│
├── main.py
├── requirements.txt
├── README.md
│
├── app/
│   ├── __init__.py
│   │
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── repair_page.py
│   │   ├── analysis_page.py
│   │   ├── settings_page.py
│   │   ├── widgets.py
│   │   └── styles.qss
│   │
│   ├── core/
│   │   ├── analyzer.py
│   │   ├── repair_engine.py
│   │   ├── ffmpeg_runner.py
│   │   ├── untrunc_runner.py
│   │   ├── recovery_methods.py
│   │   ├── file_utils.py
│   │   └── validators.py
│   │
│   ├── workers/
│   │   ├── repair_worker.py
│   │   └── analysis_worker.py
│   │
│   ├── models/
│   │   ├── video_info.py
│   │   ├── repair_result.py
│   │   └── app_settings.py
│   │
│   └── assets/
│       ├── icons/
│       └── ffmpeg/
│           ├── ffmpeg.exe
│           ├── ffprobe.exe
│           └── untrunc.exe
│
└── output/
```

---

## 4. GUI Design with PySide6

Use **PySide6 Widgets** first. It is easier than QML for this type of desktop utility.

### Main Window Layout

```text
--------------------------------------------------
| Video Fixer Pro                                 |
--------------------------------------------------
| Sidebar              | Main Content             |
|                      |                          |
|  1. Repair Video     | Drag & Drop damaged file |
|  2. Analyze Video    | Select reference video   |
|  3. Batch Repair     | Choose repair mode       |
|  4. Settings         | Start repair             |
|                      | Progress + logs          |
--------------------------------------------------
```

### Repair Page Components

```text
[Damaged video file]  Browse...
[Reference video]     Browse... optional
[Output folder]       Browse...

Repair mode:
( ) Auto repair
( ) Remux only
( ) Faststart / moov relocation
( ) Re-encode
( ) Recover with reference video
( ) Extract streams

[Analyze] [Start Repair] [Cancel]

Progress bar
Log window
Result status
Open output folder button
```

### Important GUI Rule

Long tasks like FFmpeg repair must not run directly in the GUI thread.

Use:

- `QThread`
- `QObject` worker
- Qt signals and slots
- or `QProcess`

Otherwise, the app will freeze while repairing.

---

## 5. Core Repair Workflow

### Step 1 — Validate Input

Check:

```text
- File exists
- Extension is .mp4, .mov, .m4v, .3gp
- File size > 0
- Output folder exists
- Enough disk space
- ffmpeg/ffprobe available
- untrunc available if reference repair is selected
```

### Step 2 — Analyze Damaged Video

Use FFprobe:

```bash
ffprobe -v error -show_format -show_streams damaged.mp4
```

Possible analysis results:

```text
Case A: ffprobe reads file successfully
→ Try remux or re-encode.

Case B: moov atom not found
→ Try untrunc with reference video.

Case C: invalid data found
→ Try stream extraction or re-encode.

Case D: no readable streams
→ File may be too damaged.
```

The MP4 `moov atom` contains important metadata needed for normal playback. If it is missing, many players/editors cannot open the file correctly. Some cases can be fixed by relocating metadata, but truly missing metadata often requires a reference-video method.

---

## 6. Repair Methods to Implement

## Method 1 — Remux Repair

Use when the video is readable but the container has problems.

### Command

```bash
ffmpeg -y -err_detect ignore_err -i damaged.mp4 -c copy repaired_remux.mp4
```

### Python Function

```python
def repair_remux(input_file, output_file):
    cmd = [
        "ffmpeg", "-y",
        "-err_detect", "ignore_err",
        "-i", input_file,
        "-c", "copy",
        output_file
    ]
    return run_command(cmd)
```

---

## Method 2 — Faststart / Moov Relocation

Use when the file plays but has problems in browsers, websites, or editing software.

### Command

```bash
ffmpeg -y -i input.mp4 -c copy -movflags +faststart output.mp4
```

### Python Function

```python
def repair_faststart(input_file, output_file):
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-c", "copy",
        "-movflags", "+faststart",
        output_file
    ]
    return run_command(cmd)
```

---

## Method 3 — Re-encode Repair

Use when remux fails.

### Command

```bash
ffmpeg -y -err_detect ignore_err -i damaged.mp4 -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 160k repaired_encoded.mp4
```

### Python Function

```python
def repair_reencode(input_file, output_file):
    cmd = [
        "ffmpeg", "-y",
        "-err_detect", "ignore_err",
        "-i", input_file,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "160k",
        output_file
    ]
    return run_command(cmd)
```

---

## Method 4 — Untrunc Repair with Reference Video

Use when:

```text
- moov atom is missing
- file is truncated
- video came from phone, dashcam, camera, drone, OBS, etc.
- user has another working video from the same device/settings
```

### Command

```bash
untrunc good_reference.mp4 broken_video.mp4
```

### Python Function

```python
def repair_with_untrunc(reference_file, damaged_file, output_folder):
    cmd = [
        "untrunc",
        reference_file,
        damaged_file
    ]
    return run_command(cmd, cwd=output_folder)
```

The reference video should come from the same camera/app and should use the same or very similar:

```text
- resolution
- codec
- FPS
- audio settings
- recording mode
```

---

## Method 5 — Extract Streams

Use when the MP4 container is broken but some video/audio stream data is still readable.

### Extract Video

```bash
ffmpeg -y -err_detect ignore_err -i damaged.mp4 -map 0:v:0 -c copy video_track.h264
```

### Extract Audio

```bash
ffmpeg -y -err_detect ignore_err -i damaged.mp4 -map 0:a:0 -c copy audio_track.aac
```

### Rebuild MP4

```bash
ffmpeg -y -r 30 -i video_track.h264 -i audio_track.aac -c copy rebuilt.mp4
```

---

## 7. Auto Repair Logic

```text
User selects damaged video
        |
        v
Run ffprobe
        |
        +-- readable?
        |      |
        |      +-- yes → try remux
        |              |
        |              +-- success → verify output
        |              |
        |              +-- fail → try re-encode
        |
        +-- moov atom missing?
        |      |
        |      +-- reference video available?
        |              |
        |              +-- yes → try untrunc
        |              |
        |              +-- no → ask user for reference video
        |
        +-- still failed?
               |
               +-- try extraction mode
               |
               +-- final report
```

### Auto Repair Pseudo-code

```python
def auto_repair(input_file, output_folder, reference_file=None):
    analysis = analyze_video(input_file)

    if analysis.is_readable:
        result = repair_remux(input_file, output_folder)
        if result.success and verify_output(result.output_file):
            return result

        result = repair_faststart(input_file, output_folder)
        if result.success and verify_output(result.output_file):
            return result

        result = repair_reencode(input_file, output_folder)
        if result.success and verify_output(result.output_file):
            return result

    if analysis.moov_atom_missing:
        if reference_file:
            result = repair_with_untrunc(reference_file, input_file, output_folder)
            if result.success:
                return result
        else:
            return RepairResult(
                success=False,
                method="reference_required",
                output_file=None,
                message="This file likely needs a reference video from the same device.",
                log=analysis.error_message or ""
            )

    result = extract_streams(input_file, output_folder)
    return result
```

---

## 8. Data Models

### VideoInfo

```python
from dataclasses import dataclass

@dataclass
class VideoInfo:
    path: str
    readable: bool
    duration: float | None
    codec_video: str | None
    codec_audio: str | None
    width: int | None
    height: int | None
    fps: float | None
    has_audio: bool
    has_video: bool
    error_message: str | None
    moov_atom_missing: bool
```

### RepairResult

```python
from dataclasses import dataclass

@dataclass
class RepairResult:
    success: bool
    method: str
    output_file: str | None
    message: str
    log: str
```

### RepairJob

```python
from dataclasses import dataclass

@dataclass
class RepairJob:
    input_file: str
    output_folder: str
    reference_file: str | None
    mode: str
```

---

## 9. Worker System for PySide6

Use a worker so the GUI does not freeze.

```python
from PySide6.QtCore import QObject, Signal

class RepairWorker(QObject):
    progress = Signal(int)
    log = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, job):
        super().__init__()
        self.job = job
        self.cancel_requested = False

    def run(self):
        try:
            result = auto_repair(
                input_file=self.job.input_file,
                output_folder=self.job.output_folder,
                reference_file=self.job.reference_file
            )
            self.finished.emit(result)
        except Exception as e:
            self.failed.emit(str(e))
```

### FFmpeg Progress Parsing

FFmpeg outputs progress information in stderr, for example:

```text
time=00:01:20.00
```

To show progress:

1. Get full video duration from FFprobe.
2. Parse current `time=`.
3. Convert it to seconds.
4. Calculate:

```text
progress = current_time / total_duration * 100
```

---

## 10. GUI Safety Features

The app should never overwrite the original file.

Required safety features:

```text
- Always create a new output file
- Original file stays untouched
- Output filename includes the repair method
- Save repair log
- Ask before replacing existing output
- Cancel button
- Crash-safe temporary folder
- Clear warning when reference video is required
```

Example output files:

```text
video_repaired_remux.mp4
video_repaired_faststart.mp4
video_repaired_reencode.mp4
video_repaired_untrunc.mp4
video_repair_log.txt
```

---

## 11. User-Friendly Error Messages

Examples:

```text
"FFmpeg can read the file. Trying remux repair..."
"Remux failed. Trying faststart repair..."
"Faststart failed. Trying full re-encode..."
"Moov atom missing. Please choose a healthy reference video from the same camera."
"Recovery completed, but output has warnings."
"Repair failed. The media data may be missing or too damaged."
"FFmpeg was not found. Please configure the FFmpeg path in Settings."
"Output folder does not have enough free space."
```

---

## 12. Settings Page

Include these settings:

```text
FFmpeg path
FFprobe path
Untrunc path
Default output folder
Default repair mode
Overwrite existing files: yes/no
Keep temporary files: yes/no
Theme: light/dark
Hardware acceleration: yes/no
Default CRF quality
Default re-encode preset
```

Recommended re-encode presets:

```text
ultrafast
superfast
veryfast
faster
fast
medium
slow
slower
veryslow
```

Recommended CRF values:

```text
18 = high quality, larger file
23 = default good balance
28 = smaller file, lower quality
```

---

## 13. Batch Repair Page

Later, add batch repair mode.

Features:

```text
- Drag multiple MP4/MOV files
- Choose output folder
- Use same repair mode for all
- Optional same reference video
- Show table with results
```

Table columns:

```text
File | Status | Method | Output | Error
```

---

## 14. Testing Plan

Prepare damaged test files:

```text
1. Healthy MP4
2. MP4 with moov atom at end
3. Truncated MP4
4. MP4 with broken timestamps
5. MP4 without audio
6. MOV from iPhone
7. Dashcam MP4
8. Large file > 5 GB
9. Empty/corrupt fake MP4
10. Video with only audio stream
```

Test cases:

```text
- App does not freeze
- Cancel button works
- Logs are saved
- Output is playable
- Original file is untouched
- App handles missing FFmpeg
- App handles missing FFprobe
- App handles missing reference video
- App handles invalid file
- App handles non-ASCII paths
- App handles very large files
- App handles output folder permission problems
```

---

## 15. Development Roadmap

### Phase 1 — CLI Backend First

Before building the GUI, create and test:

```text
analyzer.py
ffmpeg_runner.py
repair_engine.py
validators.py
```

Goal:

```text
python main.py --input damaged.mp4 --output output/
```

---

### Phase 2 — Basic PySide6 GUI

Add:

```text
file picker
output folder picker
repair mode selector
start button
log box
progress bar
```

---

### Phase 3 — Worker Threads

Move repair processes into a worker thread.

Use:

```text
QThread
Signal
Slot
QObject worker
```

---

### Phase 4 — Auto Repair Engine

Implement:

```text
analyze → choose method → repair → verify → report
```

---

### Phase 5 — Reference Video Repair

Add `untrunc` integration.

---

### Phase 6 — Batch Mode

Add support for multiple files.

---

### Phase 7 — Packaging

Use PyInstaller:

```bash
pyinstaller --noconfirm --windowed --name VideoFixerPro main.py
```

Bundle:

```text
ffmpeg.exe
ffprobe.exe
untrunc.exe
```

---

## 16. Best Repair Logic Summary

Recommended repair order:

```text
1. Analyze with ffprobe
2. Try remux
3. Try faststart
4. Try re-encode
5. If moov atom is missing → use untrunc with reference video
6. Try stream extraction
7. Verify output
8. Generate final report
```

---

## 17. Minimum Version Features

For the first working version, implement only:

```text
- One damaged video input
- Optional reference video input
- Output folder selection
- Auto repair mode
- FFprobe analysis
- Remux repair
- Faststart repair
- Re-encode repair
- Untrunc repair
- Log window
- Progress bar
- Open output folder button
```

Avoid adding batch repair and advanced settings before the basic repair workflow works correctly.

---

## 18. Future Advanced Features

Possible future improvements:

```text
- Batch repair
- Preview repaired video inside the app
- Automatic camera profile detection
- Compare damaged video with reference video
- Save repair history
- Export repair report as PDF
- Dark/light theme
- Drag-and-drop files
- Automatic FFmpeg binary detection
- Hardware acceleration with NVIDIA/Intel/AMD
- Language support: English, German, French
```

---

## 19. Final Architecture Overview

```text
GUI Layer
│
├── main_window.py
├── repair_page.py
├── settings_page.py
│
Worker Layer
│
├── repair_worker.py
├── analysis_worker.py
│
Core Layer
│
├── analyzer.py
├── repair_engine.py
├── ffmpeg_runner.py
├── untrunc_runner.py
├── recovery_methods.py
├── validators.py
│
Model Layer
│
├── VideoInfo
├── RepairResult
├── RepairJob
│
External Tools
│
├── ffmpeg
├── ffprobe
└── untrunc
```

---

## 20. Final Notes

The most important part of this app is not the GUI. The most important part is the **repair engine** and the **automatic decision logic**.

A professional app should:

```text
- never modify the original file
- try multiple repair methods
- save detailed logs
- explain clearly why repair failed
- support reference-video recovery
- verify the repaired output
- keep the GUI responsive
```

This plan gives a strong foundation for building a real MP4 repair/recovery desktop app in Python with PySide6.
