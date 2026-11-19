"""Title, description, tags and hashtags of a video, built from the topic module and data/sources/<slug>.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# channel keywords (docs/channel_brief.md section 4)
CHANNEL_TAGS = ["animated map", "map timelapse", "US history map", "United States map", "US population history", "census data",
                "American history", "US map animation", "how America grew", "data visualization", "US states", "America Over Time"]


def build(topic, slug_for_ref):
    """-> (title, description, tags). `topic` is the module mapviz.topics.<x>."""
    src_path = ROOT / "data" / "sources" / f"{topic.SLUG}.json"
    srcs = json.loads(src_path.read_text(encoding="utf-8")) if src_path.exists() else {"sources": {}}
    used = {}
    for e in srcs.get("events", []):
        used[e["source"]] = srcs["sources"][e["source"]]
    for m in srcs.get("migrations", []):
        used[m["source"]] = srcs["sources"][m["source"]]
    # no links: YouTube rejects URLs in descriptions of channels without phone verification (and no personal GitHub link either)
    lines = [f"- {v['publisher']}: {v['title']}" for v in list(used.values())[:10]]
    desc = (f"{topic.HOOK}\n\n"
            "No narration: an animated map, a year counter, a legend and short captions. Every number comes from official open data.\n\n"
            "DATA AND SOURCES\n"
            "- Population: U.S. Census Bureau (public domain)\n"
            "- Map data: Natural Earth (public domain)\n"
            "- Music: Yoiyami, cynicmusic (CC0), OpenGameArt.org\n"
            + "\n".join(lines) + "\n"
            "\n"
            "New animated maps every Monday and Friday.\n\n"
            + " ".join(topic.HASHTAGS) + "\n\n"
            + f"[ref: map-timelapse/{slug_for_ref}]")
    tags, n = [], 0
    for t in dict.fromkeys(list(topic.TAGS) + CHANNEL_TAGS):
        if n + len(t) + 1 > 450:     # YouTube: all tags together up to 500 characters
            break
        tags.append(t)
        n += len(t) + 1
    return topic.TITLE, desc, tags
