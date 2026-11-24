#!/bin/bash
# Final assembly: concat chunks + subtle grain + burned subtitles + mastered audio (-14 LUFS)
set -e
P=$(cd "$(dirname "$0")/.." && pwd); B=$P/build; OUT=$P/..
cd $B
ffmpeg -y -hide_banner -loglevel error -stats -f concat -safe 0 -i chunks/list.txt -i audio/mix.wav \
  -filter_complex "[0:v]noise=alls=3:allf=t+u,ass=subtitles.ass:fontsdir=$P/fonts[v];[1:a]acompressor=threshold=-24dB:ratio=2:attack=20:release=250:makeup=1.5,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 19 -profile:v high -pix_fmt yuv420p -r 24 -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest "$OUT/FINAL_DOCUMENTARY.mp4"
ffmpeg -y -hide_banner -loglevel error -i "$OUT/NARRATION.wav" -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a pcm_s24le "$OUT/NARRATION_master.wav" && mv "$OUT/NARRATION_master.wav" "$OUT/NARRATION.wav"
echo ASSEMBLED
