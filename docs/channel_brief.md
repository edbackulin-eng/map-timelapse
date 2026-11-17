# Channel brief — choose one of each (owner sets them in YouTube Studio)

## 1. Channel name + handle (handles checked 17.11.2026: youtube.com/@handle returns 404 = no channel)

| # | Name | Handle | Idea |
|---|------|--------|------|
| 1 | **America Over Time** | @AmericaOverTime | plain search phrase, says exactly what the channel is |
| 2 | **Lit Up Atlas** | @LitUpAtlas | brand from the glowing look of every map |
| 3 | **Heatmap History** | @HeatmapHistory | heat-map style + history, easy to remember |

A free handle can still be taken by someone else before you claim it — claim it in Studio right after choosing.

## 2. Artwork drafts (`branding/drafts/`)

- Thumbnails (1280×720): **A** "AMERICA LIGHTS UP" + curved arrow NY→LA, fire palette; **B** "1790 → 2020 / WHERE AMERICA LIVES", ice palette, ring on the Boston–Washington corridor; **C** "1790 → 2020 / EAST TO WEST", magma palette, straight green arrow. Phone check: `check_thumbs_210x118.png`.
- Banners (2560×1440, name inside the 1546×423 safe area): **A** centred name over the map; **B** name left, map right; **C** full-width map, name across it. Safe-area check: `check_banners_safe_area.png`. Each banner shows a different name candidate only for preview — the chosen style is re-rendered with the chosen name.
- Avatars (800×800, check at 98 px: `check_avatars_98.png`): **A** glowing map; **B** monogram over the map (letters follow the chosen name); **C** map + yellow arrow east→west.

All map pixels are real data: 2020 Census tract populations (Census Bureau "Centers of Population 2020", 85k tracts) on Census cartographic state boundaries 2023. No AI imagery. Font: Anton (SIL Open Font License, file in `assets/fonts/`).

## 3. Channel description (paste into Studio → Customization → Basic info)

Watch America change on the map. Every video is an animated timelapse of one thing growing across the United States — population from 1790 to 2020, railroads, the Interstate highways, the largest cities, how the states joined the Union, immigration decade by decade.

No narration — just smooth animated maps, a year counter, a clear legend and short captions. Every number and name on screen comes from official open data: the US Census Bureau, the DHS Yearbook of Immigration Statistics, USGS, the Library of Congress and Natural Earth. Sources are listed under each video.

New maps every Monday and Friday.

## 4. Channel keywords (Studio → Settings → Channel → Keywords)

animated map, map timelapse, US history map, United States map, US population history, population density map, census data, American history, US map animation, how America grew, railroad history, interstate highway history, largest US cities, US states history, immigration history, data visualization, historical maps, heat map, geography, maps

## 5. Data licences (to be confirmed on each source site before the trial video is rendered)

- US Census Bureau — US Government work, public domain (17 U.S.C. §105). Note: census.gov blocks this PC (Cloudflare 403), so data is fetched on the GitHub runner (`fetch-census.yml`); api.census.gov now requires a free API key — not needed so far (static www2.census.gov files are used).
- Natural Earth — public domain.
- Music: CC0 only.
