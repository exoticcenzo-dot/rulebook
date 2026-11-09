#!/usr/bin/env python3
"""THE RULE BOOK: script-driven dialogue episodes.
usage: show.py still EP t1 t2.. | show.py render EP"""
import sys, os, json, math, random, subprocess, wave, textwrap
import numpy as np, cv2
import film as F
import engine as E
from film import W, H, FPS, clamp, ease, out, mix, line, circle, quad, text, POSES, pose_mix
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = HERE + "/out"
S = json.load(open(HERE + "/series.json")); CAST = S["characters"]
FLOOR = 1360
Z = 1.25
SETS = {}

def px(c): return tuple(int(v) for v in c)

def grad(top, bot, a=0, b=H):
    k = np.linspace(0, 1, b - a, dtype=np.float32)[..., None, None]
    g = np.clip(np.array(top, np.float32) * (1 - k) + np.array(bot, np.float32) * k, 0, 255)
    return np.repeat(g, W, axis=1)

def rect(i, x0, y0, x1, y1, c): cv2.rectangle(i, (int(x0), int(y0)), (int(x1), int(y1)), c, -1, cv2.LINE_AA)

def glow(i, s=26, k=.8):
    g = cv2.GaussianBlur(i, (0, 0), s); return cv2.addWeighted(i, 1, g, k, 0)

def window_pane(i, x, y, w, h, sky, frame=(70, 90, 110)):
    rect(i, x, y, x + w, y + h, sky)
    cv2.ellipse(i, (x + w // 2, y), (w // 2, w // 2), 0, 180, 360, sky, -1, cv2.LINE_AA)
    cv2.ellipse(i, (x + w // 2, y), (w // 2, w // 2), 0, 180, 360, frame, 6, cv2.LINE_AA)
    for a, b, c, d in ((x, y, x, y + h), (x + w, y, x + w, y + h), (x, y + h, x + w, y + h), (x + w // 2, y - w // 2, x + w // 2, y + h), (x, y + h // 2, x + w, y + h // 2)):
        cv2.line(i, (a, b), (c, d), frame, 6, cv2.LINE_AA)

def chandelier(i, x, y, c=(120, 220, 255), L=0):
    cv2.line(i, (x, 0), (x, y), (60, 90, 110), 4)
    cv2.ellipse(i, (x, y + 20), (120, 34), 0, 0, 180, (70, 150, 200), 8, cv2.LINE_AA)
    for k in range(-3, 4):
        circle(i, (x + k * 36, y + 26 + (9 - k * k) * 3), 12, c)

def sofa(i, x0, x1, y, col, dark):
    rect(i, x0, y - 340, x1, y - 70, col)
    for sx in range(x0 + 10, x1 - 40, (x1 - x0) // 3):
        rect(i, sx, y - 165, sx + (x1 - x0) // 3 - 14, y - 66, tuple(min(255, v + 18) for v in col))
    rect(i, x0 - 40, y - 262, x0 + 26, y - 18, dark); rect(i, x1 - 26, y - 262, x1 + 40, y - 18, dark)
    rect(i, x0 - 20, y - 18, x0 + 8, y, (40, 50, 60)); rect(i, x1 - 8, y - 18, x1 + 20, y, (40, 50, 60))

def base(top, bot): return np.clip(grad(top, bot), 0, 255).astype(np.uint8)

def mansion():
    i = base((46, 52, 74), (26, 30, 44))
    for x in range(0, W, 240): rect(i, x, 0, x + 6, FLOOR, (38, 44, 62))
    for x in (40, 390, 740): window_pane(i, x, 480, 300, 520, (62, 34, 20), (86, 118, 150))
    r = random.Random(2)
    for _ in range(40):
        x = r.choice((60, 410, 760)) + r.randint(0, 260); circle(i, (x, r.randint(440, 980)), 2, (230, 230, 200))
    i = glow(i, 24, .45); chandelier(i, 540, 170)
    i[FLOOR - 30:] = base((96, 110, 124), (34, 38, 48))[FLOOR - 30:]
    for x in range(-200, W + 200, 190): cv2.line(i, (x, FLOOR - 30), (int(x * 1.6 - 320), H), (60, 70, 82), 2, cv2.LINE_AA)
    rect(i, 0, FLOOR - 40, W, FLOOR - 30, (30, 36, 50))
    sofa(i, 160, 900, FLOOR, (62, 42, 120), (46, 30, 96))
    for y in (FLOOR - 150,): rect(i, 470, y + 60, 570, y + 110, (60, 60, 160))
    # plant and table lamp
    rect(i, 1, FLOOR - 120, 120, FLOOR - 30, (40, 60, 90))
    for a in range(-4, 5): cv2.ellipse(i, (60, FLOOR - 120), (22, 150), a * 18, 180, 360, (50, 110, 60), -1, cv2.LINE_AA)
    return i, None

def hotel():
    i = base((30, 42, 62), (20, 26, 34))
    for x in range(40, W, 200): rect(i, x, 300, x + 150, FLOOR - 280, (40, 58, 80))
    window_pane(i, 340, 500, 400, 430, (70, 34, 18), (120, 150, 180))
    r = random.Random(4)
    for _ in range(90):
        x = r.randint(350, 730); h = r.randint(760, 930); rect(i, x, h, x + 8, h + 12, (110, 190, 240))
    i = glow(i, 18, .4)
    chandelier(i, 220, 210); chandelier(i, 860, 210)
    i[FLOOR - 200:] = base((30, 28, 54), (14, 14, 26))[FLOOR - 200:]
    f = np.zeros((H, W, 4), np.uint8)
    t = 1170
    rect(f, 60, t, 1020, t + 34, (238, 240, 245, 255)); rect(f, 90, t + 34, 990, FLOOR + 90, (210, 216, 226, 255))
    for x, c in ((220, (80, 150, 240)), (430, (120, 200, 90)), (650, (70, 90, 230)), (860, (90, 200, 245))):
        cv2.ellipse(f, (x, t - 2), (88, 18), 0, 0, 360, (250, 250, 250, 255), -1, cv2.LINE_AA)
        cv2.ellipse(f, (x, t - 8), (46, 26), 0, 180, 360, c + (255,), -1, cv2.LINE_AA)
    for x in (330, 540, 750):
        rect(f, x - 8, t - 56, x + 8, t, (235, 235, 235, 255)); circle(f, (x, t - 72), 10, (100, 220, 255, 255))
    return i, f

def gameroom():
    i = base((54, 16, 34), (20, 8, 18))
    rect(i, 800, 660, 1060, 1090, (14, 12, 16)); rect(i, 812, 672, 1048, 1078, (140, 60, 30))
    r = random.Random(9)
    for k in range(9):
        h = r.randint(70, 330); rect(i, 826 + k * 24, 1040 - h, 842 + k * 24, 1040, (60, 230, 250) if k % 2 else (240, 120, 230))
    i = glow(i, 26, .9)
    cv2.line(i, (0, 470), (W, 470), (240, 100, 255), 8, cv2.LINE_AA); i = glow(i, 18, .6)
    for x, y, c in ((90, 560, (70, 200, 255)), (290, 610, (200, 90, 255)), (500, 560, (90, 230, 120))):
        rect(i, x, y, x + 150, y + 210, (30, 22, 38)); rect(i, x + 12, y + 12, x + 138, y + 198, c)
    i[FLOOR - 30:] = base((46, 22, 44), (10, 8, 14))[FLOOR - 30:]
    sofa(i, 80, 740, FLOOR, (120, 58, 38), (92, 44, 30))
    return i, None

def plane():
    i = base((180, 176, 170), (120, 118, 116))
    for x in range(40, W, 240):
        cv2.ellipse(i, (x + 90, 800), (62, 92), 0, 0, 360, (210, 150, 90), -1, cv2.LINE_AA)
        cv2.ellipse(i, (x + 90, 800), (62, 92), 0, 0, 360, (70, 70, 70), 7, cv2.LINE_AA)
    rect(i, 0, 410, W, 500, (150, 146, 140))
    i[FLOOR - 25:] = base((60, 50, 54), (30, 26, 30))[FLOOR - 25:]
    for x, d in ((250, 1), (730, -1)):
        bx = x - 110 * d
        rect(i, bx - 70, FLOOR - 620, bx + 70, FLOOR - 40, (120, 60, 40))
        rect(i, min(bx, x + 150 * d), FLOOR - 170, max(bx, x + 150 * d), FLOOR - 56, (140, 74, 50))
    return i, None

def tokyo():
    i = base((70, 26, 40), (20, 10, 20))
    r = random.Random(12); x = -20
    neon = [(255, 90, 230), (90, 230, 255), (90, 240, 120), (60, 110, 255)]
    while x < W:
        w = r.randint(130, 230); top = r.randint(260, 640)
        rect(i, x, top, x + w, FLOOR, (34, 22, 32))
        for wy in range(top + 26, FLOOR - 40, 46):
            for wx in range(x + 16, x + w - 20, 40):
                if r.random() < .45: rect(i, wx, wy, wx + 22, wy + 28, (70, 110, 150))
        c = r.choice(neon); sx = x + w - 40; sy = top + 60
        rect(i, sx, sy, sx + 36, sy + 300, (20, 16, 24))
        for k in range(5):
            rect(i, sx + 8, sy + 16 + k * 56, sx + 28, sy + 50 + k * 56, c)
        x += w + 8
    i = glow(i, 18, .9)
    rect(i, 0, FLOOR - 24, W, H, (24, 22, 28))
    for k in range(-2, 8):
        rect(i, 90 + k * 130, FLOOR + 90, 180 + k * 130, FLOOR + 120, (220, 220, 220))
    lamp = base((80, 70, 80), (10, 10, 14))[FLOOR:]
    i[FLOOR:] = cv2.addWeighted(i[FLOOR:], .7, lamp, .4, 0)
    return i, None

def paris():
    i = base((130, 80, 110), (60, 90, 170))
    pts = np.array([(540, 300), (505, 760), (420, 1250), (470, 1250), (530, 900), (550, 900), (610, 1250), (660, 1250), (575, 760)], np.int32)
    cv2.fillPoly(i, [pts], (30, 40, 60), cv2.LINE_AA)
    for y in (760, 1000): rect(i, 470, y, 610, y + 18, (30, 40, 60))
    r = random.Random(1); x = 0
    while x < W:
        w = r.randint(120, 200); top = r.randint(860, 1020); rect(i, x, top, x + w, FLOOR, (50, 66, 100))
        for wy in range(top + 26, FLOOR - 40, 62):
            for wx in range(x + 14, x + w - 24, 46): rect(i, wx, wy, wx + 20, wy + 34, (120, 180, 230))
        x += w + 2
    rect(i, 0, FLOOR - 24, W, H, (60, 66, 80))
    return i, None

def dubai():
    i = base((170, 100, 40), (120, 170, 240))
    cv2.circle(i, (820, 1010), 120, (120, 200, 255), -1, cv2.LINE_AA)
    for x, w, top in ((60, 70, 660), (190, 90, 500), (340, 60, 300), (450, 110, 700), (620, 80, 420), (770, 96, 620), (920, 100, 780)):
        pts = np.array([(x, FLOOR), (x, top + 60), (x + w // 2, top), (x + w, top + 60), (x + w, FLOOR)], np.int32)
        cv2.fillPoly(i, [pts], (70, 56, 50), cv2.LINE_AA)
        for wy in range(top + 80, FLOOR - 40, 34): rect(i, x + 10, wy, x + w - 10, wy + 8, (150, 190, 230))
    rect(i, 0, FLOOR - 24, W, H, (100, 150, 190))
    return i, None

def harare():
    i = base((200, 150, 100), (150, 200, 240))
    for x, w, top, c in ((30, 260, 760, (120, 120, 130)), (320, 200, 620, (100, 110, 124)), (560, 280, 800, (130, 120, 112)), (860, 200, 700, (108, 116, 120))):
        rect(i, x, top, x + w, FLOOR, c)
        for wy in range(top + 30, FLOOR - 40, 62):
            for wx in range(x + 18, x + w - 30, 54): rect(i, wx, wy, wx + 30, wy + 34, (60, 80, 100))
    for tx, sc in ((140, 1.0), (700, 1.2)):
        cv2.line(i, (tx, FLOOR), (tx, FLOOR - int(300 * sc)), (40, 60, 80), int(20 * sc))
        for a in range(-4, 5):
            cv2.ellipse(i, (tx + a * int(30 * sc), FLOOR - int(350 * sc) + a * a * 3), (int(90 * sc), int(52 * sc)), 0, 0, 360, (180, 80, 200), -1, cv2.LINE_AA)
    rect(i, 0, FLOOR - 24, W, H, (70, 90, 120))
    return i, None

BUILDERS = dict(mansion=mansion, hotel=hotel, gameroom=gameroom, plane=plane, tokyo=tokyo, paris=paris, dubai=dubai, harare=harare)

def get_set(n):
    if n not in SETS: SETS[n] = BUILDERS[n]()
    return SETS[n]

# seated world height: seat level relative to the floor line
SEAT = 130
POSES_X = {
    "sit": dict(hip=(0, -135), neck=(10, -282), head=(16, -342), hF=(70, -176), hB=(46, -170), fF=(112, 0), fB=(82, 0)),
    "seat": dict(hip=(0, -130), neck=(14, -278), head=(24, -338), hF=(96, -254), hB=(70, -240), fF=(90, 0), fB=(70, 0)),
    "seat2": dict(hip=(0, -135), neck=(10, -282), head=(16, -342), hF=(70, -176), hB=(46, -170), fF=(112, 0), fB=(82, 0)),
    "eat": dict(hip=(0, -130), neck=(16, -278), head=(30, -336), hF=(76, -300), hB=(84, -238), fF=(90, 0), fB=(70, 0)),
    "game": dict(hip=(0, -135), neck=(22, -278), head=(42, -332), hF=(96, -212), hB=(78, -208), fF=(112, 0), fB=(82, 0)),
}

class Cam2:
    z = Z
    def __init__(s, ox, fy): s.ox, s.fy = ox, fy
    def p(s, x, y): return (s.ox + x * Z, s.fy + y * Z)

def draw_char(canvas, c, t, speaking, shot_t, mouth=False):
    L = CAST[c["who"]]
    pose = c["pose"]
    P = POSES.get(pose) or POSES_X.get(pose) or POSES["stand"]
    P = {k: v for k, v in P.items()}
    if pose == "walk":
        P = dict(POSES["stand"]); w = math.sin(shot_t * 11) * 46
        P["fF"] = (w, 0); P["fB"] = (-w, 0); P["hF"] = (-w * .6, -176); P["hB"] = (w * .6, -176)
    if pose == "eat":
        P["hF"] = (70, -290 + math.sin(shot_t * 7) * 28)
    if pose == "game":
        j = math.sin(shot_t * 19) * 5; P["hF"] = (P["hF"][0] + j, P["hF"][1]); P["hB"] = (P["hB"][0] - j, P["hB"][1])
    if speaking:
        b = math.sin(shot_t * 10)
        P["head"] = (P["head"][0], P["head"][1] + b * 4)
        if pose == "stand":
            P["hF"] = (86 + b * 12, -262 + b * 30)
    pw, ph = 640, 860
    patch = np.zeros((ph, pw, 3), np.uint8)
    ox, fy = pw // 2, ph - 30
    m = c.get("mood", "neutral")
    if speaking:
        m = "shock" if mouth else "neutral"
    hand = E.fig(patch, Cam2(ox, fy), 0, 0, P, L, t, m)
    if pose == "game":
        rect(patch, hand[0] - 18, hand[1] - 14, hand[0] + 58, hand[1] + 26, (36, 36, 44))
    if pose == "eat":
        cv2.line(patch, (int(hand[0]), int(hand[1])), (int(hand[0] + 26), int(hand[1] - 38)), (210, 210, 210), 6, cv2.LINE_AA)
    if c["face"] == "l":
        patch = cv2.flip(patch, 1)
    g = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY).astype(np.float32)
    a = np.clip(g / 12, 0, 1)[..., None]
    x0 = int(c["x"] - ox); y0 = int(FLOOR - fy)
    xa, xb = max(0, x0), min(W, x0 + pw); ya, yb = max(0, y0), min(H, y0 + ph)
    if c.get("_alpha", 1) <= 0: return
    sub = canvas[ya:yb, xa:xb].astype(np.float32); pa = patch[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32)
    al = a[ya - y0:yb - y0, xa - x0:xb - x0]
    canvas[ya:yb, xa:xb] = np.clip(sub * (1 - al) + pa * al, 0, 255).astype(np.uint8)

def duration(tx): return .65 + len(tx) / 16.0

def trap_bed(N, sr, seed):
    """Original dark trap instrumental. Generated fresh per episode; no existing song or melody."""
    r = np.random.default_rng(1000 + seed)
    bpm = 132 + int(r.integers(0, 17)); step = 60 / bpm / 4
    root = 41.2 * 2 ** (int(r.integers(0, 7)) / 12)
    scale = [0, 3, 5, 7, 10]
    out_ = np.zeros(N, np.float32)
    def put(at, x, g=1):
        i = int(at * sr); j = min(N, i + len(x))
        if 0 <= i < N: out_[i:j] += x[:j - i] * g
    def env(d, k):
        u = np.arange(int(d * sr)) / sr; return u, np.exp(-u * k)
    bars = int(N / sr / (step * 16)) + 2
    bass = [int(r.choice(scale)) for _ in range(4)]
    bass[0] = 0
    pat808 = [0, 3, 6, 10, 11, 14]
    bell = [12 + int(r.choice(scale)) for _ in range(8)]
    bell_steps = sorted(int(v) for v in r.choice(32, 8, replace=False))
    for b in range(bars):
        t0 = b * 16 * step
        note = bass[b % 4]
        for st_ in pat808:
            if r.random() < .12: continue
            d = step * 3.4; u, e = env(d, 2.2)
            f = root * 2 ** (note / 12)
            gl = np.cumsum(np.full(len(u), f)) / sr
            w = np.tanh(2.4 * np.sin(2 * np.pi * gl)) * e
            put(t0 + st_ * step, w.astype(np.float32), .85)
        u, e = env(.2, 26)
        nz = r.normal(0, 1, len(u)).astype(np.float32)
        snare = (nz * .8 + np.sin(2 * np.pi * 190 * u) * .5) * e
        put(t0 + 8 * step, snare, .55)
        roll = int(r.integers(0, 4))
        for h in range(16):
            sub = 3 if h in (6, 14) and roll else 1
            for q in range(sub):
                u, e = env(.05, 150)
                hat = r.normal(0, 1, len(u)).astype(np.float32) * e
                hat = np.diff(hat, prepend=0)
                put(t0 + (h + q / sub) * step, hat, .26 if h % 2 == 0 else .15)
        if b % 2 == 0:
            for k, st2 in enumerate(bell_steps):
                u, e = env(.7, 5)
                f = root * 8 * 2 ** (bell[k] / 12)
                w = (np.sin(2 * np.pi * f * u) + .4 * np.sin(2 * np.pi * f * 2.76 * u)) * e
                put(t0 + st2 * step, w.astype(np.float32), .13)
    return out_ / max(1e-6, np.abs(out_).max()) * .8

class Show:
    def __init__(s, ep):
        s.e = json.load(open(f"{HERE}/scripts/ep{ep:03d}.json")); s.n = ep
        t = 0; s.tl = []; s.ev = []; s.info = {}; s.sp = []
        for sh in s.e["shots"]:
            a = t; lines = []
            for ln in sh["lines"]:
                x = V.say(ln[0], ln[1]); au = len(x) / 44100
                d = au + .32; s.info[t] = (au, V.envelope(x))
                s.sp.append((t + .08, x)); lines.append((t, t + d, ln)); t += d
            card = end = None
            if sh.get("card"):
                x = V.say("cenzo", sh["card"]); d = max(2.2, len(x) / 44100 + .55)
                s.sp.append((t + .2, x)); card = (t, t + d); t += d
            if sh.get("end"):
                x = V.say("narrator", sh["end"]); s.next = s.e.get("next", "NEXT EPISODE TOMORROW"); y = V.say("narrator", s.next)
                s.sp.append((t + .15, x)); s.sp.append((t + .25 + len(x) / 44100, y))
                d = max(2.8, (len(x) + len(y)) / 44100 + .75); end = (t, t + d); t += d
            s.tl.append(dict(a=a, b=t, sh=sh, lines=lines, card=card, end=end))
        if s.e.get("promo"):
            x = V.say("cenzo", "NEED A VIDEO LIKE THIS FOR YOUR BUSINESS? MESSAGE ME. WE MAKE THEM.")
            s.sp.append((t + .25, x)); d = max(4.5, len(x) / 44100 + 1.0)
            s.tl.append(dict(a=t, b=t + d, sh=dict(set=s.e["shots"][-1]["set"], cast=[], lines=[], promo=True), lines=[], card=None, end=None)); t += d
        if s.e.get("credit_song"):
            x = V.say("cenzo", "RESPECT TO FUTURE. REGARDS, EXOTICCENZO.")
            s.sp.append((t + .25, x)); d = max(4.2, len(x) / 44100 + 1.4)
            s.tl.append(dict(a=t, b=t + d, sh=dict(set=s.e["shots"][-1]["set"], cast=[], lines=[], credit=True), lines=[], card=None, end=None)); t += d
        s.D = t + .15

    def shot_at(s, t):
        for x in s.tl:
            if x["a"] <= t < x["b"]: return x
        return s.tl[-1]

    def frame(s, t):
        x = s.shot_at(t); sh = x["sh"]; st = t - x["a"]
        back, front = get_set(sh["set"])
        cur = None
        for a, b, ln in x["lines"]:
            if a <= t < b: cur = (a, b, ln)
        # poses change as lines land
        cast = {c["who"]: dict(c) for c in sh["cast"]}
        for a, b, ln in x["lines"]:
            if a <= t and len(ln) > 2:
                cast[ln[0]].update(ln[2])
        img = back.copy()
        spk = cur[2][0] if cur else None
        order = list(cast.values())
        for c in order:
            talk = bool(cur) and c["who"] == spk and t - cur[0] < s.info[cur[0]][0] + .08
            mouth = False
            if talk:
                env = s.info[cur[0]][1]; k = int(clamp(t - cur[0] - .08, 0, 999) * 30)
                mouth = k < len(env) and env[k] > .045
            draw_char(img, c, t, talk, st, mouth)
        if front is not None:
            a = front[..., 3:].astype(np.float32) / 255
            img = np.clip(img * (1 - a) + front[..., :3] * a, 0, 255).astype(np.uint8)
        if sh.get("prop") == "book":
            f = cast["clyde"]; bx = int(f["x"]) - 120; by = FLOOR - 330
            rect(img, bx, by, bx + 150, by + 100, (40, 80, 140)); rect(img, bx + 12, by + 8, bx + 140, by + 92, (70, 130, 200))
            rect(img, bx + 60, by + 34, bx + 95, by + 62, (120, 220, 255))
        # slow push in
        z = 1 + .035 * clamp(st / max(.1, x["b"] - x["a"]))
        M = np.array([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * FLOOR]], np.float32)
        img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR)
        img = (img.astype(np.float32) * F.vignette()).astype(np.uint8)
        A = (50, 190, 255)
        shade = np.ones((H, 1, 1), np.float32); shade[:300] = np.linspace(.38, 1, 300, dtype=np.float32)[..., None, None]
        img = (img.astype(np.float32) * shade).astype(np.uint8)
        text(img, f"EP {s.n}  ·  {s.e['title']}", 505, 165, 34, col=A, track=3, glow=.3)
        if cur:
            s.bubble(img, cur, t, cast, A)
        if x["card"] and x["card"][0] <= t < x["card"][1]:
            k = window(t, x["card"][0], x["card"][1], .1, .15)
            img = (img * (1 - .72 * k)).astype(np.uint8)
            text(img, sh["card"], 505, 640, 104, col=A, alpha=k)
        if x["end"] and x["end"][0] <= t:
            k = ease((t - x["end"][0]) / .2)
            img = (img * (1 - .78 * k)).astype(np.uint8)
            text(img, sh["end"], 505, 560, 92, alpha=k, n=typed(sh["end"], t, x["end"][0] + .05, 30))
            if t > x["end"][0] + .9:
                text(img, s.next, 505, 760, 44, col=A, alpha=ease((t - x["end"][0] - .9) / .2), track=4)
                text(img, S["handle"], 505, 850, 52, alpha=ease((t - x["end"][0] - 1.1) / .2), track=5)
        if sh.get("promo"):
            k = ease(st / .2)
            img = (img * (1 - .84 * k)).astype(np.uint8)
            text(img, "NEED A VIDEO\nLIKE THIS FOR\nYOUR BUSINESS?", 505, 420, 84, alpha=k)
            text(img, "ANIMATED ADS AND EXPLAINERS", 505, 800, 38, col=A, alpha=k, track=2, glow=.25)
            text(img, "WITH CHARACTER VOICES", 505, 860, 38, col=A, alpha=k, track=2, glow=.25)
            text(img, "MESSAGE " + S["handle"], 505, 985, 52, alpha=k, track=3)
        if sh.get("credit"):
            k = ease(st / .25)
            img = (img * (1 - .86 * k)).astype(np.uint8)
            text(img, "REGARDS,", 505, 410, 46, alpha=k, track=4)
            text(img, "EXOTICCENZO", 505, 480, 74, col=A, alpha=k, track=4)
            text(img, "BEAT INSPIRED BY", 505, 660, 34, alpha=k, track=4, glow=.2)
            text(img, '"' + s.e["credit_song"].upper() + '"', 505, 720, 52, alpha=k, track=2)
            text(img, "FUTURE", 505, 830, 86, col=A, alpha=k, track=8)
            text(img, "NAYVADIUS DEMUN WILBURN", 505, 950, 38, alpha=k, track=2, glow=.2)
            text(img, "AKA PLUTO · FUTURE HENDRIX · MEATHEAD", 505, 1010, 28, alpha=k, track=1, glow=.2)
            text(img, "ORIGINAL INSTRUMENTAL", 505, 1090, 26, alpha=k, track=3, glow=.15)
        dd = min(abs(t - b["a"]) for b in s.tl[1:]) if len(s.tl) > 1 else 9
        if dd < .07: img = (img * (dd / .07)).astype(np.uint8)
        return img

    def bubble(s, img, cur, t, cast, A):
        a, b, ln = cur
        who, tx = ln[0], ln[1]
        c = cast[who]; L = CAST[who]
        lines = textwrap.wrap(tx, 17)
        n = len(lines); fs = 50; lh = int(fs * 1.2)
        cw = 30.5
        wd = int(max(len(l) for l in lines) * cw) + 96; ht = lh * n + 92
        seated = c["pose"] != "stand" and c["pose"] != "walk"
        hy = FLOOR - (360 if seated else 412) * Z - 88
        cx = clamp(c["x"], wd / 2 + 56, 930 - wd / 2)
        bot = min(hy, 980); y0 = int(bot - ht); x0 = int(cx - wd / 2)
        p = out((t - a) / .12)
        ov = img.copy()
        col = (250, 250, 252)
        cv2.rectangle(ov, (x0 + 26, y0), (x0 + wd - 26, y0 + ht), col, -1, cv2.LINE_AA)
        cv2.rectangle(ov, (x0, y0 + 26), (x0 + wd, y0 + ht - 26), col, -1, cv2.LINE_AA)
        for q in ((x0 + 26, y0 + 26), (x0 + wd - 26, y0 + 26), (x0 + 26, y0 + ht - 26), (x0 + wd - 26, y0 + ht - 26)):
            cv2.circle(ov, q, 26, col, -1, cv2.LINE_AA)
        tipx = int(clamp(c["x"] + (24 if c["face"] == "r" else -24), x0 + 40, x0 + wd - 40))
        tri = np.array([(tipx - 26, y0 + ht - 3), (tipx + 26, y0 + ht - 3), (tipx, int(min(hy + 46, y0 + ht + 62)))], np.int32)
        cv2.fillConvexPoly(ov, tri, col, cv2.LINE_AA)
        name = L["name"]; nw = int(len(name) * 21 + 34)
        nx = x0 + 22
        cv2.rectangle(ov, (nx, y0 - 26), (nx + nw, y0 + 30), px(L["accent"]), -1, cv2.LINE_AA)
        img[:] = cv2.addWeighted(ov, p, img, 1 - p, 0)
        if p < .5: return
        text(img, name, nx + nw / 2, y0 - 22, 30, col=(20, 20, 24), glow=0, track=2)
        chars = "".join(lines); typed_n = (t - a - .08) / max(.3, s.info[a][0]) * len(chars) * 1.15
        text(img, "\n".join(lines), cx, y0 + 42, fs, col=(24, 22, 28), n=clamp(typed_n, 0, len(chars)), track=0, glow=0)

    def audio(s, path):
        sr = 44100; N = int(s.D * sr); t = np.arange(N) / sr
        rng = np.random.default_rng(s.n)
        m = np.zeros(N, np.float32); fx = np.zeros(N, np.float32)
        def add(b, a, x, g=1):
            i = int(a * sr); j = min(N, i + len(x))
            if 0 <= i < N: b[i:j] += x[:j - i] * g
        def kick(d=.3):
            q = np.arange(int(d * sr)) / sr
            return np.sin(2 * np.pi * (46 * q + 7 * (1 - np.exp(-q * 34)))) * np.exp(-q * 13)
        m += trap_bed(N, sr, s.n)
        for x in s.tl:
            if x["card"]: add(fx, x["card"][0], kick(.9), 1)
            if x["end"]: add(fx, x["end"][0], kick(1.0), 1)
            add(fx, x["a"], kick(.4), .4)
        sp = np.zeros(N, np.float32)
        for a, y in s.sp: add(sp, a, y)
        z = m * .15 + fx * .16 + sp; z *= np.minimum(1, (s.D - t) / .3)
        z = np.tanh(z * 1.05) / np.tanh(1.05) * .94
        pcm = (np.stack([z, z], 1) * 32767).astype(np.int16)
        with wave.open(path, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())

from film import window, typed
import voices as V

def render(ep):
    s = Show(ep); b = f"{OUT}/ep{ep:03d}"
    v, a, tmp, fin = b + ".v.mp4", b + ".wav", b + ".tmp.mp4", b + ".mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", v], stdin=subprocess.PIPE)
    for f in range(int(s.D * FPS)):
        p.stdin.write(s.frame(f / FPS).tobytes())
    p.stdin.close(); assert p.wait() == 0
    s.audio(a)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-i", v, "-i", a, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", tmp])
    os.replace(tmp, fin); os.remove(v); os.remove(a); print(fin, round(s.D, 1), "s", flush=True)

if __name__ == "__main__":
    if sys.argv[1] == "still":
        s = Show(int(sys.argv[2]))
        for ts in sys.argv[3:]:
            cv2.imwrite(f"{OUT}/v{sys.argv[2]}_{ts}.jpg", s.frame(float(ts)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    elif sys.argv[1] == "duration":
        print(Show(int(sys.argv[2])).D)
    else:
        render(int(sys.argv[2]))
