# Daily episode routine

> **Updated 2026-11-16 by Vincenzo's request:** the Future song credit card was removed on purpose (videos now loop back to the opening shot), lessons are life rules from Episode 16, and the whole video is 20-25 seconds. If a run's instructions mention 10:00/18:00 slots, `credit_song`, a credit card check, 8-10 lines or ~35 seconds, those are out of date: follow this file and `series.json`.

One new episode a day, published at 20:00 Africa/Harare (13:00 US Eastern) on TikTok through vidIQ (since 2026-11-19; Metricool is no longer used). Episodes up to 24 went out twice a day; from Episode 25 (22 Nov) it is one a day at 20:00 only. Story and content rules live in `rules_for_daily_scripts` and `masterplan` in `series.json`.

## Script format
Copy `scripts/ep005.json`. Fields: ep, chapter, title, lesson, hook, caption, optional next, and shots[]. Each shot has set, cast (who, x, pose, face, mood), lines ([who, text, optional {mood, pose}]), and optional card, end, outro.
- who: cenzo, clyde, nia (displays MTORIRO), zeke (displays SOLO), maya (displays JAMAL). New characters go in `series.json` and `voices.py`.
- sets: harare, bulawayo, home, alley, villa, mansion, hotel, gameroom, gym, desk, plane, train, ship, tokyo, paris, dubai. Build every new country before using it, with its landmarks, shops and street life. Add new ones in `show.py` BUILDERS.
- Sets include `station` (Harare station) and `bulawayo_station` (same concourse, signed Bulawayo). Silent action lines use {"beat": seconds}; write them in brackets in the script, the brackets are not shown on screen.
- poses: stand, walk, sit, seat, seat2, eat, game, lift, curl (gym: lift or curl; desk: seat). Moods: neutral, happy, smug, shock, angry, focus.
- x between 200 and 850.
- Background people appear automatically and differ each episode. For a bigger crowd set `crowd` on a shot, for example 40; Episode 100 uses 120 or more on outdoor sets.
- hook: 2 lines at most, under 14 characters per line.
- card: the rule, spoken by EXOTICCENZO.
- Abroad: add `{"tr": "translated line"}` as each line's options, including the outro. No speech bubbles: abroad uses the same close-ups and English word captions, and the translation shows as a small subtitle above the speaker's head. tokyo=Japanese, paris=French, dubai=Arabic; on new countries set `lang` on the shot (ISO code) and add its font to LANG_FONT in show.py if not Latin, Cyrillic, Greek, Arabic or CJK. If no font exists, leave English and say so in the summary. Bubble colours change automatically.
- `vote`: list of the caption's 2 or 3 answer options (short, e.g. ["To say sorry", "The pages", "To join us"]). The end card shows them as A) B) C) with COMMENT A OR B, because TikTok comment polls cannot be created through any API. Set it on every episode. Next episode, count comments that are just a letter (or name an option) and follow the most-voted/most-liked.
- The story shot before the outro needs `end`: the cliffhanger question, 4 words or fewer. Pick the cliffhanger type from `cliffhanger_plan` in series.json and follow the CLIFFHANGERS rule: cut on the question not the answer, rotate the type, one open question, open the next episode on new tension (no recap), always pay it off. Log it as `cliffhanger_type`.
- Last shot has `"outro": true`: EXOTICCENZO alone, happy, same set, 1 short line.

## End of video
- next: leave unset; the end card says NEXT EPISODE TOMORROW (one episode a day). Never use NEXT EPISODE TONIGHT.
- End: no credits. The video loops: after the end card it cuts back for 0.9s to the opening shot with the hook on screen, so the replay feels seamless. Make the hook and the last line connect (the last line can lead straight into the hook). credit_song is no longer used.
- promo: leave unset. Paid adverts are off.

## 80-day countdown (from Episode 21)
Episode N is story DAY N-20 of 80 (Ep 100 = DAY 80/80, the final piece). The renderer adds a red DAY N/80 badge above the hook automatically. Caption: 'THE RULE BOOK Ep N (Day N-20/80)'. See the 80-DAY COUNTDOWN rule and plot_threads the_deadline (THE COLLECTOR) in series.json.

## Other files
- `fans.json`: comments read, fan cast, ideas, removal requests. Fan characters go in `series.json` with their TikTok username as the name.
- `trends.json`: current trends mapped to the story.
- `slang.json`: current American Gen Z slang and vetted Zimbabwean words, plus an avoid list. See the LANGUAGE AND RELATABILITY rule. Use one when it fits. Never add copyrighted songs.

## Look from Episode 15
From Episode 15 the renderer switches to the illustrated cartoon style on its own (`illus_from: 15` in series.json): big-head stickmen in real clothes, close-ups on whoever is talking, 2-3 word caption chunks at the bottom with the spoken word highlighted. Scripts don't need a `style` field. Keep lines short and punchy so the captions read well.

## Automatic polish (renderer, from 2026-11-16)
Punch-in zoom (~14%) and a short shake on shock/angry/happy lines, springy squash-and-stretch, idle blinks, caption colour per speaker (their accent), music ducked under dialogue, audio normalised to -14 LUFS. Use moods deliberately: shock/angry/happy lines get the punch-in, so save them for the 2-4 real punchlines and reactions per episode.
Crowds: outdoor extras freeze, turn toward the speaker and a few film on phones during shock/angry lines; Bucket Hat Guy (running gag) is hidden in every outdoor crowd. See the BACKGROUND rule.
Pun sign: one joke per episode from signs.json (shop board outdoors, poster indoors). Regulars: tout, aunty, fruit vendor, baguette man always in their spots (REGULARS in show.py).
Rewatch layer (automatic): 2-frame ghost flashes of the cliffhanger card at 3.2 s and 10.4 s; one secret frame at 5.0 s using the optional script field "secret". See the LOOPS AND REWATCH rule.

## Summary extras (from 2026-11-17 research)
- POLL TO PIN: TikTok creator comment polls take up to 5 options and a time limit; give the caption's options (2, or 3 on viewer-vote episodes) and suggest 24 hours.
- PLAYLIST: tell Vincenzo which TikTok playlist to add the episode to, one per chapter, named 'THE RULE BOOK Ch N: <chapter title>' (e.g. 'THE RULE BOOK Ch 2: THE SIGNATURE'), so new viewers can binge in order.
- Follow the CREATOR PLAYBOOK rule in series.json (save/share bait, viewer vote episodes, silent episode, Sunday CLYDE'S PLAN segment, Solo rivalry score, fans on background signs).

## Free edit layer (fx.py, from Episode 22; `fx_from` in series.json)
Replaces CapCut/Canva/Picsart-style polish with code, no credits: warm colour grade, soft bloom, vignette and light film grain; shot transitions rotating whip-pan, zoom-blur and glitch; captions that bounce in, with keywords/numbers bigger and flashing yellow; extra synthesized SFX (record scratch on every 2nd shock line, bass boom on the rule card and happy punchlines, riser into the end card, typewriter clicks on the question, phone blip on phone-prop shots, digital zap on glitch cuts). All automatic; scripts need nothing new. The cut into the final loop shot stays hard so the loop is seamless.

## Added 2026-11-18 (similar-content research)
- `open_loops` in series.json is the continuity ledger: cliffhangers come from it; close loops when paid off (CONTINUITY LEDGER rule). Callback to an earlier episode about every 3rd ep.
- Optional script field `shoutout`: {"user": "...", "text": "..."} shows COMMENT OF THE DAY on the outro (COMMENT OF THE DAY rule).
- Holiday specials (US Thanksgiving 26 Nov, Black Friday 27 Nov, Christmas, New Year) and a CLYDE TAKEOVER caption once a chapter (SPECIALS AND TAKEOVERS rule).

## Silent beats (from Episode 28)
For the chapter's silent episode, a line can take `{"beat": seconds}` (e.g. `["zeke", "(HOLDS OUT HIS HAND)", {"beat": 1.4, "mood": "neutral"}]`): no voice, the text shows as an on-screen action caption in the speaker's colour, and the mood still drives faces, punch-ins and SFX. A shot may have `"lines": []` when it only carries the rule `card`.
