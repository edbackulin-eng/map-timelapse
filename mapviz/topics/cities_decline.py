"""Topic: American cities in decline 1900-2020 (national map; city circles turn red when a city falls below its highest census count)."""
from types import SimpleNamespace

from .. import story as _s
from .sun_belt import SOURCES as _SB

SLUG = "cities-decline"
YEARS = list(range(1900, 2021, 10))
RUN, HOLD = 16.0, 21.0
CITIES_FILE = "data/cities_decline.json"
CITY_LEGEND = "CITY (CENSUS COUNT)"
LEGEND_CIRCLES = [((235, 40, 40), "CITY BELOW ITS PEAK")]
INTRO_LINE = "AMERICAN CITIES IN DECLINE  1900 → 2020"
FIRST_LABEL = "THE U.S. IN 1900"
REGION_CAPTION = False
FRONTIER = False
SHOW_CENTER = False
CREDIT_EVENTS = "EVENT SOURCES: NATIONAL ARCHIVES, FHWA, CENSUS BUREAU"
TITLE = "American Cities in Decline: Detroit, St. Louis, Cleveland (1900–2020)"
HOOK = ("In 1950 Detroit had 1.85 million people; in 2020 it had 639,000. St. Louis, Cleveland, Pittsburgh and Buffalo lost half or more. "
        "Watch America's big cities rise, peak and shrink on the map, census by census.")
HASHTAGS = ["#Detroit", "#USHistory", "#Census", "#MapAnimation"]
TAGS = ["american cities in decline", "detroit population decline", "rust belt cities", "shrinking cities", "st louis population",
        "cleveland population", "us cities population history"]


def _cities(X):
    return [c for c in X.cities()]


def _pop(c, y):
    return c["pop"].get(str(y))


def _peak_before(c, years):
    v = [_pop(c, y) for y in years if _pop(c, y)]
    return max(v) if v else None


def city_fill(c, i, pop, fin):
    """white -> red as a city falls below its highest earlier census count (5% below = fully red)."""
    ys = YEARS if fin else YEARS[:i]
    pk = max([v for v in (c["pops"][k] for k in range(len(ys))) if v] or [0])
    if not pk or pop >= pk:
        return (255, 255, 255)
    f = min(1.0, (1 - pop / pk) / 0.05)
    return (255, 255 - 215 * f, 255 - 215 * f)


def _shrink(X, y0, y1):
    both = [c for c in _cities(X) if _pop(c, y0) and _pop(c, y1)]
    ch = {c["name"]: (_pop(c, y1) / _pop(c, y0) - 1) * 100 for c in both}
    return both, ch


def facts(i, X):
    D, Y = X.D, X.YEARS
    y = Y[i]
    if i == 0:
        cs = {c["name"]: _pop(c, y) for c in _cities(X) if _pop(c, y)}
        top = max(cs, key=cs.get)
        return [dict(label=FIRST_LABEL, text=f"{D['us_total'][y]:,} PEOPLE COUNTED", hl=[]),
                dict(label="LARGEST CITY", text=f"{top.upper()}  ·  {cs[top]:,}", hl=[]),
                dict(label="DETROIT IN 1900", text=f"{cs['Detroit']:,} PEOPLE", hl=[]),
                dict(label="ST. LOUIS IN 1900", text=f"{cs['St. Louis']:,} PEOPLE", hl=[])]
    y0 = Y[i - 1]
    both, ch = _shrink(X, y0, y)
    lose = [n for n in ch if ch[n] < 0]
    out = [dict(label=f"CITIES THAT SHRANK, {y0}-{y}", text=f"{len(lose)} OF THESE {len(both)}", hl=[])]
    if lose:
        n = min(lose, key=ch.get)
        out.append(dict(label=f"BIGGEST DROP SINCE {y0}", text=f"{n.upper()}  ·  {ch[n]:.1f}%", hl=[]))
    g = max(ch, key=ch.get)
    out.append(dict(label=f"FASTEST GROWTH SINCE {y0}", text=f"{g.upper()}  ·  +{X.pct_txt(ch[g])}", hl=[]))
    below = {}
    for c in _cities(X):
        v = _pop(c, y)
        pk = _peak_before(c, [yy for yy in Y if yy < y])
        if v and pk and v < pk:
            pky = max((yy for yy in Y if yy < y and _pop(c, yy)), key=lambda yy: _pop(c, yy))
            below[c["name"]] = ((v / pk - 1) * 100, pky)
    if below:
        n = min(below, key=lambda k: below[k][0])
        out.append(dict(label="FURTHEST BELOW ITS PEAK", text=f"{n.upper()}  ·  {below[n][0]:.0f}% SINCE {below[n][1]}", hl=[]))
    else:
        cs = {c["name"]: _pop(c, y) for c in _cities(X) if _pop(c, y)}
        top = max(cs, key=cs.get)
        out.append(dict(label="LARGEST CITY", text=f"{top.upper()}  ·  {cs[top]:,}", hl=[]))
    return out


def captions(i, X):
    D, Y = X.D, X.YEARS
    if i == 0:
        return [(X.INTRO + 5.5, 7.5, "AMERICA'S BIG CITIES: HOW THEY GREW, PEAKED AND SHRANK, 1900 TO 2020")]
    y0, y1 = Y[i - 1], Y[i]
    out = []
    zoom = next((z for z in X.zooms if z["y1"] == y1), None)
    c = next((c for c in X.cities() if zoom and c["name"] == zoom["name"]), None)
    both, ch = _shrink(X, y0, y1)
    lose = [n for n in ch if ch[n] < 0]
    if c:
        out.append((0.8, 7.0, f"{zoom['name'].upper()} {y0}-{y1}: {_pop(c, y0):,} → {_pop(c, y1):,} PEOPLE"))
    else:
        out.append((0.8, 7.0, f"{y0}-{y1}: {len(lose)} OF THESE {len(both)} BIG CITIES LOSE PEOPLE"))
    nb = sum(1 for c in _cities(X) if _pop(c, y1) and (_peak_before(c, [yy for yy in Y if yy < y1]) or 0) > _pop(c, y1))
    tot = len([c for c in _cities(X) if _pop(c, y1)])
    out.append((X.RUN + 3.2, 7.5, f"{y1}: {nb} OF {tot} CITIES {'IS' if nb == 1 else 'ARE'} BELOW {'ITS' if nb == 1 else 'THEIR'} PEAK"))
    t1 = D["us_total"][y1]
    out.append((X.RUN + 12.0, 7.5, f"MEANWHILE THE U.S. GROWS TO {t1:,} PEOPLE"))
    return out


def dyn(name, D):
    import json
    from ..core import ROOT
    cs = json.load(open(ROOT / CITIES_FILE))
    if name == "peak1950":
        n = sum(1 for c in cs if max(c["pop"], key=lambda y: c["pop"][y]) == "1950")
        return f"{n} OF THESE {len(cs)} CITIES HAVE THEIR HIGHEST CENSUS COUNT EVER IN 1950"
    if name == "detroit":
        c = next(c for c in cs if c["name"] == "Detroit")
        a, b = c["pop"]["1950"], c["pop"]["2020"]
        return f"DETROIT: {b:,} PEOPLE IN 2020, DOWN {100 * (1 - b / a):.0f}% FROM {a:,} IN 1950"
    raise KeyError(name)


SOURCES = dict(_s.SOURCES)
SOURCES["gi_bill"] = _SB["gi_bill"]
EVENTS = [
    dict(year=1916, icon="arrows", title="GREAT MIGRATION", text="ABOUT 6 MILLION BLACK AMERICANS LEAVE THE SOUTH, 1910-1970, MANY FOR NORTHERN CITIES", src="greatmig"),
    dict(year=1944, icon="house", title="GI BILL", text="4.3 MILLION VETERAN HOME LOANS BY 1955", src="gi_bill"),
    dict(year=1950, icon="star", title="THE PEAK", text="", src="census_cities", dyn="peak1950"),
    dict(year=1957, icon="shield", title="INTERSTATE HIGHWAYS", text="1956 LAW AUTHORIZES 41,000 MILES OF FREEWAYS", src="interstate"),
    dict(year=2020, icon="star", title="DETROIT", text="", src="census_cities", dyn="detroit"),
]
MIGRATIONS = []
for _m in _s.MIGRATIONS:
    if _m["name"].startswith("gm_"):
        MIGRATIONS.append(dict(_m))
    elif _m["name"].startswith("sun_"):
        MIGRATIONS.append(dict(_m, y0=1960, y1=2020))
RAILS, TRANSCON = [], []
ZOOMS = [
    dict(name="Detroit", y0=1950, y1=1960, center=(-83.1, 42.4), zoom=7.5, why="THE FIRST LOSSES"),
    dict(name="St. Louis", y0=1960, y1=1970, center=(-90.3, 38.65), zoom=7.5, why="ST. LOUIS SHRINKS"),
    dict(name="Cleveland", y0=1970, y1=1980, center=(-81.7, 41.45), zoom=7.5, why="CLEVELAND SHRINKS"),
    dict(name="Pittsburgh", y0=1980, y1=1990, center=(-79.95, 40.45), zoom=7.5, why="PITTSBURGH SHRINKS"),
    dict(name="Buffalo", y0=1990, y1=2000, center=(-78.85, 42.9), zoom=7.5, why="BUFFALO SHRINKS"),
]
story = SimpleNamespace(SOURCES=SOURCES, EVENTS=EVENTS, MIGRATIONS=MIGRATIONS, RAILS=RAILS, TRANSCON=TRANSCON, ZOOMS=ZOOMS)
COVER = dict(big="1950 → 2020", small="CITIES SHRINK", center=(-84.0, 41.5), fill=3.2, cx=0.45, cy=0.6)
