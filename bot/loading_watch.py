from PIL import ImageStat

from ocr_engine import capture_region


def _brightness(rgb):
    r, g, b = rgb
    return (r + g + b) / 3.0


def is_loading_bar_present(sct, settings):
    region = settings["capture_regions"]["loading_strip"]
    img = capture_region(sct, region)

    points = settings.get("black_bar_sample_points", [])
    threshold = settings.get("black_bar_brightness_threshold", 32)
    required_dark = settings.get("black_bar_required_dark_points", 5)

    dark_count = 0
    sampled = []

    for x, y in points:
        if x < 0 or y < 0 or x >= img.width or y >= img.height:
            continue
        pixel = img.getpixel((x, y))
        bright = _brightness(pixel)
        sampled.append((x, y, int(bright)))
        if bright <= threshold:
            dark_count += 1

    return {
        "matched": dark_count >= required_dark,
        "dark_count": dark_count,
        "sampled": sampled,
        "raw_img": img
    }