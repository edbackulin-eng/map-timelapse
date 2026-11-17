# Channel brief — choose one of each (owner sets them in YouTube Studio)

## 1. Channel name + handle (handles checked 17.11.2026: youtube.com/@handle returns 404 = no channel)

| # | Name | Handle | Idea |
|---|------|--------|------|
| 1 | **America Over Time** | @AmericaOverTime | plain search phrase, says exactly what the channel is |
| 2 | **Lit Up Atlas** | @LitUpAtlas | brand from the glowing look of every map |
| 3 | **Heatmap History** | @HeatmapHistory | heat-map style + history, easy to remember |

A free handle can still be taken by someone else before you claim it — claim it in Studio right after choosing.

## 2. Artwork v2 — bright choropleth style (`branding/v2/`, rendered on GitHub by `branding.yml`)

Owner 17.11: name **America Over Time (@AmericaOverTime)**; glowing-dots style rejected.

- Style: regions fully filled by data, red (low) → orange → yellow → green (high); lightness varies
  (dark red L*≈29, yellow L*≈87, teal-green L*≈50, green end leans blue) — see `check_colorblind.png`
  (deuteranopia / protanopia simulation) and `legend_scale.png`. Light-blue ocean, neutral light
  neighbours (Natural Earth), dark state borders, Anton text with thick dark outline, yellow arrows.
- Thumbnails: **A** county density 2020 + "AMERICA FILLS UP" + arrow east→west; **B** state density 2020,
  "331 MILLION", arrow + "NEW JERSEY 1,263 / SQ MI"; **C** close-up of the East (counties), big
  "1790 → 2020", "EAST TO WEST". Check: `check_thumbs_210x118.png`.
- Banner: county map + name panel inside the 1546×423 safe area (`check_banner.png`).
- Avatar: state density map + "AOT" (`check_avatar.png`: 400 / 98 / 48 px circles).
- Every number is read from Census files at render time: US 331,449,281 and New Jersey density
  1,263.0 / sq mi (apportionment.csv, 2020); county density = 2020 Census county population
  (CenPop2020_Mean_CO) / land area in sq mi (2020 Gazetteer).

## 3. Channel description (paste into Studio → Customization → Basic info)

Watch America change on the map. Every video is an animated timelapse of one thing growing across the United States — population from 1790 to 2020, railroads, the Interstate highways, the largest cities, how the states joined the Union, immigration decade by decade.

No narration — just smooth animated maps, a year counter, a clear legend and short captions. Every number and name on screen comes from official open data: the US Census Bureau, the DHS Yearbook of Immigration Statistics, USGS, the Library of Congress and Natural Earth. Sources are listed under each video.

New maps every Monday and Friday.

## 4. Channel keywords (Studio → Settings → Channel → Keywords)

animated map, map timelapse, US history map, United States map, US population history, population density map, census data, American history, US map animation, how America grew, railroad history, interstate highway history, largest US cities, US states history, immigration history, data visualization, historical maps, heat map, geography, maps

## 5. Data licences (checked 17.11.2026 on the source sites)

- **Natural Earth** — naturalearthdata.com/about/terms-of-use: "All versions of Natural Earth raster +
  vector map data found on this website are in the public domain"; credit optional ("Made with Natural Earth").
- **US Census Bureau** — Data Stewardship policy DS-027 (www2.census.gov/foia/ds_policies/ds027.pdf):
  data/works created by Census Bureau employees are generally not subject to copyright in the US;
  census.gov/about/policies/citation.html asks to cite the Census Bureau as the source (copies of
  the citation/open-data/terms pages are in `data/census/licences/`). Census API is not used (needs
  a key, and its attribution notice applies only to API users).
- Attribution line for every description: "Data: U.S. Census Bureau. Map data: Made with Natural Earth."
- Music: CC0 only.
