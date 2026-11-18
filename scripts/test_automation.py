"""Offline tests of the upload guards (no network, no token)."""
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from automation import meta, youtube  # noqa: E402

ok = True


def check(name, cond):
    global ok
    print(("PASS " if cond else "FAIL ") + name)
    ok &= bool(cond)


class FakeList:
    def __init__(self, items): self.items = items
    def execute(self): return {"items": self.items}


class FakeCh:
    def __init__(self, items): self.items = items
    def list(self, **kw): return FakeList(self.items)


class FakeYT:
    def __init__(self, items): self._i = items
    def channels(self): return FakeCh(self._i)


good = [{"id": "UC_GOOD", "snippet": {"title": "America Over Time"}}]
check("right channel passes", youtube.assert_channel(FakeYT(good), "UC_GOOD")["id"] == "UC_GOOD")
for name, yt, exp in (("wrong channel id", FakeYT(good), "UC_OTHER"), ("empty YT_CHANNEL_ID", FakeYT(good), ""), ("two channels", FakeYT(good * 2), "UC_GOOD"),
                      ("no channel", FakeYT([]), "UC_GOOD")):
    try:
        youtube.assert_channel(yt, exp)
        check(name + " refused", False)
    except youtube.Doubt:
        check(name + " refused", True)

vids = [{"id": "a", "title": "x", "description": "blah [ref: map-timelapse/sun-belt]", "privacy": "private", "publish_at": "2026-11-23T18:00:00Z", "published_at": None},
        {"id": "b", "title": "US Population 1790–2020: How America Grew Across the Map", "description": "", "privacy": "public",
         "publish_at": None, "published_at": "2026-11-20T18:00:00Z"}]
check("marker found", youtube.find_existing(vids, "sun-belt", "T")["id"] == "a")
check("same title found", youtube.find_existing(vids, "us-population-1790-2020", vids[1]["title"])["id"] == "b")
check("new slug not found", youtube.find_existing(vids, "texas", "Texas") is None)

# slots: Monday and Friday 20:00 Kyiv, winter (UTC+2) and summer (UTC+3)
for now, exp in ((datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc), "2026-11-20T18:00:00"),      # Tue -> Fri 20:00 EET = 18:00 UTC
                 (datetime(2026, 7, 1, 12, 0, tzinfo=timezone.utc), "2026-07-03T17:00:00")):         # Wed -> Fri 20:00 EEST = 17:00 UTC
    s = youtube.next_slot((), now)
    check(f"slot {now.date()} -> {s.isoformat()}", s.strftime("%Y-%m-%dT%H:%M:%S") == exp)
s2 = youtube.next_slot(["2026-11-20T18:00:00Z"], datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc))
check("taken slot skipped -> Monday", s2.strftime("%Y-%m-%d") == "2026-11-23")
check("scheduled_ahead counts future publishAt", youtube.scheduled_ahead(vids, datetime(2026, 11, 20, tzinfo=timezone.utc)) == 1)

for mod in ("us_population", "sun_belt", "texas", "california", "cities_decline", "expansion"):
    t = importlib.import_module("mapviz.topics." + mod)
    title, desc, tags = meta.build(t, t.SLUG)
    check(f"{mod}: title<=100, desc<=5000, ref marker, 3-5 hashtags, tags", len(title) <= 100 and len(desc) <= 5000 and f"[ref: map-timelapse/{t.SLUG}]" in desc
          and 3 <= len(t.HASHTAGS) <= 5 and len(tags) >= 8)
    print(f"   {title} | desc {len(desc)} chars | {len(tags)} tags")
sys.exit(0 if ok else 1)
