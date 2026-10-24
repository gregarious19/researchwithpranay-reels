#!/usr/bin/env bash
# finish.sh IN.mp4 OUT.mp4 — one clean encode in Instagram's recommended format:
# H.264 High@4.1, yuv420p, BT.709, 30 fps, 2 s closed GOPs, faststart; AAC-LC 48 kHz stereo 128 kbps,
# loudness normalized to -16 LUFS; audio trimmed to the video. (Manim's stitched segments get rejected.)
set -euo pipefail
vdur=$(ffprobe -v error -select_streams v -show_entries stream=duration -of csv=p=0 "$1")
ffmpeg -nostdin -v error -y -i "$1" -t "$vdur" \
  -c:v libx264 -preset medium -crf 16 -tune animation -profile:v high -level:v 4.1 -pix_fmt yuv420p \
  -r 30 -g 60 -keyint_min 60 -sc_threshold 0 -bf 2 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a aac -profile:a aac_low -ar 48000 -ac 2 -b:a 128k \
  -movflags +faststart "$2"
