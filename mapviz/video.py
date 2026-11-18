"""Trial video: U.S. population 1790-2020 as a bright choropleth timelapse (no voice).

Frame layout 1920x1080: dark left panel (year, total, legend), map box, fact-card band, footnote.
All numbers come from data/population.json (built + validated by scripts/build_popdata.py).
"""
from __future__ import annotations

import json
import math
import subprocess
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .choro import (NEIGHBOUR, NEIGHBOUR_LINE, OCEAN, STATE_NAMES, STOPS, counties, county_density_2020,
                    lakes, neighbours, scale_color)
from .choro import render as choro_render
from .core import FONT, ROOT, View, albers, states

W, H, FPS = 1920, 1080, 24
MAPBOX = (470, 14, 1900, 905)
RX0, RY0, RX1, RY1 = 452, 0, 1920, 930
UNCOUNTED = (205, 198, 178)
NAVY = (8, 18, 60)
YEL, WHITE, BLACK = (255, 222, 0), (255, 255, 255), (0, 0, 0)
BREAKS = [2, 6, 18, 45, 100, 250]
LABELS = ["UNDER 2", "2–6", "6–18", "18–45", "45–100", "100–250", "250+"]
YEARS = list(range(1790, 2021, 10))

INTRO, TRANS, CARD, NCARD, FINALE = 8.0, 4.0, 5.0, 4, 28.0
BLOCK0 = INTRO + NCARD * CARD            # 28 s
BLOCK = TRANS + NCARD * CARD             # 24 s
TOTAL_S = BLOCK0 + BLOCK * (len(YEARS) - 1) + FINALE
TOTAL_FRAMES = int(round(TOTAL_S * FPS))


@lru_cache(None)
def F(size):
    return ImageFont.truetype(str(FONT), size)


def T(d, xy, s, size, fill=WHITE, stroke=None, anchor="la"):
    stroke = max(3, size // 12) if stroke is None else stroke
    d.text(xy, s, font=F(size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=BLACK)


# ---- changes: growth = green triangle up, decline = red triangle down (a "+" next to a number reads as "-" on a phone)
import re as _re
UP_COL, DOWN_COL = (70, 235, 100), (255, 75, 75)
CHG_RE = _re.compile(r"([▲▼]\d[\d.,]*(?: MILLION|%)?)")
CHG_SCALE = 1.22


def up(s):
    return "▲" + s


def down(s):
    return "▼" + s


def chg(v, fmt="{:.1f}%"):
    """signed change -> '▲12.3%' or '▼5.0%' (markup that rich_text() draws in colour)"""
    return (up if v >= 0 else down)(fmt.format(abs(v)))


def rich_parts(s):
    return [p_ for p_ in CHG_RE.split(s) if p_]


def rich_len(s, size, stroke=None):
    n = 0.0
    for p_ in rich_parts(s):
        if CHG_RE.fullmatch(p_):
            sz = int(size * CHG_SCALE)
            n += sz * 0.62 + F(sz).getlength(p_[1:]) + size * 0.12
        else:
            n += F(size).getlength(p_)
    return n


def rich_text(d, xy, s, size, fill=WHITE, stroke=None, anchor="la", alpha=255):
    """like T() but the changes (▲12.3% / ▼5.0%) are drawn as a coloured triangle + number, 22% bigger.
    anchor: 'la' (left, top) or 'mm' (centre) - the only ones used by the video."""
    stroke = max(3, size // 12) if stroke is None else stroke
    x, y = xy
    fill = tuple(fill[:3]) + (alpha,)
    blk = BLACK + (alpha,)
    asc, desc = F(size).getmetrics()
    base = y + (asc - desc) / 2 if anchor == "mm" else y + asc
    if anchor == "mm":
        x -= rich_len(s, size) / 2
    for p_ in rich_parts(s):
        if CHG_RE.fullmatch(p_):
            sz = int(size * CHG_SCALE)
            col = UP_COL if p_[0] == "▲" else DOWN_COL
            h, w = sz * 0.62, sz * 0.66
            top, bot = base - h - sz * 0.04, base - sz * 0.04
            tri = [(x + w / 2, top), (x + w, bot), (x, bot)] if p_[0] == "▲" else [(x, top), (x + w, top), (x + w / 2, bot)]
            # dark outline, then fill
            d.polygon(tri, fill=blk, outline=blk)
            d.line(tri + [tri[0]], fill=blk, width=max(2, stroke - 1), joint="curve")
            d.polygon(tri, fill=col + (alpha,))
            x += w + size * 0.12
            d.text((x, base), p_[1:], font=F(sz), fill=col + (alpha,), anchor="ls", stroke_width=stroke, stroke_fill=blk)
            x += F(sz).getlength(p_[1:])
        else:
            d.text((x, base), p_, font=F(size), fill=fill, anchor="ls", stroke_width=stroke, stroke_fill=blk)
            x += F(size).getlength(p_)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def cls(d):
    return int(np.searchsorted(BREAKS, d, side="right"))


# ------------------------------------------------------------------ data / facts
@lru_cache(None)
def data():
    d = json.load(open(ROOT / "data/population.json"))
    d["pop"] = {ab: {int(y): v for y, v in dd.items()} for ab, dd in d["pop"].items()}
    d["dens"] = {ab: {int(y): v for y, v in dd.items()} for ab, dd in d["dens"].items()}
    d["us_total"] = {int(y): v for y, v in d["us_total"].items()}
    d["center"] = {int(y): v for y, v in d["center"].items()}
    return d


def miles(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 3958.8 * math.asin(math.sqrt(h))


def compass(a, b):
    dy = b["lat"] - a["lat"]
    dx = (b["lon"] - a["lon"]) * math.cos(math.radians((a["lat"] + b["lat"]) / 2))
    ang = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    return ["NORTH", "NORTHEAST", "EAST", "SOUTHEAST", "SOUTH", "SOUTHWEST", "WEST", "NORTHWEST"][int(((ang + 22.5) % 360) // 45)]


def pct_txt(p):
    return f"{p:,.0f}%" if p >= 100 else f"{p:.1f}%"


def cards(i):
    """Four fact cards for census index i: dicts(label, name, value, fmt, hl)."""
    D = data()
    y = YEARS[i]
    pop = {ab: D["pop"][ab].get(y) for ab in STATE_NAMES if ab != "DC"}
    pop = {k: v for k, v in pop.items() if v}
    out = []
    nm = lambda ab: STATE_NAMES[ab].upper()
    if i == 0:
        out.append(dict(label="THE FIRST U.S. CENSUS", text="{v} PEOPLE COUNTED", value=D["us_total"][y], hl=[]))
    top = max(pop, key=pop.get)
    out.append(dict(label="MOST POPULOUS STATE", text=f"{nm(top)}  ·  " + "{v}", value=pop[top], hl=[top]))
    if i == 0:
        dn = max(pop, key=lambda a: D["dens"][a][y])
        out.append(dict(label="DENSEST STATE (PEOPLE PER SQ MI)", text=f"{nm(dn)}  ·  " + "{v}",
                        value=round(D["dens"][dn][y]), hl=[dn]))
    else:
        py = YEARS[i - 1]
        gr = {a: (pop[a] / D["pop"][a][py] - 1) * 100 for a in pop if py in D["pop"][a] and D["pop"][a][py] >= 25000}
        fa = max(gr, key=gr.get)
        out.append(dict(label=f"FASTEST GROWTH SINCE {py} (LOWER 48)", text=f"{nm(fa)}  ·  +{pct_txt(gr[fa])}", value=None, hl=[fa]))
        new = [a for a in pop if py not in D["pop"][a]]
        if new:
            names = [nm(a) for a in sorted(new, key=lambda a: -pop[a])]
            txt = ", ".join(names[:3]) + (f" +{len(names) - 3} MORE" if len(names) > 3 else "")
            out.append(dict(label="FIRST COUNTED IN THE CENSUS", text=txt, value=None, hl=new))
        else:
            gn = {a: pop[a] - D["pop"][a][py] for a in pop if py in D["pop"][a]}
            ga = max(gn, key=gn.get)
            v = gn[ga]
            vt = f"+{v / 1e6:.1f} MILLION" if v >= 1e6 else f"+{v:,}"
            out.append(dict(label=f"BIGGEST GAIN SINCE {py} (LOWER 48)", text=f"{nm(ga)}  ·  {vt} PEOPLE", value=None, hl=[ga]))
    c = D["center"][y]
    if i == 0:
        txt = c["loc"].upper()
    else:
        c0 = D["center"][YEARS[i - 1]]
        txt = f"{c['loc'].upper()}  ·  MOVED {miles(c0, c):.0f} MI {compass(c0, c)}"
    out.append(dict(label="CENTER OF POPULATION", text=txt, value=None, hl=[], center=True))
    return out


# ------------------------------------------------------------------ static layers
class Layers:
    def __init__(self):
        v = View(W, H)
        allp = np.vstack([r for rings in states().values() for r in rings])
        x0, y0 = allp.min(0)
        x1, y1 = allp.max(0)
        bx0, by0, bx1, by1 = MAPBOX
        v.s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
        v.ox = bx0 + ((bx1 - bx0) - (x1 - x0) * v.s) / 2 - x0 * v.s
        v.oy = by0 + ((by1 - by0) - (y1 - y0) * v.s) / 2 + y1 * v.s
        self.view = v
        ss = 3
        # ---- base: ocean + neighbouring countries
        base = Image.new("RGB", (W * 2, H * 2), OCEAN)
        d = ImageDraw.Draw(base)
        for _, rings in neighbours():
            for r in rings:
                x, y = v.px(r[:, 0], r[:, 1])
                d.polygon(list(zip(x * 2, y * 2)), fill=NEIGHBOUR, outline=NEIGHBOUR_LINE, width=2)
        self.base = np.asarray(base.resize((W, H), Image.LANCZOS)).copy()
        # ---- lakes mask (applied after states)
        lm = Image.new("L", (W * 2, H * 2), 0)
        d = ImageDraw.Draw(lm)
        for r in lakes():
            x, y = v.px(r[:, 0], r[:, 1])
            d.polygon(list(zip(x * 2, y * 2)), fill=255)
        self.lakes = np.asarray(lm.resize((W, H), Image.LANCZOS)).copy()
        # ---- state borders
        bl = Image.new("L", (W * ss, H * ss), 0)
        d = ImageDraw.Draw(bl)
        self.st = {}
        for ab, rings in states().items():
            pts = [list(zip(*[a * ss for a in v.px(r[:, 0], r[:, 1])])) for r in rings]
            for p in pts:
                d.line(p + p[:1], fill=255, width=int(2.4 * ss), joint="curve")
            xs = [q[0] / ss for p in pts for q in p]
            ys = [q[1] / ss for p in pts for q in p]
            ox, oy = max(0, int(min(xs)) - 10), max(0, int(min(ys)) - 10)
            ex, ey = min(W, int(max(xs)) + 11), min(H, int(max(ys)) + 11)
            bw, bh = ex - ox, ey - oy
            if bw <= 0 or bh <= 0:
                continue
            sh = lambda: Image.new("L", (bw * ss, bh * ss), 0)
            m, o1, o2 = sh(), sh(), sh()
            dm, d1, d2 = ImageDraw.Draw(m), ImageDraw.Draw(o1), ImageDraw.Draw(o2)
            for p in pts:
                q = [(a - ox * ss, b - oy * ss) for a, b in p]
                dm.polygon(q, fill=255)
                d1.line(q + q[:1], fill=255, width=11 * ss, joint="curve")
                d2.line(q + q[:1], fill=255, width=5 * ss, joint="curve")
            f = lambda im: np.asarray(im.resize((bw, bh), Image.BOX)).astype(np.float32)[..., None] / 255
            self.st[ab] = dict(box=(ox, oy, ex, ey), mask=f(m), dark=f(o1), yel=f(o2))
        self.borders = np.asarray(bl.resize((W, H), Image.BOX)).astype(np.float32)[..., None] / 255
        self.px = lambda lon, lat: tuple(float(a) for a in v.px(*albers(lon, lat)))
        self.base_u8 = self.base.copy()
        self.base_r = self.base[RY0:RY1, RX0:RX1].astype(np.float32)
        self.lakes_r = (self.lakes[RY0:RY1, RX0:RX1, None].astype(np.float32) / 255)
        self.borders_r = self.borders[RY0:RY1, RX0:RX1] * 0.92
        self._finale = None

    def finale_img(self):
        if self._finale is None:
            fills = {}
            for g, dd in county_density_2020().items():
                fills[g] = STOPS[cls(dd)]
            self._finale = np.asarray(choro_render_frame(self.view, fills))[RY0:RY1, RX0:RX1].astype(np.float32)
        return self._finale


def choro_render_frame(view, fills):
    """Full-frame county choropleth identical in style to the state frames (ocean/neighbours/lakes/lines)."""
    img = choro_render(view, fills, level="county", county_line_alpha=60, state_line_w=7)
    return img


# ------------------------------------------------------------------ frame renderer
class Renderer:
    def __init__(self):
        self.L = Layers()
        D = data()
        self.D = D
        self.cards = [cards(i) for i in range(len(YEARS))]
        self.cent_px = {y: self.L.px(D["center"][y]["lon"], D["center"][y]["lat"]) for y in YEARS}
        # class matrix: state -> list(class or None) per year
        self.cm = {ab: [(cls(D["dens"][ab][y]) if y in D["dens"].get(ab, {}) else None) for y in YEARS]
                   for ab in self.L.st}

    # ---- timeline helpers
    def locate(self, t):
        """-> (block i, local time in block). Finale is block len(YEARS)."""
        if t < BLOCK0:
            return 0, t
        t -= BLOCK0
        i = int(t // BLOCK) + 1
        if i >= len(YEARS):
            return len(YEARS), t - BLOCK * (len(YEARS) - 1)
        return i, t - BLOCK * (i - 1)

    def state_colour(self, ab, i, p):
        """colour of state at transition i-1 -> i, progress p (0..1)."""
        a = self.cm[ab][i - 1] if i > 0 else None
        b = self.cm[ab][i]
        if i == 0:
            a = b
        if a is None and b is None:
            return UNCOUNTED
        if a is None:
            c1 = np.array(STOPS[b], float)
            return tuple(np.array(UNCOUNTED) * (1 - p) + c1 * p)
        if b is None:
            return UNCOUNTED
        return scale_color((a + (b - a) * p) / 6.0)

    def frame(self, n):
        t = n / FPS
        i, lt = self.locate(t)
        fin = i == len(YEARS)
        ii = len(YEARS) - 1 if fin else i
        L = self.L
        cv = L.base_r.copy()
        p = 1.0
        if ii > 0 and lt < TRANS and not fin:
            p = ease(lt / TRANS)
        for ab, s in L.st.items():
            x0, y0, x1, y1 = s["box"]
            col = np.array(self.state_colour(ab, ii, p), np.float32)
            reg = cv[y0 - RY0:y1 - RY0, x0 - RX0:x1 - RX0]
            reg += (col - reg) * s["mask"]
        cv += (np.array(OCEAN, np.float32) - cv) * L.lakes_r
        cv *= 1 - L.borders_r
        if fin:
            a = ease(lt / 4.0)
            cv = cv * (1 - a) + L.finale_img() * a
        card = None
        ci = -1
        cs = (INTRO if ii == 0 else TRANS)
        if not fin and lt >= cs:
            ci = min(NCARD - 1, int((lt - cs) // CARD))
            card = self.cards[ii][ci]
            pulse = 0.55 + 0.45 * math.sin((lt - cs) * 5.0)
            for ab in card["hl"]:
                s = L.st.get(ab)
                if not s:
                    continue
                x0, y0, x1, y1 = s["box"]
                reg = cv[y0 - RY0:y1 - RY0, x0 - RX0:x1 - RX0]
                reg -= reg * s["dark"] * 0.9
                reg += (np.array(YEL, np.float32) - reg) * s["yel"] * pulse
        full = L.base_u8.copy()
        full[RY0:RY1, RX0:RX1] = np.clip(cv, 0, 255).astype(np.uint8)
        img = Image.fromarray(full)
        d = ImageDraw.Draw(img, "RGBA")
        # ---- centre of population: trail + dot
        yr_idx = ii
        pts = [self.cent_px[y] for y in YEARS[:yr_idx]]
        if ii > 0 and p < 1 and not fin:
            a, b = self.cent_px[YEARS[ii - 1]], self.cent_px[YEARS[ii]]
            pts.append((a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p))
        else:
            pts.append(self.cent_px[YEARS[ii]])
        if len(pts) > 1:
            d.line(pts, fill=BLACK + (255,), width=11, joint="curve")
            d.line(pts, fill=YEL + (255,), width=5, joint="curve")
        cx, cy = pts[-1]
        r = 15 + (6 * (0.5 + 0.5 * math.sin(lt * 6)) if (card and card.get("center")) else 0)
        d.ellipse([cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5], fill=BLACK + (255,))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 40, 40, 255), outline=WHITE + (255,), width=4)
        # ---- left panel
        d.rectangle([0, 0, 452, 912], fill=NAVY + (240,))
        d.line([(452, 0), (452, 912)], fill=YEL + (255,), width=5)
        if fin:
            yshow, tot = 2020, self.D["us_total"][2020]
        else:
            if ii > 0 and p < 1:
                yshow = int(round(YEARS[ii - 1] + (YEARS[ii] - YEARS[ii - 1]) * p))
                tot = int(round(self.D["us_total"][YEARS[ii - 1]] + (self.D["us_total"][YEARS[ii]] - self.D["us_total"][YEARS[ii - 1]]) * p))
            else:
                yshow, tot = YEARS[ii], self.D["us_total"][YEARS[ii]]
        T(d, (226, 108), str(yshow), 190, fill=YEL, stroke=10, anchor="mm")
        T(d, (28, 205), "U.S. POPULATION", 34, fill=WHITE, stroke=3)
        T(d, (28, 232), f"{tot:,}", 86, fill=YEL, stroke=6)
        T(d, (28, 350), "PEOPLE PER SQ MI", 34, fill=WHITE, stroke=3)
        yy = 398
        for k, lab in enumerate(LABELS):
            d.rectangle([28, yy, 92, yy + 36], fill=STOPS[k] + (255,), outline=BLACK + (255,), width=3)
            T(d, (108, yy + 18), lab, 32, fill=WHITE, stroke=3, anchor="lm")
            yy += 46
        d.rectangle([28, yy, 92, yy + 36], fill=UNCOUNTED + (255,), outline=BLACK + (255,), width=3)
        T(d, (108, yy + 18), "NOT YET COUNTED", 32, fill=WHITE, stroke=3, anchor="lm")
        yy += 50
        d.ellipse([46, yy + 4, 74, yy + 32], fill=(255, 40, 40, 255), outline=WHITE + (255,), width=3)
        T(d, (108, yy + 18), "CENTER OF POPULATION", 28, fill=WHITE, stroke=3, anchor="lm")
        # ---- bottom: card band + footnote
        d.rectangle([0, 912, W, H], fill=NAVY + (255,))
        d.line([(0, 912), (W, 912)], fill=YEL + (255,), width=5)
        if card is not None:
            self.draw_card(img, d, card, lt - cs - ci * CARD, CARD)
        elif not fin and ii > 0 and lt < TRANS:
            y0_, y1_ = YEARS[ii - 1], YEARS[ii]
            g = (self.D["us_total"][y1_] / self.D["us_total"][y0_] - 1) * 100
            self.draw_card(img, d, dict(label=f"U.S. POPULATION GROWTH, {y0_} → {y1_}", text=f"+{pct_txt(g)}", value=None, hl=[]), lt, TRANS)
        if fin:
            self.draw_finale(img, d, lt)
        if ii == 0 and lt < INTRO:
            self.draw_intro(img, lt)
        d = ImageDraw.Draw(img, "RGBA")
        T(d, (W // 2, 1062), "AREAS AS TODAY'S STATES  ·  ALASKA & HAWAII ARE COUNTED IN THE TOTALS, NOT SHOWN", 22,
          fill=WHITE, stroke=3, anchor="mm")
        return np.asarray(img)

    def draw_card(self, img, d, card, ct, dur):
        a = ease(ct / 0.5) * (1 - ease((ct - (dur - 0.5)) / 0.5))
        if a <= 0.01:
            return
        dy = int((1 - ease(ct / 0.5)) * 40)
        y0 = 922 + dy
        ov = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rounded_rectangle([24, 0, W - 24, 124], radius=26, fill=NAVY + (int(238 * a),),
                             outline=YEL + (int(255 * a),), width=6)
        label_a = int(255 * a)
        od.text((60, 6), card["label"], font=F(32), fill=YEL + (label_a,), stroke_width=3, stroke_fill=BLACK + (label_a,))
        if card["value"] is not None:
            v = int(round(card["value"] * ease(ct / 1.6)))
            txt = card["text"].replace("{v}", f"{v:,}")
        else:
            txt = card["text"]
        od.text((60, 38), txt, font=F(58), fill=WHITE + (label_a,), stroke_width=6, stroke_fill=BLACK + (label_a,))
        img.paste(ov, (0, y0), ov)

    def draw_intro(self, img, lt):
        a = ease(lt / 1.0) * (1 - ease((lt - (INTRO - 1.5)) / 1.5))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rounded_rectangle([520, 250, 1860, 650], radius=36, fill=NAVY + (int(235 * a),),
                             outline=YEL + (int(255 * a),), width=8)
        c = int(255 * a)
        od.text((1190, 390), "AMERICA OVER TIME", font=F(150), fill=YEL + (c,), anchor="mm", stroke_width=10, stroke_fill=BLACK + (c,))
        od.text((1190, 540), "U.S. POPULATION  1790 → 2020", font=F(76), fill=WHITE + (c,), anchor="mm", stroke_width=6, stroke_fill=BLACK + (c,))
        img.paste(ov, (0, 0), ov)

    def draw_finale(self, img, d, lt):
        a1 = ease((lt - 3.0) / 1.0) * (1 - ease((lt - 13.0) / 1.0))
        a2 = ease((lt - 14.0) / 1.0)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        if a1 > 0.01:
            c = int(255 * a1)
            od.rounded_rectangle([24, 922, W - 24, 1046], radius=26, fill=NAVY + (int(238 * a1),), outline=YEL + (c,), width=6)
            od.text((60, 926), "EVERY COUNTY IN THE LOWER 48, 2020 CENSUS", font=F(32), fill=YEL + (c,), stroke_width=3, stroke_fill=BLACK + (c,))
            od.text((60, 958), f"{self.D['us_total'][2020]:,} PEOPLE", font=F(58), fill=WHITE + (c,), stroke_width=6, stroke_fill=BLACK + (c,))
        if a2 > 0.01:
            c = int(255 * a2)
            od.rounded_rectangle([520, 170, 1860, 800], radius=36, fill=NAVY + (int(240 * a2),), outline=YEL + (c,), width=8)
            lines = [("AMERICA OVER TIME", 100, YEL), ("DATA: U.S. CENSUS BUREAU", 58, WHITE),
                     ("MAP DATA: NATURAL EARTH", 58, WHITE), ("MUSIC: VITALEZZZ (CC0), OPENGAMEART.ORG", 50, WHITE),
                     ("NEW ANIMATED MAP EVERY MONDAY & FRIDAY", 50, YEL)]
            y = 250
            for s, sz, col in lines:
                od.text((1190, y), s, font=F(sz), fill=col + (c,), anchor="mm", stroke_width=max(4, sz // 12), stroke_fill=BLACK + (c,))
                y += sz + 62
        img.paste(ov, (0, 0), ov)


# ------------------------------------------------------------------ CLI helpers
def render_range(start, end, out, crf=22):
    r = Renderer()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(start, min(end, TOTAL_FRAMES)):
        pr.stdin.write(r.frame(n).tobytes())
    pr.stdin.close()
    pr.wait()
    return pr.returncode
