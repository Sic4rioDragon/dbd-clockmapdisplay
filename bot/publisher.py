import json
from datetime import datetime, timezone
from urllib import request, error


def slugify_map_name(name: str) -> str:
    slug = name.lower().replace("'", "")
    out = []

    for ch in slug:
        if ch.isalnum():
            out.append(ch)
        else:
            out.append("-")

    slug = "".join(out)

    while "--" in slug:
        slug = slug.replace("--", "-")

    return slug.strip("-")


def build_publish_history(history: list) -> list:
    items = []

    for entry in history:
        if entry.get("type") != "match":
            continue

        items.append({
            "map_name": entry.get("map_name"),
            "source_name": entry.get("source_name"),
            "updated_at": datetime.fromtimestamp(entry.get("time", 0), tz=timezone.utc).isoformat(),
        })

    return items[:10]


def publish_map_update(settings: dict, map_name: str, source_name: str, history: list):
    publish = settings.get("publish", {})

    if not publish.get("enabled"):
        return

    api_url = publish["api_base_url"].rstrip("/") + "/api/update-map"
    token = publish.get("update_token", "")

    if not token:
        print("[PUBLISH] Skipped, no update token set.")
        return

    payload = {
        "map_name": map_name,
        "image_slug": slugify_map_name(map_name),
        "source_name": source_name,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "history": build_publish_history(history),
    }

    data = json.dumps(payload).encode("utf-8")

    req = request.Request(
        api_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "dbd-clockmapdisplay/1.0",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=10) as resp:
            resp.read()
            print("[PUBLISH] Update sent.")
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[PUBLISH] Failed: HTTP {e.code} - {body}")
        raise
    except Exception as e:
        print(f"[PUBLISH] Failed: {e}")
        raise