"""Rewrite title/description/tags of every video in state/episodes.json from the current meta.build (snippet only; publishAt untouched)."""
import importlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from automation import meta, youtube  # noqa: E402

yt = youtube.service()
youtube.assert_channel(yt, os.environ.get("YT_CHANNEL_ID", ""))
q = {t["id"]: t for t in json.loads((ROOT / "data" / "topic_queue.json").read_text(encoding="utf-8"))["topics"]}
for e in json.loads((ROOT / "state" / "episodes.json").read_text(encoding="utf-8")):
    vid = e.get("youtube_id")
    if not vid:
        continue
    topic = importlib.import_module("mapviz.topics." + q[e["slug"]]["module"].replace("-", "_"))
    title, desc, tags = meta.build(topic, e["slug"])
    sn = yt.videos().list(part="snippet", id=vid).execute()["items"][0]["snippet"]
    sn.update(title=title, description=desc, tags=tags)
    yt.videos().update(part="snippet", body={"id": vid, "snippet": {k: sn[k] for k in ("title", "description", "tags", "categoryId")}}).execute()
    print("updated", vid, e["slug"], "| links:", "http" in desc)
