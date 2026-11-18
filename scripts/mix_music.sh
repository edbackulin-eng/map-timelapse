#!/bin/bash
# usage: mix_music.sh <video_only.mp4 (any audio ignored)> <out.mp4>
# Only the two tracks that passed Content ID (first-light-particles, november-snow), looped in turn.
# "A cup of tea" (TAD) got a Content ID claim (Slow strong / Jack the Simple) on 2026-11-18: never use it.
set -e
M=assets/music; V=$1; O=$2
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
ffmpeg -y -loglevel error -i "$V" -i $M/oga-first-light-particles.mp3 -i $M/oga-november-snow.mp3 -i $M/oga-first-light-particles.mp3 -i $M/oga-november-snow.mp3 \
  -filter_complex "[1:a][2:a]acrossfade=d=5[a12];[a12][3:a]acrossfade=d=5[a123];[a123][4:a]acrossfade=d=5[a1234];[a1234]atrim=0:$D,afade=t=in:d=3,loudnorm=I=-20:TP=-2:LRA=7,afade=t=out:st=$(python3 -c "print($D-6)"):d=6[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$O"
