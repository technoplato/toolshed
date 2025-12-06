import json
from pathlib import Path

MANIFEST_FILE = Path("data/clips/manifest.json")

def main():
    with open(MANIFEST_FILE, 'r') as f:
        data = json.load(f)
        
    target_id = "clip_youtube_jAlKYYr1bpY_0_60.wav"
    new_id = "clip_youtube_jAlKYYr1bpY_0_60_TEST.wav"
    
    # Find target
    target_entry = next((c for c in data if c['id'] == target_id), None)
    
    if not target_entry:
        print(f"Target {target_id} not found.")
        return
        
    # Check if new exists
    if any(c['id'] == new_id for c in data):
        print(f"New ID {new_id} already exists. Removing it first.")
        data = [c for c in data if c['id'] != new_id]
        
    # Duplicate
    import copy
    new_entry = copy.deepcopy(target_entry)
    new_entry['id'] = new_id
    # Keep the same clip path so it loads the same audio
    # new_entry['clip_path'] is already correct
    
    data.append(new_entry)
    
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"Duplicated {target_id} to {new_id}")

if __name__ == "__main__":
    main()
