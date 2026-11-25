# WAR FILES (@WarFilesInfo) — production memory

YouTube channel of historical / military documentaries. The owner writes in Spanish; videos are in English.

## Titles and thumbnails — ALWAYS
Follow `WAR_FILES_PLAYBOOK/TITULOS_Y_MINIATURAS.md` for every video (rule of thirds, channel palette + one accent
color, Bebas Neue/Oswald, combine 2–3 thumbnail types, title ≤55 chars that opens a curiosity loop, title and
thumbnail complement each other, 3 genuinely different thumbnail variants, homepage simulation test with
`WAR_FILES_PLAYBOOK/homepage_test.py`, backup titles + CTR plan).

## Channel identity (since 2026-11)
- Logo: brass seal with stencil "WF" monogram — `WAR_FILES_PLAYBOOK/brand/LOGO_WAR_FILES_transparent_1000.png`
  (use it on end cards of new videos; the old helmet logo is retired). Generator: `WAR_FILES_BRANDING/src/branding.py`.
- Banner: `WAR_FILES_BRANDING/FINAL/BANNER_WAR_FILES_2560x1440.jpg`.

## Real images rule (owner's instruction, Nov 2026) — ALWAYS
- Letters, documents, people, places, objects and anything else that must be "the real one" are shown with REAL,
  commercially-usable images — never illustrations or AI stand-ins.
- Search first with `WAR_FILES_PLAYBOOK/photo_search.py` (Openverse + Library of Congress).
- IMAGE CHECK BEFORE PRODUCTION (owner's instruction): after the script/shot plan and BEFORE rendering the video,
  search every real person/document/place the video shows, then send the owner ONE list of what is missing
  (who/what, date, what it should show, timestamp/scene) and WAIT for the photos or the owner's go-ahead.
  Never render with silhouettes/placeholders for real people without asking first.
- If a needed real image is not found there, STOP and tell the owner exactly which images are missing (person/document/
  place, date, what it should show). The owner will supply commercially-free photos. Do not substitute an unrelated real
  person's photo or a generated likeness.
- Illustrations/recreations are only for things with no surviving image (e.g. events nobody photographed), and stay labelled.
- Record source + licence for every image; credit on screen and in the description; flag unclear provenance before publishing.

## YouTube upload defaults
- Category: Education · Education type: Other (documentary, not a lesson) · Level: None · Made for kids: No.

## Project layout
- One folder per documentary: `WAR_FILES_<SUBJECT>/` with deliverables at the top and `project/` (src, assets, research, build).
- Do not modify previous documentary projects; copy shared code (`common.py`, `props.py`) into the new project.
- Large media (mp4/wav, build/) is git-ignored; deliver videos with SendUserFile (limit 400 MiB) and tell the owner to download.

## Production lessons
- Narration: Kokoro TTS (`/home/user/models`), voice 0.55 am_michael + 0.45 am_onyx, speed ~0.9, generated per paragraph.
- Verify narration with Whisper small (`/home/user/models/whisper-small-ct2`, faster-whisper; pass numpy audio, not file paths).
  Fix mispronunciations with respellings in `SPOKEN`; coarticulation can break names (e.g. "chose Huelva" → rephrase).
- Subtitles and shot cuts are timed from Whisper word timestamps.
- Licensed real photos (preferred): `WAR_FILES_PLAYBOOK/photo_search.py` — Openverse (CC0/PDM/BY/BY-SA only) + Library of
  Congress ("unrestricted" only). Environment `War-Files-YT` allows api.openverse.org, www.loc.gov, tile.loc.gov,
  catalog.archives.gov, live.staticflickr.com. NARA's API needs a key (owner requests it from Catalog_API@nara.gov;
  save via request_credential, host catalog.archives.gov, header x-api-key).
- Wikimedia Commons: request slowly (rate limits trigger long 429 blocks); use standard thumbnail sizes or originals;
  never spoof user agents; record license/author per image; credit on screen.
- No AI image/video generation is configured; a Gemini API key would need to be added as an environment network secret
  (header `x-goog-api-key`) by the owner.
- Historical rules: distinguish documented / attributed / disputed; no invented quotes or documents; label every
  reconstruction (DRAMATIZATION / ILLUSTRATION / RECREATION); no graphic images of the dead.
