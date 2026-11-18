"""Topic: US expansion from 13 to 50 states, 1790-1960 (statehood map; Alaska and Hawaii as insets).
Admission dates: U.S. Senate, 'States in the Senate' pages (data/statehood/senate_pages.txt, fetched 2026-11-18)."""
import math
import re
from datetime import date
from functools import lru_cache
from types import SimpleNamespace

import numpy as np
import shapefile
from PIL import Image, ImageDraw

from .. import story as _s
from ..core import CENSUS, ROOT

SLUG = "13-to-50-states"
YEARS = list(range(1790, 1921, 10)) + [1960]      # 1920-1960: one block (no admissions until 1959)
RUN, HOLD = 14.0, 17.0
CITIES_FILE = "data/cities_none.json"
COUNTER_LABEL = "STATES IN THE UNION"
LEGEND_TITLE = "BECAME A STATE"
LEGEND_NONE = "NOT YET A STATE"
INTRO_LINE = "FROM 13 TO 50 STATES  1790 → 1959"
FIRST_LABEL = "THE FIRST CENSUS"
REGION_CAPTION = False
FRONTIER = False
SHOW_CENTER = False
SHOW_ROADS = False
FINALE_COUNTIES = False
HL_DARK = 0.0
FOOTER = "STATE SHAPES AS TODAY'S  ·  ADMISSION DATES: U.S. SENATE  ·  POPULATION: U.S. CENSUS BUREAU"
FINAL_CAPTION = "1959: HAWAII BECOMES THE 50TH STATE"
CREDIT_EVENTS = "EVENT SOURCES: U.S. SENATE, STATE DEPARTMENT OFFICE OF THE HISTORIAN, NATIONAL ARCHIVES"
TITLE = "US Expansion from 13 to 50 States: Every Admission on the Map (1787–1959)"
HOOK = ("From the 13 original states to Hawaii in 1959: watch every state join the Union on the map, with the purchases, "
        "treaties and annexations that made the country, and the population at every census.")
HASHTAGS = ["#USHistory", "#Statehood", "#AmericanHistory", "#MapAnimation"]
TAGS = ["us expansion from 13 to 50 states", "us expansion timeline", "how the us got its states", "statehood timeline", "us territorial expansion",
        "states by date of admission", "manifest destiny map"]

ORIGINAL = {"DE", "PA", "NJ", "GA", "CT", "MA", "MD", "SC", "NH", "VA", "NY", "NC", "RI"}
ERAS = [((40, 95, 190), "ORIGINAL 13 (1787-1790)", 1790), ((0, 160, 150), "1791-1820", 1820), ((120, 200, 60), "1821-1850", 1850),
        ((255, 200, 0), "1851-1890", 1890), ((245, 115, 35), "1891-1959", 1960)]
LEGEND = [(c, lab) for c, lab, _ in ERAS]
UNC = (205, 200, 185)
NAMES = {}
MONTHS = {m: k for k, m in enumerate("January February March April May June July August September October November December".split(), 1)}


@lru_cache(None)
def admissions():
    """abbr -> (fractional year, date, order) from the Senate pages."""
    txt = (ROOT / "data/statehood/senate_pages.txt").read_text(encoding="utf-8")
    out = {}
    for blk in txt.split("== ")[1:]:
        head, _, body = blk.partition("\n")
        ab = head.split()[0]
        if ab == "POLICY":
            continue
        m = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}), (\d{4})", body)
        if ab == "DE" and not m:          # page sentence is cut before the date: Delaware ratified first, December 7, 1787
            d = date(1787, 12, 7)
        else:
            d = date(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
        fy = d.year + (d.timetuple().tm_yday - 1) / 365.25
        out[ab] = (fy, d)
    order = sorted(out, key=lambda a: out[a][0])
    return {a: (out[a][0], out[a][1], order.index(a) + 1) for a in out}


def adm_year(ab):
    a = admissions().get(ab)
    if a is None:
        return 9999.0
    return -1.0 if ab in ORIGINAL else a[0]


def era_colour(ab):
    y = admissions()[ab][0]
    for c, _, last in ERAS:
        if y < last + 1:
            return c
    return ERAS[-1][0]


def state_fill(ab, Y):
    a = adm_year(ab)
    if ab == "DC":
        return (150, 150, 150)
    if Y < a:
        return UNC
    f = min(1.0, (Y - a) / 0.1)      # fast fade: the counter stops at the census year right after late-year admissions
    c = era_colour(ab)
    return tuple(UNC[k] + (c[k] - UNC[k]) * f for k in range(3))


def counter_value(Y):
    return sum(1 for ab in admissions() if adm_year(ab) <= Y)


def _names():
    from ..choro import STATE_NAMES
    return dict(STATE_NAMES, AK="Alaska", HI="Hawaii")


def _new(y0, y1):
    """states admitted while the counter runs from y0 to y1 (y0 < date <= y1)"""
    return sorted((ab for ab in admissions() if ab not in ORIGINAL and y0 < admissions()[ab][0] <= y1), key=lambda a: admissions()[a][0])


def facts(i, X):
    D, Y = X.D, X.YEARS
    nm = _names()
    y = Y[i]
    if i == 0:
        return [dict(label=FIRST_LABEL, text=f"{D['us_total'][y]:,} PEOPLE COUNTED", hl=[]),
                dict(label="STATES IN THE UNION", text="13", hl=sorted(ORIGINAL)),
                dict(label="THE LAST OF THE 13", text="RHODE ISLAND  ·  MAY 29, 1790", hl=["RI"])]
    y0 = Y[i - 1]
    new = _new(y0, y)
    n = counter_value(y)
    out = []
    if new:
        names = [nm[a].upper() for a in new]
        txt = ", ".join(names[:3]) + (f" +{len(names) - 3} MORE" if len(names) > 3 else "")
        out.append(dict(label=f"NEW STATES SINCE {y0}", text=txt, hl=new))
    else:
        out.append(dict(label=f"NEW STATES SINCE {y0}", text="NONE", hl=[]))
    n0 = counter_value(y0)
    out.append(dict(label="STATES IN THE UNION", text=f"{n}" + (f"  (WAS {n0} IN {y0})" if n0 != n else ""), hl=[]))
    out.append(dict(label=f"U.S. POPULATION, {y} CENSUS", text=f"{D['us_total'][y]:,}", hl=[]))
    return out


def captions(i, X):
    D, Y = X.D, X.YEARS
    nm = _names()
    if i == 0:
        return [(X.INTRO + 5.5, 7.5, "EVERY STATE, THE DAY IT JOINED THE UNION: 1787 TO 1959")]
    y0, y1 = Y[i - 1], Y[i]
    new = _new(y0, y1)
    if not new:
        t = f"{y0}-{y1}: NO NEW STATES"
    else:
        names = [nm[a].upper() for a in new]
        t = f"{y0}-{y1}: {len(new)} NEW STATE{'S' if len(new) > 1 else ''}: " + ", ".join(names)
        if len(t) > 70:
            t = f"{y0}-{y1}: {len(new)} NEW STATES JOIN THE UNION"
    n = counter_value(y1)
    return [(0.8, 7.0, t), (X.RUN + 2.5, 7.0, f"{y1}: {n} STATES  ·  CENSUS POPULATION {D['us_total'][y1]:,}")]


# ---------------------------------------------------------------- map extras: admission labels + Alaska / Hawaii insets
INSETS = {"AK": (1738, 585, 1905, 705), "HI": (1745, 735, 1905, 815)}


def _alb(lon, lat, lat1, lat2, lon0, lat0):
    n = (math.sin(math.radians(lat1)) + math.sin(math.radians(lat2))) / 2
    c = math.cos(math.radians(lat1)) ** 2 + 2 * n * math.sin(math.radians(lat1))
    r0 = math.sqrt(c - 2 * n * math.sin(math.radians(lat0))) / n
    lon = np.radians(np.asarray(lon) - lon0)
    rho = np.sqrt(c - 2 * n * np.sin(np.radians(np.asarray(lat)))) / n
    return rho * np.sin(n * lon), r0 - rho * np.cos(n * lon)


@lru_cache(None)
def inset_polys():
    r = shapefile.Reader(str(CENSUS / "states" / "cb_2023_us_state_20m"))
    out = {}
    for sr in r.iterShapeRecords():
        ab = sr.record["STUSPS"]
        if ab not in INSETS:
            continue
        pts = np.array(sr.shape.points, float)
        parts = list(sr.shape.parts) + [len(pts)]
        rings = []
        for a, b in zip(parts[:-1], parts[1:]):
            p = pts[a:b].copy()
            if ab == "AK":
                p[:, 0] = np.where(p[:, 0] > 0, p[:, 0] - 360, p[:, 0])
                x, y = _alb(p[:, 0], p[:, 1], 55, 65, -154, 50)
            else:
                if p[:, 0].min() < -160.6:          # leave out the far northwestern islets
                    continue
                x, y = _alb(p[:, 0], p[:, 1], 8, 18, -157, 13)
            rings.append(np.column_stack([x, y]))
        allp = np.vstack(rings)
        x0, y0 = allp.min(0)
        x1, y1 = allp.max(0)
        bx0, by0, bx1, by1 = INSETS[ab]
        s = min((bx1 - bx0 - 12) / (x1 - x0), (by1 - by0 - 26) / (y1 - y0))
        ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2 - x0 * s
        oy = by0 + 20 + ((by1 - by0 - 20) - (y1 - y0) * s) / 2 + y1 * s
        out[ab] = [list(zip(ox + r_[:, 0] * s, oy - r_[:, 1] * s)) for r_ in rings if len(r_) >= 3]
    return out


@lru_cache(None)
def centroids(ox, oy, s):
    from ..core import states
    out = {}
    for ab, rings in states().items():
        r_ = max(rings, key=len)
        x, y = r_[:, 0].mean(), r_[:, 1].mean()
        out[ab] = (ox + x * s, oy - y * s)
    for ab, box in INSETS.items():
        out[ab] = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 8)
    fix = {"FL": (40, 25), "MI": (25, 40), "LA": (-20, 0), "KY": (10, 0), "VA": (20, 0), "MD": (0, -10), "ID": (0, 30), "CA": (-25, 30),
           "TX": (0, 0), "WV": (-8, 0), "NY": (30, 0), "OK": (25, 0)}
    for ab, (dx, dy) in fix.items():
        if ab in out:
            out[ab] = (out[ab][0] + dx, out[ab][1] + dy)
    return out


LABEL_S = 4.5


def label_time(ab, B0, BLK):
    fy = admissions()[ab][0]
    for i in range(1, len(YEARS)):
        y0, y1 = YEARS[i - 1], YEARS[i]
        if y0 < fy <= y1:
            return B0 + BLK * (i - 1) + RUN * (fy - y0) / (y1 - y0)
    return None


def draw_extra(R, img, t, i, lt, Y, fin):
    from ..video import F, NAVY, YEL, WHITE, BLACK
    from .. import video2 as V
    d = ImageDraw.Draw(img, "RGBA")
    # insets
    for ab, box in INSETS.items():
        d.rounded_rectangle(box, radius=10, fill=(150, 205, 240, 255), outline=NAVY + (255,), width=3)
        col = tuple(int(v) for v in state_fill(ab, Y if not fin else 1961))
        for poly in inset_polys()[ab]:
            d.polygon(poly, fill=col + (255,), outline=(22, 22, 34, 255))
        d.text((box[0] + 8, box[1] + 3), {"AK": "ALASKA", "HI": "HAWAII"}[ab], font=F(22), fill=WHITE + (255,), stroke_width=3, stroke_fill=BLACK + (255,))
    # admission labels: the state name and year, for LABEL_S seconds from the moment the counter reaches the date
    b = R.base
    cen = centroids(float(b.ox), float(b.oy), float(b.s))
    for ab in admissions():
        if ab in ORIGINAL:
            continue
        ta = label_time(ab, V.B0, V.BLK)
        if ta is None or not (ta <= t < ta + LABEL_S):
            continue
        u = t - ta
        a = min(1.0, u / 0.35, (LABEL_S - u) / 0.5)
        A = int(255 * max(0.0, a))
        x, y = cen[ab]
        nm = _names()[ab].upper()
        yr = str(admissions()[ab][1].year)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        dl.text((x, y - 15), nm, font=F(30), fill=WHITE + (255,), anchor="mm", stroke_width=4, stroke_fill=BLACK + (255,))
        dl.text((x, y + 17), yr, font=F(30), fill=YEL + (255,), anchor="mm", stroke_width=4, stroke_fill=BLACK + (255,))
        if A < 255:
            lay.putalpha(lay.getchannel("A").point(lambda v, a_=A: v * a_ // 255))
        img.paste(lay, (0, 0), lay)


def dyn(name, D):
    if name == "wv":
        return f"WEST VIRGINIA SPLITS FROM VIRGINIA AND BECOMES STATE NO. {admissions()['WV'][2]}"
    if name == "last2":
        return f"ALASKA (JANUARY 3) AND HAWAII (AUGUST 21) BECOME STATES {admissions()['AK'][2]} AND {admissions()['HI'][2]}"
    raise KeyError(name)


SOURCES = dict(_s.SOURCES)
SOURCES.update({
    "senate": dict(title="States in the Senate (one page per state: admission date and order)", publisher="U.S. Senate",
                   url="https://www.senate.gov/states/statesmap.htm",
                   supports="Admission date and order of all 50 states (e.g. https://www.senate.gov/states/OH/intro.htm)."),
    "florida": dict(title="Acquisition of Florida: Treaty of Adams-Onis (1819) and Transcontinental Treaty (1821)", publisher="U.S. Department of State, Office of the Historian",
                    url="https://history.state.gov/milestones/1801-1829/florida", supports="Spain cedes Florida to the United States, 1819."),
    "oregon": dict(title="The Oregon Territory, 1846", publisher="U.S. Department of State, Office of the Historian",
                   url="https://history.state.gov/milestones/1830-1860/oregon-territory", supports="Settlement on the 49th parallel; Senate ratified the treaty June 18, 1846."),
    "mexwar": dict(title="The Annexation of Texas, the Mexican-American War, and the Treaty of Guadalupe-Hidalgo, 1845-1848",
                   publisher="U.S. Department of State, Office of the Historian", url="https://history.state.gov/milestones/1830-1860/texas-annexation",
                   supports="Texas annexation 1845; the 1848 treaty ends the war and transfers the Southwest to the United States."),
    "gadsden": dict(title="Gadsden Purchase, 1853-1854", publisher="U.S. Department of State, Office of the Historian",
                    url="https://history.state.gov/milestones/1830-1860/gadsden-purchase", supports="$10 million for 29,670 square miles that later became part of Arizona and New Mexico."),
    "alaska": dict(title="Purchase of Alaska, 1867", publisher="U.S. Department of State, Office of the Historian",
                   url="https://history.state.gov/milestones/1866-1898/alaska-purchase", supports="March 30, 1867: Seward agrees to buy Alaska from Russia for $7.2 million."),
    "hawaii": dict(title="Joint Resolution to Provide for Annexing the Hawaiian Islands to the United States (1898)", publisher="National Archives, Milestone Documents",
                   url="https://www.archives.gov/milestone-documents/joint-resolution-for-annexing-the-hawaiian-islands", supports="On July 7, 1898, the Hawaiian Islands were annexed by this joint resolution."),
})
SOURCES["louisiana"] = dict(SOURCES["louisiana"], supports="530,000,000 acres purchased from France in 1803 for $15 million.")

EVENTS = [
    dict(year=1803, icon="scroll", title="LOUISIANA PURCHASE", text="530 MILLION ACRES BOUGHT FROM FRANCE FOR $15 MILLION", src="louisiana"),
    dict(year=1819, icon="scroll", title="FLORIDA", text="ADAMS-ONIS TREATY: SPAIN CEDES FLORIDA", src="florida"),
    dict(year=1845, icon="star", title="TEXAS ANNEXED", text="TEXAS JOINS AS THE 28TH STATE", src="mexwar"),
    dict(year=1846, icon="scroll", title="OREGON TREATY", text="THE NORTHWEST BORDER IS SET AT THE 49TH PARALLEL", src="oregon"),
    dict(year=1848, icon="scroll", title="GUADALUPE HIDALGO", text="THE MEXICAN-AMERICAN WAR ENDS; THE SOUTHWEST PASSES TO THE U.S.", src="mexwar"),
    dict(year=1853, icon="scroll", title="GADSDEN PURCHASE", text="$10 MILLION FOR 29,670 SQUARE MILES, LATER PART OF ARIZONA AND NEW MEXICO", src="gadsden"),
    dict(year=1863, icon="star", title="WEST VIRGINIA", text="", src="senate", dyn="wv"),
    dict(year=1867, icon="scroll", title="ALASKA PURCHASE", text="BOUGHT FROM RUSSIA FOR $7.2 MILLION", src="alaska"),
    dict(year=1898, icon="scroll", title="HAWAII ANNEXED", text="JULY 7, 1898: CONGRESS ANNEXES THE HAWAIIAN ISLANDS", src="hawaii"),
    dict(year=1959, icon="star", title="49 AND 50", text="", src="senate", dyn="last2"),
]
MIGRATIONS, RAILS, TRANSCON, ZOOMS = [], [], [], []
story = SimpleNamespace(SOURCES=SOURCES, EVENTS=EVENTS, MIGRATIONS=MIGRATIONS, RAILS=RAILS, TRANSCON=TRANSCON, ZOOMS=ZOOMS)
COVER = dict(big="13 → 50", small="EVERY NEW STATE", center=(-96.0, 38.0), fill=1.0, cx=0.5, cy=0.62, mode="statehood")
