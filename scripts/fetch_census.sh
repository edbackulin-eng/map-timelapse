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
curl -fsSL -o cb_2023_us_county_20m.zip "$B/geo/tiger/GENZ2023/shp/cb_2023_us_county_20m.zip"
mkdir -p counties && (cd counties && unzip -o -q ../cb_2023_us_county_20m.zip) && rm cb_2023_us_county_20m.zip
# licence / terms pages, saved as evidence of the check
mkdir -p ../licences
for u in https://www.census.gov/about/policies/citation.html \
         https://www.census.gov/data/developers/about/terms-of-service.html \
         https://www.census.gov/about/policies/open-gov/open-data.html; do
  f=../licences/census_$(basename "$u" .html).html
  curl -fsSL -o "$f" "$u" || echo "fail $u"
done
ls -la ../licences
