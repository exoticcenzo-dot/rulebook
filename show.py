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

def desk():
    i = base((34, 22, 18), (12, 10, 12))
    for mx, my in ((130, 560), (430, 520), (730, 560)):
        rect(i, mx - 8, my - 8, mx + 268, my + 208, (30, 30, 34)); rect(i, mx, my, mx + 260, my + 200, (22, 16, 12))
        r = random.Random(mx); y_ = my + 100
        for k in range(16):
            x_ = mx + 12 + k * 15; dy = r.randint(-30, 30); c = (70, 70, 235) if dy > 0 else (90, 215, 110)
            cv2.line(i, (x_ + 4, min(y_, y_ + dy) - 10), (x_ + 4, max(y_, y_ + dy) + 10), c, 1, cv2.LINE_AA)
            rect(i, x_, min(y_, y_ + dy), x_ + 8, max(y_, y_ + dy) + 2, c); y_ = int(clamp(y_ + dy, my + 28, my + 172))
    i = glow(i, 20, .7)
    i[FLOOR - 30:] = base((40, 34, 38), (12, 12, 14))[FLOOR - 30:]
    f = np.zeros((H, W, 4), np.uint8)
    rect(f, 40, 1120, 1040, 1160, (70, 80, 92, 255)); rect(f, 80, 1160, 130, FLOOR, (46, 50, 58, 255)); rect(f, 950, 1160, 1000, FLOOR, (46, 50, 58, 255))
    for kx in (240, 690): rect(f, kx, 1104, kx + 170, 1120, (42, 42, 50, 255))
    return i, f

def gym():
    i = base((40, 42, 46), (20, 20, 24))
    for x in range(60, W, 330):
        rect(i, x, 380, x + 280, 1010, (86, 84, 76)); rect(i, x + 8, 388, x + 272, 1002, (120, 112, 96))
        cv2.line(i, (x + 40, 960), (x + 170, 430), (150, 142, 124), 8, cv2.LINE_AA)
    for lx in (220, 860):
        rect(i, lx - 150, 240, lx + 150, 254, (235, 245, 255))
    i = glow(i, 22, .6)
    i[FLOOR - 30:] = base((58, 56, 60), (18, 18, 22))[FLOOR - 30:]
    rect(i, 30, FLOOR - 260, 70, FLOOR - 30, (52, 54, 60)); rect(i, 960, FLOOR - 260, 1000, FLOOR - 30, (52, 54, 60)); rect(i, 30, FLOOR - 196, 1000, FLOOR - 182, (52, 54, 60))
    for dx in range(100, 960, 96):
        cv2.line(i, (dx - 24, FLOOR - 210), (dx + 24, FLOOR - 210), (120, 120, 128), 8, cv2.LINE_AA)
        for e_ in (dx - 24, dx + 24): circle(i, (e_, FLOOR - 210), 14, (46, 46, 54))
    return i, None

BUILDERS = dict(gym=gym, desk=desk, mansion=mansion, hotel=hotel, gameroom=gameroom, plane=plane, tokyo=tokyo, paris=paris, dubai=dubai, harare=harare)


def label(i, tx, x, y, sc, col, bg=None):
    (w, h), _ = cv2.getTextSize(tx, cv2.FONT_HERSHEY_DUPLEX, sc, max(1, int(sc * 2)))
    if bg is not None: rect(i, x - 12, y - h - 12, x + w + 12, y + 12, bg)
    cv2.putText(i, tx, (x, y), cv2.FONT_HERSHEY_DUPLEX, sc, col, max(1, int(sc * 2)), cv2.LINE_AA)

def shopfront(i, x, w, top, wall, name, awn):
    rect(i, x, top, x + w, FLOOR, wall)
    label(i, name, x + 14, top + 58, .95, (30, 30, 34), (235, 235, 225))
    for wx in range(x + 18, x + w - 70, 92):
        rect(i, wx, top + 110, wx + 72, FLOOR - 130, (95, 80, 60)); rect(i, wx + 4, top + 114, wx + 68, FLOOR - 134, (150, 130, 90))
    for ax in range(x, x + w, 34):
        quad(i, [(ax, top + 78), (ax + 34, top + 78), (ax + 42, top + 120), (ax + 8, top + 120)], awn if (ax - x) // 34 % 2 == 0 else (235, 235, 235))
    rect(i, x + w - 76, FLOOR - 190, x + w - 18, FLOOR, (46, 64, 92))

def kombi(i, x, y):
    rect(i, x, y - 110, x + 300, y - 22, (235, 235, 240)); rect(i, x, y - 60, x + 300, y - 40, (170, 90, 30))
    for k in range(4): rect(i, x + 16 + k * 70, y - 100, x + 74 + k * 70, y - 66, (120, 90, 60))
    for e_ in (x + 60, x + 240): circle(i, (e_, y - 18), 25, (24, 24, 28)); circle(i, (e_, y - 18), 11, (150, 150, 158))

def jacaranda(i, tx, sc):
    cv2.line(i, (tx, FLOOR), (tx, FLOOR - int(330 * sc)), (40, 60, 86), int(22 * sc))
    r = random.Random(tx)
    for _ in range(26):
        cv2.circle(i, (tx + r.randint(-140, 140), FLOOR - int((330 + r.randint(0, 150)) * sc)), r.randint(30, 62), (190 + r.randint(-20, 20), 90, 165), -1, cv2.LINE_AA)

def powerline(i):
    for px_ in (70, 720):
        cv2.line(i, (px_, FLOOR), (px_, 420), (50, 56, 66), 12); cv2.line(i, (px_ - 60, 450), (px_ + 60, 450), (50, 56, 66), 8)
    cv2.line(i, (0, 470), (W, 470), (40, 44, 50), 3, cv2.LINE_AA); cv2.line(i, (0, 500), (W, 492), (40, 44, 50), 3, cv2.LINE_AA)

def road(i, base_col=(82, 96, 112)):
    rect(i, 0, FLOOR - 26, W, H, base_col)
    rect(i, 0, FLOOR - 26, W, FLOOR + 40, (150, 158, 166))
    for k in range(-1, 9): rect(i, 60 + k * 170, FLOOR + 130, 160 + k * 170, FLOOR + 148, (235, 235, 230))

def harare():
    i = base((210, 165, 110), (170, 210, 245))
    for bx, w, h in ((120, 150, 660), (300, 130, 560), (470, 180, 720), (690, 140, 610)):
        rect(i, bx, FLOOR - h, bx + w, FLOOR, (172, 164, 150))
        for wy in range(FLOOR - h + 24, FLOOR - 320, 54):
            for wx in range(bx + 14, bx + w - 24, 40): rect(i, wx, wy, wx + 24, wy + 32, (120, 106, 84))
    x = -10
    for n_, w, c, a in (("TUCKSHOP", 260, (110, 170, 215), (40, 40, 200)), ("SALON", 210, (170, 200, 150), (150, 60, 150)), ("BAKERY", 230, (135, 190, 225), (30, 140, 230)), ("HARDWARE", 290, (150, 170, 190), (40, 140, 60)), ("BUTCHERY", 260, (130, 150, 200), (40, 40, 180))):
        shopfront(i, x, w, FLOOR - 360, c, n_, a); x += w
    jacaranda(i, 140, .95); jacaranda(i, 880, 1.1); powerline(i); road(i); kombi(i, 690, FLOOR + 10)
    label(i, "HARARE", 410, 320, 1.6, (255, 255, 255))
    return i, None

def bulawayo():
    i = base((225, 185, 130), (150, 205, 245))
    x = -10
    for n_, w, c in (("GENERAL DEALER", 370, (160, 200, 225)), ("TAILOR", 240, (140, 175, 205)), ("CAFE", 240, (170, 210, 180)), ("CHEMIST", 300, (195, 200, 150))):
        rect(i, x, FLOOR - 470, x + w, FLOOR, c); label(i, n_, x + 16, FLOOR - 410, .9, (35, 35, 40))
        rect(i, x, FLOOR - 340, x + w, FLOOR - 316, (235, 235, 230))
        for px_ in range(x + 24, x + w, 80): rect(i, px_, FLOOR - 316, px_ + 12, FLOOR, (235, 235, 230))
        for wx in range(x + 46, x + w - 40, 80): rect(i, wx, FLOOR - 280, wx + 46, FLOOR - 120, (95, 80, 62))
        x += w
    for tx in (190, 620, 990):
        cv2.line(i, (tx, FLOOR), (tx, FLOOR - 420), (54, 72, 92), 14)
        for a in range(0, 360, 40):
            cv2.ellipse(i, (tx, FLOOR - 430), (120, 26), a, 0, 180, (60, 130, 70), -1, cv2.LINE_AA)
    road(i, (96, 116, 140)); label(i, "BULAWAYO", 370, 340, 1.5, (255, 255, 255))
    return i, None

def train():
    i = base((132, 138, 142), (92, 96, 100))
    for x in range(40, W, 260):
        rect(i, x, 560, x + 200, 860, (190, 170, 130)); rect(i, x + 6, 566, x + 194, 854, (205, 190, 150))
        pts = np.array([(x + 6, 780), (x + 70, 690), (x + 130, 740), (x + 194, 670), (x + 194, 854), (x + 6, 854)], np.int32)
        cv2.fillPoly(i, [pts], (70, 120, 80), cv2.LINE_AA)
    rect(i, 0, 470, W, 500, (58, 58, 64))
    for x in range(30, W, 120): cv2.line(i, (x, 500), (x, 540), (150, 150, 158), 4); cv2.ellipse(i, (x, 550), (16, 12), 0, 0, 360, (150, 150, 158), 4, cv2.LINE_AA)
    i[FLOOR - 25:] = base((70, 58, 50), (32, 28, 26))[FLOOR - 25:]
    for x in (240, 760):
        rect(i, x - 110, FLOOR - 560, x + 110, FLOOR - 50, (40, 90, 150)); rect(i, x - 110, FLOOR - 172, x + 130, FLOOR - 60, (56, 110, 170))
    return i, None

def ship():
    i = base((230, 180, 120), (200, 170, 140))
    rect(i, 0, 980, W, FLOOR - 120, (150, 110, 60))
    r = random.Random(4)
    for _ in range(80):
        x = r.randint(0, W); y = r.randint(990, FLOOR - 140); cv2.line(i, (x, y), (x + r.randint(20, 60), y), (205, 165, 110), 2, cv2.LINE_AA)
    cv2.circle(i, (830, 960), 90, (150, 225, 255), -1, cv2.LINE_AA)
    for k in range(7):
        x = r.randint(60, W - 60); y = r.randint(420, 760); cv2.ellipse(i, (x, y), (22, 12), 0, 180, 360, (245, 245, 245), 3, cv2.LINE_AA); cv2.ellipse(i, (x + 42, y), (22, 12), 0, 180, 360, (245, 245, 245), 3, cv2.LINE_AA)
    rect(i, 0, FLOOR - 120, W, H, (120, 150, 180))
    for x in range(-20, W, 110): cv2.line(i, (x, FLOOR - 120), (x, FLOOR - 230), (235, 235, 235), 8)
    cv2.line(i, (0, FLOOR - 230), (W, FLOOR - 230), (235, 235, 235), 8); cv2.line(i, (0, FLOOR - 175), (W, FLOOR - 175), (235, 235, 235), 5)
    cv2.circle(i, (90, FLOOR - 170), 44, (40, 40, 220), 16, cv2.LINE_AA)
    return i, None

def home():
    i = base((60, 96, 130), (36, 56, 80))
    window_pane(i, 360, 500, 360, 390, (205, 170, 120), (235, 235, 235))
    rect(i, 300, 400, 360, 930, (40, 40, 190)); rect(i, 720, 400, 780, 930, (40, 40, 190))
    for x, y, w, h in ((60, 480, 180, 240), (830, 480, 190, 230)):
        rect(i, x, y, x + w, y + h, (70, 90, 110)); rect(i, x + 12, y + 12, x + w - 12, y + h - 12, (150, 195, 225))
    rect(i, 60, 790, 240, 900, (60, 80, 110))
    label(i, "HOME", 465, 455, 1.2, (240, 240, 240))
    i[FLOOR - 30:] = base((80, 110, 140), (30, 40, 56))[FLOOR - 30:]
    sofa(i, 160, 900, FLOOR, (60, 130, 170), (42, 100, 135))
    return i, None

def alley():
    i = base((30, 26, 22), (10, 10, 12))
    for x, w, h in ((-10, 300, 900), (280, 250, 780), (520, 270, 960), (780, 320, 860)):
        rect(i, x, FLOOR - h, x + w, FLOOR, (40, 44, 50))
        for k in range(40):
            r_ = random.Random(x * k); bx, by = r_.randint(x, x + w - 50), r_.randint(FLOOR - h, FLOOR - 60); rect(i, bx, by, bx + 44, by + 20, (46 + r_.randint(0, 14), 50, 58))
        for wy in range(FLOOR - h + 60, FLOOR - 240, 150): rect(i, x + 60, wy, x + 130, wy + 80, (22, 24, 28)); rect(i, x + 60, wy + 76, x + 130, wy + 80, (70, 70, 74))
    cv2.circle(i, (560, 700), 240, (40, 70, 110), -1, cv2.LINE_AA); i = cv2.GaussianBlur(i, (0, 0), 2)
    rect(i, 540, 520, 552, FLOOR, (30, 30, 34)); circle(i, (546, 510), 18, (120, 210, 255))
    rect(i, 780, FLOOR - 150, 930, FLOOR - 28, (40, 58, 56)); rect(i, 780, FLOOR - 150, 930, FLOOR - 134, (60, 80, 78))
    for x in (120, 640): rect(i, x, FLOOR - 92, x + 76, FLOOR - 28, (34, 38, 44))
    rect(i, 0, FLOOR - 26, W, H, (26, 28, 32))
    return i, None

def villa():
    i = base((200, 150, 95), (170, 205, 235))
    rect(i, 80, 700, 1000, FLOOR - 26, (236, 240, 244)); quad(i, [(40, 700), (1040, 700), (920, 560), (160, 560)], (70, 90, 130))
    for x in (160, 400, 640, 830): rect(i, x, 780, x + 120, 1090, (120, 130, 110)); rect(i, x + 8, 788, x + 112, 1082, (190, 170, 120))
    for x in range(110, 1000, 120): rect(i, x, 1120, x + 14, FLOOR - 26, (245, 245, 248))
    for tx in (50, 1040):
        for k in range(5): cv2.ellipse(i, (tx, FLOOR - 120 - k * 90), (56 - k * 8, 64), 0, 0, 360, (50, 110, 60), -1, cv2.LINE_AA)
    rect(i, 0, FLOOR - 26, W, H, (90, 130, 90))
    rect(i, 0, FLOOR + 120, W, H, (150, 158, 165))
    return i, None

BUILDERS.update(alley=alley, villa=villa, harare=harare, bulawayo=bulawayo, train=train, ship=ship, home=home)

def get_set(n):
    if n not in SETS: SETS[n] = BUILDERS[n]()
    return SETS[n]

# seated world height: seat level relative to the floor line
SEAT = 130
POSES_X = {
    "sit": dict(hip=(0, -135), neck=(10, -282), head=(16, -342), hF=(70, -176), hB=(46, -170), fF=(112, 0), fB=(82, 0)),
    "seat": dict(hip=(0, -130), neck=(14, -278), head=(24, -338), hF=(96, -254), hB=(70, -240), fF=(90, 0), fB=(70, 0)),
    "lift": dict(hip=(0, -176), neck=(2, -322), head=(6, -382), hF=(78, -470), hB=(-70, -470), fF=(42, 0), fB=(-42, 0)),
    "curl": dict(hip=(0, -176), neck=(4, -322), head=(10, -382), hF=(56, -300), hB=(40, -176), fF=(34, 0), fB=(-34, 0)),
    "seat2": dict(hip=(0, -135), neck=(10, -282), head=(16, -342), hF=(70, -176), hB=(46, -170), fF=(112, 0), fB=(82, 0)),
    "eat": dict(hip=(0, -130), neck=(16, -278), head=(30, -336), hF=(76, -300), hB=(84, -238), fF=(90, 0), fB=(70, 0)),
    "game": dict(hip=(0, -135), neck=(22, -278), head=(42, -332), hF=(96, -212), hB=(78, -208), fF=(112, 0), fB=(82, 0)),
}


SKIN = [(52, 74, 102), (40, 58, 84), (66, 92, 128), (34, 48, 70), (84, 116, 156), (120, 158, 205)]
CLOTH = [(60, 60, 200), (190, 120, 40), (70, 170, 90), (40, 170, 230), (150, 60, 150), (215, 215, 220), (50, 50, 60), (30, 110, 200), (120, 200, 200), (100, 90, 180)]

def npc(i, x, y, sc, skin, shirt, pants, phase, kind="walk", dir_=1, hat=None):
    """A background person. y = feet, sc = size."""
    leg = 72 * sc; torso = 92 * sc; hd = 22 * sc; th = max(3, 15 * sc)
    hip = (x, y - leg * 1.05); nk = (x, hip[1] - torso)
    if kind == "walk":
        w = math.sin(phase) * 32 * sc
        lf, rf, la, ra = (x + w, y), (x - w, y), (x - w * .8, hip[1] - 8 * sc), (x + w * .8, hip[1] - 8 * sc)
    elif kind == "run":
        w = math.sin(phase * 1.6) * 42 * sc
        lf, rf, la, ra = (x + w, y - abs(w) * .2), (x - w, y - abs(w) * .2), (x - w, nk[1] + 40 * sc), (x + w, nk[1] + 40 * sc)
    elif kind == "stand":
        lf, rf, la, ra = (x - 15 * sc, y), (x + 15 * sc, y), (x - 26 * sc, hip[1]), (x + 26 * sc, hip[1])
    elif kind == "press":
        v = (math.sin(phase) + 1) / 2 * 42 * sc
        lf, rf, la, ra = (x - 22 * sc, y), (x + 22 * sc, y), (x - 42 * sc, nk[1] - 34 * sc - v), (x + 42 * sc, nk[1] - 34 * sc - v)
    elif kind == "squat":
        v = (math.sin(phase) + 1) / 2 * 34 * sc
        hip = (x, hip[1] + v); nk = (x, hip[1] - torso)
        lf, rf, la, ra = (x - 28 * sc, y), (x + 28 * sc, y), (x - 34 * sc, nk[1] + 2), (x + 34 * sc, nk[1] + 2)
    elif kind == "sit":
        hip = (x, y); nk = (x, y - torso); lf, rf = (x + 30 * sc * dir_, y + 22 * sc), (x + 20 * sc * dir_, y + 22 * sc)
        v = math.sin(phase) * 5 * sc
        la, ra = (x + 34 * sc * dir_, nk[1] + 44 * sc + v), (x + 24 * sc * dir_, nk[1] + 48 * sc)
    else:
        lf, rf, la, ra = (x, y), (x, y), (x + 26 * sc, nk[1] + 34 * sc), (x - 24 * sc, hip[1])
    line(i, hip, lf, th, pants); line(i, hip, rf, th, pants)
    line(i, hip, nk, th * 1.5, shirt)
    line(i, nk, la, th * .8, shirt); line(i, nk, ra, th * .8, shirt)
    if kind == "press":
        line(i, (x - 70 * sc, la[1]), (x + 70 * sc, la[1]), max(2, 5 * sc), (150, 150, 160))
        for e_ in (x - 70 * sc, x + 70 * sc): circle(i, (e_, la[1]), 13 * sc, (50, 50, 60))
    if kind == "squat":
        line(i, (x - 74 * sc, nk[1] + 3), (x + 74 * sc, nk[1] + 3), max(2, 5 * sc), (150, 150, 160))
        for e_ in (x - 74 * sc, x + 74 * sc): circle(i, (e_, nk[1] + 3), 14 * sc, (50, 50, 60))
    hc = (nk[0], nk[1] - hd * 1.05); circle(i, hc, hd, skin)
    if hat is not None:
        quad(i, [(hc[0] - hd, hc[1] - 4 * sc), (hc[0] - hd * .7, hc[1] - hd * 1.1), (hc[0] + hd * .7, hc[1] - hd * 1.1), (hc[0] + hd, hc[1] - 4 * sc)], hat)
    circle(i, (hc[0] + 7 * sc * dir_, hc[1] - 3 * sc), max(1.2, 2.6 * sc), (15, 15, 18))

LOCAL_STYLE = {"tokyo": [(30, 30, 34), (60, 60, 66), (235, 235, 240), (160, 90, 200), (70, 170, 220)],
 "paris": [(40, 44, 60), (120, 130, 150), (230, 225, 215), (40, 40, 46), (70, 60, 130)],
 "dubai": [(245, 245, 245), (230, 235, 240), (30, 30, 36), (210, 225, 235)],
 "alley": [(26, 26, 30), (42, 44, 50), (34, 36, 54), (20, 20, 24)],
 "villa": [(230, 230, 235), (40, 90, 170), (190, 200, 210), (30, 40, 60)]}

def extras(img, sh, t, ep):
    """Everyday people who belong in this place; a different crowd each episode."""
    name = sh["set"]; shot_s = abs(hash(("x", name, ep, sh.get("card", "")))) % 100000
    r = random.Random(ep * 97 + shot_s)
    outdoors = name in ("tokyo", "paris", "dubai", "harare", "bulawayo", "port", "alley", "villa")
    want = sh.get("crowd", 0)
    style = LOCAL_STYLE.get(name, CLOTH)
    pick = lambda: (r.choice(SKIN if name in ("harare", "bulawayo", "alley") else SKIN + SKIN[3:]), r.choice(style), r.choice(CLOTH[5:8] + [(70, 60, 45)]))
    if outdoors:
        for k in range(want or (r.randint(14, 22) if name in ("harare", "bulawayo") else r.randint(12, 18))):
            skin, shirt, pants = pick(); layer = r.random()
            y = FLOOR - 22 - layer * 34; sc = .78 + (1 - layer) * .34; spd = r.uniform(26, 62) * r.choice((-1, 1)); x0 = r.uniform(0, W + 200)
            x = (x0 + spd * t) % (W + 240) - 120
            npc(img, x, y, sc, skin, shirt, pants, t * (4 + r.random() * 3) + k, r.choice(("walk", "walk", "walk", "stand")), 1 if spd > 0 else -1, r.choice((None, None, r.choice(CLOTH))) if name != "alley" else (28, 28, 34))
    elif name == "gym":
        spots = [(120, "run"), (300, "press"), (470, "squat"), (640, "press"), (800, "squat"), (960, "run")]
        for k, (x, kind) in enumerate(spots):
            skin, shirt, pants = pick(); npc(img, x + r.uniform(-25, 25), FLOOR - 34, .82, skin, shirt, pants, t * (2.6 + k * .3) + k, kind)
        for k in range(want or 3):
            skin, shirt, pants = pick(); x = (r.uniform(0, W) + r.uniform(20, 50) * t) % (W + 200) - 100
            npc(img, x, FLOOR - 26, .95, skin, shirt, pants, t * 5 + k, "walk")
        ix = 540 + math.sin(t * .8) * 260
        npc(img, ix, FLOOR - 30, 1.0, SKIN[1], (30, 30, 200), (40, 40, 48), t * 4, "walk", 1, (30, 30, 200))
        text(img, "COACH", ix, FLOOR - 265, 22, col=(30, 30, 220), track=1, glow=0)
    elif name == "hotel":
        for k, x in enumerate((110, 330, 760, 970)):
            skin, shirt, pants = pick(); npc(img, x, FLOOR - 140, .72, skin, shirt, pants, t * 3 + k, "sit", 1 if k % 2 == 0 else -1)
            rect(img, x - 62, FLOOR - 120, x + 62, FLOOR - 100, (225, 228, 235)); rect(img, x - 8, FLOOR - 100, x + 8, FLOOR - 30, (120, 120, 128))
        wx = (r.uniform(0, W) + 70 * t) % (W + 200) - 100
        npc(img, wx, FLOOR - 30, .95, SKIN[0], (240, 240, 245), (28, 28, 34), t * 5, "tray"); rect(img, wx + 2, FLOOR - 222, wx + 60, FLOOR - 214, (205, 205, 212))
    elif name in ("plane", "train"):
        for k in range(want or 3):
            skin, shirt, pants = pick(); x = (30, 500, 1040)[k % 3]
            rect(img, x - 62, FLOOR - 380, x + 62, FLOOR - 40, (92, 72, 60)); npc(img, x, FLOOR - 175, .92, skin, shirt, pants, t * 2 + k, "sit", r.choice((1, -1)))
        cx = (r.uniform(0, W) + 44 * t) % (W + 200) - 100
        npc(img, cx, FLOOR - 40, 1.05, SKIN[2], (150, 60, 40), (40, 30, 30), t * 4, "tray", 1, (150, 60, 40))
    elif name == "ship":
        for k in range(want or 9):
            skin, shirt, pants = pick(); x = (r.uniform(0, W) + r.uniform(-30, 30) * t) % W
            npc(img, x, FLOOR - 95 - r.uniform(0, 70), r.uniform(.7, .95), skin, shirt, pants, t * 3 + k, r.choice(("walk", "stand", "stand")))
    elif name in ("mansion", "home", "gameroom", "desk"):
        n_ = want or 2
        for k in range(n_):
            skin, shirt, pants = pick(); x = (70 if k % 2 == 0 else 1010) + r.uniform(-25, 25) + (k // 2) * (90 if k % 2 == 0 else -90)
            npc(img, x, FLOOR - 28, .86, skin, shirt, pants, t * 2.2 + k, "stand", 1 if k % 2 == 0 else -1)

class Cam2:
    def __init__(s, ox, fy, z=Z): s.ox, s.fy, s.z = ox, fy, z
    def p(s, x, y): return (s.ox + x * s.z, s.fy + y * s.z)

CURRENT_EP = 1
def hash_str(t_): return sum(ord(c) * (i + 1) for i, c in enumerate(t_))
# Outfit eras, every 20 episodes. Styles only, no real logos.
OUTFITS = {
 "cenzo": [dict(top=(34, 34, 40), pants=(46, 46, 54), gear=["chain"]),
           dict(top=(150, 55, 120), pants=(38, 38, 44), gear=["chain", "fur"], fur=(24, 24, 28)),
           dict(top=(232, 232, 236), pants=(32, 32, 38), gear=["chain"]),
           dict(top=(26, 26, 30), pants=(26, 26, 30), gear=["chain", "fur"], fur=(60, 190, 240))],
 "clyde": [dict(top=(40, 130, 240), pants=(238, 238, 240), gear=["chain", "headphones"]),
           dict(top=(70, 220, 190), pants=(160, 90, 220), gear=["chain", "fur"], fur=(235, 225, 245)),
           dict(top=(220, 110, 220), pants=(245, 245, 245), gear=["chain"]),
           dict(top=(245, 245, 245), pants=(240, 170, 60), gear=["chain", "fur"], fur=(90, 220, 240))],
}
def glowup(who, base_):
    """Appearance by chapter: changes every 10 episodes, starting at episode 11."""
    L = dict(base_); stage = max(0, (CURRENT_EP - 1) // 10)
    if who == "cenzo": L["muscle"] = min(1.0, stage * .34)
    if who == "clyde": L["scale"] = 1 + min(.09, stage * .03)
    look = (CURRENT_EP - 1) // 20
    fits = OUTFITS.get(who)
    if fits and look > 0:
        fit = fits[min(look, len(fits)) - 1]
        L.update({k: v for k, v in fit.items() if k != "gear"})
        L["gear"] = fit.get("gear", L.get("gear", []))
    elif not fits and look > 0:
        r_ = random.Random(hash_str(who) + look * 31)
        L["top"], L["pants"] = r_.choice(CLOTH), r_.choice(CLOTH)
    return L

def draw_char(canvas, c, t, speaking, shot_t, mouth=False):
    L = glowup(c["who"], CAST[c["who"]])
    pose = c["pose"]
    P = POSES.get(pose) or POSES_X.get(pose) or POSES["stand"]
    P = {k: v for k, v in P.items()}
    if pose == "walk":
        P = dict(POSES["stand"]); w = math.sin(shot_t * 11) * 46
        P["fF"] = (w, 0); P["fB"] = (-w, 0); P["hF"] = (-w * .6, -176); P["hB"] = (w * .6, -176)
    if pose == "eat":
        P["hF"] = (70, -290 + math.sin(shot_t * 7) * 28)
    if pose == "lift":
        v = (math.sin(shot_t * 3.2) + 1) / 2 * 80; P["hF"] = (78, -390 - v); P["hB"] = (-70, -390 - v)
    if pose == "curl":
        v = (math.sin(shot_t * 4) + 1) / 2; P["hF"] = (56 - 8 * v, -190 - 130 * v)
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
    hand = E.fig(patch, Cam2(ox, fy, Z * L.get("scale", 1)), 0, 0, P, L, t, m)
    if pose == "lift":
        hy_ = int(hand[1]); bx0 = int(ox - 240); bx1 = int(ox + 240)
        cv2.line(patch, (bx0, hy_), (bx1, hy_), (150, 150, 158), 11, cv2.LINE_AA)
        for px_ in (bx0 + 10, bx0 + 36, bx1 - 10, bx1 - 36):
            cv2.line(patch, (px_, hy_ - 62), (px_, hy_ + 62), (60, 60, 70), 22, cv2.LINE_AA)
    if pose == "curl":
        hx_, hy_ = int(hand[0]), int(hand[1])
        cv2.line(patch, (hx_ - 40, hy_), (hx_ + 40, hy_), (120, 120, 128), 11, cv2.LINE_AA)
        for px_ in (hx_ - 40, hx_ + 40): cv2.circle(patch, (px_, hy_), 22, (60, 60, 70), -1, cv2.LINE_AA)
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


BUBBLE_COLORS = [(250, 250, 252), (205, 240, 255), (215, 245, 215), (250, 225, 215), (245, 215, 245), (190, 235, 255), (225, 225, 255)]
SET_LANG = {"tokyo": "ja", "paris": "fr", "dubai": "ar"}
_DJ = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
LANG_FONT = {"ja": (_CJK, 0), "ko": (_CJK, 1), "zh": (_CJK, 2)}
RTL = {"ar", "he", "fa", "ur"}
_tr_cache = {}

def tr_mask(tx, lang, size=44, maxw=660):
    """Render a translated line to a mask, wrapped to the bubble."""
    from PIL import Image, ImageDraw, ImageFont
    key = (tx, lang, size)
    if key in _tr_cache: return _tr_cache[key]
    path, idx = LANG_FONT.get(lang, (_DJ, 0))
    font = ImageFont.truetype(path, size, index=idx, layout_engine=ImageFont.Layout.RAQM)
    kw = dict(direction="rtl", language=lang) if lang in RTL else dict(language=lang)
    words = list(tx) if lang in LANG_FONT else tx.split(" ")
    sep = "" if lang in LANG_FONT else " "
    lines, cur = [], ""
    for w in words:
        t2 = (cur + sep + w) if cur else w
        if font.getlength(t2, **kw) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = t2
    if cur: lines.append(cur)
    lh = int(size * 1.34); wd = int(max(font.getlength(l, **kw) for l in lines)) + 8; ht = lh * len(lines) + 8
    im = Image.new("L", (wd, ht), 0); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text(((wd - font.getlength(l, **kw)) / 2, i * lh), l, font=font, fill=255, **kw)
    a = np.asarray(im, np.float32) / 255
    _tr_cache[key] = a
    return a

def font_ok(lang):
    return lang not in LANG_FONT or os.path.exists(LANG_FONT[lang][0])

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
        global CURRENT_EP
        s.e = json.load(open(f"{HERE}/scripts/ep{ep:03d}.json")); s.n = ep; CURRENT_EP = ep
        t = 0; s.tl = []; s.ev = []; s.info = {}; s.sp = []
        for sh in s.e["shots"]:
            a = t; lines = []
            for ln in sh["lines"]:
                x = V.say(ln[0], ln[1]); au = len(x) / 44100
                d = au + .16; s.info[t] = (au, V.envelope(x))
                s.sp.append((t + .08, x)); lines.append((t, t + d, ln)); t += d
            card = end = None
            if sh.get("card"):
                x = V.say("cenzo", sh["card"]); d = max(1.6, len(x) / 44100 + .4)
                s.sp.append((t + .2, x)); card = (t, t + d); t += d
            if sh.get("end"):
                x = V.say("narrator", sh["end"]); s.next = s.e.get("next", "NEXT EPISODE TOMORROW"); y = V.say("narrator", s.next)
                s.sp.append((t + .15, x)); s.sp.append((t + .25 + len(x) / 44100, y))
                d = max(1.9, (len(x) + len(y)) / 44100 + .45); end = (t, t + d); t += d
            s.tl.append(dict(a=a, b=t, sh=sh, lines=lines, card=card, end=end))
        if s.e.get("promo"):
            x = V.say("cenzo", "NEED A VIDEO LIKE THIS FOR YOUR BUSINESS? MESSAGE ME. WE MAKE THEM.")
            s.sp.append((t + .25, x)); d = max(4.5, len(x) / 44100 + 1.0)
            s.tl.append(dict(a=t, b=t + d, sh=dict(set=s.e["shots"][-1]["set"], cast=[], lines=[], promo=True), lines=[], card=None, end=None)); t += d
        if s.e.get("credit_song"):
            d = 2.2
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
        if not sh.get("promo") and not sh.get("credit"):
            extras(img, sh, t, s.n)
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
        pv, i_, pr = W / 2, 0, clamp(st / max(.1, x["b"] - x["a"]))
        tx = 0.
        if cur:
            i_ = [q[0] for q in x["lines"]].index(cur[0]); pv = cast[spk]["x"]
            pr = clamp((t - cur[0]) / max(.1, cur[1] - cur[0]))
            if cast[spk].get("mood") == "shock" and t - cur[0] < .3:
                tx = math.sin(t * 70) * 11
        z = 1.05 + .09 * (i_ % 2) + .025 * pr
        s._z = z
        M = np.array([[z, 0, (1 - z) * pv + tx], [0, z, (1 - z) * FLOOR]], np.float32)
        img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR)
        img = (img.astype(np.float32) * F.vignette()).astype(np.uint8)
        A = (50, 190, 255)
        shade = np.ones((H, 1, 1), np.float32); shade[:300] = np.linspace(.38, 1, 300, dtype=np.float32)[..., None, None]
        img = (img.astype(np.float32) * shade).astype(np.uint8)
        hk = s.e.get("hook")
        if hk and t < 2.2:
            text(img, hk, 505, 175, 108, alpha=1 - ease((t - 2.05) / .15))
        else:
            text(img, f"CH {(s.n - 1) // 10 + 1}  ·  EP {s.n}  ·  {s.e['title']}", 505, 165, 34, col=A, track=3, glow=.3)
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
        text(img, "@exoticcenzo", 505, 1385, 38, alpha=.62, track=3, glow=.2)
        dd = min(abs(t - b["a"]) for b in s.tl[1:]) if len(s.tl) > 1 else 9
        if dd < .07: img = (img * (dd / .07)).astype(np.uint8)
        return img

    def bubble(s, img, cur, t, cast, A):
        a, b, ln = cur
        who, tx = ln[0], ln[1]
        c = cast[who]; L = CAST[who]
        opts = ln[2] if len(ln) > 2 else {}
        tr = opts.get("tr"); shot_set = s.shot_at(t)["sh"]["set"]
        lang = s.shot_at(t)["sh"].get("lang") or SET_LANG.get(shot_set)
        if tr and not (lang and font_ok(lang)): tr = None
        fs = 30 if tr else 50; cw = 18.5 if tr else 30.5
        lines = textwrap.wrap(tx, 34 if tr else 17)
        n = len(lines); lh = int(fs * 1.2)
        trm = tr_mask(tr, lang) if tr else None
        trh = (trm.shape[0] + 12) if tr else 0
        wd = max(int(max(len(l) for l in lines) * cw), trm.shape[1] if tr else 0) + 96; ht = lh * n + 92 + trh
        seated = c["pose"] != "stand" and c["pose"] != "walk"
        hy = FLOOR - (360 if seated else 412) * Z * glowup(who, CAST[who]).get("scale", 1) - 88
        hy = FLOOR - (FLOOR - hy) * getattr(s, "_z", 1)
        cx = clamp(c["x"], wd / 2 + 56, 930 - wd / 2)
        bot = min(hy, 980); y0 = int(bot - ht); x0 = int(cx - wd / 2)
        p = out((t - a) / .12)
        ov = img.copy()
        col = BUBBLE_COLORS[(hash_str(tx) + s.n) % len(BUBBLE_COLORS)]
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
        if tr:
            mh, mw = trm.shape; px0 = int(cx - mw / 2); py0 = y0 + 40
            al = trm[..., None]; roi = img[py0:py0 + mh, px0:px0 + mw].astype(np.float32)
            img[py0:py0 + mh, px0:px0 + mw] = (roi * (1 - al) + np.array((24, 22, 28), np.float32) * al).astype(np.uint8)
            text(img, "\n".join(lines), cx, y0 + 40 + mh + 2, fs, col=(70, 70, 78), track=0, glow=0)
            return
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
