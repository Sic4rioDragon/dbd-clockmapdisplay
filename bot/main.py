import threading
import time

import mss
import pytesseract

from config import load_settings
from debug_tools import archive_attempt, save_latest
from hotkey import start_global_hotkey
from ocr_engine import choose_best_result, run_region_ocr
from server import start_http_server
from state_store import append_history, build_state, write_state


def make_attempt_summary(results):
    return [
        {
            "source_name": r["source_name"],
            "raw_text": r["raw_text"],
            "cleaned": r["cleaned"],
            "matched": r["matched"],
            "score": r["score"],
        }
        for r in results
    ]


def pretty_source_name(source_name: str | None) -> str:
    names = {
        "tab_map_name": "tab/details text",
        "loading_strip": "loading banner",
    }
    return names.get(source_name or "", source_name or "unknown source")


def pretty_status_waiting() -> str:
    return "Waiting for map"


def pretty_status_manual() -> str:
    return "Manual check requested"


def pretty_status_candidate(result, count, needed) -> str:
    return f"Candidate from {pretty_source_name(result['source_name'])}: {result['matched']} ({count}/{needed})"


def pretty_status_detected(map_name, source_name) -> str:
    return f"Detected from {pretty_source_name(source_name)}: {map_name}"


def main():
    settings = load_settings()
    pytesseract.pytesseract.tesseract_cmd = settings["tesseract_path"]

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
    last_invalid_signature = None

    write_state(
        settings["output_json"],
        build_state(
            map_name=None,
            raw_text="",
            score=0,
            port=settings["http_port"],
            status=pretty_status_waiting(),
            history=history
        )
    )

    try:
        with mss.mss() as sct:
            while True:
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
                            source_name=last_source
                        )
                    )

                results = [
                    run_region_ocr(sct, settings, "loading_strip"),
                    run_region_ocr(sct, settings, "tab_map_name")
                ]

                save_latest(settings["debug_dir"], results)

                invalid_candidates = []
                for r in results:
                    if r["cleaned"] and not r["matched"]:
                        invalid_candidates.append((r["source_name"], r["cleaned"]))

                current_invalid_signature = tuple(invalid_candidates) if invalid_candidates else None

                best = choose_best_result(results, settings["min_confidence"])
                now = time.time()

                if manual_check:
                    for r in results:
                        if not r["cleaned"]:
                            print(f"[CHECK] {r['source_name']}: no text")
                        elif r["matched"] and r["score"] >= settings["min_confidence"]:
                            print(f"[CHECK] {r['source_name']}: '{r['cleaned']}' -> {r['matched']} ({r['score']})")
                        else:
                            print(f"[CHECK] {r['source_name']}: '{r['cleaned']}' -> no valid match ({r['score']})")

                    archive_attempt(
                        settings["debug_dir"],
                        "manual",
                        results,
                        {"results": make_attempt_summary(results)}
                    )

                if best:
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
                            append_history(history, {
                                "time": int(now),
                                "type": "match",
                                "source_name": source_name,
                                "raw_text": cleaned,
                                "map_name": matched,
                                "score": score
                            }, settings["max_history"])

                            archive_attempt(
                                settings["debug_dir"],
                                "accepted",
                                results,
                                {"results": make_attempt_summary(results)}
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
                                source_name=source_name
                            )
                        )

                        last_map = matched
                        last_source = source_name
                        last_match_time = now
                        last_invalid_signature = None
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
                                source_name=best["source_name"]
                            )
                        )
                else:
                    pending_key = None
                    pending_count = 0

                    if current_invalid_signature != last_invalid_signature:
                        last_invalid_signature = current_invalid_signature

                    if last_map and (now - last_match_time >= settings["clear_after_seconds"]):
                        print("[CLEAR] No valid map detected for a while, clearing overlay.")
                        append_history(history, {
                            "time": int(now),
                            "type": "clear",
                            "raw_text": "",
                            "map_name": None,
                            "score": 0
                        }, settings["max_history"])

                        write_state(
                            settings["output_json"],
                            build_state(
                                map_name=None,
                                raw_text="",
                                score=0,
                                port=settings["http_port"],
                                status=pretty_status_waiting(),
                                history=history
                            )
                        )
                        last_map = None
                        last_source = None
                    else:
                        write_state(
                            settings["output_json"],
                            build_state(
                                map_name=last_map,
                                raw_text="",
                                score=0,
                                port=settings["http_port"],
                                status=pretty_status_waiting(),
                                history=history,
                                source_name=last_source
                            )
                        )

                time.sleep(settings["poll_interval_ms"] / 1000.0)

    except KeyboardInterrupt:
        print("\n[STOP] Bot stopped by user.")
    finally:
        try:
            server.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    main()