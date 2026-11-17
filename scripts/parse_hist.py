"""Parse Forstall (Census 1996) Part II state table from OCR text; validate against sums and apportionment.csv."""
import csv, json, re, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
T = (root / "data/hist/txt/forstall.txt").read_text(encoding="utf-8").splitlines()

def pages():
    out, cur = [], None
    for i, ln in enumerate(T):
        if re.search(r"POPUL.?ATION OF STATES: (\d{4})-(\d{4})", ln):
            cur = {"start": i, "hdr": None, "rows": []}; out.append(cur)
        elif cur is not None:
            if cur["hdr"] is None and re.search(r"\b1[789]\d0\b|\b20\d0\b", ln) and len(re.findall(r"\b\d{4}\b", ln)) >= 5:
                cur["hdr"] = ln
            elif cur["hdr"] is not None:
                if "HISTORICAL DATES" in ln: break
                cur["rows"].append(ln)
    return out

NUM = re.compile(r"[\d.,'~•\-]*\d[\d.,'~•]*")
def parse_page(p):
    hdr = p["hdr"]
    cols = [(int(m.group()), m.end()) for m in re.finditer(r"\d{4}", hdr)]
    res = {}
    for ln in p["rows"]:
        m = re.match(r"\s*([A-Za-z][A-Za-z .]+?)\s{2,}(.*)$", ln)
        if not m:
            m2 = re.match(r"\s*(UNITED STATES)\s+(.*)$", ln)
            if not m2: continue
            m = m2
        name = m.group(1).strip().replace("Califomia", "California").replace("UNITED STATES", "United States")
        base = len(ln) - len(m.group(2))
        vals = {}
        for t in NUM.finditer(m.group(2)):
            end = base + t.end()
            digits = re.sub(r"\D", "", t.group())
            if not digits: continue
            yr = min(cols, key=lambda c: abs(c[1] - end))[0]
            vals[yr] = int(digits)
        res[name] = vals
    return res

data = {}
for p in pages():
    for k, v in parse_page(p).items():
        data.setdefault(k, {}).update({y: n for y, n in v.items()})
json.dump(data, open(root / "data/hist/forstall_parsed.json", "w"), indent=0, sort_keys=True)

# validation
ap = {}
with open(root / "data/census/apportionment.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        ap[(r["Name"], int(r["Year"]))] = int(r["Resident Population"].replace(",", ""))
states = [k for k in data if k != "United States"]
print("rows", len(states))
for y in range(1790, 1991, 10):
    s = sum(data[k].get(y, 0) for k in states)
    us = data["United States"].get(y)
    print(y, "sum", s, "US", us, "diff", s - us if us else None)
bad = []
for k in states:
    for y in range(1910, 1991, 10):
        a = ap.get((k, y)); v = data[k].get(y)
        if a is not None and v != a: bad.append((k, y, v, a))
print("OCR vs apportionment (1910-1990) mismatches:", len(bad), "of", sum(1 for k in states for y in range(1910,1991,10) if (k,y) in ap))
for b in bad[:12]: print(" ", b)
