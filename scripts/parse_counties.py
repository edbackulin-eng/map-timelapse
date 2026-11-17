"""Parse Part III (county tables) of Forstall 1996 (OCR text) -> data/counties_hist.json.
Columns are taken from the state-total row of each table; county tokens are assigned to columns with a
monotonic dynamic-programming alignment. Validation: sum of counties vs printed state total, per state/year."""
import json, re, sys
from collections import defaultdict
from pathlib import Path
root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from mapviz.choro import STATE_NAMES  # noqa: E402
T = (root / "data/hist/txt/forstall_full.txt").read_text(encoding="utf-8", errors="replace").splitlines()
SN = {re.sub(r"[^A-Z]", "", v.upper()): k for k, v in STATE_NAMES.items()}
SN["ALASKA"] = "AK"; SN["HAWAII"] = "HI"; SN["DISTRICTOFCOLUMBIA"] = "DC"
NUM = re.compile(r"[\d.,'~•]*\d[\d.,'~•]*")
ALLY = list(range(1990, 1779, -10))

def norm(n):
    return re.sub(r"[^A-Za-z]", "", re.sub(r"\(.*?\)|\*", "", n)).lower()

def tokens(s, off):
    out = []
    for t in NUM.finditer(s):
        d = re.sub(r"\D", "", t.group())
        if d: out.append((off + t.end(), int(d)))
    return out

def years_of(line):
    """years in the header line, tolerant to OCR damage like '1~40' (fills gaps by the decade sequence)."""
    ys = [int(x) for x in re.findall(r"\b(1[789]\d0|20\d0)\b", line)]
    return ys

heads = [i for i, l in enumerate(T) if l.lstrip().startswith("POPULATION OF COUNTIES")]
tables = []
for hi in heads:
    h = T[hi]
    comp = re.sub(r"[^A-Z]", "", h.upper().split("COUNTIES", 1)[1])
    ab = next((v for k, v in sorted(SN.items(), key=lambda kv: -len(kv[0])) if comp.startswith(k) or ("ISLANDS" in comp and k in comp)), None)
    if not ab or "NOTES" in h: continue
    hdr = next((j for j in range(hi + 1, hi + 6) if len(re.findall(r"\b\d[\d~l]{3}\b", T[j])) >= 4), None)
    if hdr is None: continue
    hy = [int(x) if x.isdigit() else None for x in re.findall(r"\b\d[\d~l]{3}\b", T[hdr])]
    # reconstruct the year sequence from the first/last valid year
    valid = [y for y in hy if y]
    first, n = valid[0], len(hy)
    cols_years = [first - 10 * i for i in range(n)]
    # state total row = first non-empty row below the header
    k = hdr + 1
    while k < len(T) and not T[k].strip(): k += 1
    mm = re.match(r"\s*([A-Za-z .]+?)\s{2,}(.*)$", T[k])
    if not mm: continue
    tot = tokens(mm.group(2), len(T[k]) - len(mm.group(2)))
    if len(tot) < max(3, n - 2): 
        # no usable total row; fall back to header positions
        pos = [m.end() for m in re.finditer(r"\b\d[\d~l]{3}\b", T[hdr])]
        totvals = {}
    else:
        pos = [p for p, _ in tot]
        totvals = {y: v for y, (p, v) in zip(cols_years, tot)}
        if len(pos) < n: pos = [m.end() for m in re.finditer(r"\b\d[\d~l]{3}\b", T[hdr])]; totvals = {}
    rows = []
    for r in range(k + 1, k + 150):
        if r >= len(T): break
        l = T[r]
        if re.search(r"NOTES|County Notes|POPULATION OF COUNTIES|^\s*Part [IVm]+", l): break
        if not l.strip(): continue
        mm = re.match(r"\s*([A-Za-z][A-Za-z.'’\- ()]*?)(?:\s{2,}|\s(?=[\d.,\-]))(.*)$", l)
        if not mm: continue
        tk = tokens(mm.group(2), len(l) - len(mm.group(2)))
        if not tk: continue
        # monotone assignment of k tokens to n columns minimising position error
        kk = len(tk)
        if kk > n: tk = tk[:n]; kk = n
        INF = 1e18
        dp = [[INF] * (n + 1) for _ in range(kk + 1)]
        bk = [[0] * (n + 1) for _ in range(kk + 1)]
        dp[0] = [0.0] * (n + 1)
        for i in range(1, kk + 1):
            for j in range(i, n + 1):
                best, arg = dp[i][j - 1], 0  # column j-1 unused
                c = dp[i - 1][j - 1] + abs(tk[i - 1][0] - pos[j - 1])
                if c < best and True: best, arg = c, 1
                dp[i][j] = best; bk[i][j] = arg
        j = n; i = kk; assign = {}
        while i > 0 and j > 0:
            if bk[i][j] == 1: assign[j - 1] = tk[i - 1][1]; i -= 1; j -= 1
            else: j -= 1
        rows.append((mm.group(1).strip(), {cols_years[c]: v for c, v in assign.items()}))
    tables.append((ab, totvals, rows))

state_tot = defaultdict(dict)
counties = defaultdict(dict)
for ab, totvals, rows in tables:
    state_tot[ab].update(totvals)
    for name, vals in rows:
        e = counties[(ab, norm(name))]
        e.setdefault("name", name); e.setdefault("pop", {}).update(vals)
json.dump({"counties": {f"{a}|{k}": v for (a, k), v in counties.items()}, "state_totals": state_tot},
          open(root / "data/counties_hist.json", "w"))
print("tables", len(tables), "counties", len(counties), "states with totals", len(state_tot))
import collections
okc = collections.Counter(); nc = collections.Counter(); worst = []
for ab, t in state_tot.items():
    for y, v in t.items():
        s = sum(e["pop"].get(y, 0) for (a, _), e in counties.items() if a == ab)
        nc[y] += 1
        if s == v: okc[y] += 1
        else: worst.append((round(abs(s - v) / max(v, 1), 4), ab, y, s, v))
print({y: (okc[y], nc[y]) for y in sorted(nc)})
print("missing states:", [a for a in list(STATE_NAMES) if a not in state_tot])
for w in sorted(worst, reverse=True)[:12]: print(w)
