import queue, json, time
import sounddevice as sd
import vosk, pyautogui

# ---------------- SETUP ----------------
q = queue.Queue()

def callback(indata, frames, time_, status):
    if status:
        print(status)
    q.put(bytes(indata))

model = vosk.Model("vosk-model-small-en-us-0.15")
rec = vosk.KaldiRecognizer(model, 16000)

stream = sd.RawInputStream(
    samplerate=16000,
    blocksize=2000,        # faster processing
    dtype="int16",
    channels=1,
    callback=callback
)
stream.start()

print("🎙️ Voice Control Ready — say left / right / up / down / jump")
print("Keep your game window active.  Ctrl+C to stop.\n")

# ---------------- CONTROL ----------------
last_time = 0
cooldown = 0.75   # prevents repeated triggers

while True:
    try:
        data = q.get()
        heard = ""

        # check for final or partial words
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            heard = res.get("text", "").lower()
        else:
            res = json.loads(rec.PartialResult())
            heard = res.get("partial", "").lower()

        # no speech detected
        if not heard:
            continue

        now = time.time()
        if now - last_time < cooldown:
            continue  # skip extra triggers too soon

        # match commands
        if "left" in heard:
            pyautogui.press("left")
            print("⚡ LEFT")
            last_time = now

        elif "right" in heard:
            pyautogui.press("right")
            print("⚡ RIGHT")
            last_time = now

        elif "up" in heard or "jump" in heard:
            pyautogui.press("up")
            print("⚡ JUMP")
            last_time = now

        elif "d" in heard or "duck" in heard or "lower" in heard:
            pyautogui.press("down")
            print("⚡ DOWN")
            last_time = now

    except KeyboardInterrupt:
        print("\n🛑 Voice control stopped.")
        break

stream.stop()
stream.close()
