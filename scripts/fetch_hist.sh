#!/usr/bin/env bash
# Historical Census documents (state populations 1790-1990, centers of population, DS-027 policy).
set -uo pipefail
mkdir -p data/hist/pdf data/hist/txt && cd data/hist
get() { # name url...
  n=$1; shift
  for u in "$@"; do
    if curl -fsSL -A "Mozilla/5.0 (compatible; map-timelapse-research)" -o "pdf/$n.pdf" "$u" && file "pdf/$n.pdf" | grep -q PDF; then
      echo "OK $n <- $u"; pdftotext -layout "pdf/$n.pdf" "txt/$n.txt"; return; fi
  done; echo "FAIL $n"; rm -f "pdf/$n.pdf"
}
get ds027 https://www2.census.gov/foia/ds_policies/ds027.pdf
get cop2020_doc https://www2.census.gov/geo/pdfs/reference/cenpop2020/COP2020_documentation.pdf
get table16 https://www.census.gov/population/www/censusdata/files/table-16.pdf \
  https://www2.census.gov/programs-surveys/decennial/tables/time-series/historical-populations/table-16.pdf \
  "https://webarchive.library.unt.edu/web/20090829221343/http:/www.census.gov/population/www/censusdata/files/table-16.pdf"
get table2 https://www.census.gov/population/www/censusdata/files/table-2.pdf \
  "https://webarchive.library.unt.edu/web/20090829221343/http:/www.census.gov/population/www/censusdata/files/table-2.pdf"
get cenpop_map https://www.census.gov/content/dam/Census/newsroom/press-kits/2021/center-of-population/map-center-of-population-1790-2020.pdf
ls -la pdf txt
