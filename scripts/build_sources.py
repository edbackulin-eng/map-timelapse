"""Write data/sources/<slug>.json (and data/sources.json for the first video): every event / migration / data layer with its source.
TOPIC=<module> selects the topic (default us-population)."""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from mapviz import video2 as V  # noqa: E402

TP = V.TP
story = TP.story
out = {"retrieved": "2026-11-17", "slug": TP.SLUG, "sources": story.SOURCES, "events": [], "migrations": [], "layers": {}}
for ev in story.EVENTS:
    out["events"].append(dict(year=ev["year"], title=ev["title"], text=V.event_text(ev), source=ev["src"], url=story.SOURCES[ev["src"]]["url"]))
for m in story.MIGRATIONS:
    out["migrations"].append(dict(name=m["name"], years=[m["y0"], m["y1"]], label=m["label"], source=m["src"], url=story.SOURCES[m["src"]]["url"],
                                  note="arrow geometry is schematic (region to region), not a measured flow"))
out["layers"] = {
    "state_populations": ["census_states", "census_apport"], "cities": ["census_cities"], "zoom_counties": ["census_counties", "census_apport"],
    "centers_of_population": ["census_centers"], "interstates": ["ne_roads", "interstate"],
}
if getattr(TP, "FOCUS", None):
    out["layers"]["counties"] = dict(sources=["census_counties", "census_counties_0010", "census_centers"],
                                     note="county density on today's county boundaries (2020 land area); before 1900 the map shows the state average.")
    out["sources"]["census_counties_0010"] = dict(title="County population totals: Census 2000 (co-est2009-alldata) and Census 2010 (co-est2019-alldata)",
                                                  publisher="U.S. Census Bureau", url="https://www2.census.gov/programs-surveys/popest/datasets/",
                                                  supports="CENSUS2000POP and CENSUS2010POP of every county")
    out["layers"]["cities"] = ["census_cities"]
if story.RAILS or story.TRANSCON:
    out["layers"]["railroads"] = dict(sources=["railmaps", "golden_spike"],
                                      note="SIMPLIFIED polylines through well-known cities; construction dates are decade-level approximations except the 1863-1869 transcontinental (NPS).")
if TP.FRONTIER:
    out["layers"]["frontier"] = dict(sources=["frontier"], note="approximation: a state counts as settled when its Census density is 2+ people per sq mi (state-level, not county-level).")
(root / "data" / "sources").mkdir(exist_ok=True)
(root / "data" / "sources" / f"{TP.SLUG}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
if TP.SLUG.startswith("us-population"):
    (root / "data/sources.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(len(out["events"]), "events,", len(out["migrations"]), "migrations ->", f"data/sources/{TP.SLUG}.json")
