# Speaker Diarization & Identification Benchmark

A comprehensive benchmark tool for comparing open source speaker diarization and identification solutions. This tool processes audio files and outputs per-word timestamps with speaker identity IDs, making it easy to map speakers to user records.

## Features

- **Multiple Solutions**: Benchmarks 3+ open source diarization pipelines
- **Word-Level Timestamps**: Provides per-word timestamps with speaker IDs
- **Performance Metrics**: Tracks processing time, memory usage, and accuracy
- **Clear Documentation**: Comprehensive logging and detailed results
- **Easy Integration**: Simple API for mapping speaker IDs to user records

## Supported Solutions

### 1. pyannote.audio ⭐ (Recommended)
- **Best for**: Production-ready speaker diarization
- **Pros**: Industry standard, highly accurate, well-maintained
- **Cons**: Requires Hugging Face token, segment-level (needs ASR for word-level)
- **Model**: `pyannote/speaker-diarization-3.1`
- **License**: MIT

### 2. WhisperX ⭐ (Best for Word-Level)
- **Best for**: Word-level timestamps with speaker identification
- **Pros**: Combines ASR + diarization, word-level output, no separate ASR needed
- **Cons**: Slower processing, higher memory usage
- **Models**: Whisper (base/large) + pyannote diarization
- **License**: MIT

### 3. SpeechBrain
- **Best for**: Speaker verification and identification
- **Pros**: End-to-end toolkit, good for known speakers
- **Cons**: Requires custom diarization pipeline, not built-in
- **Model**: `speechbrain/spkrec-ecapa-voxceleb`
- **License**: Apache 2.0

## Installation

### Prerequisites

- Python 3.10+
- `uv` package manager
- Hugging Face account (for pyannote.audio and WhisperX diarization)

### Setup

```bash
cd apps/speaker-diarization-benchmark

# Install dependencies with uv
uv sync

# Activate virtual environment
source .venv/bin/activate  # or `uv run` prefix for commands
```

### Hugging Face Token Setup

1. Create a Hugging Face account: https://huggingface.co/
2. Accept the terms for these models:
   - `pyannote/speaker-diarization-3.1`
   - `pyannote/segmentation-3.0` (used by WhisperX)
3. Generate a token: https://huggingface.co/settings/tokens
4. Set the token:
   ```bash
   export HUGGING_FACE_TOKEN="your_token_here"
   ```

## Usage

### Basic Usage

```bash
# Run benchmark on an audio file
uv run python src/benchmark.py path/to/audio.wav

# Specify output directory
uv run python src/benchmark.py path/to/audio.wav --output-dir results/

# Use GPU (if available)
uv run python src/benchmark.py path/to/audio.wav --device cuda
```

### Output Format

The benchmark generates:

1. **JSON Results** (`{audio_name}_results.json`):
   ```json
   {
     "audio_file": "example",
     "results": [
       {
         "solution": "WhisperX",
         "processing_time": 12.34,
         "memory_usage_mb": 2048.5,
         "words": [
           {
             "word": "Hello",
             "start": 0.5,
             "end": 0.8,
             "speaker_id": "SPEAKER_00",
             "confidence": 0.95
           }
         ]
       }
     ]
   }
   ```

2. **CSV Files** (one per solution):
   - Columns: `word`, `start`, `end`, `speaker_id`, `confidence`
   - Easy to import into databases or analysis tools

### Mapping Speaker IDs to User Records

The speaker IDs (e.g., `SPEAKER_00`, `SPEAKER_01`) are arbitrary identifiers. To map them to actual user records:

```python
# Example mapping function
def map_speaker_to_user(speaker_id: str, audio_metadata: dict) -> str:
    """
    Map speaker ID to user record ID.
    
    This is where you'd implement:
    - Voice fingerprinting/matching
    - Known speaker database lookup
    - User enrollment system
    """
    # Example: Simple lookup table
    speaker_mapping = {
        "SPEAKER_00": "user_123",
        "SPEAKER_01": "user_456",
    }
    return speaker_mapping.get(speaker_id, "unknown_user")
```

## Solution Comparison

| Solution | Word-Level | Accuracy | Speed | Memory | Setup Complexity |
|----------|-----------|----------|-------|--------|------------------|
| **pyannote.audio** | ⚠️ Needs ASR | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Medium |
| **WhisperX** | ✅ Built-in | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Low |
| **SpeechBrain** | ❌ Custom | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | High |

### Recommendations

- **For word-level timestamps**: Use **WhisperX** (simplest, all-in-one)
- **For production accuracy**: Use **pyannote.audio** + separate ASR (Whisper)
- **For known speakers**: Use **SpeechBrain** with custom pipeline

## Performance Benchmarks

Example results on a 5-minute audio file with 2 speakers:

```
┌─────────────────┬────────┬───────┬──────────┬──────────┐
│ Solution        │ Status │ Words │ Time (s) │ Memory   │
├─────────────────┼────────┼───────┼──────────┼──────────┤
│ WhisperX        │ ✓      │ 450   │ 45.2     │ 2048.5   │
│ pyannote.audio  │ ✓      │ 0*    │ 12.3     │ 512.0    │
└─────────────────┴────────┴───────┴──────────┴──────────┘

* pyannote provides segments, not words (needs ASR)
```

## Architecture

```
┌─────────────┐
│ Audio Input │
└──────┬──────┘
       │
       ├──► pyannote.audio ──► Segments + Speaker IDs
       │
       ├──► WhisperX ─────────► Words + Timestamps + Speaker IDs
       │
       └──► SpeechBrain ──────► Speaker Verification
       
       └──► Benchmark Runner ─► JSON/CSV Output
```

## Development

### Running Tests

```bash
uv run pytest tests/
```

### Adding New Solutions

1. Create a new pipeline class inheriting from `BaseDiarizationPipeline`
2. Implement the `process()` method
3. Add initialization in `BenchmarkRunner._initialize_pipelines()`

Example:

```python
class NewSolutionPipeline(BaseDiarizationPipeline):
    def __init__(self):
        super().__init__("NewSolution")
        # Initialize model
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        # Process audio
        # Return BenchmarkResult with words
```

## Troubleshooting

### Common Issues

1. **Hugging Face token errors**:
   - Ensure token is set: `export HUGGING_FACE_TOKEN="your_token"`
   - Accept model terms on Hugging Face website

2. **CUDA out of memory**:
   - Use `--device cpu` flag
   - Reduce batch size in WhisperX

3. **Model download failures**:
   - Check internet connection
   - Models download on first use (can be large)

4. **Audio format issues**:
   - Convert to WAV format: `ffmpeg -i input.mp3 output.wav`
   - Ensure mono/stereo compatibility

## License

MIT License - See LICENSE file for details

## References

- [pyannote.audio Documentation](https://github.com/pyannote/pyannote-audio)
- [WhisperX Documentation](https://github.com/m-bain/whisperX)
- [SpeechBrain Documentation](https://speechbrain.github.io/)
- [Speaker Diarization Survey](https://arxiv.org/abs/2101.09624)

## Contributing

Contributions welcome! Please:
1. Add tests for new features
2. Update documentation
3. Follow existing code style
4. Add new solutions via the pipeline interface
