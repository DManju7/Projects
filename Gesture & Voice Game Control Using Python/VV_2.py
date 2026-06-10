import queue
import sounddevice as sd
import vosk
import json
import pyautogui
import time
import sys

# ---------------- CONFIG ----------------
MODEL_PATH = "vosk-model-small-en-us-0.15" 

# how long to auto-release a held key if no stop command arrives (seconds)
AUTO_RELEASE_SECONDS = 5.0

# minimum gap between accepting commands to avoid duplicates (seconds)
DEBOUNCE = 0.25

# mapping spoken token -> key name (pyautogui key names)
HOLD_KEYS = {
    "left": "left",
    "right": "right",
    "down": "down",
    "up": "up"
}
# one-shot actions (press)
PRESS_KEYS = {
    "jump": "space",
    "space": "space",
    "enter": "enter",
    "start": "enter",
    "shoot": "ctrl",
    "fire": "ctrl"
}

# synonyms: map words you might say to canonical tokens
SYNONYMS = {
    "brake": "left",      # example for hill climb: brake might be left
    "accelerate": "right",
    "gas": "right",
    "duck": "down",
    "back":"down",
    "right": "right",
    "go":"up"
}

# ---------------- END CONFIG ----------------

q = queue.Queue()

def callback(indata, frames, time_, status):
    if status:
        print("Audio status:", status, file=sys.stderr)
    q.put(bytes(indata))

# load model
try:
    model = vosk.Model(MODEL_PATH)
except Exception as e:
    print("Error loading model:", e)
    sys.exit(1)

rec = vosk.KaldiRecognizer(model, 16000)

# state for held keys
held = {}  # key -> timestamp when it was pressed
last_accept_time = 0.0
last_detected_token = None

print("🎙️ Instant Voice Controller (hold support) ready.")
print("Say: left/right/up/down to hold, 'stop' to release, 'jump' for one-shot.\n")
print("Make sure Terminal has Microphone and Accessibility permissions (macOS).")
print("Press Ctrl+C to quit.\n")

# open stream
stream = sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback)
stream.start()

try:
    while True:
        data = q.get()
        # prefer partial result for instant detection
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
        else:
            res = json.loads(rec.PartialResult())

        # partial has key "partial", final has "text"
        partial = res.get("partial", "").strip().lower()
        final = res.get("text", "").strip().lower()
        cmd_text = partial or final
        if not cmd_text:
            # nothing recognized this frame
            # check auto-release for held keys
            now = time.time()
            to_release = []
            for k, t in list(held.items()):
                if now - t > AUTO_RELEASE_SECONDS:
                    to_release.append(k)
            for k in to_release:
                pyautogui.keyUp(k)
                print(f"⏱️ Auto-released: {k}")
                del held[k]
            continue

        now = time.time()
        # basic debounce (prevents repeated triggers from repeated partials)
        if now - last_accept_time < DEBOUNCE and cmd_text == last_detected_token:
            # ignore repeated identical token shortly after
            continue

        # map synonyms
        tokens = cmd_text.split()
        detected = None
        for tok in tokens[::-1]:  # check last recognized words first
            tok = tok.strip()
            if not tok:
                continue
            if tok in SYNONYMS:
                tok = SYNONYMS[tok]
            # prefer exact hold keys
            if tok in HOLD_KEYS:
                detected = ("HOLD", HOLD_KEYS[tok], tok)
                break
            if tok in PRESS_KEYS:
                detected = ("PRESS", PRESS_KEYS[tok], tok)
                break
            if tok in ("stop", "release", "hold on", "holdoff", "hold off"):
                detected = ("STOP", None, tok)
                break
            if tok in ("quit", "exit"):
                detected = ("QUIT", None, tok)
                break

        if not detected:
            # nothing relevant in partial
            last_detected_token = cmd_text
            last_accept_time = now
            continue

        typ, key, raw = detected

        # handle quit
        if typ == "QUIT":
            print("👋 Quit command detected. Exiting.")
            break

        # STOP -> release all held keys
        if typ == "STOP":
            for k in list(held.keys()):
                try:
                    pyautogui.keyUp(k)
                except Exception:
                    pass
                print(f"🛑 Released: {k}")
                del held[k]
            last_accept_time = now
            last_detected_token = cmd_text
            continue

        # PRESS -> single tap
        if typ == "PRESS":
            pyautogui.press(key)
            print(f"⚡ PRESS: {raw} -> {key}")
            last_accept_time = now
            last_detected_token = cmd_text
            continue

        # HOLD -> start holding the key if not already
        if typ == "HOLD":
            # if the requested key already held, do nothing
            if key in held:
                # update timestamp to prevent auto-release
                held[key] = now
                # no print to reduce spam
            else:
                # if opposite directional key is held, release it first
                opp = None
                if key == "left" and "right" in held:
                    opp = "right"
                elif key == "right" and "left" in held:
                    opp = "left"
                elif key == "up" and "down" in held:
                    opp = "down"
                elif key == "down" and "up" in held:
                    opp = "up"
                if opp:
                    try:
                        pyautogui.keyUp(opp)
                        print(f"🔁 Released opposite: {opp}")
                    except Exception:
                        pass
                    if opp in held:
                        del held[opp]

                # keyDown the requested key
                pyautogui.keyDown(key)
                held[key] = now
                print(f"⏳ HOLD START: {raw} -> {key}")

            last_accept_time = now
            last_detected_token = cmd_text

        # cleanup: auto-release old holds
        now = time.time()
        to_release = []
        for k, t in list(held.items()):
            if now - t > AUTO_RELEASE_SECONDS:
                to_release.append(k)
        for k in to_release:
            try:
                pyautogui.keyUp(k)
                print(f"⏱️ Auto-released: {k}")
            except Exception:
                pass
            del held[k]

except KeyboardInterrupt:
    print("\n🛑 Keyboard interrupt — stopping.")
finally:
    # ensure all held keys are released
    for k in list(held.keys()):
        try:
            pyautogui.keyUp(k)
            print(f"Cleanup released: {k}")
        except Exception:
            pass
    stream.stop()
    stream.close()
    print("Stopped.")
