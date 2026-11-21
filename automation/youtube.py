"""YouTube for America Over Time: private uploads with a publishAt, never twice, never to another channel.

Token: YT_TOKEN_JSON (OAuth refresh token of THIS channel, Google Cloud project hypothetica-511509), environment only.
Channel guard: the id of the channel the token opens must equal YT_CHANNEL_ID (GitHub variable). Anything else -> no upload
(owner: never upload to What If or any other channel by mistake).
Anti-duplicate (same rules as the archive channel, owner 17.11): the channel's COMPLETE uploads list is read (every page,
retried, checked against the ids the state knows); a video whose description carries "[ref: map-timelapse/<slug>]" or has the
same title is the episode already uploaded. If the list cannot be read in full, Doubt is raised: nothing is uploaded.
Slots: Monday and Friday 20:00 Europe/Kyiv (the zone's DST is handled by zoneinfo), at least 30 min ahead, one video a day.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
SCHEDULE = {"timezone": "Europe/Kyiv", "local_time": "20:00", "weekdays": [0, 4], "min_lead_minutes": 30}
REF = "[ref: map-timelapse/{slug}]"


class Doubt(RuntimeError):
    """Not sure the channel was read in full or the token opens the right channel: no upload."""


def _retry(fn, what, tries=4):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:                                       # noqa: BLE001
            last = e
            print(f"WARN {what} failed ({i + 1}/{tries}): {str(e)[:160]}")
            time.sleep(2 * 3 ** i)
    raise Doubt(f"{what} failed {tries} times: {str(last)[:200]}")


def service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    d = json.loads(os.environ["YT_TOKEN_JSON"])
    cred = Credentials(token=None, refresh_token=d["refresh_token"], client_id=d["client_id"], client_secret=d["client_secret"],
                       token_uri=d.get("token_uri", "https://oauth2.googleapis.com/token"), scopes=d.get("scopes") or SCOPES)
    return build("youtube", "v3", credentials=cred, cache_discovery=False)


def assert_channel(yt, expected_id):
    """The token must open exactly the expected channel."""
    if not expected_id or not expected_id.strip():
        raise Doubt("YT_CHANNEL_ID is not set (GitHub variable): refusing to upload")
    items = _retry(lambda: yt.channels().list(part="snippet", mine=True).execute(), "channel").get("items", [])
    if len(items) != 1:
        raise Doubt(f"the token opens {len(items)} channels, expected exactly 1")
    ch = items[0]
    if ch["id"] != expected_id.strip():
        raise Doubt(f"WRONG CHANNEL: the token opens {ch['id']} ({ch['snippet']['title']}), expected {expected_id.strip()}")
    return ch


def all_uploads(yt, known_ids=()):
    """Every video of the channel (private and scheduled too): snippet + status, each page retried."""
    ch = _retry(lambda: yt.channels().list(part="contentDetails", mine=True).execute(), "channel")["items"][0]
    pl = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok, total = [], None, None
    while True:
        r = _retry(lambda t=tok: yt.playlistItems().list(part="contentDetails", playlistId=pl, maxResults=50, pageToken=t).execute(),
                   "uploads page")
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        total = (r.get("pageInfo") or {}).get("totalResults", total)
        tok = r.get("nextPageToken")
        if not tok:
            break
    if total is not None and len(ids) < total:
        raise Doubt(f"the uploads list has {len(ids)} of {total} videos")
    vids = []
    for k in range(0, len(ids), 50):
        part = ids[k:k + 50]
        vids += _retry(lambda p=part: yt.videos().list(part="snippet,status", id=",".join(p)).execute(), "video details")["items"]
    seen = {v["id"] for v in vids}
    missing = [i for i in known_ids if i not in seen]
    if missing:
        raise Doubt(f"the state knows videos the list lacks: {missing}")
    return [{"id": v["id"], "title": v["snippet"].get("title", ""), "description": v["snippet"].get("description", ""),
             "privacy": v["status"].get("privacyStatus"), "publish_at": v["status"].get("publishAt"),
             "published_at": v["snippet"].get("publishedAt")} for v in vids]


def find_existing(videos, slug, title):
    ref = REF.format(slug=slug)
    for v in videos:
        if ref in v["description"]:
            return v
    for v in videos:
        if v["title"].strip() == title.strip():
            return v
    return None


def channel_dates(videos):
    out = []
    for v in videos:
        t = v["publish_at"] or (v["published_at"] if v["privacy"] in ("public", "unlisted") else None)
        if t:
            out.append(t)
    return out


def scheduled_ahead(videos, now=None):
    now = now or datetime.now(timezone.utc)
    n = 0
    for v in videos:
        if v["publish_at"] and datetime.fromisoformat(v["publish_at"].replace("Z", "+00:00")) > now:
            n += 1
    return n


def next_slot(taken=(), now=None, cfg=SCHEDULE):
    """The nearest free Mon/Fri 20:00 Kyiv slot, as an aware UTC datetime."""
    tz = ZoneInfo(cfg["timezone"])
    now = now or datetime.now(timezone.utc)
    hh, mm = (int(x) for x in cfg["local_time"].split(":"))
    days = {datetime.fromisoformat(t.replace("Z", "+00:00")).astimezone(tz).date() for t in taken}
    d = now.astimezone(tz).date()
    for _ in range(120):
        slot = datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz)
        if slot.weekday() in cfg["weekdays"] and slot.astimezone(timezone.utc) - now >= timedelta(minutes=cfg["min_lead_minutes"]) \
                and d not in days:
            return slot.astimezone(timezone.utc)
        d += timedelta(days=1)
    raise RuntimeError("no free slot in 120 days")


def plain_description(text, limit=5000):
    """owner 21.11: the channel has no advanced features, so no links: every source as plain text without
    http(s)://, no angle brackets, at most 5000 bytes."""
    import re
    text = re.sub(r"https?://", "", str(text or "")).replace("<", "").replace(">", "")
    raw = text.encode("utf-8")
    return raw[:limit].decode("utf-8", "ignore").rsplit("\n", 1)[0] if len(raw) > limit else text


def upload(yt, video, title, description, tags, publish_at):
    """Private + publishAt. selfDeclaredMadeForKids=false, containsSyntheticMedia=false, category 27 (Education)."""
    description = plain_description(description)
    from googleapiclient.http import MediaFileUpload
    status = {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False,
              "publishAt": publish_at.strftime("%Y-%m-%dT%H:%M:%SZ")}
    body = {"snippet": {"title": title[:100], "description": description[:5000], "tags": tags[:30], "categoryId": "27",
                        "defaultLanguage": "en", "defaultAudioLanguage": "en"}, "status": status}
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(video), chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]


def set_thumbnail(yt, video_id, path):
    from googleapiclient.http import MediaFileUpload
    yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(path))).execute()
