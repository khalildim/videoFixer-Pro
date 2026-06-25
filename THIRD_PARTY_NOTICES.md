# Third-Party Notices

This repository may include bundled third-party binaries under `app/assets/ffmpeg/` for user convenience. These binaries are not licensed under the VideoFixer Pro application license.

## FFmpeg And FFprobe

Bundled files:

- `ffmpeg.exe`
- `ffprobe.exe`

Source: https://www.gyan.dev/ffmpeg/builds/

FFmpeg is licensed under LGPLv2.1-or-later or GPLv2-or-later depending on build options. The bundled Gyan.dev build used here reports `--enable-gpl` in its configuration, so treat these FFmpeg/FFprobe binaries as GPL-covered binaries.

Official FFmpeg license information: https://ffmpeg.org/legal.html

## Untrunc

Bundled files:

- `untrunc.exe`
- required runtime DLL files shipped with the Windows build

Source: https://github.com/anthwlock/untrunc

Untrunc and its bundled runtime/library files are distributed under their own upstream licenses. Keep upstream license files and source links available when distributing packaged builds.

## Application Code

The VideoFixer Pro application is freeware for personal and non-commercial use only. See `LICENSE`.
