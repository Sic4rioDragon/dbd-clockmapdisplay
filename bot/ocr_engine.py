import re
from PIL import Image, ImageOps
import pytesseract
import mss
from rapidfuzz import process, fuzz

from maps import ALIASES, KNOWN_MAPS


IGNORED_PATTERNS = [
    r"^CRN[_\-A-Z0-9]+$",
    r"^UNKNOWNTILE$",
    r"^[A-Z]{2,}[_\-][A-Z0-9_]+$",
]

IGNORED_EXACT = {
    "TAB",
    "TTAB",
    "BACK",
    "QUIT",
    "ESC",
    "MENU",
    "MAP",
    "DETAILS",
    "MATCHDETAILS",
    "BACKTAB",
    "GRAY",
    "GREY",
    "WHITE",
    "BLACK",
    "BLUE",
    "RED",
    "GREEN",
    "YELLOW",
    "PURPLE",
    "BROWN",
    "ORANGE"
}

REALM_PREFIXES = [
    "WITHERED ISLE",
    "DVARKA DEEPWOOD",
    "ORMOND",
    "BACKWATER SWAMP",
    "YAMAOKA ESTATE",
    "RED FOREST",
    "CROTUS PRENN ASYLUM",
    "CROTUS PREN ASYLUM",
    "COLDWIND FARM",
    "AUTOHAVEN WRECKERS",
    "MACMILLAN ESTATE",
    "FORSAKEN BONEYARD",
    "RACCOON CITY",
    "SPRINGWOOD",
]


def normalize_text(text: str) -> str:
    text = text.upper()
    text = text.replace("|", "I").replace("’", "'")
    text = re.sub(r"[^A-Z0-9' \-_]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" L", " I")
    return text


def alias_key(text: str) -> str:
    return normalize_text(text).replace("'", "").strip()


def normalize_roman_ocr(text: str) -> str:
    text = normalize_text(text)
    replacements = [
        (" 111", " III"),
        (" 11", " II"),
        (" 1V", " IV"),
        (" V1", " VI"),
        (" 1", " I"),
        (" L", " I"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text.strip()


def strip_realm_prefixes(cleaned: str) -> str:
    text = cleaned
    for prefix in REALM_PREFIXES:
        if text.startswith(prefix + " "):
            text = text[len(prefix):].strip()
    return text


def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.resize((img.width * 4, img.height * 4), Image.Resampling.LANCZOS)
    img = img.point(lambda p: 0 if p < 185 else 255)
    return img


def capture_region(sct, region):
    fixed = {
        "left": int(region["left"]),
        "top": int(region["top"]),
        "width": int(region["width"]),
        "height": int(region["height"]),
    }
    shot = sct.grab(fixed)
    return Image.frombytes("RGB", shot.size, shot.rgb)


def is_ignored_text(cleaned: str) -> bool:
    compact = re.sub(r"[^A-Z0-9]", "", cleaned)

    if compact in IGNORED_EXACT:
        return True

    for pattern in IGNORED_PATTERNS:
        if re.fullmatch(pattern, compact):
            return True

    return False


def likely_useful_text(cleaned: str, min_text_length: int) -> bool:
    if is_ignored_text(cleaned):
        return False
    letters_only = re.sub(r"[^A-Z]", "", cleaned)
    return len(letters_only) >= min_text_length


def best_match(raw_text: str, min_text_length: int):
    cleaned = normalize_roman_ocr(raw_text)
    cleaned = strip_realm_prefixes(cleaned)

    if not likely_useful_text(cleaned, min_text_length):
        return None, 0, cleaned

    alias_lookup = {alias_key(k): v for k, v in ALIASES.items()}
    key = alias_key(cleaned)

    if key in alias_lookup and len(re.sub(r"[^A-Z]", "", cleaned)) >= min_text_length:
        return alias_lookup[key], 100, cleaned

    normalized_choices = {name: alias_key(name) for name in KNOWN_MAPS}

    compact_key = re.sub(r"[^A-Z0-9]", "", key)
    compact_choices = {
        name: re.sub(r"[^A-Z0-9]", "", normalized)
        for name, normalized in normalized_choices.items()
    }

    for original, compact in compact_choices.items():
        if compact == compact_key:
            return original, 100, cleaned

    for original, compact in compact_choices.items():
        if compact_key and (compact_key in compact or compact in compact_key):
            return original, 95, cleaned

    best = process.extractOne(
        key,
        normalized_choices.values(),
        scorer=fuzz.WRatio
    )

    if not best:
        return None, 0, cleaned

    matched_normalized, score, _ = best

    for original, normalized in normalized_choices.items():
        if normalized == matched_normalized:
            return original, score, cleaned

    return None, 0, cleaned


def run_region_ocr(sct: mss.mss, settings: dict, source_name: str):
    region = settings["capture_regions"][source_name]
    raw_img = capture_region(sct, region)
    ocr_img = preprocess_for_ocr(raw_img)

    raw_text = pytesseract.image_to_string(
        ocr_img,
        config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' I-_"
    ).strip()

    matched, score, cleaned = best_match(
        raw_text=raw_text,
        min_text_length=settings["min_text_length"]
    )

    return {
        "source_name": source_name,
        "raw_img": raw_img,
        "ocr_img": ocr_img,
        "raw_text": raw_text,
        "cleaned": cleaned,
        "matched": matched,
        "score": score,
    }


def choose_best_result(results, min_confidence):
    valid = [
        r for r in results
        if r["matched"] and r["score"] >= min_confidence
    ]
    if not valid:
        return None

    priority = {
        "tab_map_name": 2,
        "loading_strip": 1,
    }

    valid.sort(
        key=lambda r: (r["score"], priority.get(r["source_name"], 0)),
        reverse=True
    )
    return valid[0]