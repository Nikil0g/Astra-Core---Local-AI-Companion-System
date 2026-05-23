import sounddevice as sd
from scipy.io.wavfile import write

fs = 48000
seconds = 5

print("Говори...")

recording = sd.rec(
    int(seconds * fs),
    samplerate=fs,
    channels=1,
    dtype='int16',
    device=20,
    blocking=True
)

sd.wait()

write("test.wav", fs, recording)

print("Запись сохранена как test.wav")