#!/usr/bin/env bash
# Fetch US Census open data (public domain, US Government work) into data/census/
set -euo pipefail
mkdir -p data/census && cd data/census
curl -fsSL -o pop2020_county.json "https://api.census.gov/data/2020/dec/pl?get=NAME,P1_001N&for=county:*"
curl -fsSL -o pop2020_us.json "https://api.census.gov/data/2020/dec/pl?get=P1_001N&for=us:*"
curl -fsSL -o gaz_counties_2020.zip "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_counties_national.zip"
unzip -o -q gaz_counties_2020.zip && rm gaz_counties_2020.zip
curl -fsSL -o cb_2023_us_state_20m.zip "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_20m.zip"
ls -la
