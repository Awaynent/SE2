import os
import sounddevice as sd
from scipy.io.wavfile import write
import time

SAMPLE_RATE = 16000  # Hz
DURATION = 3         # seconds per sample (adjustable)
SAMPLES_PER_USER = 5

def capture(faculty_id):
    save_dir = f"voices/{faculty_id}"
    os.makedirs(save_dir, exist_ok=True)

    print(f"\nRecording {SAMPLES_PER_USER} voice samples for faculty ID: {faculty_id}")
    print("Please speak clearly when prompted. Short sentence or passphrase (3 seconds each).")
    time.sleep(1)

    for i in range(1, SAMPLES_PER_USER + 1):
        print(f"\nSample {i}/{SAMPLES_PER_USER} — starting in 2 seconds...")
        time.sleep(2)
        print("Recording...")
        recording = sd.rec(int(SAMPLE_RATE * DURATION), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
        sd.wait()
        filename = f"{save_dir}/sample_{i}.wav"
        write(filename, SAMPLE_RATE, recording)  # writes int16 WAV
        print(f"Saved: {filename}")

    print("\nVoice capture complete!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python capture_voice.py <faculty_id>")
    else:
        capture(sys.argv[1])