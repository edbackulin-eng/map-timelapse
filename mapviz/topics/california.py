"""Topic: California population growth 1850-2020 (state mode: camera on California, county map from 1900)."""
from types import SimpleNamespace

from .. import story as _s
from . import _state
from .sun_belt import SOURCES as _SB

SLUG = "california"
FOCUS = "CA"
YEARS = list(range(1850, 2021, 10))
RUN, HOLD = 12.0, 20.5
VIEW_FILL, VIEW_SHIFT = 0.94, (60, 0)
CITIES_FILE = "data/cities_ca.json"
CITY_LEGEND = "CITY IN THE U.S. TOP 100"
COUNTER_LABEL = "CALIFORNIA POPULATION"
INTRO_LINE = "CALIFORNIA POPULATION  1850 → 2020"
FIRST_LABEL = "CALIFORNIA IN 1850"
REGION_CAPTION = False
FRONTIER = False
SHOW_CENTER = False
FOOTER = "BEFORE 1900: STATE AVERAGE  ·  FROM 1900: COUNTIES (TODAY'S BOUNDARIES)  ·  DATA: U.S. CENSUS BUREAU"
FINAL_CAPTION = "2020: 39,538,223 PEOPLE IN CALIFORNIA, THE MOST POPULOUS STATE"
CREDIT_EVENTS = "EVENT SOURCES: NPS, USGS, FHWA, CENSUS BUREAU"
TITLE = "California Population Growth 1850–2020: From Gold Rush to 39 Million"
HOOK = ("In 1850 California counted 92,597 people. In 2020 it counted 39.5 million. Watch the state fill up county by county, "
        "from the Gold Rush and the railroad to Los Angeles, the Bay Area and the Inland Empire.")
HASHTAGS = ["#California", "#CaliforniaHistory", "#Census", "#MapAnimation"]
TAGS = ["california population", "california population growth", "california population over time", "california history",
        "los angeles population growth", "california population decline", "bay area growth"]

facts, captions = _state.make("CA", "California")
CAP0 = captions.CAP0 = "HOW 92,597 CALIFORNIANS BECAME 39.5 MILLION: 1850 TO 2020"


def dyn(name, D):
    if name == "passes_ny":
        y = next(y for y in YEARS if D["pop"]["CA"][y] > D["pop"]["NY"][y])
        return f"BY {y} CALIFORNIA IS THE MOST POPULOUS STATE: {D['pop']['CA'][y] / 1e6:.1f} MILLION VS {D['pop']['NY'][y] / 1e6:.1f} IN NEW YORK"
    if name == "seats":
        a, b = _state.seats_change("California", 2010, 2020)
        return f"CALIFORNIA {'GAINS' if b > a else 'LOSES'} A HOUSE SEAT: {a} → {b}"
    raise KeyError(name)


SOURCES = dict(_s.SOURCES)
SOURCES.update({
    "usgs_1906": dict(title="The Great 1906 San Francisco Earthquake", publisher="U.S. Geological Survey",
                      url="https://earthquake.usgs.gov/earthquakes/events/1906calif/18april/",
                      supports="April 18, 1906, 5:12 a.m.; the often-quoted 700 deaths are believed to underestimate the loss of life by a factor of 3 or 4."),
    "nps_ww2": _SB["nps_ww2"],
})
SOURCES["nps_ww2"] = dict(SOURCES["nps_ww2"], supports="In the first two months of 1942 alone, a million people migrated to California, Oregon, and Washington (p. 58).")

EVENTS = [
    dict(year=1869, icon="train", title="GOLDEN SPIKE", text="THE FIRST TRANSCONTINENTAL RAILROAD LINKS CALIFORNIA TO THE EAST", src="golden_spike"),
    dict(year=1906, icon="house", title="SAN FRANCISCO EARTHQUAKE", text="QUAKE AND FIRE: DEATHS LIKELY 3-4 TIMES THE OFTEN-QUOTED 700", src="usgs_1906"),
    dict(year=1935, icon="wind", title="DUST BOWL", text="DROUGHT AND DUST PUSH FAMILIES WEST: AN ESTIMATED 210,000 REACH CALIFORNIA", src="dustbowl"),
    dict(year=1942, icon="ship", title="WARTIME MOVES", text="A MILLION PEOPLE MOVE TO CALIFORNIA, OREGON AND WASHINGTON IN EARLY 1942", src="nps_ww2"),
    dict(year=1957, icon="shield", title="INTERSTATE HIGHWAYS", text="1956 LAW AUTHORIZES 41,000 MILES OF FREEWAYS", src="interstate"),
    dict(year=1970, icon="star", title="NUMBER ONE", text="", src="census_states", dyn="passes_ny"),
    dict(year=2020, icon="star", title="HOUSE SEATS", text="", src="census_apport", dyn="seats"),
]
MIGRATIONS, RAILS, TRANSCON = [], [], []
ZOOMS = [
    dict(name="Los Angeles", y0=1920, y1=1930, center=(-118.2, 34.0), zoom=2.6, why="LOS ANGELES BOOMS"),
    dict(name="San Francisco", y0=1940, y1=1950, center=(-122.25, 37.7), zoom=2.8, why="THE BAY AREA"),
    dict(name="San Diego", y0=1950, y1=1960, center=(-117.1, 32.8), zoom=2.8, why="SAN DIEGO GROWS"),
    dict(name="San Jose", y0=1970, y1=1980, center=(-121.9, 37.3), zoom=2.8, why="SAN JOSE GROWS"),
    dict(name="Riverside", y0=1990, y1=2000, center=(-117.4, 34.0), zoom=2.6, why="INLAND SOUTHERN CALIFORNIA"),
]
story = SimpleNamespace(SOURCES=SOURCES, EVENTS=EVENTS, MIGRATIONS=MIGRATIONS, RAILS=RAILS, TRANSCON=TRANSCON, ZOOMS=ZOOMS)
COVER = dict(big="1850 → 2020", small="CALIFORNIA GROWS", center=(-119.5, 36.5), fill=3.0, cx=0.45, cy=0.58)
