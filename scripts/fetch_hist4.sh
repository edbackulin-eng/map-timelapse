#!/usr/bin/env bash
set -uo pipefail
mkdir -p data/cencounts && cd data/cencounts
UA="Mozilla/5.0 (compatible; map-timelapse-research)"
try() { # st
  s=$1
  for u in "https://www.census.gov/population/cencounts/${s}190090.txt" \
           "https://www.census.gov/population/www/censusdata/cencounts/files/${s}190090.txt" \
           "https://www2.census.gov/programs-surveys/decennial/tables/time-series/coc1990/${s}190090.txt" \
           "https://www2.census.gov/library/publications/decennial/1990/population-of-states-and-counties-us-1790-1990/${s}190090.txt"; do
    if curl -fsSL --max-time 40 -A "$UA" -o ${s}.txt "$u" && [ -s ${s}.txt ] && ! grep -qi "<html" ${s}.txt; then echo "OK $s <- $u"; return; fi
  done; echo "FAIL $s"; rm -f ${s}.txt
}
for s in al ak az ar ca co ct de dc fl ga hi id il in ia ks ky la me md ma mi mn ms mo mt ne nv nh nj nm ny nc nd oh ok or pa ri sc sd tn tx ut vt va wa wv wi wy; do try $s; done
ls | wc -l; head -30 al.txt 2>/dev/null
