"""Bright choropleth renderer: regions fully filled by data, light ocean, dark borders.

Colour scale red (low / decline) -> orange -> yellow -> green (high / growth). Lightness
is not flat: dark red (L*~29) ... yellow (L*~87) ... teal-green (L*~50), and the green end
leans blue, so deuteranopes/protanopes see dark-brown vs blue-grey ends plus a bright middle.
Every map also carries a legend with numbers.

Data: US Census Bureau cartographic boundaries (cb_2020 counties, cb_2023 states),
Natural Earth 1:50m countries + lakes (public domain).
"""
from __future__ import annotations

import csv
from functools import lru_cache

import numpy as np
import shapefile
from PIL import Image, ImageDraw

from .core import CENSUS, ROOT, View, albers, states

NE = ROOT / "data" / "ne"

OCEAN = (150, 205, 245)
NEIGHBOUR = (243, 240, 230)
NEIGHBOUR_LINE = (165, 165, 160)
STATE_LINE = (22, 22, 34)

STOPS = [(140, 0, 30), (225, 25, 30), (255, 110, 0), (255, 215, 0),
         (130, 222, 30), (0, 190, 110), (0, 135, 120)]


def scale_color(v):
    """v in 0..1 -> RGB, continuous along STOPS."""
    v = float(np.clip(v, 0, 1)) * (len(STOPS) - 1)
    i = min(int(v), len(STOPS) - 2)
    t = v - i
    a, b = np.array(STOPS[i]), np.array(STOPS[i + 1])
    return tuple(int(round(x)) for x in a + (b - a) * t)


def class_color(value, breaks):
    """Discrete class colour: breaks = upper bounds of the first len(STOPS)-1 classes."""
    k = int(np.searchsorted(breaks, value, side="right"))
    return STOPS[min(k, len(STOPS) - 1)]


# ---------------- geometry ----------------
def _rings(shape):
    pts = np.array(shape.points)
    parts = list(shape.parts) + [len(pts)]
    out = []
    for a, b in zip(parts[:-1], parts[1:]):
        x, y = albers(pts[a:b, 0], pts[a:b, 1])
        out.append(np.column_stack([x, y]))
    return out


@lru_cache(None)
def counties():
    """{GEOID: (state abbr, [rings])} lower 48 + DC, 2020 boundaries."""
    r = shapefile.Reader(str(CENSUS / "counties" / "cb_2020_us_county_20m"))
    out = {}
    for sr in r.iterShapeRecords():
        if sr.record["STUSPS"] in ("AK", "HI", "PR"):
            continue
        out[sr.record["GEOID"]] = (sr.record["STUSPS"], _rings(sr.shape))
    return out


@lru_cache(None)
def neighbours():
    r = shapefile.Reader(str(NE / "ne_50m_admin_0_countries"))
    out = []
    for sr in r.iterShapeRecords():
        if sr.record["CONTINENT"] != "North America" and sr.record["ADM0_A3"] not in ("CUB", "BHS"):
            continue
        out.append((sr.record["ADM0_A3"], _rings(sr.shape)))
    return out


@lru_cache(None)
def lakes():
    r = shapefile.Reader(str(NE / "ne_50m_lakes"))
    out = []
    for sr in r.iterShapeRecords():
        lon = np.array(sr.shape.points)[:, 0]
        lat = np.array(sr.shape.points)[:, 1]
        if lon.min() > -130 and lon.max() < -60 and lat.min() > 24 and lat.max() < 55:
            out.extend(_rings(sr.shape))
    return out


# ---------------- data ----------------
@lru_cache(None)
def county_density_2020():
    """GEOID -> people per sq mi of land, 2020 Census (CenPop2020 counts / Gazetteer land area)."""
    pop = {}
    with open(CENSUS / "CenPop2020_Mean_CO.txt", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            pop[row["STATEFP"] + row["COUNTYFP"]] = int(row["POPULATION"])
    area = {}
    with open(CENSUS / "2020_Gaz_counties_national.txt", encoding="utf-8") as f:
        rows = csv.reader(f, delimiter="\t")
        head = [h.strip() for h in next(rows)]
        gi, ai = head.index("GEOID"), head.index("ALAND_SQMI")
        for row in rows:
            area[row[gi].strip()] = float(row[ai])
    return {g: pop[g] / area[g] for g in pop if g in area and area[g] > 0}


@lru_cache(None)
def apportionment():
    """{(name, year): dict} from Census apportionment.csv (resident population 1910-2020)."""
    out = {}
    with open(CENSUS / "apportionment.csv", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            out[(row["Name"], int(row["Year"]))] = row
    return out


def num(s):
    return float(str(s).replace(",", "")) if s not in ("", None) else None


STATE_NAMES = {
    "AL": "Alabama", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
    "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia", "FL": "Florida",
    "GA": "Georgia", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
}


# ---------------- drawing ----------------
def render(view: View, fills: dict, level="state", ss=2, county_line_alpha=70,
           state_line_w=None) -> Image.Image:
    """fills: {state abbr or county GEOID: rgb}. Missing regions -> light neutral."""
    W, H = view.w * ss, view.h * ss
    img = Image.new("RGB", (W, H), OCEAN)
    d = ImageDraw.Draw(img)

    def poly(r):
        x, y = view.px(r[:, 0], r[:, 1])
        return list(zip(x * ss, y * ss))

    lw = max(1, round(view.w / 1280 * 1.2 * ss))
    for code, rings in neighbours():
        for r in rings:
            d.polygon(poly(r), fill=NEIGHBOUR, outline=NEIGHBOUR_LINE, width=lw)
    if level == "county":
        cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(cl)
        for g, (_, rings) in counties().items():
            col = fills.get(g, NEIGHBOUR)
            for r in rings:
                p = poly(r)
                d.polygon(p, fill=col)
                cd.line(p + p[:1], fill=(20, 20, 30, county_line_alpha), width=max(1, ss // 1))
        img.paste(Image.alpha_composite(img.convert("RGBA"), cl).convert("RGB"))
        d = ImageDraw.Draw(img)
    else:
        for ab, rings in states().items():
            for r in rings:
                d.polygon(poly(r), fill=fills.get(ab, NEIGHBOUR))
    for r in lakes():
        d.polygon(poly(r), fill=OCEAN)
    sw = state_line_w or max(2, round(view.w / 1280 * 2.2 * ss))
    for ab, rings in states().items():
        for r in rings:
            p = poly(r)
            d.line(p + p[:1], fill=STATE_LINE, width=sw, joint="curve")
    return img.resize((view.w, view.h), Image.LANCZOS)


def legend(img, xy, labels, title, size=1.0, colors=None):
    """Big legend: coloured boxes + numbers. labels: list of strings, one per colour."""
    from .core import text
    colors = colors or STOPS
    x, y = xy
    bw, bh = int(46 * size), int(34 * size)
    text(img, (x, y), title, int(30 * size), fill=(255, 255, 255), shadow=False)
    y += int(44 * size)
    d = ImageDraw.Draw(img)
    for c, lab in zip(colors, labels):
        d.rectangle([x, y, x + bw, y + bh], fill=c, outline=(20, 20, 30), width=max(2, int(3 * size)))
        text(img, (x + bw + int(12 * size), y + bh // 2), lab, int(28 * size), fill=(255, 255, 255),
             anchor="lm", shadow=False)
        y += bh + int(6 * size)
