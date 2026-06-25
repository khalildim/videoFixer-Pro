from __future__ import annotations


DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {
    "en": "English",
    "de": "Deutsch",
}


TRANSLATIONS = {
    "de": {
        "analyze": "Analysieren",
        "analyze_video": "Video analysieren",
        "analyzing": "Analysiere...",
        "audio_codec": "Audio-Codec",
        "auto_repair": "Automatische Reparatur",
        "browse": "Durchsuchen...",
        "cancel": "Abbrechen",
        "choose_damaged_video_and_output": "Wählen Sie ein beschädigtes Video und einen Ausgabeordner aus.",
        "choose_video_to_analyze": "Wählen Sie eine Videodatei zur Analyse aus.",
        "damaged_video": "Beschädigtes Video",
        "default_crf_quality": "Standard-CRF-Qualität",
        "default_output_folder": "Standard-Ausgabeordner",
        "default_reencode_preset": "Standard-Re-Encode-Voreinstellung",
        "default_repair_mode": "Standard-Reparaturmodus",
        "duration": "Dauer",
        "error": "Fehler",
        "executables_filter": "Programme (*.exe);;Alle Dateien (*.*)",
        "extract_streams": "Streams extrahieren",
        "faststart": "Faststart / moov verschieben",
        "ffmpeg_path": "FFmpeg-Pfad",
        "ffprobe_path": "FFprobe-Pfad",
        "fps": "FPS",
        "hardware_acceleration": "Hardwarebeschleunigung",
        "has_audio": "Hat Audio",
        "has_video": "Hat Video",
        "keep_temporary_files": "Temporäre Dateien behalten",
        "language": "Sprache",
        "missing_file": "Fehlende Datei",
        "missing_input": "Fehlende Eingabe",
        "moov_atom_missing": "Moov-Atom fehlt",
        "no": "Nein",
        "none": "keine",
        "open_output_folder": "Ausgabeordner öffnen",
        "optional": "Optional",
        "output_folder": "Ausgabeordner",
        "overwrite_existing_files": "Vorhandene Dateien überschreiben",
        "path": "Pfad",
        "readable": "Lesbar",
        "ready": "Bereit",
        "recover_with_reference": "Mit Referenzvideo wiederherstellen",
        "reencode": "Re-Encode",
        "reference_video": "Referenzvideo",
        "remux_only": "Nur Remux",
        "repair_complete": "Reparatur abgeschlossen",
        "repair_error": "Reparaturfehler",
        "repair_failed": "Reparatur fehlgeschlagen",
        "repair_mode": "Reparaturmodus",
        "repair_running": "Reparatur läuft...",
        "repair_video": "Video reparieren",
        "resolution": "Auflösung",
        "save_settings": "Einstellungen speichern",
        "select_executable": "Programm auswählen",
        "select_folder": "Ordner auswählen",
        "select_video": "Video auswählen",
        "settings": "Einstellungen",
        "settings_saved": "Einstellungen gespeichert",
        "settings_saved_message": "Die Einstellungen wurden gespeichert.",
        "start_repair": "Reparatur starten",
        "unknown": "unbekannt",
        "untrunc_path": "Untrunc-Pfad",
        "video_codec": "Video-Codec",
        "video_file": "Videodatei",
        "video_filter": "Videodateien (*.mp4 *.mov *.m4v *.3gp);;Alle Dateien (*.*)",
        "yes": "Ja",
    }
}


def normalize_language(language: str | None) -> str:
    if not language:
        return DEFAULT_LANGUAGE
    normalized = language.lower().split("_", 1)[0].split("-", 1)[0]
    return normalized if normalized in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def language_items() -> list[tuple[str, str]]:
    return [(label, code) for code, label in SUPPORTED_LANGUAGES.items()]


def t(key: str, language: str | None = None) -> str:
    code = normalize_language(language)
    if code == DEFAULT_LANGUAGE:
        return _english(key)
    return TRANSLATIONS.get(code, {}).get(key, _english(key))


def _english(key: str) -> str:
    return {
        "analyze": "Analyze",
        "analyze_video": "Analyze Video",
        "analyzing": "Analyzing...",
        "audio_codec": "Audio codec",
        "auto_repair": "Auto repair",
        "browse": "Browse...",
        "cancel": "Cancel",
        "choose_damaged_video_and_output": "Choose a damaged video and an output folder.",
        "choose_video_to_analyze": "Choose a video file to analyze.",
        "damaged_video": "Damaged video",
        "default_crf_quality": "Default CRF quality",
        "default_output_folder": "Default output folder",
        "default_reencode_preset": "Default re-encode preset",
        "default_repair_mode": "Default repair mode",
        "duration": "Duration",
        "error": "Error",
        "executables_filter": "Executables (*.exe);;All files (*.*)",
        "extract_streams": "Extract streams",
        "faststart": "Faststart / moov relocation",
        "ffmpeg_path": "FFmpeg path",
        "ffprobe_path": "FFprobe path",
        "fps": "FPS",
        "hardware_acceleration": "Hardware acceleration",
        "has_audio": "Has audio",
        "has_video": "Has video",
        "keep_temporary_files": "Keep temporary files",
        "language": "Language",
        "missing_file": "Missing file",
        "missing_input": "Missing input",
        "moov_atom_missing": "Moov atom missing",
        "no": "No",
        "none": "none",
        "open_output_folder": "Open Output Folder",
        "optional": "Optional",
        "output_folder": "Output folder",
        "overwrite_existing_files": "Overwrite existing files",
        "path": "Path",
        "readable": "Readable",
        "ready": "Ready",
        "recover_with_reference": "Recover with reference video",
        "reencode": "Re-encode",
        "reference_video": "Reference video",
        "remux_only": "Remux only",
        "repair_complete": "Repair complete",
        "repair_error": "Repair error",
        "repair_failed": "Repair failed",
        "repair_mode": "Repair mode",
        "repair_running": "Repair running...",
        "repair_video": "Repair Video",
        "resolution": "Resolution",
        "save_settings": "Save Settings",
        "select_executable": "Select executable",
        "select_folder": "Select folder",
        "select_video": "Select video",
        "settings": "Settings",
        "settings_saved": "Settings saved",
        "settings_saved_message": "Settings were saved.",
        "start_repair": "Start Repair",
        "unknown": "unknown",
        "untrunc_path": "Untrunc path",
        "video_codec": "Video codec",
        "video_file": "Video file",
        "video_filter": "Video files (*.mp4 *.mov *.m4v *.3gp);;All files (*.*)",
        "yes": "Yes",
    }.get(key, key)
