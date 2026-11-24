# WAR FILES (@WarFilesInfo) — production memory

YouTube channel of historical / military documentaries. The owner writes in Spanish; videos are in English.

## Titles and thumbnails — ALWAYS
Follow `WAR_FILES_PLAYBOOK/TITULOS_Y_MINIATURAS.md` for every video (rule of thirds, channel palette + one accent
color, Bebas Neue/Oswald, combine 2–3 thumbnail types, title ≤55 chars that opens a curiosity loop, title and
thumbnail complement each other, 3 genuinely different thumbnail variants, homepage simulation test with
`WAR_FILES_PLAYBOOK/homepage_test.py`, backup titles + CTR plan).

## Project layout
- One folder per documentary: `WAR_FILES_<SUBJECT>/` with deliverables at the top and `project/` (src, assets, research, build).
- Do not modify previous documentary projects; copy shared code (`common.py`, `props.py`) into the new project.
- Large media (mp4/wav, build/) is git-ignored; deliver videos with SendUserFile (limit 400 MiB) and tell the owner to download.

## Production lessons
- Narration: Kokoro TTS (`/home/user/models`), voice 0.55 am_michael + 0.45 am_onyx, speed ~0.9, generated per paragraph.
- Verify narration with Whisper small (`/home/user/models/whisper-small-ct2`, faster-whisper; pass numpy audio, not file paths).
  Fix mispronunciations with respellings in `SPOKEN`; coarticulation can break names (e.g. "chose Huelva" → rephrase).
- Subtitles and shot cuts are timed from Whisper word timestamps.
- Wikimedia Commons: request slowly (rate limits trigger long 429 blocks); use standard thumbnail sizes or originals;
  never spoof user agents; record license/author per image; credit on screen.
- No AI image/video generation is configured; a Gemini API key would need to be added as an environment network secret
  (header `x-goog-api-key`) by the owner.
- Historical rules: distinguish documented / attributed / disputed; no invented quotes or documents; label every
  reconstruction (DRAMATIZATION / ILLUSTRATION / RECREATION); no graphic images of the dead.
