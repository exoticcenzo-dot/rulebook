"""Free edit layer for THE RULE BOOK (replaces CapCut/Canva/Picsart-style polish, no credits, no licences).
All effects are generated in code (OpenCV + NumPy): colour grade, bloom, vignette, film grain,
shot transitions (whip-pan, zoom-blur, glitch) and synthesized sound effects. Switched on from
series.json "fx_from" (episode number); earlier episodes re-render exactly as before."""
import math
import numpy as np, cv2
from film import W, H, FPS, clamp

# ---------- colour grade + texture ----------
def _curve(lift, gamma, gain):
    x = np.arange(256, dtype=np.float32) / 255
    y = np.clip(lift + (gain - lift) * np.power(x, gamma), 0, 1)
    return (y * 255).astype(np.uint8)

# warm cinematic look: slightly lifted blacks, warm highlights, a touch cooler shadows (BGR order)
_LUT = np.dstack([_curve(.035, 1.04, .95),   # blue: lower gain = warmer highlights
                  _curve(.02, .98, 1.0),     # green
                  _curve(.01, .94, 1.0)])    # red: a little lifted mid-tones
_LUT = _LUT.reshape(1, 256, 3)
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_VIG = (1 - .28 * np.clip(((_xx - W / 2) / (W * .62)) ** 2 + ((_yy - H * .46) / (H * .58)) ** 2, 0, 1.4) ** 1.6)
_VIG = np.clip(_VIG, .62, 1)[..., None].astype(np.float32)
del _yy, _xx
_rng = np.random.default_rng(7)
# soft, clumpy grain at 1/3 res: reads as film texture but stays cheap for the video encoder
_GRAIN = [cv2.GaussianBlur(_rng.normal(0, 1, (H // 3, W // 3)).astype(np.float32), (0, 0), .7) for _ in range(4)]

def grade(img):
    """Warm grade + soft bloom on highlights + vignette. Applied to the scene before text overlays."""
    img = cv2.LUT(img, _LUT)
    # contrast/saturation nudge in HSV-free form: blend toward a slightly punchier copy
    small = cv2.resize(img, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    hi = cv2.threshold(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY), 200, 255, cv2.THRESH_TOZERO)[1]
    bloom = cv2.GaussianBlur(cv2.bitwise_and(small, small, mask=(hi > 0).astype(np.uint8)), (0, 0), 6)
    bloom = cv2.resize(bloom, (W, H), interpolation=cv2.INTER_LINEAR)
    out = img.astype(np.float32) * _VIG + bloom.astype(np.float32) * .22
    return np.clip(out, 0, 255).astype(np.uint8)

def grain(img, t, amt=4.0):
    """Light film grain over the whole frame; the pattern changes every 3rd frame (12 fps flicker, like film)."""
    g = _GRAIN[int(t * FPS) // 3 % len(_GRAIN)]
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    return np.clip(img.astype(np.float32) + g[..., None] * amt, 0, 255).astype(np.uint8)

# ---------- transitions ----------
KINDS = ("whip", "zoom", "glitch")
def kind_for(k):
    return KINDS[(k * 7 + 1) % 3]

def _hblur(img, n):
    n = max(1, int(n)) | 1
    k = np.zeros((1, n), np.float32); k[0, :] = 1 / n
    return cv2.filter2D(img, -1, k)

def whip(img, p, side):
    """p 0..1 strength; side -1 = leaving (moves left), +1 = arriving (comes from the right)."""
    dx = int(-side * p * W * .35) if side < 0 else int(p * W * .35)
    M = np.float32([[1, 0, dx], [0, 1, 0]])
    img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return _hblur(img, 3 + p * 90)

def zoom(img, p):
    """Zoom-blur: average of progressively scaled copies around the centre."""
    acc = img.astype(np.float32); n = 5
    for i in range(1, n):
        z = 1 + p * .06 * i
        M = np.float32([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * H * .45]])
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    z = 1 + p * .12
    M = np.float32([[z, 0, (1 - z) * W / 2], [0, z, (1 - z) * H * .45]])
    return cv2.warpAffine(np.clip(acc / n, 0, 255).astype(np.uint8), M, (W, H), borderMode=cv2.BORDER_REFLECT)

def glitch(img, p, seed):
    r = np.random.default_rng(seed)
    out = img.copy(); s = int(6 + p * 26)
    out[..., 2] = np.roll(img[..., 2], s, axis=1); out[..., 0] = np.roll(img[..., 0], -s, axis=1)
    for _ in range(int(3 + p * 9)):
        y = int(r.integers(0, H - 40)); h = int(r.integers(10, 70)); dx = int(r.integers(-90, 90) * p)
        out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
    if p > .6:
        out = cv2.addWeighted(out, .85, np.full_like(out, 255), .15, 0)
    return out

def transition(img, t, cuts, dur=.13):
    """cuts: list of (time, kind). Effect ramps up before the cut and down after it."""
    for i, (c, kind) in enumerate(cuts):
        d = t - c
        if -dur <= d < dur:
            side = -1 if d < 0 else 1
            p = 1 - abs(d) / dur; p = p * p * (3 - 2 * p)
            if kind == "whip": return whip(img, p, side)
            if kind == "zoom": return zoom(img, p)
            return glitch(img, p, int(t * FPS) + i)
    return img

# ---------- caption animation helpers ----------
KEYWORDS = {"NEVER", "ALWAYS", "SECRET", "FREE", "BROKE", "MONEY", "SORRY", "NO", "YES", "WHY", "WHAT", "WHO",
            "STOP", "RUN", "LIKES", "FOLLOWER", "GOLD", "PAGES", "PAGE", "RULE", "DEAL", "COOKED", "ATE", "LOWKEY"}
def is_key(word):
    w = word.strip(".,!?'\"-—…").upper()
    return w in KEYWORDS or any(ch.isdigit() for ch in w) or word.endswith("!") or word.endswith("?")

def bounce(dt, d=.2):
    """Scale for a caption chunk entering: 0.7 -> 1.1 -> 1.0 over ~d seconds."""
    if dt >= d: return 1.0
    x = clamp(dt / d)
    return .7 + .3 * x + .4 * math.sin(math.pi * x) * (1 - x) * 1.6

# ---------- synthesized sound effects (no samples, no licences) ----------
SR = 44100
def _q(d): return np.arange(int(d * SR)) / SR

def boom(rng=None):
    """Deep cinematic bass hit for punchlines and the rule card."""
    q = _q(1.1)
    f = 38 + 60 * np.exp(-q * 9)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-q * 3.2)
    click = np.random.default_rng(3).normal(0, 1, len(q)) * np.exp(-q * 160) * .5
    return np.tanh((body + click) * 1.6).astype(np.float32)

def scratch(rng):
    """Record-scratch style swipe for shock lines (filtered noise with a fast pitch wobble)."""
    q = _q(.42)
    nz = rng.normal(0, 1, len(q)).astype(np.float32)
    lfo = np.sin(2 * np.pi * (7 * q + 10 * q * q))
    bp = np.convolve(nz, np.ones(9) / 9, "same") - np.convolve(nz, np.ones(60) / 60, "same")
    tone = np.sin(2 * np.pi * np.cumsum(500 + 380 * lfo) / SR)
    e = np.minimum(1, q / .02) * np.exp(-q * 5)
    return ((bp * .8 + tone * .35) * e).astype(np.float32)

def riser(d=1.0, rng=None):
    """Rising noise + tone sweep that builds into the end card."""
    q = _q(d); rng = rng or np.random.default_rng(5)
    nz = rng.normal(0, 1, len(q)).astype(np.float32)
    nz = nz - np.convolve(nz, np.ones(40) / 40, "same")
    tone = np.sin(2 * np.pi * np.cumsum(220 + 900 * (q / d) ** 2) / SR)
    e = (q / d) ** 2.2
    return ((nz * .5 + tone * .35) * e).astype(np.float32)

def notify():
    """Phone notification blip (two short rising tones)."""
    a = _q(.09); b = _q(.14)
    x = np.concatenate([np.sin(2 * np.pi * 1180 * a) * np.exp(-a * 25), np.zeros(int(.03 * SR)),
                        np.sin(2 * np.pi * 1570 * b) * np.exp(-b * 18)])
    return (x * .6).astype(np.float32)

def click(rng):
    q = _q(.025); return (rng.normal(0, 1, len(q)) * np.exp(-q * 400) * .5).astype(np.float32)

def zap(rng):
    """Digital zap for glitch cuts."""
    q = _q(.22)
    f = 1800 * np.exp(-q * 14) + 120
    sq = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR))
    return (sq * np.exp(-q * 12) * .35 + rng.normal(0, .15, len(q)) * np.exp(-q * 30)).astype(np.float32)
