#!/usr/bin/env python3
"""Episode engine. Post N -> arc (N-1)//3, episode (N-1)%3. Arcs wrap around the bank.
usage: engine.py still POST t1 t2.. | engine.py post POST | engine.py poster"""
import sys, os, json, math, random, subprocess, wave
import numpy as np, cv2
import film as F
from film import W, H, FPS, FLOOR, BH, BW, clamp, ease, out, mix, Cam, line, circle, quad, ik, POSES, pose_mix, text, window, typed, ipt, slot

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE + "/out"
BANK = json.load(open(HERE + "/stories.json"))
ARCS = BANK["arcs"]
DUR = [14.0, 13.0, 16.0]
CY = .44
ROWS = 30

THEMES = {
    "dusk": dict(top=(34, 14, 26), bot=(10, 8, 12), accent=(120, 200, 255), scene="city", ray=(34, 58, 72)),
    "market": dict(top=(30, 20, 8), bot=(8, 8, 6), accent=(130, 230, 110), scene="chart", ray=(30, 62, 28)),
    "neon": dict(top=(40, 8, 34), bot=(14, 4, 12), accent=(255, 120, 235), scene="grid", ray=(70, 26, 66)),
    "sunrise": dict(top=(16, 26, 58), bot=(10, 8, 14), accent=(110, 200, 255), scene="hills", ray=(30, 66, 90)),
}
SKINS = {
    "brick": [((170, 196, 214), (205, 226, 240), (120, 142, 160))],
    "candle": [((120, 200, 90), (170, 240, 140), (70, 130, 50)), ((130, 214, 100), (180, 246, 150), (76, 140, 56))],
    "book": [((205, 90, 200), (240, 150, 235), (130, 50, 130)), ((90, 180, 245), (150, 220, 255), (50, 110, 160)), ((240, 190, 90), (255, 225, 150), (160, 120, 50))],
    "gold": [((60, 180, 235), (130, 225, 255), (30, 110, 160))],
}
_bg = {}


def background(name):
    if name in _bg:
        return _bg[name]
    T = THEMES[name]
    k = np.linspace(0, 1, H, dtype=np.float32)[..., None, None]
    b = np.ones((H, W, 3), np.float32) * (np.array(T["top"], np.float32) * (1 - k) + np.array(T["bot"], np.float32) * k)
    img = b.astype(np.uint8)
    r = random.Random(11)
    if T["scene"] == "city":
        x = -10
        while x < W:
            w = r.randint(70, 150); h = r.randint(170, 520)
            cv2.rectangle(img, (x, FLOOR - h), (x + w, FLOOR), (30, 18, 24), -1)
            for wy in range(FLOOR - h + 22, FLOOR - 16, 38):
                for wx in range(x + 14, x + w - 12, 30):
                    if r.random() < .22:
                        cv2.rectangle(img, (wx, wy), (wx + 11, wy + 17), (70, 120, 160), -1)
            x += w + r.randint(2, 18)
    elif T["scene"] == "chart":
        y = 840
        for x in range(30, W, 46):
            d = r.randint(-70, 66)
            o, c = y, y + d
            col = (46, 42, 110) if d > 0 else (50, 112, 42)
            cv2.line(img, (x, min(o, c) - 28), (x, max(o, c) + 28), col, 2, cv2.LINE_AA)
            cv2.rectangle(img, (x - 13, min(o, c)), (x + 13, max(o, c) + 2), col, -1)
            y = int(clamp(c, 620, 1090))
    elif T["scene"] == "grid":
        for i in range(-9, 10):
            cv2.line(img, (W // 2 + i * 34, 780), (W // 2 + i * 150, FLOOR), (92, 30, 88), 2, cv2.LINE_AA)
        y = 800.0; g = 12.0
        while y < FLOOR:
            cv2.line(img, (0, int(y)), (W, int(y)), (92, 30, 88), 2, cv2.LINE_AA); y += g; g *= 1.25
        cv2.circle(img, (W // 2, 770), 180, (130, 60, 160), -1, cv2.LINE_AA)
        cv2.rectangle(img, (0, 770), (W, 960), (14, 6, 16), -1)
    else:
        cv2.circle(img, (W // 2, 960), 230, (70, 140, 230), -1, cv2.LINE_AA)
        for base, col in ((960, (24, 34, 58)), (1050, (16, 20, 34))):
            pts = [(0, FLOOR)]
            for x in range(0, W + 90, 90):
                pts.append((x, base + r.randint(-90, 80)))
            pts.append((W, FLOOR))
            cv2.fillPoly(img, [np.array(pts, np.int32)], col, cv2.LINE_AA)
    img[FLOOR:] = (5, 5, 7)
    img = cv2.GaussianBlur(img, (0, 0), 3).astype(np.float32) * F.vignette()
    _bg[name] = np.clip(img, 0, 255).astype(np.uint8)
    return _bg[name]


def dim(c, k=.62): return tuple(int(v * k) for v in c)


def fig(img, cam, x, y, P, L, t, mood="neutral"):
    z = cam.z
    suit = tuple(L["suit"]); ac = tuple(L["accent"]); bk = dim(suit)
    Wp = lambda q: cam.p(x + q[0], y + q[1])
    hip, neck = P["hip"], P["neck"]
    sh = (mix(hip[0], neck[0], .93), mix(hip[1], neck[1], .93))
    gear = L.get("gear", [])
    mb = L.get("muscle", 0)
    if "cape" in gear:
        wv = math.sin(t * 7) * 18
        quad(img, [Wp(sh), Wp((sh[0] + 12, sh[1])), Wp((hip[0] - 42 + wv * .4, hip[1] + 90)), Wp((hip[0] - 118 + wv, hip[1] + 70))], ac)
    for n, root, l1, l2, b in (("fB", hip, 96, 96, -1), ("hB", sh, 84, 84, 1)):
        j = ik(root, P[n], l1, l2, b)
        line(img, Wp(root), Wp(j), (25 + 15 * mb) * z, bk); line(img, Wp(j), Wp(P[n]), (22 + 7 * mb) * z, bk)
    line(img, Wp(hip), Wp(neck), (40 + 10 * mb) * z, suit)
    if mb > 0:
        sw, hw = 26 + 40 * mb, 22 + 4 * mb
        quad(img, [Wp((sh[0] - sw, sh[1])), Wp((sh[0] + sw, sh[1])), Wp((hip[0] + hw, hip[1])), Wp((hip[0] - hw, hip[1]))], suit)
        circle(img, Wp((sh[0] - sw, sh[1] + 6)), (20 + 14 * mb) * z, suit); circle(img, Wp((sh[0] + sw, sh[1] + 6)), (20 + 14 * mb) * z, suit)
        cut = dim(suit, .62); tw = max(1.5, 3.5 * z)
        lerp = lambda k: (mix(sh[0], hip[0], k), mix(sh[1], hip[1], k))
        if mb >= .3:
            cx, cy = lerp(.24)
            line(img, Wp((cx - sw * .72, cy)), Wp((cx + sw * .72, cy)), tw, cut); line(img, Wp(lerp(.05)), Wp(lerp(.24)), tw, cut)
        if mb >= .6:
            line(img, Wp(lerp(.3)), Wp(lerp(.92)), tw, cut)
            for k in (.46, .62, .78):
                ax, ay = lerp(k); w_ = 20 + 6 * mb
                line(img, Wp((ax - w_, ay)), Wp((ax + w_, ay)), tw, cut)
    # belt and tie
    line(img, Wp((hip[0] - 18, hip[1])), Wp((hip[0] + 18, hip[1])), 12 * z, ac)
    if "tie" in gear:
        n2 = (mix(neck[0], hip[0], .55), mix(neck[1], hip[1], .55))
        line(img, Wp((neck[0], neck[1] + 12)), Wp(n2), 13 * z, ac)
    if "scarf" in gear:
        line(img, Wp((neck[0] - 18, neck[1] + 10)), Wp((neck[0] + 20, neck[1] + 8)), 20 * z, ac)
        wv = math.sin(t * 8) * 10
        line(img, Wp((neck[0] - 12, neck[1] + 14)), Wp((neck[0] - 74, neck[1] + 34 + wv)), 15 * z, ac)
    hc, R = Wp(P["head"]), 46 * z
    hair = L.get("hair")
    if hair == "afro":
        circle(img, (hc[0] - 6 * z, hc[1] - 14 * z), 66 * z, dim(ac, .55))
    circle(img, hc, R, (236, 240, 245))
    if hair == "spiky":
        for i in range(-3, 4):
            a = -math.pi / 2 + i * .36
            b1 = (hc[0] + R * .9 * math.cos(a - .2), hc[1] + R * .9 * math.sin(a - .2))
            b2 = (hc[0] + R * .9 * math.cos(a + .2), hc[1] + R * .9 * math.sin(a + .2))
            tip = (hc[0] + R * 1.5 * math.cos(a), hc[1] + R * 1.5 * math.sin(a))
            quad(img, [b1, tip, b2, hc], ac)
    elif hair == "neat":
        quad(img, [(hc[0] - R, hc[1] - 8 * z), (hc[0] - R * .7, hc[1] - R), (hc[0] + R * .8, hc[1] - R), (hc[0] - R * .2, hc[1] - R * .45)], dim(ac, .7))
    elif hair == "cap":
        quad(img, [(hc[0] - R, hc[1] - 14 * z), (hc[0] - R * .7, hc[1] - R * 1.05), (hc[0] + R * .7, hc[1] - R * 1.05), (hc[0] + R, hc[1] - 14 * z)], ac)
        line(img, (hc[0] + R * .7, hc[1] - 14 * z), (hc[0] + R * 1.65, hc[1] - 9 * z), 11 * z, dim(ac, .75))
    elif hair == "beanie":
        quad(img, [(hc[0] - R, hc[1] - 12 * z), (hc[0] - R * .75, hc[1] - R * 1.1), (hc[0] + R * .75, hc[1] - R * 1.1), (hc[0] + R, hc[1] - 12 * z)], dim(ac, .8))
        circle(img, (hc[0], hc[1] - R * 1.2), 13 * z, ac)
    elif hair == "bun":
        circle(img, (hc[0] - 8 * z, hc[1] - R * 1.2), 23 * z, dim(ac, .75))
        quad(img, [(hc[0] - R, hc[1] - 4 * z), (hc[0] - R * .7, hc[1] - R), (hc[0] + R * .7, hc[1] - R), (hc[0] - R * .1, hc[1] - R * .5)], dim(ac, .75))
    elif hair == "crown":
        pts = [(-.8, -.75), (-.85, -1.5), (-.4, -1.05), (0, -1.65), (.4, -1.05), (.85, -1.5), (.8, -.75)]
        p2 = np.array([ipt((hc[0] + a * R, hc[1] + b * R)) for a, b in pts], np.int32)
        cv2.fillPoly(img, [p2], (60, 200, 245), cv2.LINE_AA, 3)
    if "headphones" in gear:
        cv2.ellipse(img, (int(hc[0]), int(hc[1])), (int(R * 1.06), int(R * 1.06)), 0, 180, 360, ac, max(1, int(9 * z)), cv2.LINE_AA)
        circle(img, (hc[0] - R * .98, hc[1]), 16 * z, ac)
    # face
    e1, e2 = (hc[0] + 10 * z, hc[1] - 6 * z), (hc[0] + 31 * z, hc[1] - 6 * z)
    ink = (22, 22, 26)
    if L.get("red_eyes"):
        for e_ in (e1, e2):
            circle(img, e_, 10.5 * z, (70, 70, 235))
            circle(img, (e_[0] + 1 * z, e_[1] + 2 * z), 4.8 * z, ink)
            quad(img, [(e_[0] - 12 * z, e_[1] - 13 * z), (e_[0] + 12 * z, e_[1] - 13 * z), (e_[0] + 12 * z, e_[1] - 3 * z), (e_[0] - 12 * z, e_[1] - 3 * z)], (236, 240, 245))
    else:
        circle(img, e1, 5.8 * z, ink); circle(img, e2, 5.8 * z, ink)
    br = {"focus": 5, "angry": 7, "shock": -6, "smug": -2}.get(mood, 0) * z
    line(img, (e1[0] - 9 * z, e1[1] - 15 * z - br * .2), (e1[0] + 9 * z, e1[1] - 15 * z + br), 4 * z, ink)
    line(img, (e2[0] - 9 * z, e2[1] - 15 * z + br), (e2[0] + 9 * z, e2[1] - 15 * z - br * .2), 4 * z, ink)
    mc = (hc[0] + 20 * z, hc[1] + 20 * z)
    if mood in ("happy", "smug"):
        cv2.ellipse(img, ipt(mc), (int(13 * z * 8), int(9 * z * 8)), 0, 10, 170, ink, max(1, int(4 * z)), cv2.LINE_AA, 3)
    elif mood == "shock":
        circle(img, mc, 8 * z, ink)
    else:
        line(img, (mc[0] - 9 * z, mc[1]), (mc[0] + 9 * z, mc[1]), 4 * z, ink)
    if "glasses" in gear:
        for e in (e1, e2):
            cv2.circle(img, ipt(e), int(10.5 * z * 8), ac, max(1, int(4 * z)), cv2.LINE_AA, 3)
    for n, root, l1, l2, b in (("fF", hip, 96, 96, -1), ("hF", sh, 84, 84, 1)):
        j = ik(root, P[n], l1, l2, b)
        line(img, Wp(root), Wp(j), (28 + 18 * mb) * z, suit); line(img, Wp(j), Wp(P[n]), (24 + 9 * mb) * z, suit)
        circle(img, Wp(P[n]), 15 * z, ac if n == "hF" else suit)
    return Wp(P["hF"])


class Ep:
    def __init__(s, post):
        s.post = post
        s.arc_i = (post - 1) // 3
        s.arc = ARCS[s.arc_i % len(ARCS)]
        s.ep = (post - 1) % 3
        s.D = DUR[s.ep]
        s.T = THEMES[s.arc["theme"]]
        s.A = s.T["accent"]
        s.skin = SKINS[s.arc["skin"]]
        s.crew = [ARCS[i % len(ARCS)]["active"] for i in range(max(0, s.arc_i - 2), s.arc_i)]

    def brk(s, img, cam, x, y, i, ang=0, w=BW - 6, h=BH - 6):
        c, top, side = s.skin[i % len(s.skin)]
        F.brick(img, cam, x, y, w=w, h=h, ang=ang, col=c, top=top, side=side)
        if s.arc["skin"] == "candle":
            p, q = cam.p(x, y - h - 12), cam.p(x, y - h)
            line(img, p, q, 4 * cam.z, side)

    # wall state: (count, cycle phase, fallen progress)
    def state(s, t):
        if s.ep == 0:
            if t < 3:
                return 0, None
            k = (t - 3.2) / CY
            return (15, None) if k >= 15 or k < 0 and False else (max(0, int(k)), k % 1 if k >= 0 else None)
        if s.ep == 1:
            if t < 5:
                return 24, None
            k = (t - 5) / CY
            return (24, None) if k >= 5 else (19 + int(k), k % 1)
        return int(mix(24, ROWS * 3, ease(t / 3))), None

    def zoom(s, t):
        return mix(1, .5, ease(t / 3)) if s.ep == 2 else 1.0

    def fall_list(s):
        return [(23, 545, 2.4, 0), (22, 508, -3, .05), (21, 590, 3.4, .11), (20, 472, -2.5, .16), (19, 628, 2.8, .2)]

    def fall_pose(s, i, lx, sp, d, t):
        u = (t - 1.2 - d) / .72
        if u < 0:
            return None
        sx, sy, a = slot(i); u1 = clamp(u)
        y = mix(sy, 0, u1 * u1)
        if u > 1:
            y = -22 * math.sin(math.pi * clamp((u - 1) / .3))
        return mix(sx, lx, u1), y, a + sp * u1

    def world(s, t):
        z = s.zoom(t); cam = Cam(z)
        A, Pv, Ac = s.A, s.arc["passive"], s.arc["active"]
        img = np.zeros((H, W, 3), np.uint8)
        n, ph = s.state(t)
        finished = s.ep == 2 and t > 2.85
        if finished:
            k = out((t - 2.85) / .7); c = cam.p(708, -ROWS * BH - 190)
            r2 = np.zeros_like(img)
            for i in range(14):
                a = i / 14 * math.tau + (t - 3) * .22; d = 1300; e = .1
                pts = [c, (c[0] + d * math.cos(a - e), c[1] + d * math.sin(a - e)), (c[0] + d * math.cos(a + e), c[1] + d * math.sin(a + e))]
                cv2.fillConvexPoly(r2, np.array([ipt(p) for p in pts], np.int32), s.T["ray"], cv2.LINE_AA, 3)
            r2 = cv2.GaussianBlur(r2, (0, 0), 14); r2[FLOOR:] = 0
            img = cv2.add(img, (r2 * k).astype(np.uint8))
        for x, y in F.PILE:
            s.brk(img, cam, x, y, 0, w=62, h=46)
        c0, t0, sd = s.skin[0]
        F.brick(img, cam, 298, 0, w=120, h=66, col=c0, top=t0, side=sd)
        for i in range(n):
            if s.ep == 1 and i >= 19 and t >= 1.2 and t < 5 + (i - 19 + 1) * CY:
                continue
            x, y, a = slot(i); s.brk(img, cam, x, y, i, a)
        if s.ep == 1:
            n2 = clamp(int((t - 5) / CY), 0, 5) if t >= 5 else 0
            for k, (i, lx, sp, d) in enumerate(s.fall_list()):
                if t >= 5 and k < n2:
                    continue
                st = s.fall_pose(i, lx, sp, d, t)
                if st is None:
                    x, y, a = slot(i)
                    if t >= 1.2: s.brk(img, cam, x, y, i, a)
                else:
                    s.brk(img, cam, st[0], st[1], i, st[2])
        # passive
        rub = math.sin(t * 9.5) * 34 if s.arc["passive_mode"] == "polish" else math.sin(t * 2) * 6
        kk = ease((t - 2.2) / .5) if s.ep == 0 else 1
        Pk = dict(POSES["kneel"])
        Pk["hF"] = (Pk["hF"][0] + rub, Pk["hF"][1]); Pk["hB"] = (Pk["hB"][0] + rub * .8, Pk["hB"][1])
        if s.arc["passive_mode"] == "phone":
            Pk["hF"] = (92 + rub, -196); Pk["hB"] = (74 + rub, -184); Pk["head"] = (86, -260)
        mood = "smug" if s.ep == 1 and 3 <= t < 5 else "focus"
        hand = fig(img, cam, 120, 0, pose_mix(POSES["stand"], Pk, kk), Pv, t, mood)
        if kk > .6:
            if s.arc["passive_mode"] == "polish":
                q = (hand[0], hand[1] + 16 * z); wd, hg = 58 * z, 18 * z
                quad(img, [(q[0] - wd, q[1] - hg), (q[0] + wd, q[1] - hg), (q[0] + wd, q[1] + hg), (q[0] - wd, q[1] + hg)], tuple(Pv["accent"]))
            else:
                q = (hand[0] + 16 * z, hand[1] - 18 * z); wd, hg = 21 * z, 38 * z
                quad(img, [(q[0] - wd, q[1] - hg), (q[0] + wd, q[1] - hg), (q[0] + wd, q[1] + hg), (q[0] - wd, q[1] + hg)], (255, 240, 200))
        # active
        if s.ep < 2:
            mood2 = "focus"
            if ph is not None:
                P2 = pose_mix(POSES["place"], POSES["pick"], ease(ph / .3)) if ph < .3 else pose_mix(POSES["pick"], POSES["place"], ease((ph - .3) / .3)) if ph < .6 else POSES["place"]
            else:
                P2 = POSES["stand"]
                if s.ep == 1 and t >= 1.35:
                    k = ease((t - 1.35) / .25) * (1 - ease((t - 4.7) / .3))
                    P2 = pose_mix(P2, POSES["ouch"], k); mood2 = "shock" if t < 4.7 else "focus"
                elif s.ep == 0 and t < 3:
                    mood2 = "happy"
            h2 = fig(img, cam, 500, 0, P2, Ac, t, mood2)
            if ph is not None:
                sx, sy, a = slot(n)
                if .3 <= ph < .6:
                    s.brk(img, cam, (h2[0] - 700) / z + 708, (h2[1] - FLOOR) / z + 24, n)
                elif ph >= .6:
                    u = (ph - .6) / .4
                    s.brk(img, cam, mix(578, sx, u), mix(-368, sy, u) - math.sin(math.pi * u) * 90, n, a * u + (1 - u) * .4)
        else:
            y = -(n // 3) * BH
            P3 = POSES["stand"]; b = 0
            if finished:
                P3 = pose_mix(P3, POSES["cheer"], out((t - 2.85) / .35)); b = abs(math.sin((t - 3) * 7)) * 18
            fig(img, cam, 708, y - b, P3, Ac, t, "happy" if finished else "focus")
            if finished:
                r = random.Random(3)
                for _ in range(48):
                    g = r.uniform(-math.pi, 0); sp = r.uniform(180, 560); tt = (t - 3 + r.uniform(0, 1.8)) % 1.8
                    c0_ = cam.p(708, -ROWS * BH - 200)
                    circle(img, (c0_[0] + math.cos(g) * sp * tt, c0_[1] + math.sin(g) * sp * tt + 340 * tt * tt), 6 * clamp(1.4 - tt), A if r.random() < .6 else (255, 255, 255))
                for j, L in enumerate(s.crew):
                    jump = abs(math.sin((t + j) * 6)) * 16
                    fig(img, cam, -380 + j * 215, -jump, POSES["cheer"], L, t, "happy")
        g = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 9), (W, H))
        img = cv2.addWeighted(img, 1, g, .34, 0)
        out_ = cv2.add(background(s.arc["theme"]), img).astype(np.float32)
        rh = H - FLOOR if H - FLOOR < FLOOR else FLOOR
        src = cv2.GaussianBlur(img[FLOOR - rh:FLOOR][::-1].astype(np.float32), (0, 0), 2.2)
        fade = np.power(np.linspace(1, 0, rh, dtype=np.float32), 2)[..., None, None] * .34
        out_[FLOOR:FLOOR + rh] = np.clip(out_[FLOOR:FLOOR + rh] + src * fade, 0, 255)
        cv2.line(out_, (0, FLOOR), (W, FLOOR), tuple(float(v) * .35 for v in A), 2, cv2.LINE_AA)
        return np.clip(out_, 0, 255).astype(np.uint8)

    def stamp(s, img, t, a=1):
        text(img, f"{s.arc['title']}  ·  PART {s.ep + 1}/3", 505, 172, 30, col=s.A, alpha=a, track=4, glow=.3)

    def names(s, img, t, a):
        P, C = s.arc["passive"], s.arc["active"]
        text(img, P["name"], 215, 600, 62, alpha=a, col=tuple(P["accent"]), track=6)
        text(img, P["role"], 215, 680, 25, alpha=a, track=2, glow=.2)
        text(img, C["name"], 690, 600, 62, alpha=a, col=tuple(C["accent"]), track=6)
        text(img, C["role"], 690, 680, 25, alpha=a, track=2, glow=.2)

    def counters(s, img, n, a):
        u = s.arc["unit"]
        text(img, "1", 215, 1270, 110, alpha=a)
        text(img, u, 215, 1405, 32, alpha=a, track=6, glow=.3)
        text(img, str(n), 690, 1270, 110, alpha=a, col=s.A)
        text(img, u if n == 1 else u + "S", 690, 1405, 32, alpha=a, track=6, glow=.3)

    def big(s, img, t, str_, a, b, y=240, size=88, col=(255, 255, 255)):
        if a <= t < b:
            text(img, str_, 505, y, size, col=col, n=typed(str_, t, a + .05, 30), alpha=window(t, a, b, .12, .15))

    def frame(s, t):
        arc = s.arc; D = s.D
        if s.ep == 2 and t >= 7:
            if not hasattr(s, "_end"):
                s._end = (cv2.GaussianBlur(s.world(6.9), (0, 0), 7) * .17).astype(np.uint8)
            img = s._end.copy()
        else:
            img = s.world(t)
        n = s.state(t)[0]
        if s.ep < 2 or t >= 7: s.stamp(img, t, window(t, 0 if s.ep < 2 else 7, D, .2, .2))
        if s.ep == 0:
            s.big(img, t, arc["hook"], 0, 3.2, size=92)
            s.names(img, t, window(t, .7, D, .3, .2))
            s.big(img, t, arc["ep1"][0], 3.2, 6.8)
            s.big(img, t, arc["ep1"][1], 6.8, 10.3, col=s.A)
            s.big(img, t, arc["tease1"], 10.3, 14, col=(120, 120, 255))
            if t > 3.2: s.counters(img, n, window(t, 3.2, D, .25, .2))
        elif s.ep == 1:
            s.names(img, t, window(t, 0, D, .2, .2))
            shown = 19 if 1.8 <= t < 5 else n
            s.counters(img, shown, window(t, 0, D, .2, .2))
            text(img, "DAY 30", 505, 220, 44, col=s.A, alpha=window(t, 0, 1.2, .1, .15))
            s.big(img, t, arc["fall"], 1.3, 3.1, size=100, col=(90, 90, 255))
            s.big(img, t, arc["taunt"], 3.1, 5)
            s.big(img, t, arc["rebuild"], 5, 9.8, col=s.A)
            s.big(img, t, arc["tease2"], 9.8, 13)
        else:
            if t < 7:
                a = window(t, 0, 7, .25, .2)
                text(img, "DAY\n365", 262, 330, 118, alpha=a, col=s.A)
                if t > 3.3:
                    text(img, arc["same"], 262, 700, 76, n=typed(arc["same"], t, 3.4), alpha=a)
                for j, L in enumerate(s.crew):
                    if t > 3.2: text(img, L["name"], 700 + .5 * (-380 + j * 215 - 708), 905, 26, col=tuple(L["accent"]), alpha=a, track=2, glow=.25)
            else:
                M = arc["moral"]
                s.big(img, t, M[0], 7, 10.2, y=600, size=100)
                if 10.2 <= t < 12.6:
                    text(img, M[1], 505, 620, 124, col=s.A, alpha=window(t, 10.2, 12.6, .08, .15))
                s.big(img, t, arc["cta"], 12.6, D, y=470, size=112)
                if t > 13.2:
                    nx = ARCS[(s.arc_i + 1) % len(ARCS)]
                    a = window(t, 13.2, D, .25, .2)
                    text(img, f"NEXT STORY: {nx['passive']['name']} VS {nx['active']['name']}", 505, 790, 36, alpha=a, track=2, glow=.25)
                    text(img, BANK["handle"], 505, 910, 58, col=s.A, alpha=a, track=6)
        if t > D - .15:
            img = (img * clamp((D - t) / .15)).astype(np.uint8)
        return img

    def audio(s, path):
        sr = 44100; N = int(s.D * sr); t = np.arange(N) / sr
        rng = np.random.default_rng(s.post)
        m = np.zeros(N, np.float32); fx = np.zeros(N, np.float32)
        root = 110 * 2 ** (((s.arc_i * 5) % 12 - 4) / 12)
        ratios = [(1, 1.2, 1.5), (.8, 1, 1.2), (1.2, 1.5, 1.8), (.75, 1.125, 1.5)]
        for b in range(int(s.D / 3.5) + 1):
            st = b * 3.5; e = min(s.D, st + 3.9); id_ = (t >= st) & (t < e); tt = t[id_] - st
            env = np.minimum(tt / .7, 1) * np.minimum((e - t[id_]) / .7, 1)
            for r in ratios[b % 4]:
                m[id_] += env * (.05 * np.sin(2 * np.pi * root * r * tt) + .02 * np.sin(2 * np.pi * root * r * 2.004 * tt))
        def add(b, a, x, g=1):
            i = int(a * sr); j = min(N, i + len(x))
            if 0 <= i < N: b[i:j] += x[:j - i] * g
        def kick(d=.3):
            q = np.arange(int(d * sr)) / sr
            return np.sin(2 * np.pi * (46 * q + 7 * (1 - np.exp(-q * 34)))) * np.exp(-q * 13)
        def thunk(f=170):
            q = np.arange(int(.14 * sr)) / sr
            nz = np.convolve(rng.normal(0, 1, len(q)), np.ones(9) / 9, "same")
            return (np.sin(2 * np.pi * f * q) * .8 + nz * .9) * np.exp(-q * 34)
        bt = 60 / (88 + (s.arc_i % 4) * 5)
        q = .0
        while q < s.D - .4:
            add(m, q, kick(), .42); q += bt
        if s.ep == 0:
            for i in range(15): add(fx, 3.2 + (i + 1) * CY, thunk(rng.uniform(150, 195)), .55)
            add(fx, 10.3, kick(.8), 1)
        elif s.ep == 1:
            for i, (_, _, _, d) in enumerate(s.fall_list()): add(fx, 1.92 + d, thunk(95 + i * 18), .9)
            add(fx, 1.9, kick(.5), .8)
            for i in range(5): add(fx, 5 + (i + 1) * CY, thunk(rng.uniform(150, 195)), .55)
        else:
            id_ = t < 3; u = t[id_] / 3
            fx[id_] += rng.normal(0, 1, id_.sum()).astype(np.float32) * u ** 2.5 * .1 + np.sin(2 * np.pi * (60 + 240 * u) * t[id_]) * u ** 2 * .09
            add(fx, 3, kick(.9), 1); add(fx, 7, kick(.8), .8); add(fx, 10.2, kick(1), 1); add(fx, 12.6, kick(.6), .7)
        x = m * .9 + fx; x *= np.minimum(1, (s.D - t) / .4)
        x = np.tanh(x / np.abs(x).max() * 1.25) / np.tanh(1.25) * .92
        pcm = (np.stack([x, x], 1) * 32767).astype(np.int16)
        with wave.open(path, "wb") as f:
            f.setnchannels(2); f.setsampwidth(2); f.setframerate(sr); f.writeframes(pcm.tobytes())


def render(post):
    e = Ep(post); name = f"post{post:03d}_{e.arc['id']}_part{e.ep + 1}"
    v, a, tmp, fin = [f"{OUT}/{name}{x}" for x in (".v.mp4", ".wav", ".tmp.mp4", ".mp4")]
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", v], stdin=subprocess.PIPE)
    for f in range(int(e.D * FPS)):
        p.stdin.write(e.frame(f / FPS).tobytes())
    p.stdin.close(); assert p.wait() == 0
    e.audio(a)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", v, "-i", a, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp])
    os.replace(tmp, fin); os.remove(v); os.remove(a)
    print(fin, "|", e.arc["captions"][e.ep], flush=True)


def poster():
    img = np.zeros((1920, 1080, 3), np.uint8); img[:] = (9, 8, 11)
    text(img, "THE CAST", 540, 70, 88, col=(120, 200, 255))
    text(img, "A NEW STORY EVERY 3 POSTS", 540, 180, 32, track=3, glow=.2)
    cast = [(a["passive"], a) for a in ARCS] + [(a["active"], a) for a in ARCS]
    cast = [x for i in range(len(ARCS)) for x in (cast[i], cast[i + len(ARCS)])]
    cam = Cam(.58)
    class C:
        z = .58
        def __init__(s, ox, fy): s.ox, s.fy = ox, fy
        def p(s, x, y): return (s.ox + x * .58, s.fy + y * .58)
    for i, (L, a) in enumerate(cast):
        col, row = i % 2, i // 2
        x, y = 280 + col * 520, 560 + row * 400
        fig(img, C(x, y), 0, 0, POSES["stand"], L, 1.0, "happy")
        text(img, L["name"], x, y + 22, 48, col=tuple(L["accent"]), track=4)
        text(img, L["role"], x, y + 92, 23, track=2, glow=.2)
    img = img[:1920]
    cv2.imwrite(f"{OUT}/cast_poster.png", img)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "still":
        e = Ep(int(sys.argv[2]))
        for ts in sys.argv[3:]:
            cv2.imwrite(f"{OUT}/s{sys.argv[2]}_{ts}.jpg", e.frame(float(ts)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    elif c == "post":
        render(int(sys.argv[2]))
    elif c == "poster":
        poster()
