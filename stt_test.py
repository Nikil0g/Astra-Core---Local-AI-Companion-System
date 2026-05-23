from faster_whisper import WhisperModel

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

segments, info = model.transcribe(
    "test.wav",
    language="ru"
)

print("Язык:", info.language)

for segment in segments:
    print(segment.text)