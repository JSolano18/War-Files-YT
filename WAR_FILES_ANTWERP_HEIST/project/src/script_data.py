# WAR FILES — The Antwerp Diamond Heist
# Narration + scene plan. Each entry: (chapter, scene_kind, params, sentences)
# A sentence is str or (str, pause_after_seconds). Default pause 0.38 s.
# Chapter cards have no narration and a fixed duration in params["dur"].
#
# Claims attributed to Leonardo Notarbartolo's later account (WIRED, 2009) are
# explicitly flagged in the narration. Disputed figures are given as ranges.

P = 0.38   # default pause
L = 0.95   # long pause after a reveal

SCRIPT = [
# ───────────────────────── COLD OPEN ─────────────────────────
("The discovery", "vault_door", {"state": "closed", "tag": "DRAMATIZATION", "z": (1.0, 1.18), "sfx": "drone_hit"}, [
    ("Monday morning. February 17th, 2003.", 0.8),
    "Two floors beneath the streets of Antwerp, Belgium, staff arrive at one of the most heavily protected vaults in the world.",
    ("The vault door is standing open.", L),
]),
("The discovery", "boxes_wall", {"mode": "aftermath", "tag": "ILLUSTRATION", "sfx": "metal"}, [
    "Inside, rows of steel safe-deposit boxes have been forced apart.",
    ("The floor is buried in paper, torn envelopes, and empty jewelry cases.", 0.6),
]),
("The discovery", "diamonds", {"variant": "fall", "tag": "ILLUSTRATION"}, [
    ("Diamonds, gold, and jewelry — worth an estimated one hundred million dollars — are gone.", L),
]),
("The discovery", "statement", {"lines": ["NO EXPLOSION.", "NO ALARM.", "NO WITNESSES."], "accent": [2], "style": "stack", "sfx": "impact"}, [
    "There was no explosion. No alarm. No witnesses.",
    ("A vault reportedly protected by ten layers of security had not been smashed. It had been beaten — quietly, one layer at a time.", L),
]),
("The discovery", "title", {"sfx": "boom"}, [
    "This is the story of how it was done, the mistake that brought the thieves down, and the question that remains unanswered more than twenty years later.",
    ("Where are the diamonds?", 1.4),
]),

# ───────────────────────── I. ANTWERP ─────────────────────────
("Antwerp: the diamond capital", "chapter", {"num": "I", "title": "THE DIAMOND CAPITAL", "dur": 3.4}, []),
("Antwerp: the diamond capital", "map", {"mode": "europe_belgium"}, [
    "To understand this crime, you first have to understand the city.",
    "Antwerp sits in the north of Belgium, on the river Scheldt, about forty-five kilometers from Brussels.",
    ("For more than five hundred years, its fortunes have been tied to one thing above all else.", 0.5),
    ("Diamonds.", L),
]),
("Antwerp: the diamond capital", "city_night", {"tag": "ILLUSTRATION"}, [
    "By the early two thousands, Antwerp was the center of the global diamond trade.",
    "By widely cited estimates, roughly eighty percent of the world's rough diamonds passed through this one city.",
]),
("Antwerp: the diamond capital", "district", {"tag": "SIMPLIFIED ILLUSTRATION — NOT TO SCALE"}, [
    "Most of that trade happens inside a district of just a few streets beside Antwerp's Central Station.",
    ("Hoveniersstraat. Schupstraat. Rijfstraat.", 0.6),
    "Traders of dozens of nationalities work side by side in these few blocks — rough stones arriving from mines around the world, polished stones leaving for jewelers everywhere.",
    "Here, fortunes in stones change hands every day — and deals are traditionally sealed with a handshake and a single word: mazal.",
]),
("Antwerp: the diamond capital", "statement", {"lines": ["CAMERAS.", "POLICE.", "BARRIERS."], "accent": [1], "style": "row"}, [
    ("The district is watched by cameras, patrolled by police, and protected by barriers against vehicle traffic.", 0.5),
]),
("Antwerp: the diamond capital", "building", {"mode": "plain", "tag": "SIMPLIFIED ILLUSTRATION"}, [
    "And at its heart, at Schupstraat 9 to 11, stood the Antwerp Diamond Centre.",
    "Its tenants were diamond dealers. And two floors below street level, behind a massive steel door, was the vault where many of them kept their most valuable goods.",
    ("To the people who trusted it, that vault was about as safe as a place could be.", L),
]),

# ───────────────────────── II. THE TENANT ─────────────────────────
("Leonardo Notarbartolo and the crew", "chapter", {"num": "II", "title": "THE TENANT", "dur": 3.4}, []),
("Leonardo Notarbartolo and the crew", "map", {"mode": "turin_antwerp"}, [
    "Around two years before the robbery, a new tenant moved into the building.",
    "He was Italian. He presented himself as a diamond dealer. And he rented an office inside the Antwerp Diamond Centre.",
]),
("Leonardo Notarbartolo and the crew", "dossier", {"name": "LEONARDO NOTARBARTOLO", "alias": "—", "role": "TENANT, ANTWERP DIAMOND CENTRE", "note": "Convicted in 2005 of organizing the robbery", "stamp": "TENANT", "tag": "ILLUSTRATION"}, [
    ("His name was Leonardo Notarbartolo.", 0.6),
    "As a tenant, he had what every legitimate dealer in the building had: an office, a safe-deposit box of his own, and a reason to walk into the vault area.",
    "To the guards and the other dealers, he was a familiar face. Polite. Unremarkable. The kind of man nobody looks at twice.",
    ("A Belgian court would later conclude that he was something else entirely: the man who organized the robbery.", L),
]),
("Leonardo Notarbartolo and the crew", "statement", {"lines": ["THE", "SCHOOL OF TURIN"], "accent": [1], "style": "title", "sfx": "impact"}, [
    "Notarbartolo did not work alone.",
    ("He was connected to a group of thieves based around Turin, in northern Italy — a crew the press would later call the School of Turin.", 0.6),
]),
("Leonardo Notarbartolo and the crew", "crew", {"tag": "ILLUSTRATION"}, [
    "The men convicted alongside him became known by nicknames that sound as if they were written for a movie.",
    "Elio D'Onorio, called the Genius — described as an expert in alarms and electronics.",
    "Ferdinando Finotto, the Monster — described as a lock specialist, a skilled driver, and a man of enormous strength.",
    "Pietro Tavano, known as Speedy — described as Notarbartolo's longtime friend.",
    ("And a fifth man, an older specialist known only as the King of Keys, said to be one of the finest key forgers alive. His identity has never been established.", L),
]),
("Leonardo Notarbartolo and the crew", "statement", {"lines": ["MUCH OF WHAT WE KNOW", "COMES FROM ONE MAN."], "accent": [1], "style": "left"}, [
    ("One warning before we go further.", 0.4),
    "Much of what is known about these men — including their nicknames and roles — comes from Notarbartolo's own later account of the heist.",
    ("And as we'll see, his version of events is not the only one.", L),
]),

# ───────────────────────── III. THE PREPARATION ─────────────────────────
("The preparation and infiltration", "chapter", {"num": "III", "title": "THE PREPARATION", "dur": 3.4}, []),
("The preparation and infiltration", "layers", {}, [
    "Breaking into the vault meant defeating a system that, on paper, looked overwhelming.",
    "Accounts of the heist describe it in layers.",
    "A combination dial with one hundred million possible codes.",
    "A massive steel door, opened with a key reportedly about a foot long.",
    "Infrared heat detectors. A seismic sensor to pick up vibration. Doppler radar. A light sensor. And a magnetic field that would trigger the alarm if the door was opened.",
    "Inside, every safe-deposit box had a lock of its own.",
    ("And beyond all of that: guards, cameras, and the police presence of the diamond district itself.", L),
]),
("The preparation and infiltration", "statement", {"lines": ["HOW DO YOU LEARN", "A SECURITY SYSTEM", "WITHOUT BEING NOTICED?"], "accent": [2], "style": "center"}, [
    ("For a thief, the problem is not only how to beat each layer. It is how to learn what the layers are — without anyone noticing that you are looking.", L),
]),
("The preparation and infiltration", "corridor", {"tag": "DRAMATIZATION", "speed": 0.7}, [
    "According to Notarbartolo's later account, the answer was patience.",
    "As a tenant, he could go down to the vault again and again, like any other dealer — and he said he spent many months studying it.",
    ("He claimed he secretly photographed the vault, using a tiny camera concealed inside a pen.", 0.6),
]),
("The preparation and infiltration", "blueprint", {"mode": "camera", "tag": "ILLUSTRATION — BASED ON NOTARBARTOLO'S ACCOUNT"}, [
    "In his telling, one step mattered more than any other.",
    "He said the crew hid a small camera of their own above the vault door — positioned to record the guards as they dialed the combination.",
    ("If that account is true, the vault's first line of defense was defeated without anyone touching it.", L),
]),
("The preparation and infiltration", "blueprint", {"mode": "replica", "tag": "ILLUSTRATION — BASED ON NOTARBARTOLO'S ACCOUNT"}, [
    "He also described a rehearsal: the crew practicing on a replica of the vault's defenses, until every step could be performed quickly and in near silence.",
    "Belgian investigators have never confirmed every detail of this version.",
    ("What is not in doubt is that whoever entered that vault knew exactly what they would face.", L),
]),
("The preparation and infiltration", "highway", {"tag": "DRAMATIZATION"}, [
    "By February 2003, the plan was set.",
    ("The target was a weekend — two days when the offices would be closed and the building would be at its quietest.", L),
]),

# ───────────────────────── IV. THE VAULT ─────────────────────────
("Inside the high-security vault", "chapter", {"num": "IV", "title": "INSIDE THE VAULT", "dur": 3.4}, []),
("Inside the high-security vault", "building", {"mode": "entry", "tag": "ILLUSTRATION — BASED ON NOTARBARTOLO'S ACCOUNT"}, [
    "According to the account Notarbartolo later gave to WIRED magazine, the crew did not walk in through the front entrance on the street.",
    ("They approached from a neighboring property at the back — away from the cameras that watched the street.", 0.6),
]),
("Inside the high-security vault", "sensors", {"tag": "ILLUSTRATION — BASED ON NOTARBARTOLO'S ACCOUNT", "sfx": "hum"}, [
    "Every defense, he claimed, had a weakness.",
    "The heat sensor, the story goes, was neutralized with something as ordinary as hairspray — a thin coating that briefly insulated the detector.",
    "The light sensor was covered with tape.",
    "And the magnetic sensor on the vault door — the alarm that should have sounded the moment the door moved — was reportedly bypassed by holding its two halves together with an aluminum plate, so the circuit never broke.",
]),
("Inside the high-security vault", "key", {"tag": "ILLUSTRATION"}, [
    "And the famous key?",
    "In Notarbartolo's account, the crew never needed to forge it at all.",
    ("He said the real key was kept close to the vault itself — where anyone who knew to look could find it.", L),
]),
("Inside the high-security vault", "statement", {"lines": ["A SOPHISTICATED VAULT.", "A SIMPLE HUMAN HABIT."], "accent": [1], "style": "left"}, [
    ("If that is true, one of the most sophisticated vaults in the world was undone by a simple human habit.", 0.6),
    ("It is a claim that has never been independently proven. But what happened next is beyond dispute.", L),
]),

# ───────────────────────── V. THE WEEKEND ─────────────────────────
("The weekend of the robbery", "chapter", {"num": "V", "title": "THE WEEKEND", "dur": 3.4}, []),
("The weekend of the robbery", "timeline", {"mode": "weekend"}, [
    "The break-in took place over the weekend of February 15th and 16th, 2003.",
    ("By Monday morning, it would be discovered. By the following Friday, there would be an arrest.", 0.6),
]),
("The weekend of the robbery", "city_night", {"tag": "DRAMATIZATION", "variant": "late"}, [
    "That weekend, the diamond district fell quiet.",
    ("The trading halls were empty. The offices were dark.", 0.6),
]),
("The weekend of the robbery", "corridor", {"tag": "DRAMATIZATION", "speed": 1.0, "door": True, "sfx": "footsteps"}, [
    "Two levels below the street, the thieves reached the vault door.",
    ("With the combination known, the key in hand, and the sensors neutralized, the door that was supposed to stop everyone simply swung open.", L),
]),
("The weekend of the robbery", "vault_door", {"state": "open", "tag": "DRAMATIZATION", "z": (1.05, 1.22), "sfx": "door"}, [
    ("Inside were rows of safe-deposit boxes — and the crew began forcing them open, one after another, for hours.", 0.6),
]),
("The weekend of the robbery", "boxes_wall", {"mode": "opening", "tag": "ILLUSTRATION"}, [
    "How many boxes did they open?",
    ("Even that is disputed.", 0.5),
]),
("The weekend of the robbery", "bars", {"mode": "boxes"}, [
    "Commonly cited figures range from one hundred and nine to one hundred and twenty-three boxes — out of a total variously reported at between one hundred and sixty and one hundred and eighty-nine.",
]),
("The weekend of the robbery", "diamonds", {"variant": "velvet", "tag": "ILLUSTRATION"}, [
    "What they took is just as uncertain. Loose diamonds. Gold. Jewelry. Other valuables.",
    "Much of what was in those boxes was never documented.",
    ("In the diamond trade, discretion is part of the business — which makes the true size of the loss almost impossible to measure.", L),
]),
("The weekend of the robbery", "highway", {"tag": "DRAMATIZATION", "variant": "escape"}, [
    "Before Monday morning, the crew was gone, leaving behind a vault in chaos.",
    ("And somewhere between Antwerp and Brussels, they made a decision that would cost them everything.", 1.2),
]),

# ───────────────────────── VI. MONDAY ─────────────────────────
("The discovery on Monday morning", "chapter", {"num": "VI", "title": "MONDAY MORNING", "dur": 3.4}, []),
("The discovery on Monday morning", "boxes_wall", {"mode": "aftermath2", "tag": "ILLUSTRATION"}, [
    "On the morning of Monday, February 17th, the robbery was discovered.",
    "The vault was in chaos: box doors hanging open, paper and envelopes scattered across the floor.",
    ("Antwerp police — including the specialized unit dedicated to the diamond trade, known as the Diamond Squad — were called in.", 0.6),
]),
("The discovery on Monday morning", "statement", {"lines": ["NO DAMAGE TO THE DOOR.", "NO TRAIL TO FOLLOW."], "accent": [1], "style": "center"}, [
    ("At first, investigators faced a crime with almost no starting point. The vault door had not been blasted or cut. There was no obvious trail to follow.", L),
]),
("The discovery on Monday morning", "forest", {"tag": "ILLUSTRATION", "variant": "plain", "sfx": "wind"}, [
    "But that same morning, some thirty-five kilometers to the south, something unusual turned up in a patch of woodland beside the E19 highway, near Vilvoorde, just outside Brussels.",
]),
("The discovery on Monday morning", "map", {"mode": "e19"}, [
    "The land was looked after by a local man named August Van Camp.",
    ("And on his property, he found a pile of rubbish that someone had dumped among the trees.", 0.6),
]),
("The discovery on Monday morning", "forest", {"tag": "ILLUSTRATION", "variant": "trash"}, [
    "Among the garbage were envelopes bearing the name of the Antwerp Diamond Centre.",
    ("Van Camp called the police.", L),
]),

# ───────────────────────── VII. THE EVIDENCE ─────────────────────────
("The evidence that exposed the thieves", "chapter", {"num": "VII", "title": "THE EVIDENCE", "dur": 3.4}, []),
("The evidence that exposed the thieves", "evidence", {"tag": "ILLUSTRATION", "focus": None}, [
    "What investigators recovered from those woods would become the core of the case.",
    "There were torn envelopes connected to the diamond centre.",
    "There were documents and other items that could be traced to the people who had thrown them away.",
    ("And there was a half-eaten salami sandwich.", L),
]),
("The evidence that exposed the thieves", "evidence", {"tag": "ILLUSTRATION", "focus": 2}, [
    "The sandwich carried DNA. Investigators tied it to a member of the crew — although accounts differ on exactly whose DNA it was.",
    ("Other items pointed directly to Leonardo Notarbartolo.", L),
]),
("The evidence that exposed the thieves", "statement", {"lines": ["TEN LAYERS OF SECURITY.", "UNDONE BY A BAG OF GARBAGE."], "accent": [1], "style": "left", "sfx": "impact"}, [
    ("It was a staggering contrast. A crew that had allegedly outwitted one of the most secure vaults on the planet had been exposed by a pile of trash in the woods.", L),
]),
("The evidence that exposed the thieves", "forest", {"tag": "DRAMATIZATION", "variant": "night"}, [
    "Notarbartolo later described the dumping as a panicked mistake.",
    "In his account, Speedy — nervous and exhausted — scattered the garbage in the woods instead of getting rid of it as planned.",
    ("Whatever the reason, it handed investigators a direct line to the suspects.", L),
]),

# ───────────────────────── VIII. THE ARREST ─────────────────────────
("Arrests, investigation, and competing accounts", "chapter", {"num": "VIII", "title": "TWO VERSIONS", "dur": 3.4}, []),
("Arrests, investigation, and competing accounts", "timeline", {"mode": "arrest"}, [
    "On February 21st, 2003 — just five days after the break-in — Notarbartolo returned to the Antwerp Diamond Centre.",
    ("Detectives were waiting for him. He was arrested.", 0.6),
    ("From there, investigators turned to the men around him.", L),
]),
("Arrests, investigation, and competing accounts", "crew", {"tag": "ILLUSTRATION", "verdict": True}, [
    "In 2005, a Belgian court convicted Notarbartolo of organizing the heist and sentenced him to ten years in prison.",
    "Elio D'Onorio, Ferdinando Finotto, and Pietro Tavano each received five years.",
    ("The King of Keys was never identified.", L),
]),
("Arrests, investigation, and competing accounts", "split", {}, [
    "Then, in 2009, Notarbartolo told his side of the story to WIRED magazine. And it reframed everything.",
    "He claimed the crew had been hired by a diamond merchant.",
    "He claimed the robbery was part of an insurance fraud scheme.",
    "And he claimed the haul was far smaller than reported — around eighteen million euros, or roughly twenty million dollars.",
]),
("Arrests, investigation, and competing accounts", "bars", {"mode": "value"}, [
    "Many have doubted his story. Belgian authorities have never confirmed it, and the merchant he described has never been identified to the satisfaction of the courts.",
    "He also had every reason to minimize what was stolen.",
    ("And yet his version is hard to dismiss completely — because no one has ever been able to prove exactly what was inside those boxes.", L),
]),

# ───────────────────────── IX. THE MISSING DIAMONDS ─────────────────────────
("The missing diamonds and final mystery", "chapter", {"num": "IX", "title": "THE MISSING DIAMONDS", "dur": 3.4}, []),
("The missing diamonds and final mystery", "diamonds", {"variant": "dark", "tag": "ILLUSTRATION"}, [
    "Notarbartolo was released on parole in 2009.",
    ("And the diamonds? The overwhelming majority have never been recovered.", L),
    "Diamonds are small, valuable, and difficult to trace. Once they are recut or quietly sold, a stone can vanish into the legitimate market almost without a trace.",
]),
("The missing diamonds and final mystery", "questions", {}, [
    ("Was it one hundred million dollars? Or twenty?", 0.6),
    ("A brilliant theft? Or a fraud dressed up as one?", 0.6),
    ("Who was the King of Keys?", 0.6),
    ("And who, if anyone, stood behind the crew?", L),
]),
("The missing diamonds and final mystery", "vault_door", {"state": "closed", "tag": "ILLUSTRATION", "z": (1.22, 1.0), "light": "red"}, [
    "Leonardo Notarbartolo has told his story. The courts have delivered their verdict.",
    ("But neither has answered the question that matters most.", 0.8),
    "More than two decades later, Guinness World Records still lists the Antwerp Diamond Centre robbery as the largest diamond heist in history.",
    "It has inspired books, documentaries, and endless speculation.",
    ("But the most important part of the story is still locked away — not in a vault, but in the silence of the people who know where the diamonds went.", 1.6),
]),
("The missing diamonds and final mystery", "end", {"dur_min": 9.0}, [
    ("This has been WAR FILES. We don't tell stories — we open the files.", 0.8),
    ("If you want the next one, subscribe.", 2.5),
]),
]

# Spoken-form substitutions (display text -> TTS text). Applied in order.
SPOKEN = [
    ("February 17th, 2003", "February seventeenth, two thousand three"),
    ("February 15th and 16th, 2003", "February fifteenth and sixteenth, two thousand three"),
    ("February 21st, 2003", "February twenty-first, two thousand three"),
    ("February 17th", "February seventeenth"),
    ("February 2003", "February two thousand three"),
    ("Schupstraat 9 to 11", "Skoop straht nine to eleven"),
    ("In 2005", "In two thousand five"),
    ("in 2009", "in two thousand nine"),
    ("D'Onorio", "Donorio"),
    ("Hoveniersstraat", "Hohvuhneers straht"),
    ("Schupstraat", "Skoop straht"),
    ("Rijfstraat", "Rife straht"),
    ("Scheldt", "Skelt"),
    ("Vilvoorde", "Vilvorduh"),
    ("E19", "E nineteen"),
    ("WIRED", "Wired"),
    ("mazal", "mahzel"),
    ("Finotto", "Feenotto"),
    ("Pietro", "Peeyetro"),
    ("Notarbartolo", "Notarbartohlo"),
    ("Monday morning. ", "Monday morning... "),
    (" — ", ", "),
    ("—", ", "),
]

# Words highlighted (muted gold) in burned-in subtitles
HIGHLIGHT = ["one hundred million dollars", "Diamonds.", "ten layers of security", "Leonardo Notarbartolo",
             "School of Turin", "King of Keys", "the Genius", "the Monster", "Speedy", "hairspray",
             "salami sandwich", "Where are the diamonds?", "insurance fraud", "eighteen million euros",
             "twenty million dollars", "never been recovered", "largest diamond heist in history",
             "Antwerp Diamond Centre", "Diamond Squad", "August Van Camp", "February 21st, 2003",
             "ten years in prison", "five years", "a foot long", "one hundred million possible codes"]
