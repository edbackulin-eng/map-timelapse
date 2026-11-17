#!/usr/bin/env bash
set -uo pipefail
mkdir -p data/census && cd data/census
B=https://www2.census.gov/geo/docs/reference
for y in 2000 2010; do
  curl -fsSL --max-time 120 -o CenPop${y}_Mean_CO.txt $B/cenpop$y/county/CenPop${y}_Mean_CO.txt && echo "OK $y" || echo "FAIL $y"
done
mkdir -p ../hist/pages
for u in https://www.census.gov/dataviz/visualizations/020/ \
         https://www.census.gov/library/stories/2021/08/more-than-half-of-us-population-in-south-and-west.html \
         https://www.census.gov/library/visualizations/2015/dec/great-migration.html \
         https://www.census.gov/history/www/through_the_decades/fast_facts/ ; do
  f=../hist/pages/$(echo "$u" | sed 's#https://##; s#[/.]#_#g').html
  curl -fsSL --max-time 60 -A "Mozilla/5.0 (compatible; map-timelapse-research)" -o "$f" "$u" && echo "OK $u" || echo "FAIL $u"
done
head -2 CenPop2010_Mean_CO.txt CenPop2000_Mean_CO.txt
