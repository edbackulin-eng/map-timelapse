#!/bin/bash
cd /c/map-timelapse
until [ "$(gh run view 44361630121 --json status -q .status)" = completed ]; do sleep 90; done
echo "$(date -u +%H:%M) 13-to-50 render: $(gh run view 44361630121 --json conclusion -q .conclusion)"
gh workflow run remix-music.yml; sleep 60
R=$(gh run list --workflow remix-music.yml --limit 1 --json databaseId -q '.[0].databaseId')
until [ "$(gh run view $R --json status -q .status)" = completed ]; do sleep 30; done
echo "remix: $(gh run view $R --json conclusion -q .conclusion)"
gh workflow enable upload.yml; sleep 5
gh workflow run upload.yml -f unschedule_ids="EXFuVddIecE ZKFSzJIfdh4"; sleep 60
U=$(gh run list --workflow upload.yml --limit 1 --json databaseId -q '.[0].databaseId')
until [ "$(gh run view $U --json status -q .status)" = completed ]; do sleep 30; done
echo "upload: $(gh run view $U --json conclusion -q .conclusion)"
gh run view $U --log | grep -E "deleted|slot|uploaded|WARN|DOUBT" | cut -c1-200
