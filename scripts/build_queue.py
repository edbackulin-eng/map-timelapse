"""Builds data/topic_queue.json and docs/topic_queue.md (proposed topics for America Over Time)."""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent.parent
T = [
    # id, title, search queries, data, licence, engine fit, extra work
    ("sun-belt", "Sun Belt Migration: How Americans Moved South and West", "sun belt migration; rust belt to sunbelt migration",
     "Census apportionment 1910-2020 + city tables + centers of population (all already in repo)", "PD, confirmed (Census DS-027)", "yes", "none"),
    ("13-to-50-states", "US Expansion from 13 to 50 States", "us expansion from 13 to 50 states; us expansion timeline",
     "Natural Earth states + admission dates (Census / NPS / Library of Congress facts) + state pops (repo)", "PD (federal facts); page to confirm at build", "yes", "small: admission layer"),
    ("texas", "Texas Population Growth 1850-2020", "texas population growth",
     "Census state + county pops (1900-1990 in repo; 2000-2020 county totals to fetch)", "PD (Census)", "yes", "small fetch"),
    ("florida", "Florida Population Growth 1830-2020", "florida population growth; florida population boom",
     "same as Texas", "PD (Census)", "yes", "small fetch"),
    ("california", "California Population Growth 1850-2020", "california population; california population decline",
     "same as Texas", "PD (Census)", "yes", "small fetch"),
    ("cities-decline", "American Cities in Decline: Detroit, St. Louis, Cleveland", "american cities in decline",
     "Census twps0027 city tables 1790-1990 (in repo) + 2000-2020 place counts (repo)", "PD, confirmed", "yes", "none"),
    ("mean-center", "The Mean Center of US Population 1790-2020", "mean center of population; change in mean center of population",
     "Census COP2020 Table 1 (in repo) + counties for zooms", "PD, confirmed", "yes", "none"),
    ("density", "US Population Density Over Time (by county)", "us population density over time",
     "Census county pops 1900-2020 + land area (Gazetteer, in repo)", "PD, confirmed", "yes", "small fetch"),
    ("reapportionment", "How Congress Seats Moved: Reapportionment 1910-2020", "reapportionment; apportionment explained (a US-map video query is not confirmed)",
     "Census apportionment.csv (seats 1910-2020, in repo)", "PD, confirmed", "yes", "none; seats 1790-1900: small fetch"),
    ("great-migration", "The Great Migration of Black Americans 1910-1970", "african american migration; american migration history (plain 'great migration' = wildebeest, so the title must say Black Americans)",
     "Census WP56 (race by state 1790-1990) + WP76 (large cities) + 2000-2020 race counts", "PD (Census); tables to parse", "yes", "medium: table parsing"),
    ("immigration", "Immigration to America 1820-2020", "immigration to america; immigration to america 1800s / 1900s",
     "DHS Yearbook Table 2 (LPR by region/country 1820-2020) + Census WP81 foreign-born by state 1850-2000", "PD (federal); WP81 state table to confirm", "partial", "medium: arrows-from-ports layer"),
    ("dust-bowl", "The Dust Bowl: Drought and the Flight from the Plains", "dust bowl",
     "NOAA nClimDiv PDSI 1895-today + Census county pops 1930-40", "PD expected (NOAA); no licence text found in search, confirm on NCEI page", "partial", "medium: climate-division polygons"),
    ("urban", "How America Became Urban 1790-2020", "urbanization (generic; no exact US query confirmed)",
     "Census urban/rural: urpop0090 (1900-1990 by state), national 1790-1990, 2010/2020 tables", "PD (Census)", "yes", "small data"),
    ("hispanic", "Hispanic Population Growth by State 1970-2020", "us hispanic population; us states with most hispanic population",
     "Census WP56 (1970-1990) + 2000-2020 race/ethnicity counts", "PD (Census)", "yes", "small fetch"),
    ("american-indian", "American Indian Population by State 1790-2020", "american indian population",
     "Census WP56 + 2000-2020", "PD (Census)", "yes", "small fetch; careful wording"),
    ("13-colonies", "Population of the 13 Colonies 1650-1780", "13 colonies; 13 colonies every year",
     "Census 'Historical Statistics of the US, Colonial Times to 1970' (1975, US Govt). NOT the Cambridge HSUS edition (copyrighted)", "PD if the Census original is used; to verify", "partial", "small: colonies drawn on modern states, disclosed"),
    ("suffrage", "Women's Suffrage State by State 1869-1920", "women's suffrage; women's suffrage movement",
     "NARA / NPS / Library of Congress dates (facts)", "PD (federal)", "yes", "small: dates timeline, no population counter"),
    ("slavery", "Slavery in the US by State 1790-1860", "us slavery timeline; us slavery history",
     "Census WP56 / 1860 aggregate (slave vs free by state) - to confirm the table", "PD (Census)", "unknown", "check table; sensitive topic"),
    ("national-parks", "National Parks: When Each One Was Created", "us national parks; us national parks ranked",
     "NPS open data (dates, visits) + park boundaries", "PD (NPS); its copyright page to confirm", "partial", "medium: boundaries layer"),
    ("homestead", "The Homestead Act: Giving Away the West", "homestead act; homestead act of 1862 explained",
     "BLM Public Land Statistics / GLO (acres by state) - not located yet", "PD (BLM) expected; not verified", "partial", "needs a data hunt"),
    ("westward", "Westward Expansion: Frontier, Trails, Railroads", "westward expansion; westward expansion map",
     "Frontier (repo) + NPS National Historic Trails lines", "PD (NPS), confirm", "partial", "medium: trails layer"),
    ("interstates", "The Interstate Highway System 1956-1992", "interstate highway system history; interstate highway system",
     "Natural Earth roads (repo) + FHWA national miles by year (state-by-year table not found)", "PD (FHWA; Natural Earth confirmed)", "partial", "opening order stays schematic, disclosed"),
    ("territory", "US Territory Over Time 1783-1959", "us territory over time; us territorial expansion; us expansion map",
     "Census SIS 'territorial-acquisitions.pdf' (map, PD) + own clip polygons on Natural Earth", "PD", "no", "large: new clipping layer"),
    ("louisiana", "The Louisiana Purchase: What Became of It", "louisiana purchase map",
     "as Territory + Census pops of the purchase area", "PD", "no", "large: shares the Territory layer"),
    ("city-race", "Biggest US Cities Over Time: Top 10 Every Decade", "us cities population over time; us cities ranked",
     "Census twps0027 top-100 tables (repo)", "PD, confirmed", "no", "large: new bar-race scene type"),
    ("state-race", "US States by Population Over Time", "us states population over time; top us states by population 1790 to 2050",
     "Census (repo)", "PD, confirmed", "no", "large: bar-race scene type"),
    ("largest-city-state", "Largest City in Every State Over Time", "largest city in each state (weak search signal)",
     "Census top-100 lists cover only big cities; all places only 2000-2020", "PD", "no", "data gap before 2000"),
    ("railroads", "American Railroads 1830-1916", "railroad history united states; transcontinental railroad",
     "Atack (Vanderbilt/NBER) rail shapefiles; UNL Railroads and the Making of Modern America; LoC 1861 dataset", "BLOCKED: no licence stated on the pages, ask the authors", "no", "blocked until licence/permission"),
    ("counties", "US Counties Over Time", "us counties evolution; us counties every year",
     "Newberry Atlas of Historical County Boundaries", "BLOCKED: pages say both 'any lawful purpose' and CC BY-NC-SA; the channel is monetised", "no", "blocked until written permission"),
    ("gold-rush", "California Gold Rush Boomtowns 1848-1860", "gold rush (generic)",
     "CA county pops 1850/1860 (Census Part III OCR is unreliable)", "PD (Census)", "no", "data not reliable yet"),
]
js = [dict(id=a, title=b, search_queries=c, data=d, licence=e, engine_fit=f, extra_work=g, status="proposed") for a, b, c, d, e, f, g in T]
note = "Topic queue for America Over Time. status: proposed -> approved (owner) -> building -> reserve -> published. Queries from YouTube autocomplete, 17.11.2026."
(root / "data" / "topic_queue.json").write_text(json.dumps(dict(note=note, topics=js), indent=1, ensure_ascii=False), encoding="utf-8")
L = [f"# Topic queue (proposed, {len(js)} topics)", "",
     "| # | Video title | Real search queries (YouTube autocomplete) | Data source | Licence | Current engine | Extra work |", "|---|---|---|---|---|---|---|"]
for k, t in enumerate(js, 1):
    L.append(f"| {k} | {t['title']} | {t['search_queries']} | {t['data']} | {t['licence']} | {t['engine_fit']} | {t['extra_work']} |")
(root / "docs" / "topic_queue.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print(len(js), Counter(t["engine_fit"] for t in js))
