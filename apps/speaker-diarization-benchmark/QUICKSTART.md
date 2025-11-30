# Quick Start Guide

Get up and running with the speaker diarization benchmark in 5 minutes.

## 1. Install Dependencies

```bash
cd apps/speaker-diarization-benchmark
uv sync
```

## 2. Set Up Hugging Face Token

```bash
# Get your token from https://huggingface.co/settings/tokens
export HUGGING_FACE_TOKEN="your_token_here"

# Or add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
echo 'export HUGGING_FACE_TOKEN="your_token_here"' >> ~/.bashrc
```

**Important**: Accept the model terms on Hugging Face:
- Visit: https://huggingface.co/pyannote/speaker-diarization-3.1
- Click "Agree and access repository"

## 3. Prepare Audio File

```bash
# Convert to WAV if needed (recommended format)
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav

# Place in data/ directory
mkdir -p data
mv output.wav data/sample_audio.wav
```

## 4. Run Benchmark

```bash
# Basic usage
uv run python src/benchmark.py data/sample_audio.wav

# With custom output directory
uv run python src/benchmark.py data/sample_audio.wav --output-dir results/

# With GPU (if available)
uv run python src/benchmark.py data/sample_audio.wav --device cuda
```

## 5. View Results

Results are saved in:
- `data/results/{audio_name}_results.json` - Full results
- `data/results/{audio_name}_WhisperX.csv` - Word-level CSV (if WhisperX worked)
- `data/results/{audio_name}_pyannote_audio.csv` - Segment-level CSV (if pyannote worked)

## Example Output

```
🎤 Running benchmark on: sample_audio.wav
Audio duration: 120.50s

✓ pyannote.audio pipeline initialized
✓ WhisperX ready (models load on first use)
Initialized 2 pipeline(s)

Processing with pyannote.audio... ✓ pyannote.audio: 45 segments, 12.34s
Processing with WhisperX... ✓ WhisperX: 450 words, 45.67s

┌─────────────────┬────────┬───────┬──────────┬──────────┐
│ Solution        │ Status │ Words │ Time (s) │ Memory   │
├─────────────────┼────────┼───────┼──────────┼──────────┤
│ pyannote.audio  │ ✓      │ 45    │ 12.34    │ 512.0    │
│ WhisperX        │ ✓      │ 450   │ 45.67    │ 2048.5   │
└─────────────────┴────────┴───────┴──────────┴──────────┘
```

## Troubleshooting

### "No module named 'pyannote'"
```bash
uv sync
```

### "Hugging Face token not found"
```bash
export HUGGING_FACE_TOKEN="your_token"
```

### "Model access denied"
- Visit the model page on Hugging Face
- Click "Agree and access repository"
- Wait a few minutes for access to propagate

### "CUDA out of memory"
```bash
# Use CPU instead
uv run python src/benchmark.py data/sample_audio.wav --device cpu
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [example_usage.py](example_usage.py) for programmatic usage
- Customize speaker-to-user mapping for your use case
