import threading
import time

import mss
import pytesseract
from PIL import Image

from automation_helpers import (
    archive_failed_attempt,
    automation_state,
    handle_manual_check,
    make_attempt_summary,
    pretty_status_candidate,
    pretty_status_detected,
    pretty_status_loading,
    pretty_status_manual,
    pretty_status_waiting,
)
from config import load_settings
from debug_tools import archive_attempt, save_latest
from hotkey import start_global_hotkey
from loading_watch import is_loading_bar_present
from ocr_engine import choose_best_result, run_region_ocr
from server import start_http_server
from state_store import append_history, build_state, write_state

from publisher import publish_map_update

def log(msg: str):
    print(msg)


def run_bot():
    settings = load_settings()
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_path"]

    matching = settings["matching"]
    automation = settings["automation"]
    black_bar = settings["black_bar"]
    paths = settings["paths"]
    debug = settings["debug"]
    server_cfg = settings["server"]
    input_cfg = settings["input"]

    idle_poll_s = automation["idle_poll_ms"] / 1000.0
    loading_poll_s = automation["loading_ocr_poll_ms"] / 1000.0
    loading_arm_timeout_s = automation["loading_arm_timeout_ms"] / 1000.0
    loading_post_bar_grace_s = automation["loading_post_bar_grace_ms"] / 1000.0
    post_detect_cooldown_s = automation["post_detect_cooldown_ms"] / 1000.0

    paths["maps_dir"].mkdir(parents=True, exist_ok=True)
    paths["overlay_dir"].mkdir(parents=True, exist_ok=True)
    paths["output_json"].parent.mkdir(parents=True, exist_ok=True)
    paths["debug_dir"].mkdir(parents=True, exist_ok=True)

    force_check_event = threading.Event()
    start_global_hotkey(input_cfg["manual_hotkey"], force_check_event)
    server = start_http_server(
        {
            "http_host": server_cfg["host"],
            "http_port": server_cfg["port"],
            "overlay_dir": paths["overlay_dir"],
            "maps_dir": paths["maps_dir"],
            "output_json": paths["output_json"],
        },
        force_check_event,
    )

    history = []
    last_map = None
    last_source = None

    pending_key = None
    pending_count = 0

    loading_mode = False
    loading_bar_seen_streak = 0
    loading_bar_miss_streak = 0
    loading_armed = False
    loading_armed_until = 0.0
    loading_bar_last_seen_at = 0.0
    detect_cooldown_until = 0.0

    last_candidate_result = None
    last_candidate_results_snapshot = None
    last_candidate_full_img = None
    last_candidate_loading_bar = None

    write_state(
        paths["output_json"],
        build_state(
            map_name=None,
            raw_text="",
            score=0,
            port=server_cfg["port"],
            status=pretty_status_waiting(),
            history=history,
            automation={
                "mode": "idle",
                "loading_bar_detected": False,
                "loading_bar_dark_count": 0,
                "loading_armed": False,
            },
        ),
    )

    try:
        with mss.mss() as sct:
            while True:
                now = time.time()

                manual_check = force_check_event.is_set()
                if manual_check:
                    force_check_event.clear()
                    log("[CHECK] Manual check requested.")
                    write_state(
                        paths["output_json"],
                        build_state(
                            map_name=last_map,
                            raw_text="",
                            score=0,
                            port=server_cfg["port"],
                            status=pretty_status_manual(),
                            history=history,
                            source_name=last_source,
                            automation={
                                "mode": "loading" if loading_mode else "idle",
                                "loading_bar_detected": False,
                                "loading_bar_dark_count": 0,
                                "loading_armed": loading_armed,
                            },
                        ),
                    )

                loading_bar = is_loading_bar_present(sct, settings)
                in_cooldown = now < detect_cooldown_until

                if loading_bar["matched"] and not in_cooldown:
                    loading_bar_seen_streak += 1
                    loading_bar_miss_streak = 0
                    loading_bar_last_seen_at = now
                else:
                    loading_bar_miss_streak += 1
                    loading_bar_seen_streak = 0

                if loading_bar_seen_streak >= black_bar["enter_streak"] and not loading_armed and not in_cooldown:
                    loading_armed = True
                    loading_armed_until = now + loading_arm_timeout_s
                    log("[LOAD] Loading watcher armed.")

                if loading_armed and now > loading_armed_until:
                    archive_failed_attempt(
                        settings,
                        "timeout",
                        last_candidate_result,
                        last_candidate_results_snapshot,
                        last_candidate_full_img,
                        last_candidate_loading_bar,
                    )
                    loading_armed = False
                    loading_mode = False
                    pending_key = None
                    pending_count = 0
                    last_candidate_result = None
                    last_candidate_results_snapshot = None
                    last_candidate_full_img = None
                    last_candidate_loading_bar = None
                    log("[LOAD] Loading watcher timed out.")

                should_stay_loading = False
                if loading_armed:
                    if loading_bar["matched"]:
                        should_stay_loading = True
                    elif (now - loading_bar_last_seen_at) <= loading_post_bar_grace_s:
                        should_stay_loading = True

                if should_stay_loading and not loading_mode:
                    loading_mode = True
                    pending_key = None
                    pending_count = 0
                    log("[LOAD] Fast OCR started.")

                if not should_stay_loading and loading_mode:
                    archive_failed_attempt(
                        settings,
                        "left_mode",
                        last_candidate_result,
                        last_candidate_results_snapshot,
                        last_candidate_full_img,
                        last_candidate_loading_bar,
                    )
                    loading_mode = False
                    pending_key = None
                    pending_count = 0
                    last_candidate_result = None
                    last_candidate_results_snapshot = None
                    last_candidate_full_img = None
                    last_candidate_loading_bar = None
                    log("[LOAD] Fast OCR stopped.")

                monitor = sct.monitors[1]
                full_shot = sct.grab(monitor)
                full_img = Image.frombytes("RGB", full_shot.size, full_shot.rgb)

                should_ocr = manual_check or loading_mode
                results = []
                if should_ocr:
                    results = [
                        run_region_ocr(sct, settings, "loading_strip"),
                        run_region_ocr(sct, settings, "tab_map_name"),
                    ]

                extra_images = {
                    "loading_bar_probe": {"raw_img": loading_bar["raw_img"], "ocr_img": None},
                }

                if results and debug["enabled"] and debug["save_debug_images"]:
                    save_latest(paths["debug_dir"], results, full_img=full_img, extra_images=extra_images)

                if manual_check and results:
                    handle_manual_check(settings, results, loading_bar, full_img)

                best = choose_best_result(results, matching["min_confidence"]) if results else None
                auto = automation_state(loading_mode, loading_bar, loading_armed)

                if best:
                    last_candidate_result = best
                    last_candidate_results_snapshot = results
                    last_candidate_full_img = full_img
                    last_candidate_loading_bar = {
                        "matched": loading_bar["matched"],
                        "dark_count": loading_bar["dark_count"],
                        "sampled": loading_bar["sampled"],
                        "raw_img": loading_bar["raw_img"],
                    }

                    best_key = (best["matched"], best["source_name"])
                    if best_key == pending_key:
                        pending_count += 1
                    else:
                        pending_key = best_key
                        pending_count = 1

                    confirmed = manual_check or pending_count >= matching["required_confirmations"]

                    if confirmed:
                        matched = best["matched"]
                        cleaned = best["cleaned"]
                        score = best["score"]
                        source_name = best["source_name"]

                        is_new_map = matched != last_map or source_name != last_source

                        if is_new_map:
                            log(f"[MAP] {matched} ({score}) via {source_name}")
                            append_history(
                                history,
                                {
                                    "time": int(now),
                                    "type": "match",
                                    "source_name": source_name,
                                    "raw_text": cleaned,
                                    "map_name": matched,
                                    "score": score,
                                },
                                debug["max_history"],
                            )

                            try:
                                publish_map_update(settings, matched, source_name, history)
                                log("[PUBLISH] Sent update to dbdmap-api.sic4riodragon.uk")
                            except Exception as e:
                                log(f"[PUBLISH] Failed to send update: {e}")

                            archive_attempt(
                                paths["debug_dir"],
                                "accepted",
                                results,
                                {
                                    "results": make_attempt_summary(results),
                                    "loading_bar_probe": {
                                        "matched": loading_bar["matched"],
                                        "dark_count": loading_bar["dark_count"],
                                        "sampled": loading_bar["sampled"],
                                        "loading_armed": loading_armed,
                                        "loading_mode": loading_mode,
                                    },
                                },
                                full_img=full_img,
                                extra_images=extra_images,
                                enabled=debug["enabled"],
                            )

                        write_state(
                            paths["output_json"],
                            build_state(
                                map_name=matched,
                                raw_text=cleaned,
                                score=score,
                                port=server_cfg["port"],
                                status=pretty_status_detected(matched, source_name),
                                history=history,
                                source_name=source_name,
                                automation=auto,
                            ),
                        )

                        last_map = matched
                        last_source = source_name

                        detect_cooldown_until = now + post_detect_cooldown_s
                        loading_armed = False
                        loading_mode = False
                        pending_key = None
                        pending_count = 0
                        loading_bar_seen_streak = 0
                        loading_bar_miss_streak = 0

                        last_candidate_result = None
                        last_candidate_results_snapshot = None
                        last_candidate_full_img = None
                        last_candidate_loading_bar = None
                    else:
                        write_state(
                            paths["output_json"],
                            build_state(
                                map_name=last_map,
                                raw_text="",
                                score=0,
                                port=server_cfg["port"],
                                status=pretty_status_candidate(best, pending_count, matching["required_confirmations"]),
                                history=history,
                                source_name=best["source_name"],
                                automation=auto,
                            ),
                        )
                else:
                    pending_key = None
                    pending_count = 0

                    status = pretty_status_loading() if loading_mode else (f"Locked on: {last_map}" if last_map else pretty_status_waiting())
                    write_state(
                        paths["output_json"],
                        build_state(
                            map_name=last_map,
                            raw_text="",
                            score=0,
                            port=server_cfg["port"],
                            status=status,
                            history=history,
                            source_name=last_source,
                            automation=auto,
                        ),
                    )

                time.sleep(loading_poll_s if loading_mode else idle_poll_s)

    except KeyboardInterrupt:
        print("\n[STOP] Bot stopped by user.")
    finally:
        try:
            server.shutdown()
        except Exception:
            pass