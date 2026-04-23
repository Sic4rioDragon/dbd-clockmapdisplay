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
    pretty_status_match_end,
    pretty_status_waiting,
)
from config import load_settings
from debug_tools import archive_attempt, save_latest
from hotkey import start_global_hotkey
from loading_watch import is_loading_bar_present
from match_state import detect_continue_button, get_clear_after_seconds
from ocr_engine import choose_best_result, run_region_ocr
from server import start_http_server
from state_store import append_history, build_state, write_state


def run_bot():
    settings = load_settings()
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_path"]
    clear_after_seconds = get_clear_after_seconds(settings)

    idle_poll_s = settings.get("idle_poll_ms", 700) / 1000.0
    loading_poll_s = settings.get("loading_ocr_poll_ms", 200) / 1000.0
    loading_arm_timeout_s = settings.get("loading_arm_timeout_ms", 20000) / 1000.0
    loading_post_bar_grace_s = settings.get("loading_post_bar_grace_ms", 3500) / 1000.0
    post_detect_cooldown_s = settings.get("post_detect_cooldown_ms", 2000) / 1000.0

    settings["maps_dir"].mkdir(parents=True, exist_ok=True)
    settings["overlay_dir"].mkdir(parents=True, exist_ok=True)
    settings["output_json"].parent.mkdir(parents=True, exist_ok=True)
    settings["debug_dir"].mkdir(parents=True, exist_ok=True)

    force_check_event = threading.Event()
    start_global_hotkey(settings["manual_hotkey"], force_check_event)
    server = start_http_server(settings, force_check_event)

    history = []
    last_map = None
    last_source = None
    last_match_time = 0.0

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
    last_candidate_continue_check = None
    last_candidate_loading_bar = None

    write_state(
        settings["output_json"],
        build_state(
            map_name=None,
            raw_text="",
            score=0,
            port=settings["http_port"],
            status=pretty_status_waiting(),
            history=history,
            automation={
                "mode": "idle",
                "loading_bar_detected": False,
                "loading_bar_dark_count": 0,
                "continue_detected": False,
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
                    print("[CHECK] Manual map check requested.")
                    write_state(
                        settings["output_json"],
                        build_state(
                            map_name=last_map,
                            raw_text="",
                            score=0,
                            port=settings["http_port"],
                            status=pretty_status_manual(),
                            history=history,
                            source_name=last_source,
                            automation={
                                "mode": "loading" if loading_mode else "idle",
                                "loading_bar_detected": False,
                                "loading_bar_dark_count": 0,
                                "continue_detected": False,
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

                if loading_bar_seen_streak >= 2 and not loading_armed and not in_cooldown:
                    loading_armed = True
                    loading_armed_until = now + loading_arm_timeout_s
                    print("[LOAD] Black bar detected, arming loading watcher.")

                if loading_armed and now > loading_armed_until:
                    archive_failed_attempt(
                        settings,
                        "timeout",
                        last_candidate_result,
                        last_candidate_results_snapshot,
                        last_candidate_full_img,
                        last_candidate_continue_check,
                        last_candidate_loading_bar,
                    )
                    loading_armed = False
                    loading_mode = False
                    pending_key = None
                    pending_count = 0
                    last_candidate_result = None
                    last_candidate_results_snapshot = None
                    last_candidate_full_img = None
                    last_candidate_continue_check = None
                    last_candidate_loading_bar = None
                    print("[LOAD] Loading watcher timeout expired.")

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
                    print("[LOAD] Entering fast OCR mode.")

                if not should_stay_loading and loading_mode:
                    archive_failed_attempt(
                        settings,
                        "left_mode",
                        last_candidate_result,
                        last_candidate_results_snapshot,
                        last_candidate_full_img,
                        last_candidate_continue_check,
                        last_candidate_loading_bar,
                    )
                    loading_mode = False
                    pending_key = None
                    pending_count = 0
                    last_candidate_result = None
                    last_candidate_results_snapshot = None
                    last_candidate_full_img = None
                    last_candidate_continue_check = None
                    last_candidate_loading_bar = None
                    print("[LOAD] Leaving fast OCR mode.")

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

                continue_check = detect_continue_button(sct, settings)
                extra_images = {
                    "continue_button": continue_check,
                    "loading_bar_probe": {"raw_img": loading_bar["raw_img"], "ocr_img": None},
                }

                if results:
                    save_latest(settings["debug_dir"], results, full_img=full_img, extra_images=extra_images)

                if manual_check and results:
                    handle_manual_check(settings, results, continue_check, loading_bar, full_img)

                best = choose_best_result(results, settings["min_confidence"]) if results else None
                auto = automation_state(loading_mode, loading_bar, continue_check, loading_armed)

                if best:
                    last_candidate_result = best
                    last_candidate_results_snapshot = results
                    last_candidate_full_img = full_img
                    last_candidate_continue_check = {
                        "raw_text": continue_check["raw_text"],
                        "cleaned": continue_check["cleaned"],
                        "matched": continue_check["matched"],
                        "raw_img": continue_check.get("raw_img"),
                        "ocr_img": continue_check.get("ocr_img"),
                    }
                    last_candidate_loading_bar = {
                        "matched": loading_bar["matched"],
                        "dark_count": loading_bar["dark_count"],
                        "sampled": loading_bar["sampled"],
                    }

                    best_key = (best["matched"], best["source_name"])
                    if best_key == pending_key:
                        pending_count += 1
                    else:
                        pending_key = best_key
                        pending_count = 1

                    confirmed = manual_check or pending_count >= settings["required_confirmations"]

                    if confirmed:
                        matched = best["matched"]
                        cleaned = best["cleaned"]
                        score = best["score"]
                        source_name = best["source_name"]

                        if matched != last_map or source_name != last_source:
                            print(f"[OK] {source_name}: {cleaned} -> {matched} ({score})")
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
                                settings["max_history"],
                            )

                            archive_attempt(
                                settings["debug_dir"],
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
                            )

                        write_state(
                            settings["output_json"],
                            build_state(
                                map_name=matched,
                                raw_text=cleaned,
                                score=score,
                                port=settings["http_port"],
                                status=pretty_status_detected(matched, source_name),
                                history=history,
                                source_name=source_name,
                                automation=auto,
                            ),
                        )

                        last_map = matched
                        last_source = source_name
                        last_match_time = now

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
                        last_candidate_continue_check = None
                        last_candidate_loading_bar = None
                    else:
                        write_state(
                            settings["output_json"],
                            build_state(
                                map_name=last_map,
                                raw_text="",
                                score=0,
                                port=settings["http_port"],
                                status=pretty_status_candidate(best, pending_count, settings["required_confirmations"]),
                                history=history,
                                source_name=best["source_name"],
                                automation=auto,
                            ),
                        )
                else:
                    pending_key = None
                    pending_count = 0

                    if last_map and continue_check["matched"]:
                        print("[CLEAR] Continue button detected, clearing overlay.")
                        append_history(
                            history,
                            {
                                "time": int(now),
                                "type": "clear",
                                "raw_text": "CONTINUE",
                                "map_name": None,
                                "score": 0,
                            },
                            settings["max_history"],
                        )

                        write_state(
                            settings["output_json"],
                            build_state(
                                map_name=None,
                                raw_text="",
                                score=0,
                                port=settings["http_port"],
                                status=pretty_status_match_end(),
                                history=history,
                                automation=auto,
                            ),
                        )
                        last_map = None
                        last_source = None

                    elif last_map and (now - last_match_time >= clear_after_seconds):
                        print("[CLEAR] No valid map detected for a while, clearing overlay.")
                        append_history(
                            history,
                            {
                                "time": int(now),
                                "type": "clear",
                                "raw_text": "",
                                "map_name": None,
                                "score": 0,
                            },
                            settings["max_history"],
                        )

                        write_state(
                            settings["output_json"],
                            build_state(
                                map_name=None,
                                raw_text="",
                                score=0,
                                port=settings["http_port"],
                                status=pretty_status_waiting(),
                                history=history,
                                automation=auto,
                            ),
                        )
                        last_map = None
                        last_source = None
                    else:
                        status = pretty_status_loading() if loading_mode else (f"Locked on: {last_map}" if last_map else pretty_status_waiting())
                        write_state(
                            settings["output_json"],
                            build_state(
                                map_name=last_map,
                                raw_text="",
                                score=0,
                                port=settings["http_port"],
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