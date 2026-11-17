"""Download the CC0 tracks (OpenGameArt) and re-check the licence on each page."""
import json, re, subprocess, sys, urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent.parent
reg = json.load(open(root / "data/music/registry_source.json", encoding="utf-8"))["tracks"]
out = root / "assets" / "music"
out.mkdir(parents=True, exist_ok=True)
ua = {"User-Agent": "map-timelapse-licence-check"}
report = []
for t in reg:
    if t.get("status") != "active":
        continue
    html = urllib.request.urlopen(urllib.request.Request(t["page"], headers=ua), timeout=60).read().decode("utf-8", "ignore")
    lic = re.findall(r'creativecommons\.org/(publicdomain/zero|licenses)/([^"\']*)', html)
    kinds = sorted({a + "/" + b for a, b in lic})
    ok = bool(lic) and all(a == "publicdomain/zero" for a, _ in lic)
    report.append({"id": t["id"], "page": t["page"], "licence_links_on_page": kinds, "cc0_only": ok})
    if not ok:
        print("LICENCE NOT CC0-ONLY", t["id"], kinds); continue
    f = out / f"{t['id']}.mp3"
    req = urllib.request.Request(t["url"], headers=ua)
    f.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True).stdout.strip()
    report[-1]["seconds"] = float(dur); report[-1]["creator"] = t["creator"]; report[-1]["title"] = t["title"]
    print("ok", t["id"], dur, kinds)
json.dump(report, open(root / "data/music/licence_check.json", "w", encoding="utf-8"), indent=1)
