"""Historic city populations: Census twps0027 tables (1790-1990) + 2000/2010/2020 place counts + 2020 Gazetteer coords."""
import csv, json, re
from pathlib import Path
root = Path(__file__).resolve().parent.parent
YEARS = list(range(1790, 2021, 10))
# curated list: display name, state, table name stem (as printed, without ' city'/' town')
CUR = [("New York","NY","New York"),("Philadelphia","PA","Philadelphia"),("Boston","MA","Boston"),("Baltimore","MD","Baltimore"),
 ("Charleston","SC","Charleston"),("New Orleans","LA","New Orleans"),("Cincinnati","OH","Cincinnati"),("St. Louis","MO","St. Louis"),
 ("Chicago","IL","Chicago"),("Pittsburgh","PA","Pittsburgh"),("Detroit","MI","Detroit"),("Cleveland","OH","Cleveland"),
 ("Buffalo","NY","Buffalo"),("Washington","DC","Washington"),("Atlanta","GA","Atlanta"),("San Francisco","CA","San Francisco"),
 ("Los Angeles","CA","Los Angeles"),("Seattle","WA","Seattle"),("Denver","CO","Denver"),("Minneapolis","MN","Minneapolis"),
 ("Kansas City","MO","Kansas City"),("Omaha","NE","Omaha"),("Portland","OR","Portland"),
 ("Dallas","TX","Dallas"),("Houston","TX","Houston"),("San Antonio","TX","San Antonio"),("Miami","FL","Miami"),
 ("Phoenix","AZ","Phoenix"),("Las Vegas","NV","Las Vegas"),("San Diego","CA","San Diego"),("Memphis","TN","Memphis")]
def stem(n):
    n = re.sub(r"\s*\*\s*$", "", n).strip()
    return re.sub(r"\s+(city|town|borough|village|township|district|\(.*\))$", "", n).strip()
raw = {}   # (stem, st) -> {year: pop}
for k, y in enumerate(range(1790, 1991, 10)):
    t = root / f"data/cities/tab{k + 2:02d}.txt"
    for ln in t.read_text(encoding="latin-1").splitlines():
        for m in re.finditer(r"(\d+)t?\s+([A-Z][^,]*?,\s*[A-Z]{2})[^.]*?\.{2,}\s*([\d,]+)", ln):
            mm = re.match(r"(.+?),\s*([A-Z]{2})$", m.group(2).strip())
            if not mm: continue
            raw.setdefault((stem(mm.group(1)), mm.group(2)), {})[y] = int(m.group(3).replace(",", ""))
out = {}
def rows(p, enc="utf-8-sig"):
    return list(csv.DictReader(open(p, encoding=enc, errors="replace")))
st_name = {}
for r in rows(root / "data/cities/2020_Gaz_place_national.txt", "utf-8-sig") if False else []: pass
# gazetteer is tab separated
gaz = {}
with open(root / "data/cities/2020_Gaz_place_national.txt", encoding="latin-1") as f:
    rd = csv.reader(f, delimiter="\t"); head = [h.strip() for h in next(rd)]
    for r in rd:
        d = dict(zip(head, [x.strip() for x in r]))
        gaz[(d["USPS"], d["NAME"])] = (float(d["INTPTLONG"]), float(d["INTPTLAT"]), d["GEOID"])
USPS = {}
for r in rows(root / "data/cities/subest2022.csv"):
    if r["SUMLEV"] == "040": USPS[r["STNAME"]] = r["STATE"]
p2000 = {}; p2010 = {}; p2020 = {}
for r in rows(root / "data/cities/subest2009.csv"):
    if r["SUMLEV"] in ("162", "170"): p2000[(r["STATE"], r["PLACE"])] = int(r["POPCENSUS_2000"]) if r["POPCENSUS_2000"].isdigit() else 0
for r in rows(root / "data/cities/subest2019.csv"):
    if r["SUMLEV"] in ("162", "170"): p2010[(r["STATE"], r["PLACE"])] = int(r["CENSUS2010POP"]) if r["CENSUS2010POP"].isdigit() else 0
for r in rows(root / "data/cities/subest2022.csv"):
    if r["SUMLEV"] in ("162", "170"): p2020[(r["STATE"], r["PLACE"])] = int(r["ESTIMATESBASE2020"]) if r["ESTIMATESBASE2020"].isdigit() else 0
cities = []
for disp, st, key in CUR:
    pops = dict(raw.get((key, st), {}))
    if st == "DC": g = gaz.get(("DC", "Washington city"))
    else: g = gaz.get((st, key + " city")) or gaz.get((st, key + " town")) or gaz.get((st, key + " (balance)"))
    if g is None:
        cand = [k for k in gaz if k[0] == st and k[1].startswith(key)]
        print("no gazetteer exact for", disp, st, cand[:4]); 
        if not cand: continue
        g = gaz[cand[0]]
    lon, lat, geoid = g
    sfips, pfips = geoid[:2], geoid[2:]
    for y, dct in ((2000, p2000), (2010, p2010), (2020, p2020)):
        v = dct.get((sfips, pfips))
        if v: pops[y] = v
    if disp == 'Charleston': pops = {y: v for y, v in pops.items() if y < 1920}
    cities.append(dict(name=disp, st=st, lon=lon, lat=lat, pop={str(y): pops[y] for y in sorted(pops)}))
json.dump(cities, open(root / "data/cities.json", "w"), indent=0)
for c in cities:
    ys = sorted(int(y) for y in c["pop"]); gaps = [y for y in YEARS if y >= ys[0] and str(y) not in c["pop"]]
    print(f"{c['name']:15s} {ys[0]}..{ys[-1]} n={len(ys)} gaps={gaps}  2020={c['pop'].get('2020')}")
