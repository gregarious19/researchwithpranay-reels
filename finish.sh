#!/usr/bin/env bash
# finish.sh IN.mp4 OUT.mp4 — normalize loudness for Instagram (-16 LUFS), trim audio to the video, keep video untouched.
set -euo pipefail
vdur=$(ffprobe -v error -select_streams v -show_entries stream=duration -of csv=p=0 "$1")
ffmpeg -v error -y -i "$1" -t "$vdur" -c:v copy \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 192k -movflags +faststart "$2"
