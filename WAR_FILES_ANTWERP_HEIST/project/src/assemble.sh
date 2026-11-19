#!/bin/bash
# Final assembly: concat scenes + grain + watermark + burned subtitles + mastered audio
set -e
P=$(cd "$(dirname "$0")/.." && pwd); B=$P/build; OUT=$P/..
cd $B
ffmpeg -y -hide_banner -loglevel error -stats \
  -f concat -safe 0 -i clips/list.txt \
  -loop 1 -framerate 24 -i $P/assets/war_files_logo_transparent.png \
  -i audio/mix_raw.wav \
  -filter_complex "[1:v]scale=112:112:flags=lanczos,format=rgba,colorchannelmixer=aa=0.6[lg];[0:v]noise=alls=4:allf=t+u[n];[n][lg]overlay=W-w-46:38:shortest=1[w];[w]ass=subtitles.ass:fontsdir=$P/fonts[v];[2:a]acompressor=threshold=-24dB:ratio=2.2:attack=20:release=250:makeup=1.5,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]" \
  -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 18 -profile:v high -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 320k -ar 48000 -movflags +faststart -shortest $OUT/FINAL_DOCUMENTARY.mp4
# voiceover deliverable (-16 LUFS, 48 kHz 24-bit)
ffmpeg -y -hide_banner -loglevel error -i audio/voice.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a pcm_s24le $OUT/VOICEOVER.wav
cp subtitles.srt $OUT/SUBTITLES.srt
echo ASSEMBLED
