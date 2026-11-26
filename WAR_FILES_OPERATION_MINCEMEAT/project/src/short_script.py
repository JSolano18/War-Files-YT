"""WAR FILES — Short: 'The Man Who Never Existed' (new visuals, built for the Short only)."""
# (id, narration, visual kind, args)
LINES = [
 ("L1", "Hitler sent a panzer division to the wrong country... because of the man in this grave.", "photo", dict(img="grave", c0=(0.5, 0.55), c1=(0.5, 0.45), z0=1.25, z1=1.05)),
 ("L2", "There's just one problem. Major William Martin never existed.", "photo", dict(img="grave", c0=(0.5, 0.45), c1=(0.5, 0.42), z0=1.05, z1=1.4, stamp="NEVER EXISTED", circle=True)),
 ("L3", "April 1943. A body in a British officer's uniform washes up on this beach in Spain.", "photo", dict(img="beach", date="30 · 04 · 1943", z0=1.1, z1=1.25)),
 ("L4", "Chained to his coat: a briefcase of top secret letters.", "secret", {}),
 ("L5", "They revealed the Allies' next target. Greece.", "word", dict(word="GREECE", sub="NEXT ALLIED TARGET")),
 ("L6", "Spain was neutral. But it was crawling with German spies.", "photo", dict(img="hitler", z0=1.0, z1=1.12, bw=True, cover=False)),
 ("L7", "Within weeks, the letters reached Hitler's headquarters. And he believed them.", "photo", dict(img="hitler", z0=1.12, z1=1.35, bw=True, stamp="BELIEVED IT", cover=False)),
 ("L8", "German forces were rushed to Greece.", "word", dict(word="GREECE", sub="GERMAN REINFORCEMENTS", arrows=True)),
 ("L9", "Then, on July 10th, 1943, the Allies landed somewhere else.", "photo", dict(img="sicily_lct", date="10 · 07 · 1943", z0=1.05, z1=1.2)),
 ("L10", "Sicily.", "swap", dict(old="GREECE", new="SICILY")),
 ("L11", "The officer was pure fiction. His fiancée. His love letters. Even his theatre tickets.", "list", dict(items=["FIANCÉE", "LOVE LETTERS", "THEATRE TICKETS"])),
 ("L12", "But the body was real. A homeless Welshman who died in London, and was forgotten for fifty years.", "photo", dict(img="plaque", z0=1.05, z1=1.2)),
 ("L13", "So who was he? And how did two British officers pull this off?", "photo", dict(img="sicily_loc", z0=1.15, z1=1.0, bw=True)),
 ("L14", "The full story is linked right below.", "end", {}),
]
SPOKEN = [("1943", "nineteen forty-three"), ("10th", "tenth"), ("Hitler's", "Hitler's")]
