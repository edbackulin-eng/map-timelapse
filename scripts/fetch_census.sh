#!/usr/bin/env bash
# Fetch US Census open data (public domain, US Government work) into data/census/
# api.census.gov now needs a key, so only static www2.census.gov files are used.
set -euo pipefail
mkdir -p data/census && cd data/census
rm -f pop2020_county.json pop2020_us.json
B=https://www2.census.gov
curl -fsSL -o CenPop2020_Mean_CO.txt "$B/geo/docs/reference/cenpop2020/county/CenPop2020_Mean_CO.txt"
curl -fsSL -o CenPop2020_Mean_TR.txt "$B/geo/docs/reference/cenpop2020/tract/CenPop2020_Mean_TR.txt"
curl -fsSL -o apportionment.csv "$B/programs-surveys/decennial/2020/data/apportionment/apportionment.csv" || echo "apportionment missing"
ls -la
