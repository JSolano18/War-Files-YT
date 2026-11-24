# WAR FILES — The Dead Man Who Fooled Hitler (editable project)

Pipeline (run from `src/`):

| Step | Command | Output |
|---|---|---|
| Script, shots, pronunciation | edit `script_data.py` | |
| Narration (Kokoro TTS) + Whisper check | `python3 tts.py` | `build/tts/pNNN.wav(.json)`, `build/tts_report.json` |
| Edit decision list (word-synced cuts, subtitles) | `python3 timeline_m.py` | `build/timeline.json` |
| Subtitles | `python3 subs_m.py` | `../SUBTITLES.srt`, `build/subtitles.ass` |
| Score + sound design + mix | `python3 audio_m.py` | `build/audio/mix.wav`, `../NARRATION.wav` |
| Video (parallel, cross-dissolves) | `NW=4 NCH=16 python3 render_m.py` | `build/chunks/` |
| Final master | `./assemble_m.sh` | `../FINAL_DOCUMENTARY.mp4` |
| Thumbnails | `python3 thumbs_m.py` | `../thumbnails/` |
| Credits | `python3 credits_m.py` | `../IMAGE_AND_MUSIC_CREDITS.txt` |
| More archival photos | `python3 slow_fetch.py` (respects Wikimedia rate limits) | `assets/archival/` + `credits.json` |

After new archival photos arrive: `timeline_m.py` → `audio_m.py` → delete `build/chunks/*.ok` → `render_m.py` → `assemble_m.sh`.
Scene code: `scenes_m.py` (scenes), `world.py` (sea, London, valleys, interiors), `common.py`/`props.py` (shared with the Antwerp project).
Models: `/home/user/models/kokoro-v1.0.onnx`, `voices-v1.0.bin`, `whisper-small-ct2/`.
