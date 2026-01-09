import os
import sounddevice as sd
from scipy.io.wavfile import write

def register_voice(name):
    folder = f"data/voices/{name}"
    os.makedirs(folder, exist_ok=True)

    print("\nPlease speak clearly for 2 seconds...")
    fs = 16000
    duration = 2

    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    voice_path = f"{folder}/sample.wav"
    write(voice_path, fs, recording)

    print("Voice sample saved at:", voice_path)
    return voice_path


if __name__ == "__main__":
    faculty_id = input("Enter Faculty ID: ")
    register_voice(faculty_id)