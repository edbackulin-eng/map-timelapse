#!/bin/bash
# Re-render queue after the change-marker fix: US Population (already dispatched as $1) -> upload of it -> the rest in order.
cd /c/map-timelapse
POP=$1
until [ "$(gh run view $POP --json status --jq .status)" = "completed" ]; do sleep 60; done
echo "$(date -u +%H:%M) us-population render: $(gh run view $POP --json conclusion --jq .conclusion)"
# next render first, then the upload (the upload takes only us-population: sun-belt is on HOLD)
gh workflow run video.yml -f topic=sun-belt -f force=true
sleep 45
gh workflow enable upload.yml
gh workflow run upload.yml
echo "$(date -u +%H:%M) upload dispatched"
for t in sun-belt texas california cities-decline 13-to-50-states; do
  if [ "$t" != "sun-belt" ]; then
    while gh run list --workflow video.yml --limit 10 --json status --jq '.[].status' | grep -qE "pending|queued|waiting"; do sleep 120; done
    gh workflow run video.yml -f topic=$t -f force=true
    echo "$(date -u +%H:%M) dispatched $t"
    sleep 60
  fi
  if [ "$t" = "sun-belt" ]; then
    sleep 30
    while gh run list --workflow video.yml --limit 10 --json status,displayTitle --jq '.[].status' | grep -qE "pending|queued|waiting"; do sleep 120; done
    # wait for the sun-belt run to finish, then put its release back into the reserve
    SB=$(gh run list --workflow video.yml --limit 1 --json databaseId --jq '.[0].databaseId')
    until [ "$(gh run view $SB --json status --jq .status)" = "completed" ]; do sleep 120; done
    echo "$(date -u +%H:%M) sun-belt render: $(gh run view $SB --json conclusion --jq .conclusion)"
    gh release edit reserve-sun-belt --title "RESERVE: sun-belt"
  fi
done
while gh run list --workflow video.yml --limit 10 --json status --jq '.[].status' | grep -qE "pending|queued|waiting|in_progress"; do sleep 300; done
gh run list --workflow video.yml --limit 7
gh release list --limit 10
