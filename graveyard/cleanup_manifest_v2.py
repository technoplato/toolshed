import json
import os

MANIFEST_PATH = 'data/clips/manifest.json'

def main():
    with open(MANIFEST_PATH, 'r') as f:
        data = json.load(f)

    for clip in data:
        if 'transcriptions' in clip:
            # Remove mlx_whisper_turbo ONLY if mlx_whisper_turbo_seg_level exists
            if 'mlx_whisper_turbo' in clip['transcriptions'] and 'mlx_whisper_turbo_seg_level' in clip['transcriptions']:
                del clip['transcriptions']['mlx_whisper_turbo']
                print(f"Cleaned up raw transcription for {clip.get('id', 'unknown')}")
            
            # Ensure mlx_whisper_turbo_seg_level is present (it should be if we ran the experiment)
            # If not, we might want to keep mlx_whisper_turbo? 
            # User said "remove ... from the manifesto", implying global removal.
            # But if seg_level doesn't exist yet for some clips, we might lose data.
            # However, user seems to be focusing on the workflow where we generate seg_level.
            pass

    with open(MANIFEST_PATH, 'w') as f:
        json.dump(data, f, indent=4)

    print("Manifest cleaned up.")

if __name__ == "__main__":
    main()
