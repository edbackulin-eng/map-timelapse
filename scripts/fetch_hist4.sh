#!/usr/bin/env bash
# Census "Population of Counties by Decennial Census: 1900 to 1990" (Forstall) - original census.gov files are gone;
# archived copies at the UNT web archive (end-of-term crawls). Needed for the city zoom scenes.
set -uo pipefail
mkdir -p data/cencounts && cd data/cencounts
UA="Mozilla/5.0 (compatible; map-timelapse-research)"
for s in ny nj ct il in wi ca tx az; do
  ok=0
  for u in "https://webarchive.library.unt.edu/eot2008/20081105/http://www.census.gov/population/cencounts/${s}190090.txt" \
           "https://webarchive.library.unt.edu/eot2008/20080922025207/http://www.census.gov/population/cencounts/${s}190090.txt" \
           "https://webarchive.library.unt.edu/web/20080920053308/http://www.census.gov/population/cencounts/${s}190090.txt" \
           "https://webarchive.library.unt.edu/eot2008/2008/http://www.census.gov/population/cencounts/${s}190090.txt"; do
    if curl -fsSL --max-time 60 -A "$UA" -o ${s}.txt "$u" && [ -s ${s}.txt ] && ! grep -qi "<html" ${s}.txt; then echo "OK $s <- $u"; ok=1; break; fi
  done
  [ $ok = 0 ] && { echo "FAIL $s"; rm -f ${s}.txt; }
done
ls -la; head -25 ny.txt 2>/dev/null
