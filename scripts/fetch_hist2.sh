#!/usr/bin/env bash
# Second batch of Census open data: full county tables (Forstall), 100 largest urban places 1790-1990,
# gazetteer places 2020, 2000-2020 place counts, Natural Earth roads/railroads.
set -uo pipefail
mkdir -p data/hist/txt data/hist/pdf data/cities data/ne2 && cd data
UA="Mozilla/5.0 (compatible; map-timelapse-research)"
dl() { curl -fsSL --max-time 240 --connect-timeout 20 -A "$UA" -o "$1" "$2" && echo "OK $1 <- $2" || echo "FAIL $1 <- $2"; }
# Forstall full text (counties, Part III)
dl hist/pdf/forstall_full.pdf https://www2.census.gov/library/publications/decennial/1990/population-of-states-and-counties-us-1790-1990/population-of-states-and-counties-of-the-united-states-1790-1990.pdf
pdftotext -layout hist/pdf/forstall_full.pdf hist/txt/forstall_full.txt && wc -l hist/txt/forstall_full.txt
rm -f hist/pdf/forstall_full.pdf
# 100 largest urban places 1790-1990 (Gibson 1998, working paper 27)
B=https://www2.census.gov/library/working-papers/1998/demographics/pop-twps0027
for t in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29; do dl cities/tab$t.txt $B/tab$t.txt; done
dl cities/twps0027.html https://www2.census.gov/library/working-papers/1998/demo/pop-twps0027/twps0027.html
# gazetteer places 2020 (coordinates) + place counts
dl cities/gaz_place_2020.zip https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2020_Gazetteer/2020_Gaz_place_national.zip
(cd cities && unzip -o -q gaz_place_2020.zip && rm gaz_place_2020.zip)
P=https://www2.census.gov/programs-surveys/popest/datasets
dl cities/subest2022.csv $P/2020-2022/cities/totals/sub-est2022.csv
dl cities/subest2009.csv $P/2000-2009/cities/totals/sub-est2009-all.csv
dl cities/subest2019.csv $P/2010-2019/cities/totals/sub-est2019_all.csv
# Natural Earth roads / railroads (North America)
N=https://naciscdn.org/naturalearth/10m/cultural
dl ne2/roads.zip $N/ne_10m_roads_north_america.zip
dl ne2/rail.zip $N/ne_10m_railroads_north_america.zip
(cd ne2 && for z in roads rail; do unzip -o -q $z.zip -d $z && rm $z.zip; done; ls -R | head -30)
# Census pages used as event sources (census.gov blocks some clients; saved for reading)
mkdir -p hist/pages
for u in https://www.census.gov/dataviz/visualizations/020/ \
         https://www.census.gov/history/www/through_the_decades/overview/1890.html \
         https://www.census.gov/programs-surveys/decennial-census/decade/decennial-facts/1890.html \
         https://www.census.gov/history/www/reference/apportionment/ \
         https://www.census.gov/library/stories/2021/08/more-than-half-of-us-population-in-south-and-west.html \
         https://www.census.gov/geographies/reference-files/time-series/geo/centers-population.html ; do
  f=hist/pages/$(echo "$u" | sed 's#https://##; s#[/.]#_#g').html; dl "$f" "$u"
done
ls -la hist/txt cities | head -60
