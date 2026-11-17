"""Write docs/cards_report.md: every on-screen fact card, to be checked against the Census files."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mapviz import video as V
D = V.data()
out = ["# On-screen facts per census (generated; every number is computed from data/population.json)\n",
       "| Year | U.S. total (Census) | Card | Text on screen |", "|---|---|---|---|"]
for i, y in enumerate(V.YEARS):
    for c in V.cards(i):
        v = c["value"]
        t = c["text"].replace("{v}", f"{v:,}") if v is not None else c["text"]
        out.append(f"| {y} | {D['us_total'][y]:,} | {c['label']} | {t} |")
Path(__file__).resolve().parent.parent.joinpath("docs/cards_report.md").write_text("\n".join(out), encoding="utf-8")
print("\n".join(out[:30]))

# ---- cross-check "fastest growth" percentages against Census's own percent-change column (1920-2020)
import csv, re
rows = {}
with open(Path(__file__).resolve().parent.parent / "data/census/apportionment.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        rows[(r["Name"], int(r["Year"]))] = r["Percent Change in Resident Population"]
chk = ["", "## Cross-check: computed growth vs Census 'Percent Change' column (apportionment.csv)", "",
       "| Year | State | Computed on screen | Census column | OK |", "|---|---|---|---|---|"]
for i, y in enumerate(V.YEARS):
    if y < 1920: continue
    c = [c for c in V.cards(i) if c["label"].startswith("FASTEST")][0]
    m = re.match(r"(.+?)\s+·\s+\+([\d,.]+)%", c["text"]); name = m.group(1).title(); comp = float(m.group(2).replace(",", ""))
    ref = float(rows[(name, y)]); ok = abs(comp - ref) < 0.06
    chk.append(f"| {y} | {name} | {comp} | {ref} | {'yes' if ok else 'NO'} |"); assert ok, (y, name, comp, ref)
open(Path(__file__).resolve().parent.parent / "docs/cards_report.md", "a", encoding="utf-8").write("\n".join(chk))
print("\n".join(chk))
