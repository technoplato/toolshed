import os
from pyannote.audio import Pipeline

TOKEN = "REDACTED_SECRET"

print("Attempting to load pipeline...")
try:
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=TOKEN,
    )
    print("Success!")
except Exception as e:
    print(f"Error: {e}")
