"""Write data/sources.json: every event / migration / data layer with its source (url, publisher, what it supports)."""
import json, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from mapviz import story, video2 as V
out = {"retrieved": "2026-11-17", "sources": story.SOURCES, "events": [], "migrations": [], "layers": {}}
for ev in story.EVENTS:
    out["events"].append(dict(year=ev["year"], title=ev["title"], text=V.event_text(ev), source=ev["src"], url=story.SOURCES[ev["src"]]["url"]))
for m in story.MIGRATIONS:
    out["migrations"].append(dict(name=m["name"], years=[m["y0"], m["y1"]], label=m["label"], source=m["src"], url=story.SOURCES[m["src"]]["url"],
                                  note="arrow geometry is schematic (region to region), not a measured flow"))
out["layers"] = {
    "state_populations": ["census_states", "census_apport"], "cities": ["census_cities"], "zoom_counties": ["census_counties", "census_apport"],
    "centers_of_population": ["census_centers"], "interstates": ["ne_roads", "interstate"],
    "railroads": dict(sources=["railmaps", "golden_spike"], note="SIMPLIFIED polylines through well-known cities; construction dates are decade-level approximations except the 1863-1869 transcontinental (NPS)."),
    "frontier": dict(sources=["frontier"], note="approximation: a state counts as settled when its Census density is 2+ people per sq mi (state-level, not county-level)."),
}
(root / "data/sources.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(out["events"]), "events,", len(out["migrations"]), "migrations ->", "data/sources.json")
