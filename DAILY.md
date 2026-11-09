# Daily episode routine

One new episode per run, two runs a day. Episodes publish at 10:00 and 18:00 Africa/Harare on TikTok via Metricool brand 7957195. Story and content rules live in `rules_for_daily_scripts` and `masterplan` in `series.json`.

## Script format
Copy `scripts/ep005.json`. Fields: ep, chapter, title, lesson, hook, caption, credit_song, optional next, and shots[]. Each shot has set, cast (who, x, pose, face, mood), lines ([who, text, optional {mood, pose}]), and optional card, end, outro.
- who: cenzo, clyde, nia (displays MTORIRO), zeke (displays SOLO), maya (displays JAMAL). New characters go in `series.json` and `voices.py`.
- sets: harare, bulawayo, home, mansion, hotel, gameroom, gym, desk, plane, train, ship, tokyo, paris, dubai. Build every new country before using it, with its landmarks, shops and street life. Add new ones in `show.py` BUILDERS.
- poses: stand, walk, sit, seat, seat2, eat, game, lift, curl (gym: lift or curl; desk: seat). Moods: neutral, happy, smug, shock, angry, focus.
- x between 200 and 850.
- Background people appear automatically and differ each episode. For a bigger crowd set `crowd` on a shot, for example 40; Episode 100 uses 120 or more on outdoor sets.
- hook: 2 lines at most, under 14 characters per line.
- card: the rule, spoken by EXOTICCENZO.
- The story shot before the outro needs `end`: the cliffhanger question.
- Last shot has `"outro": true`: EXOTICCENZO alone, happy, same set, 1 short line.

## End of video
- next: set NEXT EPISODE TONIGHT for 10:00. Leave unset for 18:00, which says NEXT EPISODE TOMORROW.
- credit_song: a clean-titled Future song whose mood or title fits (Honest, Mask Off, Turn On the Lights, Worst Day, Magic, Tony Montana). Do not reuse within 7 episodes. The beat is original; never use his recording or copy its melody. The credit card is automatic.
- promo: leave unset. Paid adverts are off.

## Other files
- `fans.json`: comments read, fan cast, ideas, removal requests. Fan characters go in `series.json` with their TikTok username as the name.
- `trends.json`: current trends mapped to the story. Use one when it fits. Never add copyrighted songs.
