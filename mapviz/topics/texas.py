"""Topic: Texas population growth 1850-2020 (state mode: the camera stays on Texas, county map from 1900)."""
from types import SimpleNamespace

from .. import story as _s
from . import _state

SLUG = "texas"
FOCUS = "TX"
YEARS = list(range(1850, 2021, 10))
RUN, HOLD = 12.0, 20.5
VIEW_FILL, VIEW_SHIFT = 0.92, (40, -10)
CITIES_FILE = "data/cities_tx.json"
CITY_LEGEND = "CITY IN THE U.S. TOP 100"
COUNTER_LABEL = "TEXAS POPULATION"
INTRO_LINE = "TEXAS POPULATION  1850 → 2020"
FIRST_LABEL = "TEXAS IN 1850"
REGION_CAPTION = False
FRONTIER = False
SHOW_CENTER = False
FOOTER = "BEFORE 1900: STATE AVERAGE  ·  FROM 1900: COUNTIES (TODAY'S BOUNDARIES)  ·  DATA: U.S. CENSUS BUREAU"
FINAL_CAPTION = "2020: 29,145,505 PEOPLE IN TEXAS, THE 2ND MOST POPULOUS STATE"
CREDIT_EVENTS = "EVENT SOURCES: NATIONAL ARCHIVES, NOAA, NPS, NASA, FHWA, CENSUS BUREAU"
TITLE = "Texas Population Growth 1850–2020: How Texas Became a Giant"
HOOK = ("In 1850 Texas had 212,592 people. By 2020 it had 29 million. Watch it grow county by county, "
        "with Houston, Dallas, San Antonio and Austin rising out of the map.")
HASHTAGS = ["#Texas", "#TexasHistory", "#Census", "#MapAnimation"]
TAGS = ["texas population growth", "texas population", "texas population over time", "texas history", "houston population growth",
        "dallas population growth", "austin growth"]

facts, captions = _state.make("TX", "Texas")
CAP0 = captions.CAP0 = "HOW 212,592 TEXANS BECAME 29 MILLION: 1850 TO 2020"


def dyn(name, D):
    if name == "passes_ny":
        y = next(y for y in YEARS if D["pop"]["TX"][y] > D["pop"]["NY"][y])
        return f"BY {y} TEXAS HAS MORE PEOPLE THAN NEW YORK: {D['pop']['TX'][y] / 1e6:.1f} VS {D['pop']['NY'][y] / 1e6:.1f} MILLION"
    if name == "seats":
        a, b = _state.seats_change("Texas", 2010, 2020)
        return f"TEXAS GAINS {b - a} HOUSE SEATS: {a} → {b}"
    raise KeyError(name)


SOURCES = dict(_s.SOURCES)
SOURCES.update({
    "juneteenth": dict(title="National Archives Safeguards Original 'Juneteenth' General Order", publisher="National Archives",
                       url="https://www.archives.gov/news/articles/juneteenth-original-document",
                       supports="On June 19, 1865, Gen. Gordon Granger issued General Order No. 3, informing the people of Texas that all enslaved people were free."),
    "galveston": dict(title="Hurricanes in History: Galveston Hurricane 1900", publisher="NOAA National Hurricane Center",
                      url="https://www.nhc.noaa.gov/outreach/history/",
                      supports="Deadliest weather disaster in U.S. history; 8,000 deaths (estimates range from 6,000 to 12,000)."),
    "spindletop": dict(title="History of the Oil & Gas Industry (Big Thicket National Preserve)", publisher="National Park Service",
                       url="https://www.nps.gov/bith/learn/historyculture/oil-gas-industry.htm",
                       supports="The Lucas Gusher at Spindletop, just south of Beaumont, in January 1901 ushered in an eight-year oil boom in Southeast Texas."),
    "nasa_houston": dict(title="60 Years Ago: The Manned Spacecraft Center Makes Houston its Home", publisher="NASA History",
                         url="https://www.nasa.gov/history/60-years-ago-the-manned-spacecraft-center-makes-houston-its-home/",
                         supports="NASA announced Houston as the site of the Manned Spacecraft Center on September 19, 1961."),
})

EVENTS = [
    dict(year=1865, icon="scroll", title="JUNETEENTH", text="GENERAL ORDER NO. 3 TELLS THE PEOPLE OF TEXAS THAT ALL ENSLAVED PEOPLE ARE FREE", src="juneteenth"),
    dict(year=1900, icon="wind", title="GALVESTON HURRICANE", text="THE DEADLIEST U.S. WEATHER DISASTER: ABOUT 8,000 DEATHS", src="galveston"),
    dict(year=1901, icon="pick", title="SPINDLETOP", text="THE LUCAS GUSHER NEAR BEAUMONT STARTS AN OIL BOOM", src="spindletop"),
    dict(year=1957, icon="shield", title="INTERSTATE HIGHWAYS", text="1956 LAW AUTHORIZES 41,000 MILES OF FREEWAYS", src="interstate"),
    dict(year=1961, icon="rocket", title="SPACE CITY", text="NASA PICKS HOUSTON FOR ITS MANNED SPACECRAFT CENTER", src="nasa_houston"),
    dict(year=2000, icon="star", title="PASSING NEW YORK", text="", src="census_states", dyn="passes_ny"),
    dict(year=2020, icon="star", title="MORE HOUSE SEATS", text="", src="census_apport", dyn="seats"),
]
MIGRATIONS, RAILS, TRANSCON = [], [], []
ZOOMS = [
    dict(name="San Antonio", y0=1930, y1=1940, center=(-98.5, 29.45), zoom=2.6, why="SAN ANTONIO GROWS"),
    dict(name="Dallas", y0=1950, y1=1960, center=(-97.0, 32.8), zoom=2.6, why="DALLAS-FORT WORTH GROWS"),
    dict(name="Houston", y0=1970, y1=1980, center=(-95.4, 29.8), zoom=2.6, why="SPACE CITY AND OIL"),
    dict(name="Austin", y0=2000, y1=2010, center=(-97.75, 30.3), zoom=2.8, why="THE STATE CAPITAL BOOMS"),
]
story = SimpleNamespace(SOURCES=SOURCES, EVENTS=EVENTS, MIGRATIONS=MIGRATIONS, RAILS=RAILS, TRANSCON=TRANSCON, ZOOMS=ZOOMS)
COVER = dict(big="1850 → 2020", small="TEXAS GROWS", center=(-99.3, 31.3), fill=3.6, cx=0.42, cy=0.58)
