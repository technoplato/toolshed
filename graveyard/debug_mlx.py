import mlx_whisper
import time
from pathlib import Path

CLIP_PATH = "data/clips/clip_local_mssp-old-test-ep-1_0_60.wav"

print("Starting mlx-whisper debug...")
try:
    start = time.time()
    # Using the exact call from benchmark
    result = mlx_whisper.transcribe(CLIP_PATH, path_or_hf_repo="mlx-community/whisper-small", word_timestamps=True)
    end = time.time()
    print(f"Success! Time: {end - start:.2f}s")
    print(f"Text: {result['text'][:100]}...")
    if 'segments' in result and result['segments']:
        print(f"Words in first segment: {result['segments'][0].get('words', 'None')}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
