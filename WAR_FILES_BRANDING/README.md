# WAR FILES — channel branding concepts

- `logos/LOGO_A_SEAL_800.png` — **recommended**: brass seal + stencil "WF" monogram. Readable down to 32 px.
- `logos/LOGO_B_FILE_800.png` — classified file folder + TOP SECRET stamp (text unreadable below ~98 px).
- `logos/LOGO_C_HELMET_800.png` — simplified evolution of the current helmet logo.
- `logos/LOGO_SIZE_TEST.png` — each logo at YouTube sizes (400/176/98/48/32 px) on dark and light UI.
- `banners/BANNER_<X>_2560x1440.jpg` — upload size; `..._mobile_safe_area.jpg` — the 1546×423 area every device shows.
Regenerate: `python3 src/branding.py` (palette and fonts from WAR_FILES_PLAYBOOK). Tagline is a parameter of `banner()`.
