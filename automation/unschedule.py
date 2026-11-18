"""Delete our own still-scheduled (private, publishAt in the future) videos so they can be uploaded again (e.g. after a music fix).
Safety: channel id asserted; only ids that are in state/episodes.json; only videos whose publish_at is in the future.
Usage: python automation/unschedule.py <youtube_id> [...]"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from automation import youtube  # noqa: E402

STATE = ROOT / "state" / "episodes.json"


def main(ids):
    yt = youtube.service()
    youtube.assert_channel(yt, os.environ.get("YT_CHANNEL_ID", ""))
    state = json.loads(STATE.read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc)
    for vid in ids:
        e = next((x for x in state if x.get("youtube_id") == vid), None)
        if not e or datetime.fromisoformat(e["publish_at"].replace("Z", "+00:00")) <= now:
            print(f"{vid}: not in state or already published - NOT deleted")
            continue
        yt.videos().delete(id=vid).execute()
        state.remove(e)
        subprocess.run(["gh", "release", "edit", f"reserve-{e['slug']}", "--title", f"RESERVE: {e['slug']}"], cwd=ROOT)
        print(f"{vid} ({e['slug']}): deleted, release back to RESERVE")
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    subprocess.run(["git", "config", "user.name", "aot-bot"], cwd=ROOT)
    subprocess.run(["git", "config", "user.email", "aot-bot@users.noreply.github.com"], cwd=ROOT)
    subprocess.run(["git", "add", "state/episodes.json"], cwd=ROOT)
    subprocess.run(["git", "commit", "-m", "state: unscheduled " + ",".join(ids)], cwd=ROOT)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main(sys.argv[1:])
