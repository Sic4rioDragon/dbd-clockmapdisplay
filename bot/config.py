import json
from pathlib import Path


BOT_DIR = Path(__file__).resolve().parent


def deep_update(base: dict, override: dict) -> dict:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_settings():
    base_path = BOT_DIR / "settings.json"
    local_path = BOT_DIR / "settings.local.json"

    settings = load_json(base_path)

    if local_path.exists():
        local_settings = load_json(local_path)
        settings = deep_update(settings, local_settings)

    settings["paths"]["output_json"] = (BOT_DIR / settings["paths"]["output_json"]).resolve()
    settings["paths"]["overlay_dir"] = (BOT_DIR / settings["paths"]["overlay_dir"]).resolve()
    settings["paths"]["maps_dir"] = (BOT_DIR / settings["paths"]["maps_dir"]).resolve()
    settings["paths"]["debug_dir"] = (BOT_DIR / settings["paths"]["debug_dir"]).resolve()

    return settings