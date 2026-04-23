import json
import re
import time
import threading
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial

import mss
import pytesseract
from PIL import Image, ImageOps
from rapidfuzz import process, fuzz


BOT_DIR = Path(__file__).resolve().parent


MAP_SLUGS = {
    "Azarov's Resting Place": "azarovs-resting-place",
    "Blood Lodge": "blood-lodge",
    "Gas Heaven": "gas-heaven",
    "Wreckers' Yard": "wreckers-yard",
    "Wretched Shop": "wretched-shop",

    "Badham Preschool I": "badham-preschool-i",
    "Badham Preschool II": "badham-preschool-ii",
    "Badham Preschool III": "badham-preschool-iii",
    "Badham Preschool IV": "badham-preschool-iv",
    "Badham Preschool V": "badham-preschool-v",

    "Fractured Cowshed": "fractured-cowshed",
    "Rancid Abattoir": "rancid-abattoir",
    "Rotten Fields": "rotten-fields",
    "Thompson House": "thompson-house",
    "Torment Creek": "torment-creek",

    "Disturbed Ward": "disturbed-ward",
    "Father Campbell's Chapel": "father-campbells-chapel",

    "Nostromo Wreckage": "nostromo-wreckage",
    "Toba Landing": "toba-landing",

    "Dead Sands": "dead-sands",
    "Eyrie of Crows": "eyrie-of-crows",

    "Coal Tower I": "coal-tower-i",
    "Coal Tower II": "coal-tower-ii",
    "Groaning Storehouse I": "groaning-storehouse-i",
    "Groaning Storehouse II": "groaning-storehouse-ii",
    "Ironworks of Misery I": "ironworks-of-misery-i",
    "Ironworks of Misery II": "ironworks-of-misery-ii",
    "Shelter Woods I": "shelter-woods-i",
    "Shelter Woods II": "shelter-woods-ii",
    "Suffocation Pit I": "suffocation-pit-i",
    "Suffocation Pit II": "suffocation-pit-ii",

    "Mount Ormond Resort I": "mount-ormond-resort-i",
    "Mount Ormond Resort II": "mount-ormond-resort-ii",
    "Mount Ormond Resort III": "mount-ormond-resort-iii",
    "Ormond Lake Mine": "ormond-lake-mine",

    "Dead Dawg Saloon": "dead-dawg-saloon",
    "Haddonfield": "haddonfield",
    "Hawkins National Laboratory": "hawkins-national-laboratory",
    "Lery's Memorial Institute": "lerys-memorial-institute",
    "Midwich Elementary School": "midwich-elementary-school",
    "The Game": "the-game",

    "Raccoon City Police Station East Wing": "raccoon-city-police-station-east-wing",
    "Raccoon City Police Station West Wing": "raccoon-city-police-station-west-wing",

    "Mother's Dwelling": "mothers-dwelling",
    "Temple of Purgation": "temple-of-purgation",

    "Trickster's Delusion": "tricksters-delusion",

    "Grim Pantry": "grim-pantry",
    "Pale Rose": "pale-rose",

    "Forgotten Ruins": "forgotten-ruins",
    "Shattered Square": "shattered-square",

    "Fallen Refuge": "fallen-refuge",
    "Freddy Fazbear's Pizza": "freddy-fazbears-pizza",
    "Garden of Joy": "garden-of-joy",
    "Greenville Square": "greenville-square",

    "Family Residence": "family-residence",
    "Sanctum of Wrath": "sanctum-of-wrath",
}

KNOWN_MAPS = list(MAP_SLUGS.keys())

ALIASES = {
    "AZAROVS RESTING PLACE": "Azarov's Resting Place",
    "AZAROV S RESTING PLACE": "Azarov's Resting Place",
    "WRECKERS": "Wreckers' Yard",
    "WRECKERS YARD": "Wreckers' Yard",

    "COAL TOWER": "Coal Tower I",
    "COAL TOWER 1": "Coal Tower I",
    "COAL TOWER I": "Coal Tower I",
    "COAL TOWER L": "Coal Tower I",
    "COAL TOWER 11": "Coal Tower II",
    "COAL TOWER 2": "Coal Tower II",
    "COAL TOWER II": "Coal Tower II",

    "GROANING STOREHOUSE": "Groaning Storehouse I",
    "GROANING STOREHOUSE 1": "Groaning Storehouse I",
    "GROANING STOREHOUSE I": "Groaning Storehouse I",
    "GROANING STOREHOUSE 11": "Groaning Storehouse II",
    "GROANING STOREHOUSE 2": "Groaning Storehouse II",
    "GROANING STOREHOUSE II": "Groaning Storehouse II",

    "IRONWORKS OF MISERY": "Ironworks of Misery I",
    "IRONWORKS OF MISERY 1": "Ironworks of Misery I",
    "IRONWORKS OF MISERY I": "Ironworks of Misery I",
    "IRONWORKS OF MISERY 11": "Ironworks of Misery II",
    "IRONWORKS OF MISERY 2": "Ironworks of Misery II",
    "IRONWORKS OF MISERY II": "Ironworks of Misery II",

    "SHELTER WOODS": "Shelter Woods I",
    "SHELTER WOODS 1": "Shelter Woods I",
    "SHELTER WOODS I": "Shelter Woods I",
    "SHELTER WOODS 11": "Shelter Woods II",
    "SHELTER WOODS 2": "Shelter Woods II",
    "SHELTER WOODS II": "Shelter Woods II",

    "SUFFOCATION PIT": "Suffocation Pit I",
    "SUFFOCATION PIT 1": "Suffocation Pit I",
    "SUFFOCATION PIT I": "Suffocation Pit I",
    "SUFFOCATION PIT 11": "Suffocation Pit II",
    "SUFFOCATION PIT 2": "Suffocation Pit II",
    "SUFFOCATION PIT II": "Suffocation Pit II",

    "FATHER CAMPBELLS CHAPEL": "Father Campbell's Chapel",
    "FATHER CAMPBELL S CHAPEL": "Father Campbell's Chapel",

    "DEAD DOG SALOON": "Dead Dawg Saloon",
    "DEAD DAWG SALOON": "Dead Dawg Saloon",

    "THE THOMPSON HOUSE": "Thompson House",
    "THOMPSON HOUSE": "Thompson House",

    "RANCID ABBATOIR": "Rancid Abattoir",
    "RANCID ABATTOIR": "Rancid Abattoir",

    "ORMOND": "Mount Ormond Resort I",
    "ORMOND 1": "Mount Ormond Resort I",
    "ORMOND I": "Mount Ormond Resort I",
    "ORMOND II": "Mount Ormond Resort II",
    "ORMOND 2": "Mount Ormond Resort II",
    "ORMOND III": "Mount Ormond Resort III",
    "ORMOND 3": "Mount Ormond Resort III",
    "ORMOND LAKE MINE": "Ormond Lake Mine",
    "MOUNT ORMOND RESORT": "Mount Ormond Resort I",

    "MIDWICH": "Midwich Elementary School",
    "MIDWICH ELEMENTARY SCHOOL": "Midwich Elementary School",

    "LERYS": "Lery's Memorial Institute",
    "LERYS MEMORIAL INSTITUTE": "Lery's Memorial Institute",

    "RPD EAST WING": "Raccoon City Police Station East Wing",
    "RPD WEST WING": "Raccoon City Police Station West Wing",

    "THE SHATTERED SQUARE": "Shattered Square",
    "SHATTERED SQUARE": "Shattered Square",

    "MOTHERS DWELLING": "Mother's Dwelling",
    "MOTHER S DWELLING": "Mother's Dwelling",

    "NOSTROMO WRECKAGE": "Nostromo Wreckage",
    "GREENVILLE SQUARE": "Greenville Square",
    "FORGOTTEN RUINS": "Forgotten Ruins",
    "THE GAME": "The Game",
    "GARDEN OF JOY": "Garden of Joy",
    "EYRIE OF CROWS": "Eyrie of Crows",
    "TEMPLE OF PURGATION": "Temple of Purgation",
    "FAMILY RESIDENCE": "Family Residence",
    "SANCTUM OF WRATH": "Sanctum of Wrath",
    "HADDONFIELD": "Haddonfield",
    "HAWKINS": "Hawkins National Laboratory",
    "GRIM PANTRY": "Grim Pantry",
    "PALE ROSE": "Pale Rose",
    "TOBA LANDING": "Toba Landing",
    "DEAD SANDS": "Dead Sands",
    "FALLEN REFUGE": "Fallen Refuge",
    "FREDDY FAZBEARS PIZZA": "Freddy Fazbear's Pizza",
    "TRICKSTERS DELUSION": "Trickster's Delusion",
}


def load_settings():
    path = BOT_DIR / "settings.json"
    with open(path, "r", encoding="utf-8") as f:
        settings = json.load(f)

    settings["output_json"] = (BOT_DIR / settings["output_json"]).resolve()
    settings["overlay_dir"] = (BOT_DIR / settings["overlay_dir"]).resolve()
    settings["maps_dir"] = (BOT_DIR / settings["maps_dir"]).resolve()
    settings["debug_dir"] = (BOT_DIR / settings.get("debug_dir", "../output/debug")).resolve()
    settings["status_text"] = settings.get("status_text", "DBD map OCR running - waiting for map")
    settings["max_history"] = int(settings.get("max_history", 15))
    return settings


def normalize_text(text: str) -> str:
    text = text.upper()
    text = text.replace("|", "I").replace("’", "'")
    text = re.sub(r"[^A-Z0-9' ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" L", " I")
    return text


def alias_key(text: str) -> str:
    return normalize_text(text).replace("'", "").strip()


def normalize_roman_ocr(text: str) -> str:
    text = normalize_text(text)
    for old, new in [
        (" 111", " III"),
        (" 11", " II"),
        (" 1V", " IV"),
        (" V1", " VI"),
        (" 1", " I"),
        (" L", " I"),
    ]:
        text = text.replace(old, new)
    return text.strip()


def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.resize((img.width * 4, img.height * 4), Image.Resampling.LANCZOS)
    img = img.point(lambda p: 0 if p < 180 else 255)
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


def best_match(raw_text: str):
    cleaned = normalize_roman_ocr(raw_text)
    key = alias_key(cleaned)

    alias_lookup = {alias_key(k): v for k, v in ALIASES.items()}
    if key in alias_lookup:
        return alias_lookup[key], 100, cleaned

    normalized_choices = {name: alias_key(name) for name in KNOWN_MAPS}
    best = process.extractOne(key, normalized_choices.values(), scorer=fuzz.WRatio)

    if not best:
        return None, 0, cleaned

    matched_normalized, score, _ = best
    for original, normalized in normalized_choices.items():
        if normalized == matched_normalized:
            return original, score, cleaned

    return None, 0, cleaned


def build_state(map_name, raw_text, score, port, status, history):
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
        "image_url": image_url,
        "history": history,
        "updated_at": int(time.time())
    }


def write_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


class OverlayRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, overlay_dir=None, maps_dir=None, output_json=None, **kwargs):
        self.overlay_dir = Path(overlay_dir)
        self.maps_dir = Path(maps_dir)
        self.output_json = Path(output_json)
        super().__init__(*args, directory=str(self.overlay_dir), **kwargs)

    def do_GET(self):
        if self.path in ["/", "/index.html"]:
            self.path = "/overlay.html"
            return super().do_GET()

        if self.path == "/current_map.json":
            if self.output_json.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(self.output_json.read_bytes())
                return
            self.send_response(404)
            self.end_headers()
            return

        if self.path.startswith("/maps/"):
            filename = self.path[len("/maps/"):].lstrip("/")
            target = self.maps_dir / filename
            if target.exists() and target.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "image/webp")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(target.read_bytes())
                return
            self.send_response(404)
            self.end_headers()
            return

        return super().do_GET()

    def log_message(self, format, *args):
        return


def start_http_server(settings):
    host = settings["http_host"]
    port = settings["http_port"]

    handler = partial(
        OverlayRequestHandler,
        overlay_dir=settings["overlay_dir"],
        maps_dir=settings["maps_dir"],
        output_json=settings["output_json"]
    )

    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    print(f"[WEB] Overlay server running at http://{host}:{port}/")
    return server


def maybe_save_debug_images(settings, raw_img, ocr_img):
    if not settings.get("save_debug_images", False):
        return

    debug_dir = settings["debug_dir"]
    debug_dir.mkdir(parents=True, exist_ok=True)
    raw_img.save(debug_dir / "last_raw.png")
    ocr_img.save(debug_dir / "last_ocr.png")


def append_history(history, entry, max_history):
    history.insert(0, entry)
    del history[max_history:]
    return history


def main():
    settings = load_settings()
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_path"]

    output_json = Path(settings["output_json"])
    interval = settings.get("poll_interval_ms", 700) / 1000.0
    min_conf = settings.get("min_confidence", 72)
    clear_after = settings.get("clear_after_seconds", 20)
    port = settings["http_port"]

    output_json.parent.mkdir(parents=True, exist_ok=True)
    settings["maps_dir"].mkdir(parents=True, exist_ok=True)
    settings["overlay_dir"].mkdir(parents=True, exist_ok=True)

    history = []
    write_state(
        output_json,
        build_state(
            map_name=None,
            raw_text="",
            score=0,
            port=port,
            status=settings["status_text"],
            history=history
        )
    )

    server = start_http_server(settings)

    last_map = None
    last_match_time = 0
    last_error = None

    try:
        with mss.mss() as sct:
            while True:
                try:
                    img = capture_region(sct, settings["capture_region"])
                    ocr_img = preprocess_for_ocr(img)
                    maybe_save_debug_images(settings, img, ocr_img)

                    raw_text = pytesseract.image_to_string(
                        ocr_img,
                        config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' I"
                    ).strip()

                    matched, score, cleaned = best_match(raw_text)

                    if score < min_conf:
                        matched = None

                    now = time.time()

                    if matched:
                        last_match_time = now
                        if matched != last_map:
                            print(f"[OK] {cleaned} -> {matched} ({score})")
                            append_history(history, {
                                "time": int(now),
                                "type": "match",
                                "raw_text": cleaned,
                                "map_name": matched,
                                "score": score
                            }, settings["max_history"])

                        write_state(
                            output_json,
                            build_state(
                                map_name=matched,
                                raw_text=cleaned,
                                score=score,
                                port=port,
                                status=f"Detected: {matched}",
                                history=history
                            )
                        )
                        last_map = matched
                        last_error = None
                    else:
                        if raw_text:
                            print(f"[NO MATCH] {cleaned} ({score})")

                        if last_map and (now - last_match_time >= clear_after):
                            print("[CLEAR] No valid map detected for a while, clearing overlay.")
                            append_history(history, {
                                "time": int(now),
                                "type": "clear",
                                "raw_text": "",
                                "map_name": None,
                                "score": 0
                            }, settings["max_history"])

                            write_state(
                                output_json,
                                build_state(
                                    map_name=None,
                                    raw_text="",
                                    score=0,
                                    port=port,
                                    status=settings["status_text"],
                                    history=history
                                )
                            )
                            last_map = None

                    time.sleep(interval)

                except Exception as e:
                    msg = str(e)
                    if msg != last_error:
                        print(f"[ERROR] {msg}")
                        last_error = msg

                    write_state(
                        output_json,
                        build_state(
                            map_name=last_map,
                            raw_text="",
                            score=0,
                            port=port,
                            status=f"Error: {msg}",
                            history=history
                        )
                    )
                    time.sleep(interval)

    except KeyboardInterrupt:
        print("\n[STOP] Bot stopped by user.")
    finally:
        try:
            server.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()