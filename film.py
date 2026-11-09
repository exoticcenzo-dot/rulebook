#!/usr/bin/env python3
"""Perfectionist vs Action Taker: code-drawn stickman short for @ExoticWords.
usage: film.py still t1 t2 ... | film.py render | film.py audio"""
import sys, os, math, random, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
OUT = os.path.dirname(os.path.abspath(__file__)) + "/out"
os.makedirs(OUT, exist_ok=True)
FLOOR = 1180
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SCENES = [(0, 3.2), (3.2, 10.2), (10.2, 16.0), (16.0, 21.5), (21.5, 28.0)]
TOTAL = SCENES[-1][1]

# colours are BGR
WHITE = (250, 250, 250)
BACK = (165, 165, 165)
BRICK = (170, 196, 214)
BRICK_TOP = (205, 226, 240)
BRICK_SIDE = (120, 142, 160)
RED = (55, 45, 235)
GOLD = (90, 205, 255)

CYCLE = 0.44
S2_START = 3.5
FALL_T = 11.3
REBUILD_T = 13.0
RISE_T, RISE_END = 16.0, 19.0
ROWS_END = 30
BW, BH = 100, 52


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)
def out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3
def mix(a, b, k): return a + (b - a) * k


# ---------- camera ----------
class Cam:
    def __init__(s, z=1.0): s.z = z
    def p(s, x, y): return (700 + s.z * (x - 708), FLOOR + s.z * y)


def ipt(p): return (int(round(p[0] * 8)), int(round(p[1] * 8)))


def line(img, a, b, th, col):
    cv2.line(img, ipt(a), ipt(b), col, max(1, int(round(th))), cv2.LINE_AA, 3)


def circle(img, c, r, col):
    cv2.circle(img, ipt(c), int(round(r * 8)), col, -1, cv2.LINE_AA, 3)


def quad(img, pts, col):
    a = np.array([ipt(p) for p in pts], np.int32)
    cv2.fillConvexPoly(img, a, col, cv2.LINE_AA, 3)


# ---------- bricks ----------
def brick(img, cam, x, y, w=BW - 6, h=BH - 6, ang=0.0, col=BRICK, top=BRICK_TOP, side=BRICK_SIDE):
    """x,y = bottom centre in world coords"""
    ca, sa = math.cos(ang), math.sin(ang)
    def P(u, v):
        return cam.p(x + u * ca - v * sa, y + u * sa + v * ca)
    hw = w / 2
    quad(img, [P(-hw, 0), P(hw, 0), P(hw, -h), P(-hw, -h)], side)
    quad(img, [P(-hw, -h * .16), P(hw, -h * .16), P(hw, -h * .95), P(-hw, -h * .95)], col)
    quad(img, [P(-hw, -h * .78), P(hw, -h * .78), P(hw, -h), P(-hw, -h)], top)


_rng = random.Random(7)
JIT = [(_rng.uniform(-6, 6), _rng.uniform(-.05, .05)) for _ in range(ROWS_END * 3 + 3)]


def slot(i):
    r, c = i // 3, i % 3
    return (560 + BW / 2 + c * BW + (r % 2) * 24 + JIT[i][0], -r * BH, JIT[i][1])


PILE = [(416, 0), (474, 0), (445, -BH + 6)]
FALLEN = [  # index, land x, spin, delay
    (23, 545, 2.4, 0.00), (22, 508, -3.0, 0.05), (21, 590, 3.4, 0.11),
    (20, 472, -2.5, 0.16), (19, 628, 2.8, 0.2)]
FALL_DUR = 0.72


def fallen_state(idx, t):
    """world pose of a falling brick at time t, or None if not yet falling"""
    for k, (i, lx, spin, d) in enumerate(FALLEN):
        if i == idx:
            u = (t - FALL_T - d) / FALL_DUR
            if u < 0:
                return None
            sx, sy, a = slot(i)
            u1 = clamp(u)
            x = mix(sx, lx, u1)
            y = mix(sy, 0, u1 * u1)
            if u > 1:  # small bounce
                v = clamp((u - 1) / .3)
                y = -22 * math.sin(math.pi * v)
            return x, y, a + spin * u1 * (1 if u < 1 else 1)
    return None


def count_at(t):
    """bricks in the wall at time t and the active cycle phase (None=idle)"""
    if t < S2_START:
        return 0, None
    if t < 10.2:
        n = int((t - S2_START) / CYCLE)
        if n >= 15:
            return 15, None
        return n, ((t - S2_START) / CYCLE) % 1
    if t < REBUILD_T:
        return 24, None
    if t < RISE_T:
        n = int((t - REBUILD_T) / CYCLE)
        if n >= 5:
            return 24, None
        return 19 + n, ((t - REBUILD_T) / CYCLE) % 1
    k = ease((t - RISE_T) / (RISE_END - RISE_T))
    return int(mix(24, ROWS_END * 3, k)), None


# ---------- figure ----------
def ik(a, t, l1, l2, bend):
    dx, dy = t[0] - a[0], t[1] - a[1]
    d = clamp(math.hypot(dx, dy), 1e-3, (l1 + l2) * .999)
    th = math.atan2(dy, dx)
    c = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    an = th + bend * math.acos(c)
    return (a[0] + l1 * math.cos(an), a[1] + l1 * math.sin(an))


POSES = {
    "stand": dict(hip=(0, -176), neck=(0, -322), head=(4, -382), hF=(34, -176), hB=(-34, -176), fF=(30, 0), fB=(-30, 0)),
    "pick": dict(hip=(20, -126), neck=(-48, -236), head=(-92, -278), hF=(-72, -46), hB=(-58, -40), fF=(38, 0), fB=(-26, 0)),
    "place": dict(hip=(0, -180), neck=(14, -326), head=(24, -386), hF=(78, -392), hB=(60, -366), fF=(30, 0), fB=(-38, 0)),
    "ouch": dict(hip=(-6, -168), neck=(-2, -306), head=(-2, -366), hF=(44, -392), hB=(-44, -392), fF=(36, 0), fB=(-36, 0)),
    "cheer": dict(hip=(0, -180), neck=(0, -328), head=(0, -390), hF=(92, -470), hB=(-92, -470), fF=(50, 0), fB=(-50, 0)),
    "kneel": dict(hip=(-46, -104), neck=(38, -222), head=(86, -262), hF=(150, -78), hB=(128, -66), fF=(44, 0), fB=(-112, 0)),
}


def pose_mix(a, b, k):
    return {n: (mix(a[n][0], b[n][0], k), mix(a[n][1], b[n][1], k)) for n in a}


def figure(img, cam, x, y, P, bendF=1):
    z = cam.z
    W2 = lambda q: cam.p(x + q[0], y + q[1])
    hip, neck = P["hip"], P["neck"]
    sh = (mix(hip[0], neck[0], .93), mix(hip[1], neck[1], .93))
    limbs = []
    for name, root, l1, l2, b, col in [
        ("fB", hip, 96, 96, -1, BACK), ("hB", sh, 84, 84, 1, BACK)]:
        limbs.append((root, ik(root, P[name], l1, l2, b * bendF), P[name], col))
    fr = [("fF", hip, 96, 96, -1, WHITE), ("hF", sh, 84, 84, 1, WHITE)]
    for root, j, end, col in limbs:
        line(img, W2(root), W2(j), 25 * z, col); line(img, W2(j), W2(end), 22 * z, col)
    line(img, W2(hip), W2(neck), 38 * z, WHITE)
    circle(img, W2(P["head"]), 46 * z, WHITE)
    for name, root, l1, l2, b, col in fr:
        j = ik(root, P[name], l1, l2, b * bendF)
        line(img, W2(root), W2(j), 28 * z, col); line(img, W2(j), W2(P[name]), 24 * z, col)
        circle(img, W2(P[name]), 15 * z, col)
    return W2(P["hF"])


# ---------- text ----------
@functools.lru_cache(maxsize=700)
def text_patch(s, size, n, track):
    font = ImageFont.truetype(FONT, size)
    cw = font.getlength("M") + track
    lines = s.split("\n")
    lh = int(size * 1.2)
    w = int(cw * max(map(len, lines))) + 60
    h = lh * len(lines) + 60
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    left = n
    for ln, l in enumerate(lines):
        ox = (w - 60 - cw * len(l)) / 2 + 30
        for c, ch in enumerate(l):
            if left <= 0:
                break
            d.text((ox + c * cw, 30 + ln * lh), ch, font=font, fill=255)
            left -= 1
    a = np.asarray(im, np.float32) / 255
    g = cv2.GaussianBlur(a, (0, 0), size / 7)
    return a, g


def text(img, s, cx, y, size, col=(255, 255, 255), alpha=1.0, n=None, track=3, glow=.55):
    if alpha <= 0:
        return
    chars = len(s.replace("\n", ""))
    n = chars if n is None else int(n)
    a, g = text_patch(s, size, n, track)
    ph, pw = a.shape
    x0, y0 = int(cx - pw / 2), int(y - 30)
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(W, x0 + pw), min(H, y0 + ph)
    a = a[ya - y0:yb - y0, xa - x0:xb - x0] * alpha
    g = g[ya - y0:yb - y0, xa - x0:xb - x0] * alpha * glow
    roi = img[ya:yb, xa:xb].astype(np.float32)
    c = np.array(col, np.float32)
    roi = roi + g[..., None] * c * .8
    roi = roi * (1 - a[..., None]) + c * a[..., None]
    img[ya:yb, xa:xb] = np.clip(roi, 0, 255).astype(np.uint8)


def window(t, a, b, fi=.18, fo=.18):
    return ease((t - a) / fi) * (1 - ease((t - b + fo) / fo))


def typed(s, t, a, cps=26):
    return clamp((t - a) * cps, 0, len(s.replace("\n", "")))


# ---------- static layers ----------
_vig = None
def vignette():
    global _vig
    if _vig is None:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((x - W / 2) / (W * .78)) ** 2 + ((y - 1050) / (H * .62)) ** 2)
        _vig = np.clip(1.16 - d ** 2.2, .22, 1)[..., None]
    return _vig


# ---------- world ----------
def zoom_at(t):
    if t < RISE_T:
        return 1.0
    return mix(1.0, .5, ease((t - RISE_T) / (RISE_END - RISE_T)))


def wall_phase(t):
    """(bricks in wall, set of falling indices currently hidden from wall)"""
    return count_at(t)


def p_rub(t):
    return math.sin(t * 9.5) * 34


def world(t, draw_dim=False):
    z = zoom_at(t)
    cam = Cam(z)
    img = np.zeros((H, W, 3), np.uint8)
    img[:] = (7, 7, 8)
    # floor light pools
    for cx in (215, 640):
        c = cam.p(cx - 0, 0)
        cv2.ellipse(img, (int(c[0]), FLOOR), (int(280 * z + 40), int(30)), 0, 0, 360, (24, 24, 26), -1, cv2.LINE_AA)
    cv2.line(img, (0, FLOOR), (W, FLOOR), (30, 30, 32), 2, cv2.LINE_AA)

    # rays on the summit
    if t >= RISE_END - .15:
        k = out((t - RISE_END + .15) / .7)
        top_y = -ROWS_END * BH - 190
        c = cam.p(708, top_y)
        rays = np.zeros_like(img)
        for i in range(14):
            a = i / 14 * math.tau + (t - RISE_END) * .22
            d = 1300
            s = .10
            pts = [c, (c[0] + d * math.cos(a - s), c[1] + d * math.sin(a - s)),
                   (c[0] + d * math.cos(a + s), c[1] + d * math.sin(a + s))]
            cv2.fillConvexPoly(rays, np.array([ipt(p) for p in pts], np.int32), (34, 58, 72), cv2.LINE_AA, 3)
        rays = cv2.GaussianBlur(rays, (0, 0), 14)
        rays[FLOOR:] = 0
        img = cv2.add(img, (rays * k).astype(np.uint8))

    # pile
    for x, y in PILE:
        brick(img, cam, x, y, w=62, h=46)

    # P's single perfect brick, on a plinth of nothing but ego
    bx = 298
    brick(img, cam, bx, 0, w=120, h=66, col=(214, 228, 238), top=(245, 250, 252), side=(150, 165, 176))

    # A's wall
    n, ph = wall_phase(t)
    for i in range(n):
        if 10.2 <= t < RISE_T and i >= 19 and FALL_T <= t and t < REBUILD_T + (i - 19 + 1) * CYCLE:
            continue
        x, y, a = slot(i)
        if i == n - 1 and ph is None and t < 10.2:
            pass
        brick(img, cam, x, y, ang=a)
    if FALL_T <= t < RISE_T:
        n2 = max(0, min(5, int((t - REBUILD_T) / CYCLE))) if t >= REBUILD_T else 0
        for k, (i, lx, sp, d) in enumerate(FALLEN):
            if t >= REBUILD_T and k < n2:
                continue
            st = fallen_state(i, t)
            if st is None:
                sx, sy, a = slot(i)
                brick(img, cam, sx, sy, ang=a)
            else:
                brick(img, cam, st[0], st[1], ang=st[2])

    # P figure: kneeling and rubbing
    rub = p_rub(t) if t > 3.0 else 0
    k_kneel = ease((t - 2.7) / .5)
    Pk = dict(POSES["kneel"])
    Pk["hF"] = (POSES["kneel"]["hF"][0] + rub, POSES["kneel"]["hF"][1])
    Pk["hB"] = (POSES["kneel"]["hB"][0] + rub * .8, POSES["kneel"]["hB"][1])
    Pk["head"] = (POSES["kneel"]["head"][0] + rub * .1, POSES["kneel"]["head"][1])
    P1 = pose_mix(POSES["stand"], Pk, k_kneel)
    hand = figure(img, cam, 120, 0, P1)
    if t > 3.0:
        cx, cy = hand
        wd, hg = 58 * z, 20 * z
        quad(img, [(cx - wd, cy - hg + 16 * z), (cx + wd, cy - hg + 16 * z), (cx + wd, cy + hg + 16 * z), (cx - wd, cy + hg + 16 * z)], RED)

    # sparkle on perfect brick
    if t > 4:
        s = (t * .85) % 1
        amp = math.sin(math.pi * clamp(s / .4))
        c = cam.p(340, -72)
        r = 34 * amp * z
        if r > 1:
            line(img, (c[0] - r, c[1]), (c[0] + r, c[1]), 4, (255, 255, 255))
            line(img, (c[0], c[1] - r), (c[0], c[1] + r), 4, (255, 255, 255))

    # A figure
    if t < RISE_T:
        ax, ay = 500, 0
        if ph is not None:
            if ph < .3:
                P2 = pose_mix(POSES["place"], POSES["pick"], ease(ph / .3))
            elif ph < .6:
                P2 = pose_mix(POSES["pick"], POSES["place"], ease((ph - .3) / .3))
            else:
                P2 = POSES["place"]
        else:
            P2 = POSES["stand"]
            # settle after the last brick of the Day 1 run, ouch during the fall
            if t >= FALL_T + .15:
                k = ease((t - FALL_T - .15) / .25) * (1 - ease((t - REBUILD_T + .3) / .3))
                P2 = pose_mix(P2, POSES["ouch"], k)
                b = math.sin(t * 14) * 5 * k
                P2 = dict(P2); P2["head"] = (P2["head"][0] + b, P2["head"][1])
        hand2 = figure(img, cam, ax, ay, P2)
        if ph is not None:
            target = n
            sx, sy, a = slot(target)
            if .3 <= ph < .6:
                hx, hy = (hand2[0] - 700) / z + 708, (hand2[1] - FLOOR) / z
                brick(img, cam, hx, hy + 24)
            elif ph >= .6:
                u = (ph - .6) / .4
                rx, ry = 500 + 78, -392 + 24
                x = mix(rx, sx, u)
                y = mix(ry, sy, u) - math.sin(math.pi * u) * 90
                brick(img, cam, x, y, ang=a * u + (1 - u) * .4)
    else:
        # riding the top
        k = ease((t - RISE_T) / (RISE_END - RISE_T))
        rows = n // 3
        y = -rows * BH
        P3 = POSES["stand"]
        if t > RISE_END - .25:
            P3 = pose_mix(P3, POSES["cheer"], out((t - RISE_END + .25) / .35))
            bounce = abs(math.sin((t - RISE_END) * 7)) * 18 * (t > RISE_END)
        else:
            bounce = 0
        figure(img, cam, 708, y - bounce, P3)
        # sparks
        if t > RISE_END:
            r = random.Random(3)
            for _ in range(48):
                ang = r.uniform(-math.pi, 0)
                sp = r.uniform(180, 560)
                b0 = r.uniform(0, 1.8)
                tt = ((t - RISE_END + b0) % 1.8)
                c0 = cam.p(708, -ROWS_END * BH - 200)
                px = c0[0] + math.cos(ang) * sp * tt
                py = c0[1] + math.sin(ang) * sp * tt + 340 * tt * tt
                circle(img, (px, py), 6 * clamp(1.4 - tt), GOLD if r.random() < .6 else WHITE)

    # glow
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g = cv2.GaussianBlur(small, (0, 0), 9)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    img = cv2.addWeighted(img, 1.0, g, .38, 0)

    # reflection
    rh = min(FLOOR, H - FLOOR)
    src = img[FLOOR - rh:FLOOR][::-1].astype(np.float32)
    src = cv2.GaussianBlur(src, (0, 0), 2.2)
    fade = np.power(np.linspace(1, 0, rh, dtype=np.float32), 2.0)[..., None, None] * .34
    img = img.astype(np.float32)
    img[FLOOR:FLOOR + rh] = np.clip(img[FLOOR:FLOOR + rh] + src * fade, 0, 255)
    img *= vignette()
    return np.clip(img, 0, 255).astype(np.uint8)


# ---------- full frame ----------
_end = None
def frame(t):
    global _end
    if t >= 21.5:
        if _end is None:
            f = world(21.4)
            f = cv2.GaussianBlur(f, (0, 0), 7)
            _end = (f * .17).astype(np.uint8)
        img = _end.copy()
    else:
        img = world(t)

    # dip at each cut
    dip = 1.0
    for s, e in SCENES[1:]:
        d = abs(t - s)
        if d < .1:
            dip = min(dip, d / .1)

    # --- hook ---
    if t < 3.2:
        s = "ONE OF THEM\nNEVER FINISHES."
        text(img, s, 505, 330, 92, n=typed(s, t, .05, 32))
    # --- labels ---
    if .9 < t < RISE_T:
        a = window(t, .9, RISE_T, .3, .35)
        text(img, "PERFECTIONIST", 215, 690, 36, alpha=a, n=typed("PERFECTIONIST", t, .9, 40), track=5)
        text(img, "ACTION TAKER", 690, 690, 36, alpha=a, n=typed("ACTION TAKER", t, 1.3, 40), track=5)

    # --- day stamps & copy ---
    if 3.2 <= t < 10.2:
        text(img, "DAY 1", 505, 230, 52, col=(120, 200, 255), alpha=window(t, 3.2, 10.2))
        if t < 6.6:
            s = "HE'S MAKING\nIT PERFECT."
            text(img, s, 505, 330, 92, n=typed(s, t, 3.5), alpha=window(t, 3.3, 6.6))
        else:
            s = "HE'S MAKING\nIT EXIST."
            text(img, s, 505, 330, 92, n=typed(s, t, 6.7), alpha=window(t, 6.6, 10.2))
    if 10.2 <= t < 16:
        text(img, "DAY 30", 505, 230, 52, col=(120, 200, 255), alpha=window(t, 10.2, 16))
        if FALL_T - .05 <= t < REBUILD_T - .1:
            s = "IT FELL."
            text(img, s, 505, 340, 112, n=typed(s, t, FALL_T + .1, 34), col=(90, 90, 255))
        elif t >= REBUILD_T - .1:
            s = "HE REBUILT IT."
            text(img, s, 505, 340, 86, n=typed(s, t, REBUILD_T, 34), alpha=1 - ease((t - 15.8) / .2))
    # counters
    if 3.4 <= t < RISE_T:
        n = 19 if FALL_T + .5 <= t < REBUILD_T else count_at(t)[0]
        a = window(t, 3.4, RISE_T, .25, .3)
        text(img, "1", 215, 1270, 110, alpha=a, col=(255, 255, 255))
        text(img, "BRICK", 215, 1405, 32, alpha=a, track=6, glow=.3)
        text(img, str(n), 690, 1270, 110, alpha=a, col=(120, 200, 255))
        text(img, "BRICK" if n == 1 else "BRICKS", 690, 1405, 32, alpha=a, track=6, glow=.3)
    # year
    if 16.25 <= t < 21.5:
        a = window(t, 16.25, 21.5, .25, .2)
        text(img, "DAY\n365", 262, 330, 118, alpha=a, col=(120, 200, 255))
    if 19.2 <= t < 21.5:
        s = "SAME\nBRICK."
        text(img, s, 262, 700, 84, n=typed(s, t, 19.3), alpha=1 - ease((t - 21.3) / .2))
    # payoff
    if t >= 21.5:
        if t < 24.3:
            s = "YOUR FIRST\nBRICK WILL\nBE UGLY."
            text(img, s, 505, 610, 104, n=typed(s, t, 21.6, 30), alpha=window(t, 21.5, 24.3))
        elif t < 26.3:
            k = out((t - 24.3) / .22)
            text(img, "LAY IT\nANYWAY.", 505, 640, int(150 - 22 * k), col=(120, 200, 255),
                 alpha=window(t, 24.3, 26.3, .08, .15))
        else:
            s = "WHICH ONE\nARE YOU?"
            text(img, s, 505, 540, 112, n=typed(s, t, 26.35, 32), alpha=1 - ease((t - 27.8) / .2))
            text(img, "1 = PERFECTIONIST   2 = ACTION TAKER", 505, 860, 30, alpha=window(t, 26.8, 28, .25, .2), track=2, glow=.25)
            text(img, "@EXOTICCENZO", 505, 980, 58, col=(120, 200, 255), alpha=window(t, 27.0, 28, .25, .2), track=6)
    if dip < 1:
        img = (img * dip).astype(np.uint8)
    if t > TOTAL - .15:
        img = (img * clamp((TOTAL - t) / .15)).astype(np.uint8)
    return img


# ---------- render ----------
def render_scene(i):
    a, b = SCENES[i]
    final = f"{OUT}/scene{i}.mp4"
    tmp = f"{OUT}/scene{i}.tmp.mp4"
    n = int(round((b - a) * FPS))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
           "-pix_fmt", "yuv420p", "-r", str(FPS), tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        p.stdin.write(frame(a + f / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, final)
        print("scene", i, "ok", flush=True)
    else:
        sys.exit(f"scene {i} failed")


# ---------- audio ----------
def audio():
    sr = 44100
    N = int(TOTAL * sr)
    mus = np.zeros(N, np.float32)
    fx = np.zeros(N, np.float32)
    t = np.arange(N) / sr
    rng = np.random.default_rng(5)
    # pad: A minor -> F -> C -> E, slow
    prog = [(110, 130.81, 164.81), (87.31, 110, 130.81), (130.81, 164.81, 196), (82.41, 123.47, 164.81)]
    bar = 3.5
    for b in range(9):
        fr = prog[b % 4]
        s = b * bar
        e = min(TOTAL, s + bar + .4)
        idx = (t >= s) & (t < e)
        tt = t[idx] - s
        env = np.minimum(tt / .8, 1) * np.minimum((e - t[idx]) / .8, 1)
        for f in fr:
            mus[idx] += env * (.05 * np.sin(2 * np.pi * f * tt) + .022 * np.sin(2 * np.pi * f * 2.005 * tt)) * .9

    def add(buf, at, x, g=1.0):
        i = int(at * sr)
        j = min(N, i + len(x))
        if 0 <= i < N:
            buf[i:j] += x[:j - i] * g

    def kick(d=.28):
        tt = np.arange(int(d * sr)) / sr
        return np.sin(2 * np.pi * (46 * tt + 7 * (1 - np.exp(-tt * 34)))) * np.exp(-tt * 13)

    def thunk(f=170):
        tt = np.arange(int(.14 * sr)) / sr
        n = rng.normal(0, 1, len(tt))
        n = np.convolve(n, np.ones(9) / 9, "same")
        return (np.sin(2 * np.pi * f * tt) * .8 + n * .9) * np.exp(-tt * 34)

    def tick():
        tt = np.arange(int(.022 * sr)) / sr
        return rng.normal(0, 1, len(tt)) * np.exp(-tt * 300)

    # pulse from day 1
    bt = 60 / 92
    s = 3.2
    while s < 21.3:
        add(mus, s, kick(), .42)
        s += bt
    # cut hits
    for c in (3.2, 10.2, 16.0):
        add(fx, c, kick(.5), .55)
    # bricks
    for i in range(15):
        add(fx, S2_START + (i + 1) * CYCLE, thunk(rng.uniform(150, 195)), .5)
    for i in range(5):
        add(fx, REBUILD_T + (i + 1) * CYCLE, thunk(rng.uniform(150, 195)), .55)
    # polishing scrape
    idx = (t > 3.2) & (t < 21.5)
    n = rng.normal(0, 1, idx.sum()).astype(np.float32)
    n = np.convolve(n, np.ones(5) / 5, "same") - np.convolve(n, np.ones(41) / 41, "same")
    fx[idx] += n * (np.abs(np.sin(t[idx] * 9.5)) ** 2) * .03
    # crash
    for k, (_, _, _, d) in enumerate(FALLEN):
        add(fx, FALL_T + d + FALL_DUR, thunk(95 + k * 18), .9)
    add(fx, FALL_T + .72, kick(.45), .6)
    # riser + impact
    idx = (t >= RISE_T) & (t < RISE_END)
    tt = (t[idx] - RISE_T) / (RISE_END - RISE_T)
    n = rng.normal(0, 1, idx.sum()).astype(np.float32)
    fx[idx] += n * tt ** 2.5 * .1 + np.sin(2 * np.pi * (60 + 240 * tt) * (t[idx] - RISE_T)) * tt ** 2 * .09
    add(fx, RISE_END, kick(.9), 1.0)
    # triumphant shimmer
    idx = (t >= RISE_END) & (t < 21.5)
    tt = t[idx] - RISE_END
    for f in (440, 554.37, 659.25):
        fx[idx] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * .9) * .035
    # payoff hits
    add(fx, 21.5, kick(.8), .8)
    add(fx, 24.3, kick(1.0), 1.0)
    add(fx, 26.3, kick(.6), .7)
    # typewriter ticks
    for s_, cps, nch in [(.05, 32, 25), (3.5, 26, 21), (6.7, 26, 18), (21.6, 30, 26), (26.35, 32, 16)]:
        for c in range(nch):
            add(fx, s_ + c / cps, tick(), .10)
    # duck pads under payoff slightly less; end fade
    mix_ = mus * .9 + fx
    fade = np.minimum(1, (TOTAL - t) / .4)
    mix_ *= fade
    peak = np.abs(mix_).max()
    mix_ = np.tanh(mix_ / peak * 1.25) / np.tanh(1.25) * .92
    st = np.stack([mix_, mix_], 1)
    pcm = (st * 32767).astype(np.int16)
    import wave
    with wave.open(f"{OUT}/audio.wav", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
    print("audio ok")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "still":
        for s in sys.argv[2:]:
            cv2.imwrite(f"{OUT}/still_{s}.jpg", frame(float(s)), [cv2.IMWRITE_JPEG_QUALITY, 90])
    elif cmd == "render":
        for i in range(len(SCENES)):
            render_scene(i)
    elif cmd == "audio":
        audio()
