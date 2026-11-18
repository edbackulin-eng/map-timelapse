"""America Over Time v2: U.S. population 1790-2020, one master year value drives everything.

Master timeline (24 fps):
  block 0  : 1790  = 8 s title + 14 s facts
  block i  : census i-1 -> i = 11 s RUN (counter ticks year by year, cities/rails/arrows animate with the year)
             + 14 s HOLD (state colours switch exactly when the counter reaches the census year, fade 1.5 s)
  finale   : 28 s (2020 counties + credits)
"""
from __future__ import annotations

import csv
import json
import math
import re
import subprocess
from functools import lru_cache

import numpy as np
import shapefile
from PIL import Image, ImageDraw

from . import topic as _topic

TP = _topic.load()
story = TP.story
from .choro import NEIGHBOUR, NEIGHBOUR_LINE, OCEAN, STATE_NAMES, counties, lakes, neighbours
from .choro import render as choro_render
from .core import CENSUS, ROOT, albers, states
from .icons import icon
from .video import (BLACK, FPS, H, MAPBOX, NAVY, RX0, RX1, RY0, RY1, UNCOUNTED, W, WHITE, YEARS, YEL, F, Layers, T,
                    compass, data, ease, miles, pct_txt, chg, up, down, rich_len, rich_text, CHG_RE)

YEARS = TP.YEARS
NB = len(YEARS)
INTRO, RUN, HOLD, FIN, FADE = 8.0, TP.RUN, TP.HOLD, 28.0, 1.5
BLK = RUN + HOLD
B0 = INTRO + HOLD
TOTAL_S = B0 + BLK * (NB - 1) + FIN
TOTAL_FRAMES = int(round(TOTAL_S * FPS))
RW, RH = RX1 - RX0, RY1 - RY0
FOCUS = getattr(TP, "FOCUS", None)              # state mode: camera on one state, county map all the time
SHOW_CENTER = getattr(TP, "SHOW_CENTER", FOCUS is None)
COUNTY_FROM = 1900                              # first year with county counts for every county

STOPS8 = [(140, 0, 30), (225, 25, 30), (255, 110, 0), (255, 215, 0), (130, 222, 30), (0, 190, 110), (0, 135, 120), (10, 50, 125)]
BREAKS8 = [2, 6, 18, 45, 100, 250, 1000]
LABELS8 = ["UNDER 2", "2–6", "6–18", "18–45", "45–100", "100–250", "250–1,000", "1,000+"]


def cls8(d):
    return int(np.searchsorted(BREAKS8, d, side="right"))


def pos_color(pos):
    pos = min(max(pos, 0.0), len(STOPS8) - 1.0)
    i = min(int(pos), len(STOPS8) - 2)
    t = pos - i
    a, b = np.array(STOPS8[i], float), np.array(STOPS8[i + 1], float)
    return tuple(a + (b - a) * t)


def lerp_col(a, b, t):
    return tuple(np.array(a, float) * (1 - t) + np.array(b, float) * t)


# ------------------------------------------------------------------ view helper (supports zoom)
class VW:
    def __init__(self, s, ox, oy):
        self.s, self.ox, self.oy = s, ox, oy

    def px(self, x, y):
        return self.ox + np.asarray(x) * self.s, self.oy - np.asarray(y) * self.s

    def rect(self):
        """visible rectangle in albers coords for the map box region."""
        x0, x1 = (RX0 - self.ox) / self.s, (RX1 - self.ox) / self.s
        y1, y0 = (self.oy - RY0) / self.s, (self.oy - RY1) / self.s
        return x0, x1, y0, y1


def dilate(a, r):
    """boolean dilation by a (2r+1) square using integral images."""
    a = a.astype(np.int32)
    for axis in (0, 1):
        pad = [(r + 1, r) if k == axis else (0, 0) for k in range(2)]
        c = np.cumsum(np.pad(a, pad), axis=axis)
        hi = [slice(None)] * 2
        lo = [slice(None)] * 2
        hi[axis] = slice(2 * r + 1, None)
        lo[axis] = slice(None, -(2 * r + 1))
        a = c[tuple(hi)] - c[tuple(lo)]
    return a > 0


def wrap(text, size, width):
    words, lines, cur = re.findall(r"[▲▼]\d[\d.,]*(?: MILLION|%)?|\S+", text), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if rich_len(t, size) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ data loaders
@lru_cache(None)
def cities():
    cs = json.load(open(ROOT / getattr(TP, "CITIES_FILE", "data/cities.json")))
    for c in cs:
        c["ax"], c["ay"] = (float(v) for v in albers(c["lon"], c["lat"]))
        c["pops"] = [c["pop"].get(str(y)) for y in YEARS]
    return cs


@lru_cache(None)
def county_hist():
    """FIPS -> {year: pop} 1900-1990 (Census, Forstall) + 2020 (CenPop2020)."""
    out = {}
    for l in open(ROOT / "data/cencounts/1900-90.txt", encoding="latin-1"):
        m = re.match(r"^(\d{5})\s+((?:(?:-?\d+|---)\s+){10})([A-Z]{2})\s+(.*?)\s*$", l)
        if not m:
            continue
        vals = m.group(2).split()
        out[m.group(1)] = {1990 - 10 * k: int(v) for k, v in enumerate(vals) if v != "---"}
    with open(CENSUS / "CenPop2020_Mean_CO.txt", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["STATEFP"] + r["COUNTYFP"], {})[2020] = int(r["POPULATION"])
    p0010 = CENSUS / "county_2000_2010.csv"
    if p0010.exists():
        with open(p0010, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                for y, col in ((2000, "CENSUS2000POP"), (2010, "CENSUS2010POP")):
                    if r[col].strip():
                        out.setdefault(r["GEOID"], {})[y] = int(r[col])
    return out


def ctx():
    """what a topic module needs to write its own facts / captions"""
    from types import SimpleNamespace
    return SimpleNamespace(D=data(), YEARS=YEARS, RUN=RUN, HOLD=HOLD, INTRO=INTRO, county_hist=county_hist, county_area=county_area,
                           cities=cities, STATE_NAMES=STATE_NAMES, pct_txt=pct_txt, zooms=story.ZOOMS, counties=counties)


@lru_cache(None)
def county_area():
    a = {}
    with open(CENSUS / "2020_Gaz_counties_national.txt", encoding="utf-8") as f:
        rows = csv.reader(f, delimiter="\t")
        head = [h.strip() for h in next(rows)]
        gi, ai = head.index("GEOID"), head.index("ALAND_SQMI")
        for r in rows:
            a[r[gi].strip()] = float(r[ai])
    return a


@lru_cache(None)
def interstates():
    r = shapefile.Reader(str(ROOT / "data/ne2/roads/ne_10m_roads_north_america"))
    feats = []
    for sr in r.iterShapeRecords():
        rec = sr.record
        if rec["prefix"] != "I" or rec["country"] != "United States" or not str(rec["number"]).isdigit() or int(rec["number"]) >= 100:
            continue
        pts = np.array(sr.shape.points)
        if len(pts) < 2 or pts[:, 1].min() < 24.5 or pts[:, 1].max() > 49.5 or pts[:, 0].min() < -125.5 or pts[:, 0].max() > -66:
            continue
        parts = list(sr.shape.parts) + [len(pts)]
        for a, b in zip(parts[:-1], parts[1:]):
            seg = pts[a:b:2] if b - a > 6 else pts[a:b]
            if len(seg) < 2:
                continue
            x, y = albers(seg[:, 0], seg[:, 1])
            feats.append(np.column_stack([x, y]))
    rng = np.random.default_rng(7)
    order = rng.permutation(len(feats))
    return [(feats[k], rank / len(feats)) for rank, k in enumerate(order)]


def to_albers(ll):
    a = np.array(ll, float)
    x, y = albers(a[:, 0], a[:, 1])
    return np.column_stack([x, y])


def smooth(pts, n=10):
    """Catmull-Rom through the points (adds gentle curvature to simplified routes)."""
    p = np.vstack([pts[0], pts, pts[-1]])
    out = []
    for k in range(1, len(p) - 2):
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p[k]) + (-p[k - 1] + p[k + 1]) * t + (2 * p[k - 1] - 5 * p[k] + 4 * p[k + 1] - p[k + 2]) * t ** 2
                              + (-p[k - 1] + 3 * p[k] - 3 * p[k + 1] + p[k + 2]) * t ** 3))
    out.append(p[-2])
    return np.array(out)


def partial(pts, frac):
    """first `frac` of the polyline (by length)."""
    if frac >= 1:
        return pts
    seg = np.hypot(*(np.diff(pts, axis=0).T))
    cum = np.concatenate([[0], np.cumsum(seg)])
    target = cum[-1] * frac
    k = int(np.searchsorted(cum, target))
    if k <= 0:
        return pts[:1]
    k = min(k, len(pts) - 1)
    t = (target - cum[k - 1]) / max(cum[k] - cum[k - 1], 1e-9)
    return np.vstack([pts[:k], pts[k - 1] + (pts[k] - pts[k - 1]) * t])


# ------------------------------------------------------------------ facts (toasts)
def facts(i):
    if hasattr(TP, "facts"):
        return TP.facts(i, ctx())
    D = data()
    y = YEARS[i]
    nm = lambda ab: STATE_NAMES[ab].upper()
    pop = {ab: D["pop"][ab].get(y) for ab in STATE_NAMES if ab != "DC"}
    pop = {k: v for k, v in pop.items() if v}
    out = []
    if i == 0:
        out.append(dict(label=TP.FIRST_LABEL, text=f"{D['us_total'][y]:,} PEOPLE COUNTED", hl=[]))
    top = max(pop, key=pop.get)
    out.append(dict(label="MOST POPULOUS STATE", text=f"{nm(top)}  ·  {pop[top]:,}", hl=[top]))
    if i == 0:
        dn = max(pop, key=lambda a: D["dens"][a][y])
        out.append(dict(label="DENSEST STATE, PEOPLE PER SQ MI", text=f"{nm(dn)}  ·  {round(D['dens'][dn][y])}", hl=[dn]))
    else:
        py = YEARS[i - 1]
        gr = {a: (pop[a] / D["pop"][a][py] - 1) * 100 for a in pop if py in D["pop"][a] and D["pop"][a][py] >= 25000}
        fa = max(gr, key=gr.get)
        out.append(dict(label=f"FASTEST GROWTH SINCE {py}", text=f"{nm(fa)}  ·  {up(pct_txt(gr[fa]))}", hl=[fa]))
        new = [a for a in pop if py not in D["pop"][a]]
        if new:
            names = [nm(a) for a in sorted(new, key=lambda a: -pop[a])]
            txt = ", ".join(names[:3]) + (f" AND {len(names) - 3} MORE" if len(names) > 3 else "")
            out.append(dict(label="FIRST COUNTED IN THE CENSUS", text=txt, hl=new))
        else:
            gn = {a: pop[a] - D["pop"][a][py] for a in pop if py in D["pop"][a]}
            ga = max(gn, key=gn.get)
            v = gn[ga]
            vt = up(f"{v / 1e6:.1f} MILLION") if v >= 1e6 else up(f"{v:,}")
            out.append(dict(label=f"BIGGEST GAIN SINCE {py}", text=f"{nm(ga)}  ·  {vt}", hl=[ga]))
    c = D["center"][y]
    if i == 0:
        txt = c["loc"].upper()
    else:
        c0 = D["center"][YEARS[i - 1]]
        txt = f"{c['loc'].upper()}  ·  MOVED {miles(c0, c):.0f} MI {compass(c0, c)}"
    out.append(dict(label="CENTER OF POPULATION", text=txt, hl=[], center=True))
    return out


def event_text(ev):
    if ev.get("dyn"):
        return TP.dyn(ev["dyn"], data())
    if ev["icon"] == "sun":
        D = data()
        gain = {ab: D["pop"][ab][2020] - D["pop"][ab][1970] for ab in ("TX", "FL", "AZ")}
        return f"TEXAS, FLORIDA AND ARIZONA ADD {sum(gain.values()) / 1e6:.0f} MILLION PEOPLE, 1970-2020"
    return ev["text"]


def captions(i):
    """[(start_lt, dur, text)] for block i (lt = local time in block)."""
    if hasattr(TP, "captions"):
        return TP.captions(i, ctx())
    D = data()
    if i == 0:
        return [(INTRO + 5.5, 7.5, TP.CAP0)]
    y0, y1 = YEARS[i - 1], YEARS[i]
    t0, t1 = D["us_total"][y0], D["us_total"][y1]
    g = (t1 / t0 - 1) * 100
    out = []
    zoom = next((z for z in story.ZOOMS if z["y1"] == y1), None)
    if zoom:
        c = next(c for c in cities() if c["name"] == zoom["name"])
        p0, p1 = c["pop"].get(str(y0)), c["pop"].get(str(y1))
        out.append((0.8, 7.0, f"{zoom['name'].upper()} {y0}-{y1}: {p0:,} → {p1:,} PEOPLE"))
    else:
        out.append((0.8, 7.0, f"{y0}-{y1}: THE U.S. ADDS {t1 - t0:,} PEOPLE ({up(pct_txt(g))})"))
    if TP.REGION_CAPTION:
        a0, a1 = TP.region_share(D, y0), TP.region_share(D, y1)
        out.append((RUN + 2.0, 8.0, f"SOUTH + WEST: {a1:.1f}% OF AMERICANS IN {y1}, {'UP' if a1 >= a0 else 'DOWN'} FROM {a0:.1f}% IN {y0}"))
    # hold caption: largest city
    cs = [(c["pop"].get(str(y1)), c["name"]) for c in cities() if c["pop"].get(str(y1))]
    if cs:
        p, n = max(cs)
        out.append((RUN + (12.0 if TP.REGION_CAPTION else 3.2), 7.5, f"LARGEST CITY IN {y1}: {n.upper()} ({p:,})  ·  U.S. TOTAL: {t1:,}"))
    return out


# ------------------------------------------------------------------ the renderer
class Renderer:
    def __init__(self):
        self.L = Layers()
        self.D = data()
        v = self.L.view
        self.base = VW(v.s, v.ox, v.oy)
        if FOCUS:
            self.base = self.focus_view()
        self.cm = {ab: [(cls8(self.D["dens"][ab][y]) if y in self.D["dens"].get(ab, {}) else None) for y in YEARS]
                   for ab in self.L.st}
        self.facts = [facts(i) for i in range(NB)]
        self.caps = [captions(i) for i in range(NB)]
        self.cities = cities()
        self.cent = {y: tuple(float(a) for a in albers(self.D["center"][y]["lon"], self.D["center"][y]["lat"])) for y in YEARS}
        self.rails = [(n, a, b, smooth(to_albers(p))) for n, a, b, p in story.RAILS + story.TRANSCON]
        self.migs = []
        for m in story.MIGRATIONS:
            p0, p1, p2 = (np.array(q) for q in to_albers(m["pts"]))
            t = np.linspace(0, 1, 60)[:, None]
            self.migs.append(dict(m, path=(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2))
        self.roads = interstates()
        self.schedule = [self.build_schedule(i) for i in range(NB)]
        self.zoom_by_block = {YEARS.index(z["y1"]): z for z in story.ZOOMS}
        self.build_frontier()
        self.build_county_geom()
        self.finale = None

    def focus_view(self):
        rings = dict(states())[FOCUS]
        x0 = min(r[:, 0].min() for r in rings); x1 = max(r[:, 0].max() for r in rings)
        y0 = min(r[:, 1].min() for r in rings); y1 = max(r[:, 1].max() for r in rings)
        mx0, my0, mx1, my1 = MAPBOX
        fill = getattr(TP, "VIEW_FILL", 0.9)
        s = min((mx1 - mx0) / (x1 - x0), (my1 - my0) / (y1 - y0)) * fill
        dx, dy = getattr(TP, "VIEW_SHIFT", (0, 0))           # pixels
        cxp, cyp = (mx0 + mx1) / 2 + dx, (my0 + my1) / 2 + dy
        xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
        return VW(s, cxp - xc * s, cyp + yc * s)

    # ---- frontier (state-level density >= 2 per sq mi), edge between settled and unsettled states
    def build_frontier(self):
        L = self.L
        land = np.zeros((RH, RW), bool)
        masks = {}
        for ab, s in L.st.items():
            x0, y0, x1, y1 = s["box"]
            m = np.zeros((RH, RW), bool)
            m[y0 - RY0:y1 - RY0, x0 - RX0:x1 - RX0] = s["mask"][..., 0] > 0.5
            masks[ab] = m
            land |= m
        self.fe, self.fb = [], []
        for i in range(11 if TP.FRONTIER else 0):
            y = YEARS[i]
            settled = np.zeros((RH, RW), bool)
            for ab, m in masks.items():
                if self.D["dens"].get(ab, {}).get(y, 0) >= 2:
                    settled |= m
            unsettled = land & ~settled
            edge = settled & dilate(unsettled, 3)
            self.fe.append(edge)
            self.fb.append(dilate(edge, 3))
        yy, xx = np.mgrid[0:RH, 0:RW]
        self.diag = (xx + yy).astype(np.int32)

    def build_county_geom(self):
        cg = counties()
        self.cg_ids = list(cg.keys())
        self.cg_index = {g: k for k, g in enumerate(self.cg_ids)}
        self.cg_st = [cg[g][0] for g in self.cg_ids]
        self.cg_rings = [cg[g][1] for g in self.cg_ids]
        bb = np.array([[min(r[:, 0].min() for r in rings), max(r[:, 0].max() for r in rings),
                        min(r[:, 1].min() for r in rings), max(r[:, 1].max() for r in rings)] for rings in self.cg_rings])
        self.cg_bb = bb
        sg = states()
        self.sg_items = list(sg.items())

    # ---- schedule of toasts/events per block
    def build_schedule(self, i):
        out = []
        busy = 0.0
        if i == 0:
            t = INTRO + 0.6
            for k in ((0, 1, 3) if len(self.facts[0]) >= 4 else range(len(self.facts[0]))):
                out.append(dict(kind="fact", t=t, dur=4.4, f=self.facts[0][k]))
                t += 4.6
            return out
        y0, y1 = YEARS[i - 1], YEARS[i]
        for ev in sorted((e for e in story.EVENTS if y0 < e["year"] <= y1), key=lambda e: e["year"]):
            te = max(RUN * (ev["year"] - y0) / (y1 - y0), busy)
            out.append(dict(kind="event", t=te, dur=5.2, ev=ev))
            busy = te + 5.4
        t = max(RUN + 0.4, busy + 0.3)
        picks = self.facts[i]
        order = [picks[0], picks[1], picks[2]] if len(picks) >= 3 else picks
        order = list(picks) if HOLD > 20 else [picks[0], picks[1], picks[-1]]
        for f in order:
            if t + 4.2 > RUN + HOLD:
                break
            out.append(dict(kind="fact", t=t, dur=4.2, f=f))
            t += 4.5
        return out

    # ---- timeline helpers
    @staticmethod
    def locate(t):
        if t < B0:
            return 0, t
        t2 = t - B0
        i = int(t2 // BLK) + 1
        if i >= NB:
            return NB, t2 - BLK * (NB - 1)
        return i, t2 - BLK * (i - 1)

    def year_at(self, i, lt):
        if i == 0 or i >= NB:
            return float(YEARS[0]) if i == 0 else float(YEARS[-1])
        y0, y1 = YEARS[i - 1], YEARS[i]
        return y0 + (y1 - y0) * min(lt / RUN, 1.0)

    def fade_p(self, i, lt):
        if i == 0 or i >= NB or lt < RUN:
            return 0.0
        return ease((lt - RUN) / FADE)

    def state_colour(self, ab, i, p):
        if hasattr(TP, "state_fill"):
            return TP.state_fill(ab, getattr(self, "_Y", YEARS[0]))
        if i >= NB:
            i, p = NB - 1, 1.0
        a = self.cm[ab][i - 1] if i > 0 else self.cm[ab][i]
        b = self.cm[ab][i]
        if i == 0:
            a = b
        if a is None and b is None:
            return UNCOUNTED
        if a is None:
            return lerp_col(UNCOUNTED, STOPS8[b], p)
        if b is None:
            return UNCOUNTED
        return pos_color(a + (b - a) * p)

    def county_colour(self, g, i, p, st=None):
        if (i == 0 and not FOCUS) or i >= NB:
            return None
        D = county_hist()
        ar = county_area().get(g, 0)
        h = D.get(g, {})
        ya, yb = YEARS[max(i - 1, 0)], YEARS[i]
        def c(y, k):
            v = h.get(y)
            if FOCUS and y < COUNTY_FROM:
                return self.cm[st][k]           # before county counts: the state average
            return None if (v is None or ar <= 0) else cls8(v / ar)
        a, b = c(ya, max(i - 1, 0)), c(yb, i)
        if a is None and b is None:
            return UNCOUNTED
        if a is None:
            return lerp_col(UNCOUNTED, STOPS8[b], p)
        if b is None:
            return UNCOUNTED
        return pos_color(a + (b - a) * p)

    # ---- zoom
    def zoom_view(self, i, lt):
        z = self.zoom_by_block.get(i)
        if not z:
            return self.base, 1.0, None
        t_in, t_out0 = 2.6, RUN + 3.5
        if lt < t_in:
            u = ease(lt / t_in)
        elif lt < t_out0:
            u = 1.0
        elif lt < t_out0 + 2.6:
            u = 1 - ease((lt - t_out0) / 2.6)
        else:
            u = 0.0
        if u < 0.005:
            return self.base, 1.0, z
        b = self.base
        Z = math.exp(u * math.log(z["zoom"]))
        s = b.s * Z
        cx, cy = (MAPBOX[0] + MAPBOX[2]) / 2, (MAPBOX[1] + MAPBOX[3]) / 2
        p0 = ((cx - b.ox) / b.s, (b.oy - cy) / b.s)
        pc = tuple(float(a) for a in albers(*z["center"]))
        s1 = b.s * z["zoom"]
        u2 = (1 / b.s - 1 / s) / (1 / b.s - 1 / s1)
        m = (p0[0] + (pc[0] - p0[0]) * u2, p0[1] + (pc[1] - p0[1]) * u2)
        return VW(s, cx - m[0] * s, cy + m[1] * s), Z, z

    # ---- map pixels
    def map_fast(self, i, p, t):
        L = self.L
        cv = L.base_r.copy()
        for ab, s in L.st.items():
            x0, y0, x1, y1 = s["box"]
            col = np.array(self.state_colour(ab, i, p), np.float32)
            reg = cv[y0 - RY0:y1 - RY0, x0 - RX0:x1 - RX0]
            reg += (col - reg) * s["mask"]
        cv += (np.array(OCEAN, np.float32) - cv) * L.lakes_r
        cv *= 1 - L.borders_r
        return cv

    def highlight(self, cv, i, lt):
        if i >= NB:
            return
        for s_ in self.schedule[i]:
            ct = lt - s_["t"]
            if s_["kind"] == "fact" and 0 <= ct < s_["dur"]:
                pulse = 0.72 + 0.28 * math.sin(ct * 5.0)
                for ab in s_["f"].get("hl", []):
                    s = self.L.st.get(ab)
                    if not s:
                        continue
                    x0, y0, x1, y1 = s["box"]
                    reg = cv[y0 - RY0:y1 - RY0, x0 - RX0:x1 - RX0]
                    reg -= reg * s["dark"] * 0.55 * getattr(TP, "HL_DARK", 1.0)
                    reg += (np.array(YEL, np.float32) - reg) * s["yel"] * pulse

    def map_dynamic(self, vw, Z, i, p):
        ss = 2
        img = Image.new("RGB", (RW * ss, RH * ss), OCEAN)
        d = ImageDraw.Draw(img)
        x0, x1, y0, y1 = vw.rect()
        pad = 0.0
        def poly(r):
            x, y = vw.px(r[:, 0], r[:, 1])
            return list(zip((x - RX0) * ss, (y - RY0) * ss))
        from .choro import neighbours as nb
        for _, rings in nb():
            for r in rings:
                if r[:, 0].max() < x0 or r[:, 0].min() > x1 or r[:, 1].max() < y0 or r[:, 1].min() > y1:
                    continue
                d.polygon(poly(r), fill=NEIGHBOUR, outline=NEIGHBOUR_LINE, width=ss)
        scol = {}
        for ab, rings in self.sg_items:
            col = tuple(int(v) for v in self.state_colour(ab, i, p))
            if FOCUS and ab != FOCUS:
                col = tuple(int(v) for v in lerp_col(col, NEIGHBOUR, 0.6))
            scol[ab] = col
            for r in rings:
                if r[:, 0].max() < x0 or r[:, 0].min() > x1 or r[:, 1].max() < y0 or r[:, 1].min() > y1:
                    continue
                d.polygon(poly(r), fill=col)
        ca = 1.0 if FOCUS else ease((Z - 1.6) / 1.6)
        if ca > 0.01:
            bb = self.cg_bb
            vis = np.where((bb[:, 1] >= x0) & (bb[:, 0] <= x1) & (bb[:, 3] >= y0) & (bb[:, 2] <= y1))[0]
            for k in vis:
                g = self.cg_ids[k]
                if FOCUS and self.cg_st[k] != FOCUS:
                    continue
                cc = self.county_colour(g, i, p, self.cg_st[k])
                if cc is None:
                    continue
                col = tuple(int(v) for v in lerp_col(scol.get(self.cg_st[k], UNCOUNTED), cc, ca))
                own = not (FOCUS and YEARS[i] < COUNTY_FROM)     # state mode before county counts: no county lines
                for r in self.cg_rings[k]:
                    d.polygon(poly(r), fill=col, outline=(40, 40, 55) if (ca > 0.5 and own) else None, width=ss)
        for r in lakes():
            if r[:, 0].max() < x0 or r[:, 0].min() > x1 or r[:, 1].max() < y0 or r[:, 1].min() > y1:
                continue
            d.polygon(poly(r), fill=OCEAN)
        for ab, rings in self.sg_items:
            for r in rings:
                if r[:, 0].max() < x0 or r[:, 0].min() > x1 or r[:, 1].max() < y0 or r[:, 1].min() > y1:
                    continue
                q = poly(r)
                d.line(q + q[:1], fill=(22, 22, 34), width=int(2.6 * ss) + int(ss * Z ** 0.4), joint="curve")
        for g, pulse in getattr(self, "_hl", []):
            k = self.cg_index.get(g)
            if k is None:
                continue
            for r in self.cg_rings[k]:
                q = poly(r)
                d.line(q + q[:1], fill=(15, 15, 25), width=int(9 * ss), joint="curve")
                d.line(q + q[:1], fill=tuple(int(v) for v in lerp_col((150, 130, 0), YEL, pulse)), width=int(5 * ss), joint="curve")
        img = img.resize((RW, RH), Image.LANCZOS)
        return np.asarray(img).astype(np.float32)

    # ---- one frame
    def frame(self, n):
        t = n / FPS
        i, lt = self.locate(t)
        fin = i >= NB
        ii = NB - 1 if fin else i
        p = self.fade_p(i, lt) if not fin else 1.0
        Y = self.year_at(i, lt)
        self._Y = Y
        vw, Z, zdef = self.zoom_view(i, lt) if not fin else (self.base, 1.0, None)
        run_f = 1.0 if (i == 0 or fin or lt >= RUN) else lt / RUN
        # ---- map base
        self._hl = []
        if FOCUS and not fin:
            for s_ in self.schedule[i]:
                ct = lt - s_["t"]
                if s_["kind"] == "fact" and 0 <= ct < s_["dur"]:
                    self._hl += [(g, 0.72 + 0.28 * math.sin(ct * 5.0)) for g in s_["f"].get("hl", [])]
        if Z > 1.02 or FOCUS:
            cv = self.map_dynamic(vw, Z, ii, p)
        else:
            cv = self.map_fast(ii, p, t)
            self.highlight(cv, i, lt)
            # frontier (state-level >= 2/sq mi), crawling dashes; fades out after 1890
            fa = self.frontier_alpha(i, lt)
            if fa > 0.01:
                k = min(ii, 10)
                kk = max(0, min(ii - 1, 10)) if i > 0 else 0
                w = p if (i > 0 and lt >= RUN) else 0.0
                for arr_b, arr_e, wgt in ((self.fb[kk], self.fe[kk], (1 - w)), (self.fb[k], self.fe[k], w)):
                    if wgt <= 0.01 or ii > 10 + 1:
                        continue
                    dash = (((self.diag + int(t * 36)) // 11) % 2) == 0
                    cv[arr_b] *= 1 - 0.85 * fa * wgt
                    on = arr_e & dash
                    cv[on] = cv[on] * (1 - fa * wgt) + np.array(YEL, np.float32) * fa * wgt
        if fin and not FOCUS and getattr(TP, "FINALE_COUNTIES", True):
            a = ease(lt / 4.0)
            if self.finale is None:
                self.finale = self.build_finale()
            cv = cv * (1 - a) + self.finale * a
        full = self.L.base_u8.copy()
        full[RY0:RY1, RX0:RX1] = np.clip(cv, 0, 255).astype(np.uint8)
        img = Image.fromarray(full)
        # ---- highlight of facts is drawn as outline in fast path only
        self.draw_overlay(img, vw, Z, i, lt, Y, run_f, ii, fin)
        if hasattr(TP, "draw_extra"):
            TP.draw_extra(self, img, t, i, lt, Y, fin)
        d = ImageDraw.Draw(img, "RGBA")
        self.draw_panel(d, i, lt, Y, ii, fin)
        self.draw_bottom(img, d, i, lt, fin)
        self.draw_toasts(img, i, lt)
        if zdef is not None and Z > 1.3:
            self.draw_zoom_title(img, zdef, min(1.0, (Z - 1.3) / 1.0))
        if i == 0 and lt < INTRO:
            self.draw_intro(img, lt)
        if fin:
            self.draw_finale(img, lt)
        d = ImageDraw.Draw(img, "RGBA")
        T(d, (W // 2, 1058), getattr(TP, "FOOTER", "AREAS AS TODAY'S STATES  ·  ALASKA & HAWAII ARE COUNTED IN THE TOTALS, NOT SHOWN"), 30,
          fill=WHITE, stroke=3, anchor="mm")
        return np.asarray(img)

    def frontier_alpha(self, i, lt):
        if not TP.FRONTIER:
            return 0.0
        if i == 0:
            return 1.0
        if i > 11 or i >= NB:
            return 0.0
        if i < 10:
            return 1.0
        if i == 10:
            return 1.0 if lt < RUN else max(0.0, 1.0 - (lt - RUN) / 6.0)
        return 0.0

    def build_finale(self):
        D = county_hist()
        ar = county_area()
        fills = {}
        for g in self.cg_ids:
            v, a = D.get(g, {}).get(2020), ar.get(g, 0)
            fills[g] = STOPS8[cls8(v / a)] if v and a > 0 else UNCOUNTED
        from .core import View
        v = View(W, H)
        v.s, v.ox, v.oy = self.base.s, self.base.ox, self.base.oy
        im = choro_render(v, fills, level="county", county_line_alpha=60, state_line_w=7)
        return np.asarray(im)[RY0:RY1, RX0:RX1].astype(np.float32)

    # ---- overlay (2x supersampled lines/circles)
    def draw_overlay(self, img, vw, Z, i, lt, Y, run_f, ii, fin):
        ss = 2
        ov = Image.new("RGBA", (RW * ss, RH * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        def pts(a):
            x, y = vw.px(a[:, 0], a[:, 1])
            return list(zip((x - RX0) * ss, (y - RY0) * ss))
        zs = 1.0 if Z < 1.5 else 1.4
        # interstates 1956-1992 (schematic)
        g = min(1.0, max(0.0, (Y - 1956) / (1992 - 1956)))
        if getattr(TP, "SHOW_ROADS", True) and (g > 0 or i >= NB):
            if i >= NB:
                g = 1.0
            for a, th in self.roads:
                f = min(1.0, max(0.0, (g - th * 0.85) / 0.15))
                if f <= 0:
                    continue
                q = pts(partial(a, f))
                d.line(q, fill=(255, 255, 255, 240), width=int(6.4 * ss * zs), joint="curve")
                d.line(q, fill=(20, 60, 230, 255), width=int(3.6 * ss * zs), joint="curve")
        # railroads (simplified, decade-level)
        for name, ya, yb, a in self.rails:
            if Y < ya or (i >= NB):
                if i < NB:
                    continue
            f = 1.0 if (Y >= yb or i >= NB) else (Y - ya) / (yb - ya)
            f = min(1.0, max(0.0, f))
            if f <= 0:
                continue
            fade = 1.0 if Y < 1960 else max(0.35, 1 - (Y - 1960) / 80)
            q = pts(partial(a, f))
            d.line(q, fill=(0, 0, 0, int(235 * fade)), width=int(8 * ss * zs), joint="curve")
            d.line(q, fill=(255, 255, 255, int(235 * fade)), width=int(4 * ss * zs), joint="curve")
            if 0 < f < 1:
                hx, hy = q[-1]
                d.ellipse([hx - 9 * ss, hy - 9 * ss, hx + 9 * ss, hy + 9 * ss], fill=(255, 40, 40, 255), outline=(255, 255, 255, 255), width=3 * ss)
        # migration arrows
        if Z < 1.5:
            for m in self.migs:
                if Y < m["y0"] or i >= NB:
                    continue
                f = min(1.0, (Y - m["y0"]) / max(m["y1"] - m["y0"], 1))
                al = 1.0 if Y <= m["y1"] + 3 else max(0.0, 1 - (Y - m["y1"] - 3) / 8.0)
                if al <= 0.02:
                    continue
                path = partial(m["path"], max(f, 0.04))
                q = pts(path)
                a255 = int(255 * al)
                d.line(q, fill=(255, 255, 255, a255), width=int(17 * ss), joint="curve")
                d.line(q, fill=m["color"] + (a255,), width=int(10 * ss), joint="curve")
                if len(q) >= 2:
                    (x0, y0), (x1, y1) = q[-2], q[-1]
                    ang = math.atan2(y1 - y0, x1 - x0)
                    L_, W_ = 30 * ss, 24 * ss
                    tip = (x1 + math.cos(ang) * 10 * ss, y1 + math.sin(ang) * 10 * ss)
                    bx, by = tip[0] - L_ * math.cos(ang), tip[1] - L_ * math.sin(ang)
                    tri = [tip, (bx + W_ * math.sin(ang), by - W_ * math.cos(ang)), (bx - W_ * math.sin(ang), by + W_ * math.cos(ang))]
                    d.polygon(tri, fill=m["color"] + (a255,), outline=(255, 255, 255, a255), width=3 * ss)
        # centre of population trail + dot
        if not SHOW_CENTER:
            pass
        elif not fin:
            cen = [self.cent[y] for y in YEARS[:ii]]
            if i > 0 and lt < RUN:
                a_, b_ = self.cent[YEARS[i - 1]], self.cent[YEARS[i]]
                f = lt / RUN
                cen.append((a_[0] + (b_[0] - a_[0]) * f, a_[1] + (b_[1] - a_[1]) * f))
            else:
                cen.append(self.cent[YEARS[ii]])
        else:
            cen = [self.cent[y] for y in YEARS]
        ca = np.array(cen if SHOW_CENTER else [(0.0, 0.0)])
        q = pts(ca) if SHOW_CENTER else []
        if len(q) > 1:
            d.line(q, fill=(0, 0, 0, 255), width=int(11 * ss), joint="curve")
            d.line(q, fill=YEL + (255,), width=int(5 * ss), joint="curve")
        if q:
            cx, cy = q[-1]
            r = (15 + 4 * math.sin(lt * 6)) * ss if (not fin and i > 0 and lt >= RUN) else 15 * ss
            d.ellipse([cx - r - 5 * ss, cy - r - 5 * ss, cx + r + 5 * ss, cy + r + 5 * ss], fill=(0, 0, 0, 255))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 40, 40, 255), outline=(255, 255, 255, 255), width=4 * ss)
        # cities
        draws = self.city_state(i, lt, run_f, fin)
        self._labels = []
        for c, pop, ap in draws:
            rad = max(4.5, pop ** 0.4 / 18.0) * (0.55 if Z > 1.5 else 1.0) * ap
            x, y = vw.px(c["ax"], c["ay"])
            x, y = (float(x) - RX0) * ss, (float(y) - RY0) * ss
            if not (-50 <= x <= RW * ss + 50 and -50 <= y <= RH * ss + 50):
                continue
            rr = rad * ss
            d.ellipse([x - rr - 3 * ss, y - rr - 3 * ss, x + rr + 3 * ss, y + rr + 3 * ss], fill=(15, 15, 25, 255))
            cf = TP.city_fill(c, i, pop, fin) if hasattr(TP, "city_fill") else (255, 255, 255)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=tuple(int(v) for v in cf) + (235,))
            self._labels.append((pop, c["name"], x / ss + RX0, y / ss + RY0, rad, ap))
        ov = ov.resize((RW, RH), Image.LANCZOS)
        img.paste(ov, (RX0, RY0), ov)
        # labels (collision-avoiding), migration captions
        self.draw_labels(img, (lt if i == 0 else B0 + BLK * (i - 1) + lt), Z)
        d2 = ImageDraw.Draw(img, "RGBA")
        for x, y, lab, _ in self.mig_captions(lt if i == 0 else B0 + BLK * (i - 1) + lt):
            T(d2, (x, y), lab, 34, fill=WHITE, stroke=5, anchor="mm")

    def mig_captions(self, t):
        """[(x, y, label, rect)] of the migration-arrow captions at time t (also obstacles for the city labels)."""
        i, lt = self.locate(t)
        fin = i >= NB
        if fin:
            return []
        vw, Z, _ = self.zoom_view(i, lt)
        if Z >= 1.5:
            return []
        Y = self.year_at(i, lt)
        out = []
        f34 = F(34)
        for m in self.migs:
            if m["label"] and m["y0"] <= Y <= m["y1"] + 3:
                f = min(1.0, (Y - m["y0"]) / max(m["y1"] - m["y0"], 1))
                if f < 0.3:
                    continue
                path = partial(m["path"], f)
                mid = path[len(path) // 2]
                x, y = vw.px(mid[0], mid[1])
                x, y = float(x), float(y) - 36
                wd = f34.getlength(m["label"]) + 12
                out.append((x, y, m["label"], (x - wd / 2, y - 22, x + wd / 2, y + 22)))
        return out

    def city_state(self, i, lt, run_f, fin):
        out = []
        h = 0.0 if (i == 0) else (lt - RUN if lt >= RUN else -1.0)
        for c in self.cities:
            pops = c["pops"]
            if fin:
                v = pops[NB - 1]
                if v:
                    out.append((c, v, 1.0))
                continue
            b = pops[i]
            a = pops[i - 1] if i > 0 else b
            if i == 0:
                if b:
                    out.append((c, b, 1.0))
                continue
            if a and b:
                out.append((c, a + (b - a) * run_f, 1.0))
            elif b and not a:
                if h >= 0:
                    out.append((c, b, ease(h / 1.0)))
            elif a and not b:
                if h < 0:
                    out.append((c, a, 1.0))
                elif h < 1.0:
                    out.append((c, a, 1 - ease(h / 1.0)))
        return out

    # ---- city labels: planned per 4-second epoch so a label never flickers
    EP = 4.0
    FADE_L = 0.3

    def city_geom(self, t):
        i, lt = self.locate(t)
        fin = i >= NB
        vw, Z, _ = self.zoom_view(i, lt) if not fin else (self.base, 1.0, None)
        run_f = 1.0 if (i == 0 or fin or lt >= RUN) else lt / RUN
        out = []
        for c, pop, ap in self.city_state(i, lt, run_f, fin):
            rad = max(4.5, pop ** 0.4 / 18.0) * (0.55 if Z > 1.5 else 1.0) * ap
            x, y = vw.px(c["ax"], c["ay"])
            x, y = float(x), float(y)
            if not (RX0 - 25 <= x <= RX1 + 25 and RY0 - 25 <= y <= RY1 + 25):
                continue
            out.append((pop, c["name"], x, y, rad, ap))
        return out, Z

    def label_plan(self, e):
        """name -> (dx, dy, anchor) for epoch e; decided once from the geometry at the epoch midpoint,
        preferring the previous epoch's placement so labels do not jump."""
        if not hasattr(self, "_plans"):
            self._plans = {}
        if e in self._plans:
            return self._plans[e]
        prev = self.label_plan(e - 1) if e > 0 else {}
        geom, Z = self.city_geom((e + 0.5) * self.EP)
        zs = [self.city_geom(min(tq, TOTAL_S - 1e-3))[1] for tq in (e * self.EP + 0.02, (e + 1) * self.EP - 0.02)] + [Z]
        if max(zs) / min(zs) > 1.08:      # the camera is moving: no new placements in this epoch
            self._plans[e] = {}
            return {}
        ok = None   # a label needs a visible, fully grown circle during the WHOLE epoch
        obst = {}   # name -> union of the circle boxes over the epoch (circles grow while a decade runs)
        for c in geom:
            obst[c[1]] = [(c[2] - c[4] - 5, c[3] - c[4] - 5, c[2] + c[4] + 5, c[3] + c[4] + 5)]
        for tq in (e * self.EP + 0.02, (e + 1) * self.EP - 0.02):
            g2, _ = self.city_geom(min(tq, TOTAL_S - 1e-3))
            for c in g2:
                obst.setdefault(c[1], []).append((c[2] - c[4] - 5, c[3] - c[4] - 5, c[2] + c[4] + 5, c[3] + c[4] + 5))
            names = {n for pop, n, x, y, rad, ap in g2 if ap >= 0.6}
            ok = names if ok is None else ok & names
        labs = sorted((c for c in geom if c[1] in ok), reverse=True)
        k = 14 if Z > 1.5 else 11
        f = F(26)
        mig = []   # migration captions anywhere in the epoch: union box per caption
        for k_ in range(9):
            for n_, (_, _, lab, r) in enumerate(self.mig_captions(min(e * self.EP + k_ * self.EP / 8, TOTAL_S - 1e-3))):
                obst.setdefault("__mig_" + lab, []).append(r)
        circles = obst
        rmax = {n: max((b[2] - b[0]) / 2 - 5 for b in obst[n]) for n in circles if not n.startswith("__mig_")}
        placed, lpts, plan = [], [], {}
        hit = lambda a, b: not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])
        for pop, name, x, y, rad, ap in labs[:k]:
            if ap < 0.6:
                continue
            wd = f.getlength(f"{name}  {int(pop):,}") + 10 + 14   # slack: the number's width changes while it counts
            ht = 34
            cands = []
            if name in prev:
                cands.append(prev[name][:2])
            for dist in (rmax[name] + 8, rmax[name] + 34, rmax[name] + 70, rmax[name] + 110):
                for ang in (0, 180, 270, 90, 315, 45, 225, 135, 20, 340, 160, 200):
                    a = math.radians(ang)
                    cands.append((dist * math.cos(a), dist * math.sin(a) * 0.8))
            for dx, dy in cands:
                if any(math.hypot(dx, dy) < rmax[name] + 4 for _ in (0,)):
                    continue
                px_, py_ = x + dx, y + dy
                an = "lm" if dx > 4 else ("rm" if dx < -4 else "mm")
                x0 = px_ if an[0] == "l" else (px_ - wd if an[0] == "r" else px_ - wd / 2)
                rect = (x0, py_ - ht / 2, x0 + wd, py_ + ht / 2)
                if rect[0] < RX0 + 4 or rect[2] > W - 4 or rect[1] < 4 or rect[3] > RY1 - 4:
                    continue
                if any(hit(rect, r) for r in placed):
                    continue
                if any(hit(rect, c) for n2, cl in circles.items() if n2 != name for c in cl):
                    continue
                if any(rect[0] - 3 <= qx <= rect[2] + 3 and rect[1] - 3 <= qy <= rect[3] + 3 for qx, qy in lpts):
                    continue
                if math.hypot(dx, dy) > rad + 20:
                    ex = rect[0] if an[0] == "l" else (rect[2] if an[0] == "r" else px_)
                    ey = py_ if an[0] != "m" else (rect[1] if dy > 0 else rect[3])
                    nn = max(2, int(math.hypot(ex - x, ey - y) / 6))
                    pts = [(x + (ex - x) * t_ / nn, y + (ey - y) * t_ / nn) for t_ in range(1, nn)]
                    if any(r[0] - 3 <= qx <= r[2] + 3 and r[1] - 3 <= qy <= r[3] + 3 for qx, qy in pts for r in placed):
                        continue
                    lpts.extend(pts)
                placed.append(rect)
                plan[name] = (dx, dy, an)
                break
        self._plans[e] = plan
        return plan

    @staticmethod
    def clamp_label(px_, py_, an, wd):
        """keep a label inside the map box while the camera moves (zoom in/out)"""
        x0 = px_ if an[0] == "l" else (px_ - wd if an[0] == "r" else px_ - wd / 2)
        sx = 0.0
        if x0 < RX0 + 6: sx = RX0 + 6 - x0
        elif x0 + wd > W - 6: sx = W - 6 - (x0 + wd)
        sy = 0.0
        if py_ - 17 < 6: sy = 6 - (py_ - 17)
        elif py_ + 17 > RY1 - 6: sy = RY1 - 6 - (py_ + 17)
        px_, py_ = px_ + sx, py_ + sy
        x0 += sx
        return px_, py_, (x0, py_ - 17, x0 + wd, py_ + 17)

    def label_alpha(self, name, t):
        e = int(t // self.EP)
        if name not in self.label_plan(e):
            return 0.0
        tt = t - e * self.EP
        a = 1.0
        if e > 0 and name not in self.label_plan(e - 1):
            a = min(a, tt / self.FADE_L)
        if name not in self.label_plan(e + 1):
            a = min(a, (self.EP - tt) / self.FADE_L)
        return max(0.0, min(1.0, a))

    def draw_labels(self, img, t, Z):
        cur = {n: (pop, x, y, rad, ap) for pop, n, x, y, rad, ap in self._labels}
        plan = self.label_plan(int(t // self.EP))
        f = F(26)
        leads, texts = [], []
        for name, (dx, dy, an) in plan.items():
            if name not in cur:
                continue
            pop, x, y, rad, ap = cur[name]
            if ap < 0.6:
                continue
            al = self.label_alpha(name, t)
            if al <= 0.01:
                continue
            txt = f"{name}  {int(pop):,}"
            wd = f.getlength(txt) + 10
            px_, py_, rc = self.clamp_label(x + dx, y + dy, an, wd)
            lead = None
            if math.hypot(dx, dy) > rad + 20:
                x0 = rc[0]
                ex = x0 if an[0] == "l" else (x0 + wd if an[0] == "r" else px_)
                ey = py_ if an[0] != "m" else (py_ - 17 if dy > 0 else py_ + 17)
                lead = ((x, y), (ex, ey))
            texts.append(((px_, py_), txt, an, al, lead))
        d = ImageDraw.Draw(img, "RGBA")
        full = [q for q in texts if q[3] >= 0.999]
        for pos, txt, an, al, lead in full:
            if lead:
                d.line(list(lead), fill=(15, 15, 25, 255), width=5)
                d.line(list(lead), fill=(255, 255, 255, 255), width=2)
        for pos, txt, an, al, lead in full:
            T(d, pos, txt, 26, fill=WHITE, stroke=4, anchor=an)
        for pos, txt, an, al, lead in (q for q in texts if q[3] < 0.999):
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            dl = ImageDraw.Draw(lay, "RGBA")
            if lead:
                dl.line(list(lead), fill=(15, 15, 25, 255), width=5)
                dl.line(list(lead), fill=(255, 255, 255, 255), width=2)
            T(dl, pos, txt, 26, fill=WHITE, stroke=4, anchor=an)
            lay.putalpha(lay.getchannel("A").point(lambda v, a_=al: int(v * a_)))
            img.paste(lay, (0, 0), lay)

    # ---- left panel
    def draw_panel(self, d, i, lt, Y, ii, fin):
        d.rectangle([0, 0, 452, 912], fill=NAVY + (240,))
        d.line([(452, 0), (452, 912)], fill=YEL + (255,), width=5)
        D = self.D
        ser = D["pop"][FOCUS] if FOCUS else D["us_total"]
        if fin:
            yshow, tot = YEARS[-1], ser[YEARS[-1]]
        elif i == 0:
            yshow, tot = YEARS[0], ser[YEARS[0]]
        else:
            y0, y1 = YEARS[i - 1], YEARS[i]
            f = min(lt / RUN, 1.0)
            yshow = y1 if f >= 1 else int(math.floor(Y + 1e-6))
            tot = int(round(ser[y0] + (ser[y1] - ser[y0]) * f))
        if hasattr(TP, "counter_value"):
            tot = TP.counter_value(Y if not fin else YEARS[-1] + 0.99)
        T(d, (226, 108), str(yshow), 190, fill=YEL, stroke=10, anchor="mm")
        T(d, (28, 205), getattr(TP, "COUNTER_LABEL", "U.S. POPULATION"), 32, fill=WHITE, stroke=3)
        T(d, (28, 232), f"{tot:,}", 82, fill=YEL, stroke=6)
        T(d, (28, 336), getattr(TP, "LEGEND_TITLE", "PEOPLE PER SQ MI"), 32, fill=WHITE, stroke=3)
        yy = 376
        for col, lab in getattr(TP, "LEGEND", list(zip(STOPS8, LABELS8))):
            d.rectangle([28, yy, 88, yy + 28], fill=tuple(col) + (255,), outline=BLACK + (255,), width=3)
            T(d, (104, yy + 14), lab, 27, fill=WHITE, stroke=3, anchor="lm")
            yy += 36
        d.rectangle([28, yy, 88, yy + 28], fill=UNCOUNTED + (255,), outline=BLACK + (255,), width=3)
        T(d, (104, yy + 14), getattr(TP, "LEGEND_NONE", "NOT YET COUNTED"), 27, fill=WHITE, stroke=3, anchor="lm")
        yy += 38
        if SHOW_CENTER:
            d.ellipse([42, yy + 1, 70, yy + 29], fill=(255, 40, 40, 255), outline=WHITE + (255,), width=3)
            T(d, (104, yy + 14), "CENTER OF POPULATION", 27, fill=WHITE, stroke=3, anchor="lm")
            yy += 38
        if getattr(TP, "CITY_LEGEND", None):
            d.ellipse([44, yy + 3, 68, yy + 27], fill=(15, 15, 25, 255))
            d.ellipse([47, yy + 6, 65, yy + 24], fill=(255, 255, 255, 255))
            T(d, (104, yy + 14), TP.CITY_LEGEND, 27, fill=WHITE, stroke=3, anchor="lm")
            yy += 38
        for col, lab in getattr(TP, "LEGEND_CIRCLES", []):
            d.ellipse([44, yy + 3, 68, yy + 27], fill=(15, 15, 25, 255))
            d.ellipse([47, yy + 6, 65, yy + 24], fill=tuple(col) + (255,))
            T(d, (104, yy + 14), lab, 27, fill=WHITE, stroke=3, anchor="lm")
            yy += 38
        if Y <= 1891 and not fin and TP.FRONTIER:
            for x in range(28, 88, 20):
                d.line([(x, yy + 14), (x + 11, yy + 14)], fill=BLACK + (255,), width=9)
                d.line([(x, yy + 14), (x + 11, yy + 14)], fill=YEL + (255,), width=5)
            T(d, (104, yy + 14), "FRONTIER: 2+ PER SQ MI", 27, fill=WHITE, stroke=3, anchor="lm")
            yy += 38
        if (1830 <= Y or fin) and (story.RAILS or story.TRANSCON):
            d.line([(28, yy + 14), (88, yy + 14)], fill=BLACK + (255,), width=9)
            d.line([(28, yy + 14), (88, yy + 14)], fill=WHITE + (255,), width=5)
            T(d, (104, yy + 14), "RAILROADS (SIMPLIFIED)", 27, fill=WHITE, stroke=3, anchor="lm")
            yy += 38
        if (Y >= 1956 or fin) and getattr(TP, "SHOW_ROADS", True):
            d.line([(28, yy + 14), (88, yy + 14)], fill=WHITE + (255,), width=9)
            d.line([(28, yy + 14), (88, yy + 14)], fill=(30, 70, 220, 255), width=5)
            T(d, (104, yy + 14), "INTERSTATES (SCHEMATIC)", 27, fill=WHITE, stroke=3, anchor="lm")

    # ---- bottom strip: captions
    def draw_bottom(self, img, d, i, lt, fin):
        d.rectangle([0, 912, W, H], fill=NAVY + (255,))
        d.line([(0, 912), (W, 912)], fill=YEL + (255,), width=5)
        caps = self.caps[min(i, NB - 1)] if not fin else [(4.0, 9.0, getattr(TP, "FINAL_CAPTION", "2020: 331,449,281 PEOPLE IN THE 50 STATES AND D.C."))]
        shown = False
        for st, du, txt in caps:
            if st <= lt < st + du:
                shown = True
                a = ease((lt - st) / 0.5) * (1 - ease((lt - (st + du - 0.5)) / 0.5))
                if a <= 0.02:
                    continue
                size = 52 if rich_len(txt, 52) <= 1780 else 46
                rich_text(d, (W // 2, 962), txt, size, fill=WHITE, stroke=5, anchor="mm", alpha=int(255 * min(1.0, a)))
        if not shown:
            T(d, (W // 2, 972), "DATA: U.S. CENSUS BUREAU  ·  MAP: NATURAL EARTH", 36, fill=(190, 200, 225), stroke=3, anchor="mm")

    # ---- toasts (lower-left of the map)
    def draw_toasts(self, img, i, lt):
        if i >= NB:
            return
        for s in self.schedule[i]:
            ct = lt - s["t"]
            if not (0 <= ct < s["dur"]):
                continue
            a = ease(ct / 0.5) * (1 - ease((ct - (s["dur"] - 0.5)) / 0.5))
            if a <= 0.02:
                continue
            dx = int((1 - ease(ct / 0.5)) * -60)
            ov = Image.new("RGBA", (500, 214), (0, 0, 0, 0))
            od = ImageDraw.Draw(ov)
            A = int(255 * a)
            if s["kind"] == "event":
                ev = s["ev"]
                od.rounded_rectangle([4, 4, 496, 210], radius=22, fill=NAVY + (int(238 * a),), outline=YEL + (A,), width=5)
                ic = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
                icon(ImageDraw.Draw(ic), ev["icon"], 60, 60, 96)
                if a < 1:
                    ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a)))
                ov.paste(ic, (14, 20), ic)
                od.text((150, 12), str(ev["year"]), font=F(46), fill=YEL + (A,), stroke_width=4, stroke_fill=BLACK + (A,))
                od.text((150, 62), ev["title"], font=F(31), fill=WHITE + (A,), stroke_width=3, stroke_fill=BLACK + (A,))
                y = 102
                for ln in wrap(event_text(ev), 27, 335)[:4]:
                    rich_text(od, (150, y), ln, 27, fill=WHITE, stroke=3, alpha=A)
                    y += 31
            else:
                f = s["f"]
                od.rounded_rectangle([4, 62, 496, 210], radius=22, fill=NAVY + (int(238 * a),), outline=YEL + (A,), width=5)
                od.text((24, 70), f["label"], font=F(28), fill=YEL + (A,), stroke_width=3, stroke_fill=BLACK + (A,))
                y = 108
                for ln in wrap(f["text"], 42, 450)[:2]:
                    rich_text(od, (24, y), ln, 42, fill=WHITE, stroke=4, alpha=A)
                    y += 48
            img.paste(ov, (472 + dx, 694), ov)

    def draw_zoom_title(self, img, z, a):
        ov = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        A = int(255 * a)
        od.rounded_rectangle([700, 8, 1700, 82], radius=30, fill=NAVY + (int(235 * a),), outline=YEL + (A,), width=5)
        od.text((1200, 45), f"{z['name'].upper()}  ·  {z['why']}", font=F(44), fill=WHITE + (A,), anchor="mm", stroke_width=4, stroke_fill=BLACK + (A,))
        img.paste(ov, (0, 16), ov)

    def draw_intro(self, img, lt):
        a = ease(lt / 1.0) * (1 - ease((lt - (INTRO - 1.5)) / 1.5))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rounded_rectangle([520, 250, 1860, 650], radius=36, fill=NAVY + (int(235 * a),), outline=YEL + (int(255 * a),), width=8)
        c = int(255 * a)
        od.text((1190, 390), "AMERICA OVER TIME", font=F(150), fill=YEL + (c,), anchor="mm", stroke_width=10, stroke_fill=BLACK + (c,))
        od.text((1190, 540), TP.INTRO_LINE, font=F(76), fill=WHITE + (c,), anchor="mm", stroke_width=6, stroke_fill=BLACK + (c,))
        img.paste(ov, (0, 0), ov)

    def draw_finale(self, img, lt):
        a2 = ease((lt - 14.0) / 1.0)
        if a2 <= 0.01:
            return
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        c = int(255 * a2)
        od.rounded_rectangle([520, 120, 1860, 840], radius=36, fill=NAVY + (int(240 * a2),), outline=YEL + (c,), width=8)
        lines = [("AMERICA OVER TIME", 100, YEL), ("DATA: U.S. CENSUS BUREAU", 56, WHITE), ("MAP DATA: NATURAL EARTH  ·  ROADS: NATURAL EARTH", 44, WHITE),
                 ("MUSIC: YOIYAMI, CYNICMUSIC (CC0), OPENGAMEART.ORG", 48, WHITE), (TP.CREDIT_EVENTS, 40, WHITE),
                 ("NEW ANIMATED MAP EVERY MONDAY & FRIDAY", 48, YEL)]
        y = 200
        for s, sz, col in lines:
            od.text((1190, y), s, font=F(sz), fill=col + (c,), anchor="mm", stroke_width=max(4, sz // 12), stroke_fill=BLACK + (c,))
            y += sz + 56
        img.paste(ov, (0, 0), ov)


def render_range(start, end, out, crf=22):
    r = Renderer()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(start, min(end, TOTAL_FRAMES)):
        pr.stdin.write(r.frame(n).tobytes())
    pr.stdin.close()
    pr.wait()
    return pr.returncode
