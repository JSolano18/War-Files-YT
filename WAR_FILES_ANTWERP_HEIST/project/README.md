# WAR FILES: Antwerp Diamond Heist, editable project

Everything in the film is generated from source in `src/`. Re-run any step after editing.

| Step | Command (from `src/`) | Output |
|---|---|---|
| Narration text, scene plan, pronunciations | edit `script_data.py` | |
| Voice (Kokoro TTS, local) | `python3 tts.py` | `build/tts/*.wav`, `build/tts_items.json` |
| Timeline check | `python3 timeline.py` | prints runtime and scene starts |
| Score + SFX + mix | `python3 audio.py` | `build/audio/{mix_raw,voice,music_sfx}.wav` |
| Subtitles | `python3 subs.py` | `build/subtitles.{srt,ass}` |
| Scene video | `python3 render.py` | `build/clips/cNN.mp4` (cached per scene) |
| Final film | `./assemble.sh` | `../FINAL_DOCUMENTARY.mp4`, `../VOICEOVER.wav`, `../SUBTITLES.srt` |
| Thumbnails | `python3 thumbs.py` | `build/thumb_*` |
| Script, shot list, AI prompts | `python3 docs.py` | root text files |

Requirements: Python 3 with numpy, pillow, scipy, soundfile, kokoro-onnx and fonttools; ffmpeg with
libass and libx264; Kokoro model files `kokoro-v1.0.onnx` and `voices-v1.0.bin` (from
github.com/thewh1teagle/kokoro-onnx releases) in `/home/user/models/` (path set in `tts.py`).

To swap in AI-generated or licensed archival footage: render or obtain clips per
`../AI_VIDEO_PROMPTS.txt`, trim each to the scene duration in `../SHOT_LIST.csv`, replace
`build/clips/cNN.mp4` (1920x1080, 24 fps, H.264), keep the on-screen label, and re-run
`./assemble.sh`.
