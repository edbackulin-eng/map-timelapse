#!/usr/bin/env bash
# Historical Census documents (state populations 1790-1990, centers of population, DS-027 policy).
set -uo pipefail
mkdir -p data/hist/pdf data/hist/txt && cd data/hist
get() { # name url...
  n=$1; shift
  for u in "$@"; do
    if curl -fsSL --max-time 150 --connect-timeout 20 -A "Mozilla/5.0 (compatible; map-timelapse-research)" -o "pdf/$n.pdf" "$u" && file "pdf/$n.pdf" | grep -q PDF; then
      echo "OK $n <- $u"; pdftotext -layout -l ${PAGES:-400} "pdf/$n.pdf" "txt/$n.txt"; return; fi
  done; echo "FAIL $n"; rm -f "pdf/$n.pdf"
}
get ds027 https://www2.census.gov/foia/ds_policies/ds027.pdf
get cop2020_doc https://www2.census.gov/geo/pdfs/reference/cenpop2020/COP2020_documentation.pdf
PAGES=80 get forstall https://www2.census.gov/library/publications/decennial/1990/population-of-states-and-counties-us-1790-1990/population-of-states-and-counties-of-the-united-states-1790-1990.pdf
PAGES=40 get aggregate1890 https://www2.census.gov/library/publications/decennial/1890/bulletins/demographics/aggregate-population-by-states-and-territories-1790-1890.pdf
PAGES=40 get table4_1990 https://www2.census.gov/programs-surveys/decennial/1990/tables/cph-2/table-4.pdf
get cenpop_map https://www.census.gov/content/dam/Census/newsroom/press-kits/2021/center-of-population/map-center-of-population-1790-2020.pdf
ls -la pdf txt
