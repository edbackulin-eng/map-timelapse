"""Story layer for the America Over Time population video: events, migrations, railroads (simplified), sources.

Every event/migration number carries a source id that is listed in data/sources.json (written by scripts/build_sources.py).
Railroad routes are SIMPLIFIED polylines through well-known cities and are dated by decade (approximate);
they are drawn "by decade", not by exact opening date, and the video says so in the legend.
"""
from __future__ import annotations

# ------------------------------------------------------------------ sources
SOURCES = {
    "louisiana": dict(title="Louisiana Purchase, 1803", publisher="U.S. Department of State, Office of the Historian",
                      url="https://history.state.gov/milestones/1801-1829/louisiana-purchase",
                      supports="Purchase from France in 1803; about 530 million acres for $15 million."),
    "erie": dict(title="Today in History - October 26 (Erie Canal)", publisher="Library of Congress",
                 url="https://www.loc.gov/item/today-in-history/october-26/",
                 supports="Erie Canal opened October 26, 1825 between the Hudson River and Lake Erie."),
    "texas": dict(title="Texas Annexation, 1845", publisher="U.S. Department of State, Office of the Historian",
                  url="https://history.state.gov/milestones/1830-1860/texas-annexation",
                  supports="Texas admitted to the United States on December 29, 1845."),
    "goldrush": dict(title="Compromise of 1850 (teacher resource, Gold Rush background)", publisher="National Park Service",
                     url="https://www.nps.gov/teachers/classrooms/free-slave-compromise-of-1850.htm",
                     supports="News of gold brought approximately 300,000 people to California (rough, commonly cited estimate)."),
    "goldrush_loc": dict(title="The Forty-Niners", publisher="Library of Congress",
                         url="https://www.loc.gov/collections/california-first-person-narratives/articles-and-essays/early-california-history/forty-niners/",
                         supports="About 300,000 people arrived during the Gold Rush period."),
    "homestead": dict(title="Homestead Act (1862)", publisher="National Archives",
                      url="https://www.archives.gov/milestone-documents/homestead-act",
                      supports="Passed May 20, 1862; 160 acres of surveyed public land for a small fee and five years' residence."),
    "golden_spike": dict(title="The Last Spike: History at a Glance", publisher="National Park Service, Golden Spike NHP",
                         url="https://www.nps.gov/gosp/learn/historyculture/the-last-spike-history-at-a-glance.htm",
                         supports="Central Pacific (Sacramento) and Union Pacific (Omaha) joined at Promontory Summit, Utah, May 10, 1869."),
    "frontier": dict(title="Following the Frontier Line, 1790 to 1890", publisher="U.S. Census Bureau",
                     url="https://www.census.gov/dataviz/visualizations/001/",
                     supports="Census Bureau visualization of the frontier line (settled area, 2+ people per square mile); "
                              "the 1890 Census said there could hardly be said to be a frontier line any more."),
    "ellis": dict(title="Ellis Island Chronology", publisher="National Park Service",
                  url="https://www.nps.gov/elis/learn/historyculture/ellis-island-chronology.htm",
                  supports="Opened January 1, 1892; over 12 million future Americans received 1892-1954."),
    "greatmig": dict(title="The Great Migration (1910-1970)", publisher="National Archives",
                     url="https://www.archives.gov/research/african-americans/migrations/great-migration",
                     supports="Roughly 1910s-1970s; approximately six million Black people moved from the South to the North, Midwest and West."),
    "dustbowl": dict(title="Route 66: 1926-1945", publisher="National Park Service",
                     url="https://www.nps.gov/articles/route-66-1926-1945.htm",
                     supports="Cites an estimate that 210,000 people migrated to California to escape the Dust Bowl."),
    "interstate": dict(title="National Interstate and Defense Highways Act (1956)", publisher="National Archives / FHWA",
                       url="https://www.fhwa.dot.gov/interstate-70th/history_eisenhower_interstate_system.cfm",
                       supports="Signed June 29, 1956; authorized 41,000 miles of Interstate highways."),
    "railmaps": dict(title="Railroad Maps, 1828 to 1900", publisher="Library of Congress",
                     url="https://www.loc.gov/collections/railroad-maps-1828-to-1900/",
                     supports="General reference for the growth of the U.S. rail network; routes in the video are simplified."),
    "ne_roads": dict(title="Natural Earth 1:10m Roads (North America)", publisher="Natural Earth (public domain)",
                     url="https://www.naturalearthdata.com/downloads/10m-cultural-vectors/roads/",
                     supports="Present-day Interstate geometry (schematic growth 1956-1992)."),
    "census_states": dict(title="Population of States and Counties of the United States: 1790-1990 (Forstall, 1996)",
                          publisher="U.S. Census Bureau",
                          url="https://www2.census.gov/library/publications/decennial/1990/population-of-states-and-counties-us-1790-1990/population-of-states-and-counties-of-the-united-states-1790-1990.pdf",
                          supports="State populations 1790-1900."),
    "census_apport": dict(title="Apportionment Data (2020 Census)", publisher="U.S. Census Bureau",
                          url="https://www2.census.gov/programs-surveys/decennial/2020/data/apportionment/apportionment.csv",
                          supports="State populations 1910-2020."),
    "census_cities": dict(title="Population of the 100 Largest Cities and Other Urban Places in the United States: 1790 to 1990 (Gibson, 1998)",
                          publisher="U.S. Census Bureau", url="https://www2.census.gov/library/working-papers/1998/demo/pop-twps0027/twps0027.html",
                          supports="City populations 1790-1990; 2000-2020 from Census place counts."),
    "census_counties": dict(title="Population of Counties by Decennial Census: 1900 to 1990 (Forstall)", publisher="U.S. Census Bureau",
                            url="https://www.census.gov/population/www/censusdata/cencounts/files/1900-90.txt",
                            supports="County populations 1900-1990 (original link retired; mirrored at data.nber.org/census/population/cencounts/1900-90.txt)."),
    "census_centers": dict(title="Centers of Population Computation 1950-2020 (Table 1: 1790-2020)", publisher="U.S. Census Bureau",
                           url="https://www2.census.gov/geo/pdfs/reference/cenpop2020/COP2020_documentation.pdf",
                           supports="Mean center of population 1790-2020."),
}

# ------------------------------------------------------------------ events (year = when the counter shows it)
# icon names are drawn by code in mapviz/icons.py
EVENTS = [
    dict(year=1803, icon="scroll", title="LOUISIANA PURCHASE", text="U.S. BUYS LOUISIANA FROM FRANCE: 530 MILLION ACRES FOR $15 MILLION", src="louisiana"),
    dict(year=1825, icon="boat", title="ERIE CANAL OPENS", text="WATER ROUTE FROM THE HUDSON RIVER TO LAKE ERIE", src="erie"),
    dict(year=1845, icon="star", title="TEXAS JOINS THE UNION", text="TEXAS IS ADMITTED TO THE UNITED STATES", src="texas"),
    dict(year=1849, icon="pick", title="GOLD RUSH", text="GOLD FOUND IN CALIFORNIA: ABOUT 300,000 PEOPLE RUSH WEST", src="goldrush"),
    dict(year=1862, icon="house", title="HOMESTEAD ACT", text="160 ACRES OF FREE LAND FOR SETTLERS IN THE WEST", src="homestead"),
    dict(year=1869, icon="train", title="RAILS MEET", text="FIRST TRANSCONTINENTAL RAILROAD COMPLETED IN UTAH", src="golden_spike"),
    dict(year=1890, icon="fence", title="FRONTIER CLOSED", text="CENSUS DECLARES THE FRONTIER CLOSED", src="frontier"),
    dict(year=1892, icon="ship", title="ELLIS ISLAND", text="NEW YORK'S IMMIGRATION STATION OPENS: OVER 12 MILLION ARRIVE BY 1954", src="ellis"),
    dict(year=1916, icon="arrows", title="GREAT MIGRATION", text="ABOUT 6 MILLION BLACK AMERICANS LEAVE THE SOUTH, 1910-1970", src="greatmig"),
    dict(year=1935, icon="wind", title="DUST BOWL", text="DROUGHT AND DUST PUSH FAMILIES WEST: AN ESTIMATED 210,000 REACH CALIFORNIA", src="dustbowl"),
    dict(year=1957, icon="shield", title="INTERSTATE HIGHWAYS", text="1956 LAW AUTHORIZES 41,000 MILES OF FREEWAYS", src="interstate"),
    dict(year=1975, icon="sun", title="SUN BELT BOOM", text="TEXAS, FLORIDA AND ARIZONA GROW FASTEST", src="census_apport"),
]

# ------------------------------------------------------------------ migration arrows: (name, y0, y1, [(lon,lat) control pts], label, src)
MIGRATIONS = [
    dict(name="gold", y0=1848, y1=1855, color=(255, 70, 0), label="GOLD RUSH", src="goldrush",
         pts=[(-92.0, 38.0), (-106.0, 41.5), (-121.0, 38.6)]),
    dict(name="gm_chi", y0=1916, y1=1970, color=(0, 90, 255), label="GREAT MIGRATION", src="greatmig",
         pts=[(-90.3, 32.8), (-88.8, 37.0), (-87.7, 41.6)]),
    dict(name="gm_ny", y0=1916, y1=1970, color=(0, 90, 255), label="", src="greatmig",
         pts=[(-81.5, 33.0), (-77.5, 37.5), (-74.2, 40.5)]),
    dict(name="gm_la", y0=1940, y1=1970, color=(0, 90, 255), label="", src="greatmig",
         pts=[(-93.0, 31.2), (-105.0, 31.5), (-118.2, 34.0)]),
    dict(name="dust", y0=1932, y1=1940, color=(160, 0, 255), label="DUST BOWL", src="dustbowl",
         pts=[(-98.5, 36.4), (-108.5, 35.2), (-119.4, 36.4)]),
    dict(name="sun_fl", y0=1970, y1=2020, color=(255, 0, 140), label="SUN BELT", src="census_apport",
         pts=[(-78.0, 41.0), (-79.5, 35.0), (-81.6, 28.3)]),
    dict(name="sun_tx", y0=1970, y1=2020, color=(255, 0, 140), label="", src="census_apport",
         pts=[(-88.0, 42.0), (-93.0, 36.0), (-97.2, 31.3)]),
    dict(name="sun_az", y0=1970, y1=2020, color=(255, 0, 140), label="", src="census_apport",
         pts=[(-85.0, 40.8), (-100.0, 37.5), (-111.8, 33.5)]),
]

# ------------------------------------------------------------------ railroads: (name, y0, y1, [(lon,lat)...]); simplified, decade-level dates
RAILS = [
    ("B&O", 1830, 1853, [(-76.61, 39.29), (-78.76, 39.65), (-80.72, 40.07)]),
    ("Boston-Albany", 1835, 1842, [(-71.06, 42.36), (-71.80, 42.26), (-72.59, 42.10), (-73.76, 42.65)]),
    ("NY Central", 1831, 1853, [(-74.00, 40.71), (-73.76, 42.65), (-76.15, 43.05), (-77.61, 43.16), (-78.88, 42.89)]),
    ("Pennsylvania", 1834, 1854, [(-75.17, 39.95), (-76.88, 40.27), (-78.40, 40.52), (-80.00, 40.44)]),
    ("Charleston-Atlanta", 1833, 1845, [(-79.93, 32.78), (-81.97, 33.47), (-84.39, 33.75)]),
    ("Pittsburgh-Chicago", 1852, 1858, [(-80.00, 40.44), (-85.14, 41.08), (-87.63, 41.88)]),
    ("Cleveland-Chicago", 1851, 1856, [(-81.69, 41.50), (-83.54, 41.65), (-87.63, 41.88)]),
    ("Illinois Central", 1851, 1856, [(-87.63, 41.88), (-88.24, 40.12), (-89.18, 37.00)]),
    ("Chicago-Omaha", 1854, 1869, [(-87.63, 41.88), (-90.58, 41.51), (-93.60, 41.59), (-95.86, 41.26)]),
    ("Chicago-St. Louis", 1852, 1857, [(-87.63, 41.88), (-89.65, 39.80), (-90.20, 38.63)]),
    ("St. Louis-Kansas City", 1855, 1865, [(-90.20, 38.63), (-94.58, 39.10)]),
    ("Atlantic Coast", 1850, 1865, [(-77.04, 38.90), (-77.43, 37.54), (-79.93, 32.78), (-81.10, 32.08), (-81.66, 30.33)]),
    ("Atlanta-New Orleans", 1850, 1870, [(-84.39, 33.75), (-86.30, 32.37), (-88.04, 30.69), (-90.07, 29.95)]),
    ("Kansas Pacific", 1867, 1870, [(-94.58, 39.10), (-98.0, 39.0), (-104.99, 39.74)]),
    ("Texas lines", 1860, 1881, [(-94.80, 29.30), (-95.37, 29.76), (-96.80, 32.78), (-101.0, 32.0), (-106.49, 31.76)]),
    ("Santa Fe", 1868, 1885, [(-94.58, 39.10), (-95.68, 39.05), (-100.02, 37.75), (-106.65, 35.08), (-114.61, 34.85), (-118.24, 34.05)]),
    ("Sunset Route", 1877, 1883, [(-118.24, 34.05), (-114.62, 32.73), (-110.97, 32.22), (-106.49, 31.76), (-98.49, 29.42), (-95.37, 29.76), (-90.07, 29.95)]),
    ("Northern Pacific", 1870, 1883, [(-93.09, 44.95), (-96.79, 46.88), (-100.78, 46.81), (-108.50, 45.78), (-112.04, 46.59), (-117.43, 47.66), (-122.44, 47.25)]),
    ("Great Northern", 1883, 1893, [(-93.09, 44.95), (-101.30, 48.23), (-109.68, 48.55), (-117.43, 47.66), (-122.33, 47.61)]),
    ("Oregon-California", 1870, 1887, [(-122.68, 45.52), (-122.0, 42.0), (-121.49, 38.58)]),
]
# exact transcontinental (NPS): Central Pacific from Sacramento, Union Pacific from Omaha, meeting at Promontory Summit
TRANSCON = [
    ("Central Pacific", 1863, 1869, [(-121.49, 38.58), (-120.2, 39.3), (-119.81, 39.53), (-115.76, 40.83), (-112.55, 41.62)]),
    ("Union Pacific", 1865, 1869, [(-95.94, 41.26), (-100.77, 41.14), (-104.82, 41.14), (-105.59, 41.31), (-109.66, 41.53), (-111.97, 41.22), (-112.55, 41.62)]),
]

# ------------------------------------------------------------------ zoom scenes (decade run phase of block y0->y1)
ZOOMS = [
    dict(name="New York", y0=1900, y1=1910, center=(-73.95, 40.85), zoom=9.0, why="ELLIS ISLAND ERA"),
    dict(name="Chicago", y0=1910, y1=1920, center=(-87.9, 41.85), zoom=7.5, why="GREAT MIGRATION BEGINS"),
    dict(name="Los Angeles", y0=1920, y1=1930, center=(-118.0, 34.0), zoom=5.8, why="SOUTHERN CALIFORNIA BOOM"),
    dict(name="Houston", y0=1970, y1=1980, center=(-95.5, 29.8), zoom=8.0, why="SUN BELT BOOM"),
    dict(name="Phoenix", y0=1980, y1=1990, center=(-112.0, 33.5), zoom=5.5, why="DESERT CITY BOOM"),
]
