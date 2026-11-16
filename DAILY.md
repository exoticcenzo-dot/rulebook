# Daily episode routine

> **Updated 2026-11-16 by Vincenzo's request:** the Future song credit card was removed on purpose (videos now loop back to the opening shot), lessons are life rules from Episode 16, and the whole video is 20-25 seconds. If a run's instructions mention `credit_song`, a credit card check, 8-10 lines or ~35 seconds, those are out of date: follow this file and `series.json`.

One new episode per run, two runs a day. Episodes publish at 10:00 and 18:00 Africa/Harare on TikTok via Metricool brand 7957195. Story and content rules live in `rules_for_daily_scripts` and `masterplan` in `series.json`.

## Script format
Copy `scripts/ep005.json`. Fields: ep, chapter, title, lesson, hook, caption, optional next, and shots[]. Each shot has set, cast (who, x, pose, face, mood), lines ([who, text, optional {mood, pose}]), and optional card, end, outro.
- who: cenzo, clyde, nia (displays MTORIRO), zeke (displays SOLO), maya (displays JAMAL). New characters go in `series.json` and `voices.py`.
- sets: harare, bulawayo, home, alley, villa, mansion, hotel, gameroom, gym, desk, plane, train, ship, tokyo, paris, dubai. Build every new country before using it, with its landmarks, shops and street life. Add new ones in `show.py` BUILDERS.
- poses: stand, walk, sit, seat, seat2, eat, game, lift, curl (gym: lift or curl; desk: seat). Moods: neutral, happy, smug, shock, angry, focus.
- x between 200 and 850.
- Background people appear automatically and differ each episode. For a bigger crowd set `crowd` on a shot, for example 40; Episode 100 uses 120 or more on outdoor sets.
- hook: 2 lines at most, under 14 characters per line.
- card: the rule, spoken by EXOTICCENZO.
- Abroad: add `{"tr": "translated line"}` as each line's options, including the outro. tokyo=Japanese, paris=French, dubai=Arabic; on new countries set `lang` on the shot (ISO code) and add its font to LANG_FONT in show.py if not Latin, Cyrillic, Greek, Arabic or CJK. If no font exists, leave English and say so in the summary. Bubble colours change automatically.
- The story shot before the outro needs `end`: the cliffhanger question.
- Last shot has `"outro": true`: EXOTICCENZO alone, happy, same set, 1 short line.

## End of video
- next: set NEXT EPISODE TONIGHT for 10:00. Leave unset for 18:00, which says NEXT EPISODE TOMORROW.
- End: no credits. The video loops: after the end card it cuts back for 0.9s to the opening shot with the hook on screen, so the replay feels seamless. Make the hook and the last line connect (the last line can lead straight into the hook). credit_song is no longer used.
- promo: leave unset. Paid adverts are off.

## Other files
- `fans.json`: comments read, fan cast, ideas, removal requests. Fan characters go in `series.json` with their TikTok username as the name.
- `trends.json`: current trends mapped to the story. Use one when it fits. Never add copyrighted songs.

## Look from Episode 15
From Episode 15 the renderer switches to the illustrated cartoon style on its own (`illus_from: 15` in series.json): big-head stickmen in real clothes, close-ups on whoever is talking, 2-3 word caption chunks at the bottom with the spoken word highlighted. Scripts don't need a `style` field. Keep lines short and punchy so the captions read well.
