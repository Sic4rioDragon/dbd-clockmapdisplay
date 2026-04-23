import json
from pathlib import Path


BOT_DIR = Path(__file__).resolve().parent


DEFAULTS = {
    "poll_interval_ms": 1800,
    "min_confidence": 88,
    "min_text_length": 6,
    "required_confirmations": 2,
    "http_host": "127.0.0.1",
    "http_port": 8765,
    "clear_after_seconds": 20,
    "save_debug_images": True,
    "debug_dir": "../output/debug",
    "status_text": "DBD map OCR running - waiting for map",
    "max_history": 15,
    "manual_hotkey": "F8",
}


def load_settings():
    path = BOT_DIR / "settings.json"
    with open(path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    merged = {**DEFAULTS, **settings}

    merged["output_json"] = (BOT_DIR / merged["output_json"]).resolve()
    merged["overlay_dir"] = (BOT_DIR / merged["overlay_dir"]).resolve()
    merged["maps_dir"] = (BOT_DIR / merged["maps_dir"]).resolve()
    merged["debug_dir"] = (BOT_DIR / merged["debug_dir"]).resolve()

    return merged