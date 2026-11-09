# Daily episode routine

One new episode per run, two runs a day. Episodes publish at 10:00 and 18:00 Africa/Harare on TikTok via Metricool brand 7957195.

Script format: copy `scripts/ep004.json`. Fields: ep, chapter, title, lesson, caption, shots[]. Each shot has set, cast (who, x, pose, face, mood), lines ([who, text, optional {mood, pose}]), and optional card and end.
- who: cenzo, clyde, nia (displays MTORIRO), zeke (displays SOLO), maya (displays JAMAL). New characters go in `series.json` and `voices.py`.
- sets: mansion, hotel, gameroom, plane, tokyo, paris, dubai, harare. Add new ones in `show.py` BUILDERS.
- poses: stand, walk, sit, seat, seat2, eat, game. Moods: neutral, happy, smug, shock, angry, focus.
- x between 200 and 850. Keep lines under 50 characters. Aim for 28-35 seconds.
- The last shot needs `end`: the cliffhanger question.

Rules: see `rules_for_daily_scripts` in `series.json`. EXOTICCENZO alone teaches and names the lesson.

End card: set `next` to NEXT EPISODE TONIGHT for a 10:00 episode. Leave it unset for an 18:00 episode, which says NEXT EPISODE TOMORROW.

Fans: `fans.json` tracks comments already read, the fan cast, ideas, and anyone who asked to be removed. A fan character is a `series.json` entry with their TikTok username as the name.

Outro: after the shot with `end`, add one last shot with `"outro": true`: EXOTICCENZO alone, happy, in the same set, with 1-2 short lines. Either thank viewers or tell a joke that fits that episode's lesson.

Trends: `trends.json` lists current trends mapped to the story. Use one when it fits naturally, as a scene or joke format. Never add copyrighted songs to the video file.

Music and credit: every video plays a freshly generated original trap beat. Set `credit_song` to a Future song whose mood or title fits the episode (for example Honest, Mask Off, Turn On the Lights, Worst Day, Magic, Tony Montana). Do not use the real recording or copy its melody. Do not reuse the same song within 7 episodes. The credit card is added automatically after the outro.

Paid service advert: switched OFF while the account grows. Do not set `promo` or mention paid services until Vincenzo says to turn it back on.
