# Speaker Diarization Benchmark

This directory contains tools and scripts for benchmarking and improving speaker diarization using MLX and other models.

## Standard Workflow

We have standardized our pipeline on the following configuration. **Do not deviate from this without explicit approval.**

### 1. Transcription
*   **Model**: `mlx-community/whisper-large-v3-turbo`
*   **Library**: `mlx_whisper`
*   **Script**: `transcribe.py` (or `transcribe_mlx.py` which wraps it)
*   **Key Feature**: Word-level timestamps are required for our segment-level embedding approach.

### 2. Diarization (Experimental -> Standard)
Our "experimental" segment-level embedding approach has become the **de facto standard**.

*   **Script**: `experiment_segment_embedding.py`
*   **Process**:
    1.  Takes word-level segments from the transcription.
    2.  Extracts audio crops for each segment.
    3.  Generates embeddings using `pyannote/embedding`.
    4.  Clusters embeddings (Agglomerative Clustering) to assign speaker labels.
    5.  Updates `manifest.json` with `mlx_whisper_turbo_seg_level` entries.

## Usage

### Process a New Clip
```bash
# 1. Transcribe (Standardized)
uv run python transcribe_mlx.py path/to/clip.mp3

# 2. Diarize (Standardized)
uv run python experiment_segment_embedding.py --clip-id clip_filename.mp3

# 3. Cleanup (Optional but recommended)
uv run python cleanup_manifest_v2.py
```

### UI
Run the Ground Truth UI to visualize and correct diarization:
```bash
uv run python data/clips/server.py
```
Access at: `http://localhost:8000/ground_truth_ui.html`

## Key Files
*   `transcribe.py`: The source of truth for transcription configuration.
*   `experiment_segment_embedding.py`: The core diarization logic.
*   `data/clips/manifest.json`: The central database of clips and transcriptions.
*   `data/clips/ground_truth_ui.html`: The frontend for verification.

## Embeddings & Active Learning

We use a "human-in-the-loop" approach to progressively improve speaker identification.

### Embedding Model
*   **Model**: `pyannote/embedding` (Hugging Face)
*   **Dimensions**: 512-dimensional vectors.
*   **Storage**:
    *   **Known Speakers**: `data/speaker_embeddings.json` stores the "ground truth" clusters for known speakers (e.g., "Shane Gillis", "Matt McCusker").
    *   **Cache**: `data/cache/embeddings/{clip_id}.json` stores the raw embeddings for *every segment* in a processed clip.

### Active Learning Workflow
1.  **Generation**: When `experiment_segment_embedding.py` runs, it generates an embedding for every segment and saves it to the **Cache** (`data/cache/embeddings/`).
2.  **Correction**: In the Ground Truth UI, when a user manually corrects a speaker label (e.g., changing "UNKNOWN" to "Shane Gillis"):
    *   The UI sends a request to `POST /correct_segment`.
    *   The server looks up the segment's embedding in the **Cache**.
    *   The server adds this embedding to the "Shane Gillis" entry in `speaker_embeddings.json`.
3.  **Improvement**: Future runs of the diarization script will use this updated `speaker_embeddings.json` to better identify "Shane Gillis" automatically.

### Caching Details
The cache files are JSON dictionaries mapping segment indices (as strings) to their 512-dim embedding lists.
*   **Path**: `data/cache/embeddings/<clip_id>.json`
*   **Format**: `{"0": [0.1, -0.2, ...], "1": [...]}`
*   **Purpose**: Allows the server to "enroll" a segment into the known speaker database without needing to re-compute the embedding from audio on the fly.
