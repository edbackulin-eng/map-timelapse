#!/usr/bin/env bash
# Census "Population of Counties by Decennial Census: 1900 to 1990" (Forstall), one file for all states.
set -uo pipefail
mkdir -p data/cencounts && cd data/cencounts
UA="Mozilla/5.0 (compatible; map-timelapse-research)"
for u in https://www.census.gov/population/www/censusdata/cencounts/files/1900-90.txt \
         https://www2.census.gov/programs-surveys/decennial/tables/time-series/coc1990/1900-90.txt \
         https://data.nber.org/census/population/cencounts/1900-90.txt; do
  if curl -fsSL --max-time 90 -A "$UA" -o 1900-90.txt "$u" && [ -s 1900-90.txt ] && ! head -c 400 1900-90.txt | grep -qi "<html"; then echo "OK <- $u"; break; else echo "FAIL $u"; rm -f 1900-90.txt; fi
done
curl -fsSL --max-time 60 -o 00-90doc.txt https://data.nber.org/census/population/cencounts/00-90doc.txt && echo "OK doc"
ls -la; head -30 1900-90.txt
