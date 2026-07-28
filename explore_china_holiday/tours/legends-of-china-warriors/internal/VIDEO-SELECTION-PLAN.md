# Video Selection Plan — Legends of China Warriors

> **How to use this document:** Each shot below has a shortlist of candidates
> with their LLM content tags + metrics + your existing verdicts. **You pick
> which clip(s) go in each shot** (Layer 3 — your judgment). I may push back
> and we discuss. The decision + reason becomes the seed.
>
> Mark your picks: write your clip ID + reason next to each shot.
> **Both cuts need clips:** Landscape (16:9 desktop) + Portrait (9:16 mobile).

---

## How the three layers work together

| Layer | What it tells you | Source |
|---|---|---|
| **Metrics** | Will this cut jarringly? Is it static? | opencv (bright/motion/shake) |
| **Tags** | What IS this clip? Right angle/mood/grade for this beat? | LLM vision (MiniMax M3) |
| **Your pick** | Does it fit the story? Does it move you? | **YOU — the seed** |

The minus method: eliminate the `amateur`/`personal` grade clips first (auto-reject), then judge the `professional`/`broadcast` pool. Brightness should cluster within a shot for smooth cuts.

---

## SHOT 1 — HOOK: Great Wall at dawn (0:00–0:06, 6s)

**Script VO:** "China doesn't reveal itself all at once. It unfolds — over twelve days, five cities, and five thousand years."
**Needs:** A single iconic, epic image. Drone/aerial. Dawn or golden. Calm, not busy.

### Landscape candidates (for 16:9 desktop cut)

| Clip | Grade | Perspective | Mood | Motion | Bright | Your pick |
|---|---|---|---|---|---|---|
| `pexels_1193306` | broadcast | drone | epic | 23.8 | 111 | ⬜ "Sweeping aerial, Great Wall snaking through mountains" — **high motion, dramatic** |
| `pexels_30806149` | broadcast | drone | epic | 7.4 | 99 | ⬜ "Aerial drone, Great Wall snaking" — **moderate motion, calmer** |
| `pexels_30897424` | broadcast | drone | epic | 5.8 | 100 | ⬜ "Breathtaking aerial, Great Wall across rugged terrain" |
| `pexels_31300653` | broadcast | drone | epic | 6.0 | 77 | ⬜ "Aerial, Great Wall across ridges" — **darker, moodier** |
| `pexels_35834780` | broadcast | drone | epic/serene | 2.6 | 110 | ⬜ "Stone wall with watchtowers tracing along" — **very calm, low motion** |

**My recommendation:** `pexels_30806149` — broadcast grade, drone, epic, motion 7.4 (smooth but alive), brightness 99 (neutral). The opening should breathe, not whirl. `pexels_1193306` has great motion (23.8) but might be too busy for a 6s hook that needs to land the VO.

### Portrait candidates (for 9:16 mobile cut)

| Clip | Grade | Perspective | Mood | Motion | Bright | Your pick |
|---|---|---|---|---|---|---|
| `pexels_38542422` | professional | drone | serene | 4.4 | 117 | ⬜ "Fog cascading over pine-covered mountain ridge" |
| `pexels_38474888` | professional | drone | dramatic/serene | 6.3 | 122 | ⬜ "Misty aerial, glass-bottom viewing platform" |
| `pexels_36901766` | professional | drone | epic | 8.8 | 118 | ⬜ "Rocky mountain ridges and canyon slopes" |
| `pexels_35571631` | professional | high_angle | dramatic/epic | 4.9 | 104 | ⬜ "Sunrise over layered mountain ridges, golden hour" |

**⚠️ Note:** The portrait pool for shot1 is weaker — none are clearly "Great Wall." They're generic mountain aerials. This may need a re-fetch with tighter keywords, or we crop from the landscape clip.

**Your selection:**
> Landscape: _______  Reason: _______
> Portrait: _______  Reason: _______

---

## SHOT 2 — BEIJING IMPERIAL (0:06–0:14, 8s)

**Script VO:** "It begins in Beijing — at Tiananmen Square, and the Forbidden City, where emperors ruled, and history still stands."
**Needs:** Tiananmen + Forbidden City. Imperial grandeur. Eye-level or low-angle for majesty.

### Landscape candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_10848132` | professional | eye_level | dramatic/epic | 24.4 | 47 | ⬜ "Illuminated Chinese gate with portrait" — **Tiananmen at night, dark** |
| `pexels_33009797` | professional | eye_level | dramatic | 12.9 | 58 | ⬜ "Tourists before illuminated Tiananmen Gate" — **good Tiananmen** |
| `pexels_35548691` | professional | low_angle | epic | 12.6 | 107 | ⬜ "Forbidden City grand red-walled courtyard" — **good FC** |
| `pexels_2953632` | professional | eye_level/low_angle | epic | 18.0 | 122 | ⬜ "Tourists, red walls, golden-tiled roofs" — **good FC, bright** |
| `pexels_34811316` | professional | eye_level | serene | 6.3 | 119 | ⬜ "Forbidden City palace complex, traditional roofs" |

**My recommendation:** Two clips cut together — `pexels_33009797` (Tiananmen, dark dramatic, bright 58) then `pexels_35548691` (Forbidden City, bright 107). The brightness jump (58→107) is large but acceptable across a cut between two different locations. Alternatively, use `pexels_34811316` (FC, bright 119, serene) for continuity.

### Portrait candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_37217727` | professional | high_angle | energetic | 14.3 | 140 | ⬜ "Multi-lane expressway in Chinese city" — **not imperial, wrong content** |
| `pexels_37096713` | personal/professional | low_angle | epic | 14.1 | 115 | ⬜ "Beijing CBD skyline" — **modern, not imperial** |
| `pexels_34458067` | professional | high_angle/low_angle | serene | 47.6 | 123 | ⬜ "Nepalese temple plaza" — **wrong location** |

**⚠️ Problem:** The portrait pool for shot2 is weak — LLM tags show the "Beijing" portrait clips are actually modern skylines or wrong-country temples. **This needs a re-fetch** with portrait-specific keywords like "forbidden city vertical" or "tiananmen portrait."

**Your selection:**
> Landscape: _______  Reason: _______
> Portrait: _______  Reason: _______

---

## SHOT 3 — GREAT WALL HERO (0:14–0:22, 8s)

**Script VO:** "You'll walk the Great Wall — not a postcard version, the real one. Stone by stone, two thousand years in the making."
**Needs:** The hero shot. Scale + human presence. People walking the Wall.

### Landscape candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Verdict | Notes |
|---|---|---|---|---|---|---|---|
| `pexels_2881972` | professional | high_angle | energetic/epic | 4.9 | 112 | ✅ ACCEPT | "Crowds traverse the stone pathway" — **your pick, confirmed good** |
| `pexels_32904874` | professional | high_angle | epic | 14.7 | 120 | ⬜ | "Crowds ascending, mountains+clouds" — **the one you described in detail** |
| `pexels_2881966` | professional | eye_level/POV | epic/serene | 11.5 | 165 | ⬜ | "Tourists explore ancient stone pathway" — **bright 165, may be overexposed** |
| `pexels_2881976` | broadcast | POV/high_angle | epic | 7.6 | 99 | ⬜ | "Through weathered brick archway, Wall snaking" — **great framing** |

**My recommendation:** `pexels_2881972` (your confirmed accept) as the primary, possibly paired with `pexels_32904874` (the drone top-down you liked). Both are high_angle/epic, brightness 112/120 — they'll cut together smoothly.

### Portrait candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_35614363` | amateur/personal | **first_person_pov** | dramatic/energetic | 47.1 | 93 | ⬜ **The POV/action clip you flagged — different category, not for this cut** |
| `pexels_36947446` | professional | low_angle | intimate/serene | 6.3 | 139 | ⬜ "Low-angle close-up of traveler's legs walking cobblestone" |

**Your selection:**
> Landscape: _______  Reason: _______
> Portrait: _______  Reason: _______

---

## SHOT 4 — TERRACOTTA WARRIORS — THE PEAK (0:22–0:32, 10s)

**Script VO:** "In Xi'an, you stand before the Terracotta Warriors. Eight thousand soldiers, carved one by one — every face different. Every face waiting."
**Needs:** This is the emotional peak. Music drops to silence. The image must hold the screen alone. Ranks receding into shadow. A single face.

### Landscape candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Verdict | Notes |
|---|---|---|---|---|---|---|---|
| `pexels_36926082` | broadcast | eye_level/low_angle | dramatic/epic | 11.9 | 60 | ✅ ACCEPT | "Close-up terracotta horses, dimly lit" — **your pick, dark + dramatic** |
| `pexels_36926090` | broadcast | eye_level | epic | 19.3 | 81 | ⬜ | "Rows of life-sized terracotta statues in formation" — **THE pit wide** |
| `pexels_36926079` | broadcast | eye_level | epic | 18.5 | 74 | ⬜ | "Rows of intricately detailed warriors" — **detailed, dark** |
| `pexels_36926095` | professional | eye_level | dramatic | 9.6 | 69 | ⬜ | "Warrior figures in profile, weathered earth" — **the face shot** |
| `pexels_36926089` | professional | high_angle | epic | 29.7 | 91 | ⬜ | "Row of warriors exposed in archaeological pit" |

**❌ Already rejected by you:** `pexels_35195652`, `pexels_36926085`, `pexels_35195714`, `pexels_6540513`

**My recommendation:** Two clips — `pexels_36926090` (the pit wide, ranks receding, bright 81) for the "eight thousand soldiers" line, then `pexels_36926095` (warrior face in profile, bright 69) for "every face different." Both are dark (69-81 brightness) which is perfect for the music drop. Your accepted `pexels_36926082` (horses close-up, bright 60) could be a third beat.

### Portrait candidates

**⚠️ Problem:** The portrait pool for warriors has NO actual Terracotta Army clips — they're Sphinx, stone soldiers, wooden blocks. **This shot absolutely needs portrait re-fetch.** The Terracotta face reveal is the most important frame in the whole film.

**Your selection:**
> Landscape: _______  Reason: _______
> Portrait: _______  Reason: _______

---

## SHOT 5 — WATER TOWNS (0:32–0:40, 8s)

**Script VO:** "Then the pace softens — the gardens of Suzhou, the still water of Wuxi. China, catching its breath."
**Needs:** Serene. Gardens, water, bridges. Green. Calm after the warriors.

### Landscape candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_34058185` | professional | eye_level | serene | 12.7 | 80 | ⬜ "Tranquil Chinese garden, white-walled pavilions" |
| `pexels_26727896` | professional | eye_level | serene | 18.7 | 103 | ⬜ "Wooden boats with blue canopies line a canal" — **water town** |
| `pexels_10278928` | professional | eye_level | serene | 17.2 | 123 | ⬜ "Serene Chinese garden, red-lacquered pavilion" |
| `pexels_34058208` | professional | eye_level | serene | 8.7 | 103 | ⬜ "Classical Chinese garden, red-pillared pavilion" |
| `pexels_33010049` | broadcast | eye_level | serene | 4.2 | 182 | ⬜ "Chinese pavilion bridge, ornate red" — **bright 182, outlier** |

**My recommendation:** `pexels_34058185` (garden, bright 80, serene) cuts well after the dark warriors (bright 69-81) — smooth brightness transition into calm. Then `pexels_26727896` (canal boats, bright 103) for the water-town beat.

### Portrait candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_30931843` | professional | eye_level | serene | 1.9 | 150 | ⬜ "Canal scene, stone bridge" — **low motion, may be static** |
| `pexels_36049505` | professional | low_angle | serene | 24.1 | 98 | ⬜ "Stone arch bridge over calm green river" |
| `pexels_37120057` | professional | eye_level | serene | 13.9 | 102 | ⬜ "Ornate Chinese garden, whimsical insect architecture" |
| `pexels_16032143` | broadcast | drone | serene | 18.7 | 99 | ⬜ "Multi-tiered pagoda, red roofs, golden spire" |

**Your selection:**
> Landscape: _______  Reason: _______
> Portrait: _______  Reason: _______

---

## SHOT 6 — HANGZHOU TEA (0:40–0:46, 6s)

**Script VO:** "In Hangzhou, you taste it — Dragon Well tea, poured where it's grown."
**Needs:** Tea pouring close-up (sensory). Then West Lake (landscape beauty).

### Landscape candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_6691563` | broadcast | eye_level | serene | 6.9 | 73 | ⬜ "Hands pour tea from celadon teapot" — **the pour shot** |
| `pexels_6540524` | professional | eye_level | serene | 6.8 | 103 | ⬜ "Young woman pours tea in warm light" |
| `pexels_35214757` | broadcast | eye_level | serene | 5.3 | 163 | ⬜ "Chinese pleasure boat on misty lake" — **West Lake** |
| `pexels_32004794` | professional | eye_level | serene | 8.1 | 157 | ⬜ "Wooden boat with blue canopy carries tourists" — **West Lake** |

**My recommendation:** `pexels_6691563` (tea pour, broadcast, bright 73) — the sensory detail you need. Then `pexels_35214757` (boat on misty lake, broadcast, bright 163) for the West Lake beauty beat.

### Portrait candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_6540264` | broadcast | eye_level/low_angle | intimate/serene | 7.8 | 102 | ⬜ "Golden tea poured from white porcelain" — **great pour shot** |
| `pexels_5976233` | professional | eye_level | intimate/serene | 5.7 | 99 | ⬜ "Tea ceremony, steam rising" |
| `pexels_8508067` | professional | eye_level | intimate/serene | 4.4 | 80 | ⬜ "Woman performs tea ceremony" |

**Your selection:**
> Landscape: _______  Reason: _______
> Portrait: _______  Reason: _______

---

## SHOT 7 — SHANGHAI (0:46–0:50, 4s)

**Script VO:** "And Shanghai — where a four-hundred-year-old garden meets a tomorrow that's already here."
**Needs:** Old vs new contrast. Yu Garden + Bund skyline. Night cityscape = dramatic.

### Landscape candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_31776600` | broadcast | eye_level | dramatic/epic | 8.6 | 77 | ⬜ "Shanghai skyline at night, Oriental Pearl Tower" — **THE shot** |
| `pexels_34048040` | professional | eye_level | dramatic | 13.0 | 44 | ⬜ "Nighttime Bund waterfront" — **very dark, dramatic** |
| `pexels_33923468` | professional | eye_level/low_angle | energetic/epic | 9.8 | 63 | ⬜ "Nighttime traditional Chinese architecture" — **Yu Garden?** |
| `pexels_34058332` | professional | eye_level | serene | 14.4 | 83 | ⬜ "Classical Chinese garden, koi pond" — **Yu Garden** |

**My recommendation:** `pexels_34058332` (Yu Garden, bright 83, serene) then `pexels_31776600` (Shanghai skyline, broadcast, bright 77, dramatic). The old→new contrast in one cut. Both are dark-ish (77-83) so they cut together.

### Portrait candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_15911227` | broadcast | drone/high_angle | epic | 4.6 | 28 | ⬜ "Aerial night, Oriental Pearl Tower" — **very dark** |
| `pexels_15911234` | professional | drone/high_angle | epic | 7.1 | 28 | ⬜ "Aerial night, Pudong skyline" |
| `pexels_36546365` | personal/professional | eye_level | dramatic | 12.9 | 56 | ⬜ "Pudong skyline, Oriental Pearl Tower" |

**Your selection:**
> Landscape: _______  Reason: _______
> Portrait: _______  Reason: _______

---

## SHOT 8 — TRUST / CTA (0:50–0:55, 5s)

**Script VO:** "Twelve days. Flights, hotels, and the stories — all included. From fourteen ninety-nine. Your legend starts here."
**Needs:** Quick montage — hotel room, high-speed train, Peking Duck. Then logo card.

### Landscape candidates

| Clip | Grade | Perspective | Mood | Motion | Bright | Notes |
|---|---|---|---|---|---|---|
| `pexels_6466561` | professional | eye_level | calm/intimate | — | — | ⬜ "Detail/people" — needs viewing |
| `pexels_34624968` | professional | high_angle | serene | — | — | ⬜ "Detail/high_angle" |
| `pexels_18452158` | professional | low_angle | serene | — | — | ⬜ "Detail/low_angle" |
| `pexels_6091143` | professional | eye_level | dramatic | — | — | ⬜ "Action" — **possible train?** |

**⚠️ Note:** Shot8 metrics weren't fully captured (the last batch). These need viewing. The keywords were train/duck/hotel — check the gallery for content match.

**Your selection:**
> Landscape: _______  Reason: _______
> Portrait: _______  Reason: _______

---

## Summary: what needs re-fetching

Based on the LLM tags, three portrait pools are weak:

| Shot | Problem | Action |
|---|---|---|
| **shot1 portrait** | Mountain aerials, none clearly "Great Wall" | Re-fetch: "great wall vertical" / "great wall mobile" |
| **shot2 portrait** | Modern skylines + wrong-country temples, no imperial Beijing | Re-fetch: "forbidden city vertical" / "tiananmen portrait" |
| **shot4 portrait** | NO Terracotta Army clips — Sphinx, stone soldiers, wooden blocks | Re-fetch: "terracotta warriors vertical" (critical — this is the peak) |

I can run these re-fetches with tighter keywords once you confirm. The landscape pools are strong across all shots.

---

## How to fill this in

For each shot, write:
1. **Which clip(s)** you pick (by pexels ID)
2. **Why** (your reason — this is the seed)
3. **Push back on me** if you disagree with my recommendation

Example:
> Landscape: `pexels_32904874` — Reason: "the top-down drone with people climbing and clouds is more epic than 2881972, the scale sells the Wall better"
> Portrait: skip — re-fetch first

Take it shot by shot. We discuss, we disagree, we land on the cut. That discussion IS the beauty standard.
