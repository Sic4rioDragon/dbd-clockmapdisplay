from debug_tools import archive_attempt


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
    return "Waiting for next map"


def pretty_status_manual() -> str:
    return "Manual check requested"


def pretty_status_loading() -> str:
    return "Loading detected - checking map"


def pretty_status_candidate(result, count, needed) -> str:
    return f"Candidate from {pretty_source_name(result['source_name'])}: {result['matched']} ({count}/{needed})"


def pretty_status_detected(map_name, source_name) -> str:
    return f"Detected from {pretty_source_name(source_name)}: {map_name}"


def automation_state(loading_mode, loading_bar, armed):
    return {
        "mode": "loading" if loading_mode else "idle",
        "loading_bar_detected": bool(loading_bar["matched"]),
        "loading_bar_dark_count": int(loading_bar.get("dark_count", 0)),
        "loading_armed": bool(armed),
    }


def archive_failed_attempt(settings, reason, candidate_result, results_snapshot, full_img, loading_bar):
    if not candidate_result or not results_snapshot or full_img is None:
        return

    print(f"[LOAD] {reason}: {candidate_result['cleaned']} -> {candidate_result['matched']} ({candidate_result['score']})")

    archive_attempt(
        settings["paths"]["debug_dir"],
        f"failed_{reason}",
        results_snapshot,
        {
            "reason": reason,
            "candidate": {
                "source_name": candidate_result["source_name"],
                "raw_text": candidate_result["raw_text"],
                "cleaned": candidate_result["cleaned"],
                "matched": candidate_result["matched"],
                "score": candidate_result["score"],
            },
            "loading_bar_probe": {
                "matched": bool(loading_bar.get("matched", False)),
                "dark_count": int(loading_bar.get("dark_count", 0)),
                "sampled": loading_bar.get("sampled", []),
            },
        },
        full_img=full_img,
        extra_images={
            "loading_bar_probe": {
                "raw_img": loading_bar.get("raw_img"),
                "ocr_img": None,
            },
        },
        enabled=settings["debug"]["enabled"],
    )


def handle_manual_check(settings, results, loading_bar, full_img):
    any_useful = False

    for r in results:
        if not r["cleaned"]:
            continue

        any_useful = True
        if r["matched"] and r["score"] >= settings["matching"]["min_confidence"]:
            print(f"[CHECK] {r['source_name']}: '{r['cleaned']}' -> {r['matched']} ({r['score']})")
        else:
            print(f"[CHECK] {r['source_name']}: '{r['cleaned']}' -> no valid match ({r['score']})")

    if not any_useful:
        print("[CHECK] No useful text found.")

    archive_attempt(
        settings["paths"]["debug_dir"],
        "manual",
        results,
        {
            "results": make_attempt_summary(results),
            "loading_bar_probe": {
                "matched": loading_bar["matched"],
                "dark_count": loading_bar["dark_count"],
                "sampled": loading_bar["sampled"],
            },
        },
        full_img=full_img,
        extra_images={
            "loading_bar_probe": {
                "raw_img": loading_bar["raw_img"],
                "ocr_img": None,
            },
        },
        enabled=settings["debug"]["enabled"],
    )