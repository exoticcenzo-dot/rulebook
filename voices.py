"""Real character voices using the local Kokoro model. Lines are cached by hash."""
import os, re, hashlib, wave
import numpy as np
MODEL = "/home/claude/tts/kokoro-v1.0.onnx"; VOICES = "/home/claude/tts/voices-v1.0.bin"
CACHE = os.path.dirname(os.path.abspath(__file__)) + "/out/tts"; os.makedirs(CACHE, exist_ok=True)
SPEAK = {"cenzo": ("am_michael", 1.02), "clyde": ("am_puck", 1.08), "nia": ("am_eric", 1.0),
         "zeke": ("bm_george", .97), "maya": ("am_liam", 1.08), "ruva": ("af_heart", 1.04), "gogo": ("bf_emma", .9), "moyo": ("bm_daniel", .9), "tino": ("af_sarah", .98), "antoine": ("bm_lewis", .95), "grace": ("af_bella", .98), "narrator": ("am_onyx", .96)}
# Character pitch: >1 higher, <1 deeper. Speech speed is compensated so pacing stays the same.
# Makes each friend a distinct cartoon voice instead of a plain stock TTS read.
PITCH = {"antoine": .96, "cenzo": .92, "clyde": 1.12, "zeke": .88, "narrator": .94, "gogo": 1.06, "moyo": .93}
_k = None
def clean(tx):
    s = tx.replace("\n", ". ").replace('"', "").strip(". ")
    s = re.sub(r"\.\.\.", "", s).strip()
    s = s.lower()
    s = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), s)
    s = re.sub(r"\bexoticcenzo\b", "Exotic Chenzo", s, flags=re.I)
    s = re.sub(r"\bcenzo\b", "Chenzo", s, flags=re.I)
    for a, b in (("clyde", "Clyde"), ("mtoriro", "Muh-toh-ree-roh"), ("solo", "Solo"), ("jamal", "Jamal"), ("ruva", "Roova"), ("gogo", "Go-go"), ("moyo", "Moh-yo"), ("tino", "Tee-no"), ("antoine", "Ann-twan"), ("tokyo", "Tokyo")):
        s = re.sub(rf"\b{a}\b", b, s, flags=re.I)
    s = re.sub(r"\bi('|\b)", lambda m: "I" + m.group(1), s)
    s = re.sub(r"\brematch\b", "re-match", s, flags=re.I)
    # Shona / Ndebele / slang pronunciations for the American-English voice
    for a, b in (("ndeipi", "n-day-pee"), ("zvakaoma", "zvah-kah-oh-mah"), ("zvemahara", "zveh-mah-hah-rah"), ("shamwari", "shahm-wah-ree"),
                 ("ngiyabonga", "ngee-yah-bohn-gah"), ("unjani", "oon-jah-nee"), ("hwindi", "hwin-dee"), ("sadza", "sahd-zah"),
                 ("kombi", "kom-bee"), ("mabhero", "mah-beh-roh"), ("tyora", "tyoh-rah"), ("hesi", "heh-see"), ("kenge", "ken-geh"),
                 ("eish", "aysh"), ("mfana", "um-fah-nah"), ("mudhara", "moo-dah-rah"), ("delulu", "deh-loo-loo"), ("bussin", "buss-in"), ("GOAT", "goat")):
        s = re.sub(rf"\b{a}\b", b, s, flags=re.I)
    return s if s[-1:] in ".?!" else s + "."
def say(who, tx):
    """return mono float32 at 44100 Hz"""
    global _k
    v, spd = SPEAK.get(who, SPEAK["narrator"]); c = clean(tx); r = PITCH.get(who, 1.0)
    p = f"{CACHE}/{hashlib.md5((v + str(spd) + str(r) + c).encode()).hexdigest()}.npy"
    if os.path.exists(p): return np.load(p)
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro(MODEL, VOICES)
    a, sr = _k.create(c, voice=v, speed=spd / r, lang="en-us")
    n = int(len(a) * 44100 / sr / r)
    x = np.interp(np.arange(n) * sr * r / 44100, np.arange(len(a)), a).astype(np.float32)
    idx = np.where(np.abs(x) > .01)[0]
    x = x[max(0, idx[0] - 900): idx[-1] + 2200]
    x = x / np.abs(x).max() * .95
    np.save(p, x); return x
def envelope(x, fps=30):
    n = 44100 // fps
    return np.array([np.sqrt(np.mean(x[i:i + n] ** 2)) for i in range(0, len(x), n)] or [0.])
