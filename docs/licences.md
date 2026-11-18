# Licence record for the trial video "America Over Time: U.S. Population 1790-2020"

Checked 17.11.2026 on the source sites (evidence files are in the repo).

| Source | What is used | Licence / policy (quoted from the source) | Evidence |
|---|---|---|---|
| U.S. Census Bureau | state populations 1790-2020, county populations 2020, boundaries (cb_2020 counties, cb_2023 states), land area, centres of population | Data Stewardship Policy DS-027, p. 8: "Data/works created by Census Bureau employees generally are not subject to copyright protection within the United States. Census Bureau data or other works may be subject to copyright protection in foreign countries." census.gov/about/policies/citation.html asks users to cite the Census Bureau as the source. | `data/hist/pdf/ds027.pdf` (text: `data/hist/txt/ds027.txt`), `data/census/licences/` |
| Natural Earth | country borders and lakes (1:50m) | naturalearthdata.com/about/terms-of-use: "All versions of Natural Earth raster + vector map data found on this website are in the public domain." Credit is optional. | page read 17.11.2026 |
| Music (3 tracks, calm) | Yoiyami - "First Light Particles"; cynicmusic - "November Snow" (TAD "A cup of tea" REMOVED 18.11: Content ID claim "Slow strong", 7:51-10:06) | CC0 1.0 (each OpenGameArt page shows CC0 only; re-checked by `scripts/fetch_music.py` 17.11.2026) | `data/music/licence_check.json`, `data/music/registry_source.json` |
| Font Anton | all text | SIL Open Font License 1.1 | `assets/fonts/OFL-Anton.txt` |

Notes
- The Census wording says "generally"; foreign copyright is possible in theory. The figures are plain statistics and the
  Bureau is credited as the source in the video and the description, which is what its citation page asks.
- Description line for every video: "Data: U.S. Census Bureau. Map data: Natural Earth (public domain). Music: Yoiyami, cynicmusic (CC0), OpenGameArt.org."
- No AI images, no AI voice. containsSyntheticMedia=false, madeForKids=false.
- 1790-1900 state values come from the 1996 Census Bureau report "Population of States and Counties of the United States:
  1790-1990" (text OCR, validated: the sum of the states equals the printed U.S. total in every census year; two OCR faults fixed,
  see `docs/verify_report.md`). 1910-2020 come from the digital `apportionment.csv`.

Added for video v2
- County populations 1900-1990: Census Bureau product (Forstall), retrieved from the NBER mirror because census.gov retired the file; cite as U.S. Census Bureau.
- City populations: Census Bureau working paper 27 (Gibson 1998) tables, public-domain US Government work.
- Natural Earth roads (Interstates): public domain (naturalearthdata.com/about/terms-of-use).
- Event facts: sources in `data/sources.json` (NPS, Library of Congress, National Archives, State Dept. Historian, FHWA, Census Bureau): all US Government works.
- Icons: drawn in code (`mapviz/icons.py`), no images.

## Music rule (all channels, owner 18.11.2026)
A new music track goes into a video only after a TEST upload: a short private video with that track alone, checked in YouTube Studio (Content) for a Content ID claim. Claim or doubt -> status `removed` in the registry. CC0 on the source page does not protect against Content ID.
Removed: TAD "A cup of tea" (claim "Slow strong", Jack the Simple / The Orchard Music, 18.11.2026).
