import json
from datetime import datetime
from pathlib import Path


def timestamp_folder_name(prefix: str):
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}_{prefix}"


def ensure_debug_dirs(debug_dir: Path):
    debug_dir.mkdir(parents=True, exist_ok=True)
    (debug_dir / "archive").mkdir(parents=True, exist_ok=True)


def save_latest(debug_dir: Path, results, full_img=None, extra_images=None):
    ensure_debug_dirs(debug_dir)

    if full_img is not None:
      full_img.save(debug_dir / "full_raw.png")

    for result in results:
        result["raw_img"].save(debug_dir / f"{result['source_name']}_raw.png")
        result["ocr_img"].save(debug_dir / f"{result['source_name']}_ocr.png")

    if extra_images:
        for name, pair in extra_images.items():
            if pair.get("raw_img") is not None:
                pair["raw_img"].save(debug_dir / f"{name}_raw.png")
            if pair.get("ocr_img") is not None:
                pair["ocr_img"].save(debug_dir / f"{name}_ocr.png")


def archive_attempt(debug_dir: Path, prefix: str, results, extra_data: dict, full_img=None, extra_images=None):
    ensure_debug_dirs(debug_dir)

    folder = debug_dir / "archive" / timestamp_folder_name(prefix)
    folder.mkdir(parents=True, exist_ok=True)

    if full_img is not None:
        full_img.save(folder / "full_raw.png")

    for result in results:
        result["raw_img"].save(folder / f"{result['source_name']}_raw.png")
        result["ocr_img"].save(folder / f"{result['source_name']}_ocr.png")

    if extra_images:
        for name, pair in extra_images.items():
            if pair.get("raw_img") is not None:
                pair["raw_img"].save(folder / f"{name}_raw.png")
            if pair.get("ocr_img") is not None:
                pair["ocr_img"].save(folder / f"{name}_ocr.png")

    with open(folder / "results.json", "w", encoding="utf-8") as f:
        json.dump(extra_data, f, indent=2)

    return folder