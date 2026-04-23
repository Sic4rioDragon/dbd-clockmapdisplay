import json
import os
import time
from pathlib import Path

from maps import MAP_SLUGS


def build_state(map_name, raw_text, score, port, status, history, source_name=None, automation=None):
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
        "automation": automation or {},
        "updated_at": int(time.time())
    }


def write_state(path: Path, state: dict, retries: int = 8, delay: float = 0.03):
    path.parent.mkdir(parents=True, exist_ok=True)

    data = json.dumps(state, indent=2)
    tmp_path = path.with_suffix(".tmp")

    last_error = None

    for attempt in range(retries):
        try:
            with open(tmp_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())

            os.replace(tmp_path, path)
            return
        except PermissionError as e:
            last_error = e
            time.sleep(delay)
        except OSError as e:
            last_error = e
            time.sleep(delay)

    # fallback: try writing directly if atomic replace keeps getting blocked
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        return
    except Exception as e:
        last_error = e

    raise last_error


def append_history(history, entry, max_history):
    history.insert(0, entry)
    del history[max_history:]
    return history