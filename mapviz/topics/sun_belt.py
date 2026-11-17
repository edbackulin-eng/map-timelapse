"""Topic 2: Sun Belt Migration 1900-2020 (how the South and the West overtook the Northeast and the Midwest)."""
import csv
from types import SimpleNamespace

from .. import story as _s
from ..core import ROOT

SLUG = "sun-belt"
YEARS = list(range(1900, 2021, 10))
RUN, HOLD = 12.0, 25.0
INTRO_LINE = "SUN BELT MIGRATION  1900 → 2020"
FIRST_LABEL = "THE U.S. IN 1900"
CAP0 = "HOW THE SOUTH AND WEST OVERTOOK THE NORTH: 1900 TO 2020"
REGION_CAPTION = True
CREDIT_EVENTS = "EVENT SOURCES: NARA, NASA, NPS, CENSUS BUREAU"
FRONTIER = False
HOOK = ("Between 1900 and 2020 the South and West went from 38% to 62% of all Americans. Watch the Sun Belt rise on the map: "
        "state by state, city by city, with the events behind it.")
HASHTAGS = ["#SunBelt", "#USHistory", "#Census", "#MapAnimation"]
TAGS = ["sun belt migration", "rust belt to sunbelt migration", "us migration history", "american migration", "us population shift",
        "texas population growth", "florida population growth"]
TITLE = "Sun Belt Migration: How Americans Moved South and West (1900–2020)"

NE = {"CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"}
MW = {"IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"}


def region_share(D, y):
    """South + West share of the population (Census regions: every state outside the Northeast and the Midwest)."""
    tot = sw = 0
    for ab, series in D["pop"].items():
        v = series.get(y)
        if not v:
            continue
        tot += v
        if ab not in NE and ab not in MW:
            sw += v
    return 100.0 * sw / tot


def _first_year_over_half(D):
    return next(y for y in YEARS if region_share(D, y) > 50.0)


def _seats():
    rows = list(csv.DictReader(open(ROOT / "data/census/apportionment.csv", encoding="utf-8-sig")))
    out = {}
    for r in rows:
        if r["Geography Type"] == "State" and r["Year"] in ("2010", "2020") and r["Number of Representatives"].strip():
            out.setdefault(r["Name"], {})[int(r["Year"])] = int(r["Number of Representatives"])
    return {n: v[2020] - v[2010] for n, v in out.items() if 2010 in v and 2020 in v}


def dyn(name, D):
    if name == "half":
        y = _first_year_over_half(D)
        return f"BY {y} THE SOUTH AND WEST HOLD {region_share(D, y):.0f}% OF ALL AMERICANS"
    if name == "seats":
        ch = _seats()
        gain = {n: v for n, v in ch.items() if v > 0}
        lose = {n: v for n, v in ch.items() if v < 0}
        top = [n for n in ("Texas", "Florida") if n in gain] or sorted(gain, key=lambda n: -gain[n])[:2]
        big = [n for n in ("California", "New York", "Illinois") if n in lose]
        return (f"{len(gain)} STATES GAIN HOUSE SEATS ({', '.join(f'{n.upper()} +{gain[n]}' for n in top)}); "
                f"{len(lose)} LOSE ONE ({', '.join(n.upper() for n in big)}...)")
    raise KeyError(name)


SOURCES = dict(_s.SOURCES)
SOURCES.update({
    "carrier_patent": dict(title="Patent Drawing of Willis H. Carrier's Apparatus for Treating Air (U.S. Patent 808,897)", publisher="National Archives (DocsTeach)",
                           url="https://docsteach.org/document/patent-treating-air/",
                           supports="Patent 808,897 'Apparatus for Treating Air', filed 1904, issued January 2, 1906, assigned to Buffalo Forge Co."),
    "nps_ww2": dict(title="World War II and the American Home Front (National Historic Landmarks theme study)", publisher="National Park Service",
                    url="https://planning.lacity.gov/odocument/885c8f2d-af61-451e-b7a2-c77fce107429/WWII_and_the_American_Home_Front.pdf",
                    supports="More than 30 million Americans moved during the war, to bases and manufacturing centers (copy of the NPS PDF hosted on planning.lacity.gov; locate the NPS original before publishing)."),
    "gi_bill": dict(title="Servicemen's Readjustment Act (1944)", publisher="National Archives, Milestone Documents",
                    url="https://www.archives.gov/milestone-documents/servicemens-readjustment-act",
                    supports="Signed June 22, 1944; by 1955, 4.3 million home loans with a face value of $33 billion."),
    "nasa_houston": dict(title="60 Years Ago: The Manned Spacecraft Center Makes Houston its Home", publisher="NASA History",
                         url="https://www.nasa.gov/history/60-years-ago-the-manned-spacecraft-center-makes-houston-its-home/",
                         supports="NASA announced Houston as the site of the Manned Spacecraft Center on September 19, 1961."),
    "census_regions": dict(title="Census Regions and Divisions of the United States", publisher="U.S. Census Bureau",
                           url="https://www2.census.gov/geo/pdfs/maps-data/maps/reference/us_regdiv.pdf",
                           supports="Definition of the four regions; here 'South + West' = every state outside the Northeast and Midwest regions."),
})

EVENTS = [
    dict(year=1906, icon="snow", title="AIR CONDITIONING", text="PATENT 808,897 'APPARATUS FOR TREATING AIR' IS ISSUED", src="carrier_patent"),
    dict(year=1916, icon="arrows", title="GREAT MIGRATION", text="ABOUT 6 MILLION BLACK AMERICANS LEAVE THE SOUTH, 1910-1970", src="greatmig"),
    dict(year=1935, icon="wind", title="DUST BOWL", text="DROUGHT AND DUST PUSH FAMILIES WEST: AN ESTIMATED 210,000 REACH CALIFORNIA", src="dustbowl"),
    dict(year=1942, icon="ship", title="WARTIME MOVES", text="OVER 30 MILLION AMERICANS MOVE DURING WORLD WAR II, MANY TO BASES AND FACTORIES", src="nps_ww2"),
    dict(year=1944, icon="house", title="GI BILL", text="4.3 MILLION VETERAN HOME LOANS BY 1955", src="gi_bill"),
    dict(year=1957, icon="shield", title="INTERSTATE HIGHWAYS", text="1956 LAW AUTHORIZES 41,000 MILES OF FREEWAYS", src="interstate"),
    dict(year=1961, icon="rocket", title="SPACE CITY", text="NASA PICKS HOUSTON FOR ITS MANNED SPACECRAFT CENTER", src="nasa_houston"),
    dict(year=1980, icon="sun", title="SUN BELT PASSES 50%", text="", src="census_regions", dyn="half"),
    dict(year=2020, icon="star", title="HOUSE SEATS SHIFT", text="", src="census_apport", dyn="seats"),
]

MIGRATIONS = []
for _m in _s.MIGRATIONS:
    if _m["name"].startswith(("gm_", "dust")):
        MIGRATIONS.append(dict(_m))
    elif _m["name"].startswith("sun_"):
        MIGRATIONS.append(dict(_m, y0=1950, y1=2020))

RAILS = []
TRANSCON = []

ZOOMS = [
    dict(name="Los Angeles", y0=1920, y1=1930, center=(-118.0, 34.0), zoom=5.8, why="SOUTHERN CALIFORNIA BOOM"),
    dict(name="Miami", y0=1940, y1=1950, center=(-80.6, 26.3), zoom=7.5, why="FLORIDA'S ATLANTIC COAST"),
    dict(name="Dallas", y0=1950, y1=1960, center=(-97.0, 32.8), zoom=7.0, why="TEXAS CITIES BOOM"),
    dict(name="Houston", y0=1970, y1=1980, center=(-95.5, 29.8), zoom=8.0, why="SPACE CITY AND OIL"),
    dict(name="Phoenix", y0=1980, y1=1990, center=(-112.0, 33.5), zoom=5.5, why="DESERT CITY BOOM"),
]

story = SimpleNamespace(SOURCES=SOURCES, EVENTS=EVENTS, MIGRATIONS=MIGRATIONS, RAILS=RAILS, TRANSCON=TRANSCON, ZOOMS=ZOOMS)
COVER = dict(big="1900 → 2020", small="THE SUN BELT RISES", center=(-97.0, 37.0), fill=1.25, cx=0.5, cy=0.62,
             arrow=((-75.0, 42.5), (-93.5, 34.2)))
