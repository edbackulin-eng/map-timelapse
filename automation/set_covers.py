"""Set the stored covers (assets/covers/<slug>.jpg) on every video in state/episodes.json. Run once the channel is phone-verified."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import json  # noqa: E402
from automation import youtube  # noqa: E402

yt = youtube.service()
youtube.assert_channel(yt, os.environ.get("YT_CHANNEL_ID", ""))
for e in json.loads((ROOT / "state" / "episodes.json").read_text(encoding="utf-8")):
    c = ROOT / "assets" / "covers" / f"{e['slug']}.jpg"
    if e.get("youtube_id") and c.exists():
        youtube.set_thumbnail(yt, e["youtube_id"], c)
        print("cover set:", e["slug"])
