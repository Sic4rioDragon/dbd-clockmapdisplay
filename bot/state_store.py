import json
import time
from pathlib import Path

from maps import MAP_SLUGS


def build_state(map_name, raw_text, score, port, status, history, source_name=None):
    image_url = None
    if map_name:
        slug = MAP_SLUGS.get(map_name)
        if slug:
            image_url = f"http://127.0.0.1:{port}/maps/{slug}.webp"

    return {
        "status": status,
        "map_name": map_name,
        "raw_text": raw_text,
        "score": score,
        "source_name": source_name,
        "image_url": image_url,
        "history": history,
        "updated_at": int(time.time())
    }


def write_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def append_history(history, entry, max_history):
    history.insert(0, entry)
    del history[max_history:]
    return history