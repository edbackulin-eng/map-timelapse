"""Upload the next reserve video(s) of America Over Time as PRIVATE videos with publishAt (Mon/Fri 20:00 Kyiv).

Run by .github/workflows/upload.yml (daily). Safe by design:
  - no token                      -> nothing happens (exit 0)
  - wrong channel / empty YT_CHANNEL_ID / channel list not read in full (Doubt) -> nothing uploaded, exit 3
  - the episode is already on the channel (marker "[ref: map-timelapse/<slug>]" or same title) -> never uploaded again
  - the state file (state/episodes.json) is committed right after every upload; if that fails the run stops
Reserve = DRAFT release `reserve-<slug>` (title starts with RESERVE:), made by video.yml.
"""
import importlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from automation import meta, youtube  # noqa: E402

BUFFER = int(os.environ.get("AOT_BUFFER", "2"))        # videos kept scheduled ahead
MAX_PER_RUN = 2
STATE = ROOT / "state" / "episodes.json"
QUEUE = ROOT / "data" / "topic_queue.json"
DRY = os.environ.get("DRY_RUN", "") == "1"


def sh(*a, check=True):
    return subprocess.run(a, capture_output=True, text=True, check=check, cwd=ROOT).stdout


def load_state():
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else []


def persist(state, msg):
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if DRY:
        return
    sh("git", "config", "user.name", "aot-bot")
    sh("git", "config", "user.email", "aot-bot@users.noreply.github.com")
    sh("git", "add", "state/episodes.json")
    sh("git", "commit", "-m", msg)
    for _ in range(3):
        r = subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, text=True)
        if r.returncode == 0:
            return
        sh("git", "pull", "--rebase", "--autostash", check=False)
    raise RuntimeError("state commit could not be pushed: stop (a duplicate upload would be possible)")


def reserve_releases():
    out = json.loads(sh("gh", "release", "list", "--limit", "100", "--json", "tagName,name,isDraft") or "[]")
    return {r["tagName"][len("reserve-"):]: r for r in out if r["tagName"].startswith("reserve-") and r["name"].startswith("RESERVE")}


def candidates():
    q = json.loads(QUEUE.read_text(encoding="utf-8"))["topics"]
    ready = [t for t in q if t.get("module") and t["status"] in ("approved", "reserve", "zero")]
    ready.sort(key=lambda t: t.get("order", 999))
    return ready


def main():
    if not os.environ.get("YT_TOKEN_JSON", "").strip():
        print("no YT_TOKEN_JSON: nothing to do (the owner has not stored the token yet)")
        return 0
    yt = youtube.service()
    try:
        ch = youtube.assert_channel(yt, os.environ.get("YT_CHANNEL_ID", ""))
        print(f"channel ok: {ch['id']} {ch['snippet']['title']}")
        state = load_state()
        known = [e["youtube_id"] for e in state if e.get("youtube_id")]
        videos = youtube.all_uploads(yt, known)
    except youtube.Doubt as e:
        print(f"DOUBT - nothing uploaded: {e}")
        return 3
    print(f"the channel has {len(videos)} videos; scheduled ahead: {youtube.scheduled_ahead(videos)}")
    done = 0
    rel = reserve_releases()
    for t in candidates():
        if youtube.scheduled_ahead(videos) >= BUFFER or done >= MAX_PER_RUN:
            break
        slug = t["id"]
        if slug not in rel:
            continue
        topic = importlib.import_module("mapviz.topics." + t["module"].replace("-", "_"))
        title, desc, tags = meta.build(topic, slug)
        ex = youtube.find_existing(videos, slug, title)
        if ex:
            print(f"{slug}: already on the channel as {ex['id']} - not uploading again")
            if not any(e.get("youtube_id") == ex["id"] for e in state):
                state.append(dict(slug=slug, title=title, status="scheduled", youtube_id=ex["id"], publish_at=ex["publish_at"]))
                persist(state, f"state: {slug} found on the channel ({ex['id']})")
            continue
        slot = youtube.next_slot(youtube.channel_dates(videos))
        print(f"{slug}: slot {slot.isoformat()}")
        if DRY:
            print("DRY RUN: would upload", title, "\n", desc[:600])
            done += 1
            continue
        work = ROOT / "out" / "upload" / slug
        work.mkdir(parents=True, exist_ok=True)
        sh("gh", "release", "download", f"reserve-{slug}", "-p", "america-over-time_*.mp4", "-D", str(work), "--clobber")
        mp4 = next(work.glob("america-over-time_*.mp4"))
        vid = youtube.upload(yt, mp4, title, desc, tags, slot)
        cover = ROOT / "assets" / "covers" / f"{slug}.jpg"
        if cover.exists():
            youtube.set_thumbnail(yt, vid, cover)
        else:
            print(f"WARN: no cover {cover}")
        state.append(dict(slug=slug, title=title, status="scheduled", youtube_id=vid, publish_at=slot.strftime("%Y-%m-%dT%H:%M:%SZ"),
                          uploaded_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        persist(state, f"state: {slug} uploaded {vid}, publishAt {slot.isoformat()}")
        sh("gh", "release", "edit", f"reserve-{slug}", "--title", f"UPLOADED {vid}: {slug}", check=False)
        videos = youtube.all_uploads(yt, [e["youtube_id"] for e in state if e.get("youtube_id")])
        done += 1
        print(f"{slug}: uploaded {vid}")
    print(f"uploaded {done} video(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
