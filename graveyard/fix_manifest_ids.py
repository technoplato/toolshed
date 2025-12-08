import json
import os

MANIFEST_PATH = 'data/clips/manifest.json'

def main():
    with open(MANIFEST_PATH, 'r') as f:
        data = json.load(f)

    for clip in data:
        # If ID is an absolute path, convert to basename
        if os.path.isabs(clip['id']):
            new_id = os.path.basename(clip['id'])
            print(f"Updating ID: {clip['id']} -> {new_id}")
            clip['id'] = new_id
            
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(data, f, indent=4)

    print("Manifest IDs updated.")

if __name__ == "__main__":
    main()
