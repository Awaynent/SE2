import os
import json
import time
import random
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import librosa
import wave
import difflib
import re

import torch
import torchaudio

from speechbrain.pretrained import SpeakerRecognition
from vosk import Model, KaldiRecognizer

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
DB_FILE = "database.json"
SAMPLE_RATE = 16000
DURATION = 3
TEMP_FILE = "temp_verify.wav"
SCORE_THRESHOLD = 0.6
PHRASE_SIMILARITY_THRESHOLD = 0.7

VOSK_EN = "models/vosk-en"
VOSK_PH = "models/vosk-ph"

PHRASES = [
    "magandang araw sayo kaibigan",
    "may asong tumatawid ng kalsada",
    "ang kulit mo",
    "someone broke a glass bottle",
    "the dog jumped over the fence",
    "hello professor"
]

# --------------------------------------------------
# LOAD MODELS (ONCE)
# --------------------------------------------------
print("Loading speaker verification model...")
verifier = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa",
    run_opts={"device": "cpu"}
)

print("Loading Vosk models...")
vosk_models = {
    "en": Model(VOSK_EN),
    "ph": Model(VOSK_PH)
}

# --------------------------------------------------
# AUDIO UTILITIES (WINDOWS SAFE)
# --------------------------------------------------
def load_wav_tensor(path):
    signal, sr = torchaudio.load(path)
    if sr != SAMPLE_RATE:
        signal = torchaudio.functional.resample(signal, sr, SAMPLE_RATE)
    return signal

# --------------------------------------------------
# BASIC AUDIO LIVENESS
# --------------------------------------------------
def compute_basic_audio_metrics(wav_path):
    y, sr = librosa.load(wav_path, sr=SAMPLE_RATE)
    rms = np.mean(librosa.feature.rms(y=y))
    flatness = np.mean(librosa.feature.spectral_flatness(y=y))
    centroid_var = np.var(librosa.feature.spectral_centroid(y=y, sr=sr))
    return rms, flatness, centroid_var


def quick_liveness_check(wav_path):
    rms, flatness, centroid_var = compute_basic_audio_metrics(wav_path)

    if rms < 1e-4:
        return False, "Silent or very low energy audio"

    if flatness < 1e-6 and centroid_var < 100:
        return False, "Suspiciously tonal (possible replay)"

    return True, "Passed audio liveness checks"

# --------------------------------------------------
# LANGUAGE DETECTION
# --------------------------------------------------
def detect_language(text):
    if re.search(r"[ñáéíóú]", text) or any(w in text for w in ["ang", "may", "sayo"]):
        return "ph"
    return "en"

# --------------------------------------------------
# SPEECH-TO-TEXT
# --------------------------------------------------
def recognize_speech(wav_path, lang):
    wf = wave.open(wav_path, "rb")
    rec = KaldiRecognizer(vosk_models[lang], wf.getframerate())
    rec.SetWords(False)

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)

    result = json.loads(rec.FinalResult())
    return result.get("text", "").lower().strip()


def phrase_similarity(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()

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

    return phrase.lower()

# --------------------------------------------------
# VERIFY AGAINST DATABASE (FIXED)
# --------------------------------------------------
def verify_against_database(expected_phrase):
    if not os.path.exists(DB_FILE):
        print("❌ No database.json found.")
        return None

    ok, msg = quick_liveness_check(TEMP_FILE)
    print("Audio liveness:", msg)
    if not ok:
        return None

    lang = detect_language(expected_phrase)
    recognized = recognize_speech(TEMP_FILE, lang)

    if not recognized:
        print("❌ Speech not recognized")
        return None

    similarity = phrase_similarity(recognized, expected_phrase)

    print(f"Recognized phrase: '{recognized}'")
    print(f"Expected phrase:   '{expected_phrase}'")
    print(f"Phrase similarity: {similarity:.2f}")

    if similarity < PHRASE_SIMILARITY_THRESHOLD:
        print("❌ Phrase mismatch — possible replay attack")
        return None

    print("✅ Phrase verified")

    db = json.load(open(DB_FILE, "r"))
    best_score = -1.0
    best_id = None

    test_sig = load_wav_tensor(TEMP_FILE)

    for faculty_id, info in db.items():
        voice_dir = info.get("voice_path", f"voices/{faculty_id}")
        if not os.path.isdir(voice_dir):
            continue

        for fname in os.listdir(voice_dir):
            if not fname.endswith(".wav"):
                continue

            enrolled = os.path.join(voice_dir, fname)

            try:
                enrolled_sig = load_wav_tensor(enrolled)

                score, _ = verifier.verify_batch(
                    enrolled_sig,
                    test_sig
                )
                score = float(score)

                if score > best_score:
                    best_score = score
                    best_id = faculty_id

            except Exception as e:
                print(f"⚠️ Skipped {enrolled}: {e}")

    print(f"\nBest score: {best_score:.4f} (threshold {SCORE_THRESHOLD})")

    return best_id if best_score >= SCORE_THRESHOLD else None

# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------
def verify_voice():
    expected_phrase = record_temp_sample()
    return verify_against_database(expected_phrase)
