# Speaker Verification Guide

This guide explains how to use the HTML verification page to review and correct speaker assignments from diarization results.

## Overview

The verification page allows you to:
- **Review diarized segments** with timestamps and text
- **Play audio clips** for each segment
- **Assign speakers** using autocomplete from your speaker database
- **Save verified results** as JSON or CSV
- **Filter segments** by original speaker ID

## Quick Start

### 1. Generate Verification Page

After running the benchmark, generate the verification page:

```bash
cd apps/speaker-diarization-benchmark

# Basic usage
uv run python src/generate_verification_page.py \
    data/results/sample_audio_results.json \
    data/sample_audio.wav

# With speaker database
uv run python src/generate_verification_page.py \
    data/results/sample_audio_results.json \
    data/sample_audio.wav \
    --speaker-db data/speaker_database.json

# Specify solution
uv run python src/generate_verification_page.py \
    data/results/sample_audio_results.json \
    data/sample_audio.wav \
    --solution WhisperX \
    --output verification.html
```

### 2. Open in Browser

Open the generated HTML file in your web browser:

```bash
# The script will output the path, e.g.:
# data/results/sample_audio_results_verification.html

# Open with:
open data/results/sample_audio_results_verification.html  # macOS
xdg-open data/results/sample_audio_results_verification.html  # Linux
start data/results/sample_audio_results_verification.html  # Windows
```

### 3. Verify Speakers

1. **Select Audio File**: Use the file input to select the audio file (if not already loaded)
2. **Play Segments**: Click "▶ Play" to hear each segment
3. **Assign Speakers**: Type in the autocomplete field to assign speakers
4. **Filter**: Use the filter dropdown to show only specific speaker IDs
5. **Save**: Click "💾 Save Changes" to download verified results

## Speaker Database Format

The speaker database is a simple JSON file containing a list of known speaker names:

```json
[
  "Alice Johnson",
  "Bob Smith",
  "Charlie Brown"
]
```

Or as an object with metadata:

```json
{
  "speakers": [
    "Alice Johnson",
    "Bob Smith",
    "Charlie Brown"
  ],
  "metadata": {
    "last_updated": "2024-01-01"
  }
}
```

## Features

### Audio Playback

- Click "▶ Play" to play a segment
- Audio automatically stops at the segment end time
- Click again to stop playback
- Only one segment plays at a time

### Autocomplete

- Start typing a speaker name
- Matching names from the database appear in a dropdown
- Click a name or press Enter to select
- Segments are marked as "verified" when assigned

### Filtering

- Use the "Filter" dropdown to show only segments from a specific speaker ID
- Select "All Speakers" to show everything
- Useful for batch-assigning the same speaker to multiple segments

### Statistics

The page shows:
- **Total Segments**: Number of diarized segments
- **Verified**: Number of segments with assigned speakers
- **Unique Speakers**: Number of different speakers assigned

### Export Options

1. **Save Changes** (💾): Downloads a JSON file with verified results
2. **Export CSV** (📥): Downloads a CSV file with all segment data

## Verified Results Format

The saved JSON file contains:

```json
{
  "segments": [
    {
      "start": 0.5,
      "end": 1.2,
      "word": "Hello world",
      "speaker_id": "SPEAKER_00",
      "assigned_speaker": "Alice Johnson",
      "confidence": 0.95
    }
  ],
  "metadata": {
    "audio_file": "sample_audio.wav",
    "solution": "WhisperX",
    "updated_at": "2024-01-01T12:00:00Z"
  }
}
```

## Workflow Example

1. **Run Benchmark**:
   ```bash
   uv run python src/benchmark.py data/sample_audio.wav
   ```

2. **Generate Verification Page**:
   ```bash
   uv run python src/generate_verification_page.py \
       data/results/sample_audio_results.json \
       data/sample_audio.wav \
       --speaker-db data/speaker_database.json
   ```

3. **Open and Verify**:
   - Open the HTML file in browser
   - Play segments to verify accuracy
   - Assign speakers using autocomplete
   - Filter by speaker ID to batch-assign
   - Save verified results

4. **Use Verified Results**:
   - Load the saved JSON file
   - Map `assigned_speaker` to user records
   - Update your database with verified assignments

## Tips

- **Batch Assignment**: Filter by speaker ID, then assign the same speaker name to all visible segments
- **Audio Quality**: Make sure the audio file is accessible (use the file input if needed)
- **Speaker Database**: Keep your speaker database updated with all known speakers
- **Keyboard Shortcuts**: Press Enter in autocomplete field to select first match
- **Verification Status**: Verified segments are highlighted in green

## Troubleshooting

### Audio Won't Play

- Make sure you've selected the audio file using the file input
- Check that the audio file path is correct
- Try using a different browser

### Autocomplete Not Working

- Verify the speaker database JSON is valid
- Check browser console for errors
- Make sure the database file path is correct

### Segments Not Showing

- Check the filter dropdown - it might be filtering out segments
- Verify the results JSON file is valid
- Check browser console for errors

## Integration with Your System

After verification, you can integrate the results:

```python
import json

# Load verified results
with open('sample_audio_results_verified.json') as f:
    verified = json.load(f)

# Map to user records
for segment in verified['segments']:
    speaker_name = segment.get('assigned_speaker')
    if speaker_name:
        # Look up user ID from your database
        user_id = lookup_user_by_name(speaker_name)
        segment['user_id'] = user_id

# Save to your system
save_to_database(verified)
```
