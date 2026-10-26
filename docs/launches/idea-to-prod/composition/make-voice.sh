#!/bin/sh
# Regenerates assets/vo/s1.wav .. s6.wav from voiceover.txt with the free
# macOS voice, one file per line. The composition's <audio> durations are
# these files' lengths; re-measure them with ffprobe after editing a line.
set -eu
cd "$(dirname "$0")"
mkdir -p assets/vo
i=0
while IFS= read -r line; do
  i=$((i + 1))
  say -v Samantha -r 180 -o "assets/vo/s$i.aiff" "$line"
  ffmpeg -loglevel error -y -i "assets/vo/s$i.aiff" -ar 44100 -ac 1 "assets/vo/s$i.wav"
  rm "assets/vo/s$i.aiff"
done < voiceover.txt
