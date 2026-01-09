import os
import json
import time
import random
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import librosa
from speechbrain.pretrained import SpeakerRecognition


# --------------------------------------------------
# CONFIG
# --------------------------------------------------
DB_FILE = "database.json"
SAMPLE_RATE = 16000
DURATION = 3
TEMP_FILE = "temp_verify.wav"
SCORE_THRESHOLD = 0.6

PHRASES = [
    "magandang araw sayo kaibigan",
    "someone broke a glass-bottle",
    "may asong tumatawid ng kalsada",
    "the dog jumped over the fence",
    "hello professor",
    "ang kulit mo"
]

# --------------------------------------------------
# BASIC AUDIO LIVENESS (ANTI-SPOOF)
# --------------------------------------------------
def compute_basic_audio_metrics(wav_path):
    y, sr = librosa.load(wav_path, sr=SAMPLE_RATE)

    rms = np.mean(librosa.feature.rms(y=y))
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=y))
    flatness = np.mean(librosa.feature.spectral_flatness(y=y))
    centroid_var = np.var(librosa.feature.spectral_centroid(y=y, sr=sr))

    return rms, zcr, flatness, centroid_var

def quick_liveness_check(wav_path):
    rms, zcr, flatness, centroid_var = compute_basic_audio_metrics(wav_path)

    if rms < 1e-4:
        return False, "Silent or very low energy audio"

    if flatness < 1e-6 and centroid_var < 100:
        return False, "Suspiciously tonal (possible replay)"

    return True, "Passed audio liveness checks"

# --------------------------------------------------
# LOAD SPEAKER VERIFICATION MODEL (ONCE)
# --------------------------------------------------
print("Loading speaker verification model...")

verifier = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa",
    run_opts={"device": "cpu"}
)

# --------------------------------------------------
# RECORD VOICE WITH CHALLENGE
# --------------------------------------------------
def record_temp_sample():
    phrase = random.choice(PHRASES)

    print("\n🔐 VOICE LIVENESS CHECK")
    print("Please clearly say the following phrase:")
    print(f'➡️  "{phrase}"')

    time.sleep(2)

    print(f"\nRecording... (~{DURATION}s)")
    recording = sd.rec(
        int(SAMPLE_RATE * DURATION),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    write(TEMP_FILE, SAMPLE_RATE, recording)
    print("Saved temporary verification audio.")

    return phrase

# --------------------------------------------------
# VERIFY AGAINST DATABASE
# --------------------------------------------------
def verify_against_database():
    if not os.path.exists(DB_FILE):
        print("❌ No database.json found.")
        return None

    db = json.load(open(DB_FILE, "r"))

    ok, msg = quick_liveness_check(TEMP_FILE)
    print("Liveness check:", msg)
    if not ok:
        return None

    best_score = -1.0
    best_id = None

    for faculty_id, info in db.items():
        voice_dir = info.get("voice_path", f"voices/{faculty_id}")

        if not os.path.isdir(voice_dir):
            continue

        for fname in os.listdir(voice_dir):
            if not fname.endswith(".wav"):
                continue

            enrolled_file = os.path.join(voice_dir, fname)

            try:
                score, prediction = verifier.verify_files(
                    enrolled_file,
                    TEMP_FILE
                )

                score = float(score)

                if score > best_score:
                    best_score = score
                    best_id = faculty_id

            except Exception as e:
                print(f"Warning: error comparing {enrolled_file}: {e}")

    print(f"\nBest score: {best_score:.4f} (threshold {SCORE_THRESHOLD})")

    if best_score >= SCORE_THRESHOLD:
        print("✅ Voice verification SUCCESS")
        return best_id
    else:
        print("❌ Voice verification FAILED")
        return None

# --------------------------------------------------
# ENTRY POINT FOR main.py
# --------------------------------------------------
def verify_voice():
    record_temp_sample()
    return verify_against_database()

# --------------------------------------------------
# STANDALONE TEST
# --------------------------------------------------
if __name__ == "__main__":
    record_temp_sample()
    result = verify_against_database()
    if result:
        print("Verified faculty ID:", result)
    else:
        print("No match found.")
