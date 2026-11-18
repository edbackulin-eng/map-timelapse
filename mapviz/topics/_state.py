"""Shared facts / captions for one-state topics (state mode: FOCUS = 'TX', 'CA', ...).
Numbers come only from the Census tables in the repo: state totals (population.json), county counts (1900-1990 file,
2000/2010 counts, 2020 counts) and the city tables."""
import csv
from functools import lru_cache

import shapefile

from ..core import CENSUS, ROOT
from ..video import down, up


@lru_cache(None)
def county_names():
    r = shapefile.Reader(str(CENSUS / "counties" / "cb_2020_us_county_20m"))
    return {rec["GEOID"]: rec["NAME"] for rec in r.iterRecords(fields=["GEOID", "NAME"])}


def seats_change(state_name, y0, y1):
    """House seats of a state in two apportionments (Census apportionment.csv)."""
    v = {}
    for r in csv.DictReader(open(ROOT / "data/census/apportionment.csv", encoding="utf-8-sig")):
        if r["Name"] == state_name and r["Geography Type"] == "State" and r["Year"] in (str(y0), str(y1)):
            if r["Number of Representatives"].strip():
                v[int(r["Year"])] = int(r["Number of Representatives"])
    return v.get(y0), v.get(y1)


def rank(D, ab, y):
    pops = {a: s[y] for a, s in D["pop"].items() if a != "DC" and s.get(y)}
    order = sorted(pops, key=lambda a: -pops[a])
    return order.index(ab) + 1, len(order)


def county_pops(X, st, y):
    """GEOID -> population of the state's counties in year y (only counties with a count)."""
    h = X.county_hist()
    names = county_names()
    fips = {g for g, (s, _) in X.counties().items() if s == st}
    return {g: h[g][y] for g in fips if y in h.get(g, {}) and g in names}


def short(n):
    return f"{n / 1e6:.1f} MILLION" if n >= 1e6 else f"{n:,}"


def make(st, name, county_from=1900):
    """-> (facts, captions) functions for the topic module."""
    NAME = name.upper()

    def facts(i, X):
        D, Y = X.D, X.YEARS
        y = Y[i]
        ser = D["pop"][st]
        out = []
        r, n = rank(D, st, y)
        share = 100.0 * ser[y] / D["us_total"][y]
        if i == 0:
            out.append(dict(label=f"{NAME} IN {y}", text=f"{ser[y]:,} PEOPLE COUNTED", hl=[]))
        cp = county_pops(X, st, y) if y >= county_from else {}
        if cp:
            g = max(cp, key=cp.get)
            out.append(dict(label="LARGEST COUNTY", text=f"{county_names()[g].upper()}  ·  {cp[g]:,}", hl=[g]))
        if i > 0:
            py = Y[i - 1]
            cp0 = county_pops(X, st, py) if py >= county_from else {}
            gr = {g: (cp[g] / cp0[g] - 1) * 100 for g in cp if g in cp0 and cp0[g] >= 10000}
            if gr:
                g = max(gr, key=gr.get)
                out.append(dict(label=f"FASTEST-GROWING COUNTY SINCE {py}", text=f"{county_names()[g].upper()}  ·  {up(X.pct_txt(gr[g]))}", hl=[g]))
            else:
                g_ = (ser[y] / ser[py] - 1) * 100
                out.append(dict(label=f"{NAME} GROWTH SINCE {py}", text=up(X.pct_txt(g_)) if g_ >= 0 else down(f"{abs(g_):.1f}%"), hl=[]))
            s0 = 100.0 * ser[py] / D["us_total"][py]
            out.append(dict(label="SHARE OF ALL AMERICANS", text=f"{share:.1f}%  (WAS {s0:.1f}% IN {py})", hl=[]))
            r0, _ = rank(D, st, py)
            out.append(dict(label="POPULATION RANK IN THE U.S.", text=f"#{r}" + (f"  (UP FROM #{r0})" if r0 > r else (f"  (DOWN FROM #{r0})" if r0 < r else "")), hl=[]))
        else:
            out.append(dict(label="SHARE OF ALL AMERICANS", text=f"{share:.1f}%", hl=[]))
            out.append(dict(label="POPULATION RANK IN THE U.S.", text=f"#{r} OF {n} STATES AND TERRITORIES", hl=[]))
        return out

    def captions(i, X):
        D, Y = X.D, X.YEARS
        ser = D["pop"][st]
        if i == 0:
            return [(X.INTRO + 5.5, 7.5, captions.CAP0)]
        y0, y1 = Y[i - 1], Y[i]
        d = ser[y1] - ser[y0]
        g = (ser[y1] / ser[y0] - 1) * 100
        out = []
        zoom = next((z for z in X.zooms if z["y1"] == y1), None)
        c = next((c for c in X.cities() if zoom and c["name"] == zoom["name"]), None)
        if c and c["pop"].get(str(y0)) and c["pop"].get(str(y1)):
            out.append((0.8, 7.0, f"{zoom['name'].upper()} {y0}-{y1}: {c['pop'][str(y0)]:,} → {c['pop'][str(y1)]:,} PEOPLE"))
        else:
            verb = "ADDS" if d >= 0 else "LOSES"
            out.append((0.8, 7.0, f"{y0}-{y1}: {NAME} {verb} {abs(d):,} PEOPLE ({up(X.pct_txt(g)) if g >= 0 else down(f'{abs(g):.1f}%')})"))
        cs = [(c["pop"].get(str(y1)), c["name"]) for c in X.cities() if c["pop"].get(str(y1))]
        if cs:
            p, n = max(cs)
            out.append((X.RUN + 3.2, 7.5, f"LARGEST CITY IN {NAME} IN {y1}: {n.upper()} ({p:,})"))
        out.append((X.RUN + 11.5, 7.5, f"{y1}: {ser[y1]:,} PEOPLE IN {NAME}"))
        return out

    captions.CAP0 = ""
    return facts, captions
