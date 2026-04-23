import re
from PIL import Image, ImageOps
import pytesseract

from ocr_engine import capture_region


def preprocess_continue_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.resize((img.width * 3, img.height * 3), Image.Resampling.LANCZOS)
    img = img.point(lambda p: 0 if p < 170 else 255)
    return img


def detect_continue_button(sct, settings):
    region = settings["capture_regions"]["continue_button"]
    raw_img = capture_region(sct, region)
    ocr_img = preprocess_continue_ocr(raw_img)

    raw_text = pytesseract.image_to_string(
        ocr_img,
        config="--psm 7 -c tessedit_char_whitelist=CONTINUEABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ).strip()

    cleaned = re.sub(r"[^A-Z]", "", raw_text.upper())

    matched = "CONTINUE" in cleaned
    return {
        "matched": matched,
        "raw_text": raw_text,
        "cleaned": cleaned,
        "raw_img": raw_img,
        "ocr_img": ocr_img,
    }


def get_clear_after_seconds(settings):
    mode = settings.get("mode", "testing").lower()
    if mode == "normal":
        return int(settings.get("clear_after_seconds_normal", 300))
    return int(settings.get("clear_after_seconds_testing", 60))