# Open Source Speaker Diarization Solutions

This document provides detailed information about each solution benchmarked in this tool.

## Solution Comparison Matrix

| Feature | pyannote.audio | WhisperX | SpeechBrain | Resemblyzer |
|---------|---------------|----------|-------------|-------------|
| **Word-level timestamps** | ❌ (needs ASR) | ✅ | ❌ | ❌ |
| **Speaker diarization** | ✅ | ✅ | ⚠️ (custom) | ❌ |
| **Speaker identification** | ⚠️ (separate) | ⚠️ (separate) | ✅ | ✅ |
| **ASR included** | ❌ | ✅ | ❌ | ❌ |
| **Accuracy** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Memory usage** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Ease of use** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Documentation** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Active maintenance** | ✅ | ✅ | ✅ | ⚠️ |

## Detailed Solution Information

### 1. pyannote.audio

**GitHub**: https://github.com/pyannote/pyannote-audio  
**License**: MIT  
**Language**: Python  

#### Strengths
- Industry standard for speaker diarization
- Highly accurate segmentation
- Well-maintained and actively developed
- Extensive documentation
- Pre-trained models available

#### Weaknesses
- Requires Hugging Face token
- Segment-level only (needs separate ASR for words)
- More complex setup
- Requires GPU for best performance

#### Use Cases
- Production speaker diarization systems
- When you need highest accuracy
- When you have separate ASR pipeline
- Research and academic projects

#### Setup Requirements
```bash
pip install pyannote.audio
# Accept model terms on Hugging Face
# Set HUGGING_FACE_TOKEN
```

#### Model Information
- **Segmentation**: `pyannote/segmentation-3.0`
- **Diarization**: `pyannote/speaker-diarization-3.1`
- **Size**: ~500MB per model
- **Format**: PyTorch

---

### 2. WhisperX

**GitHub**: https://github.com/m-bain/whisperX  
**License**: MIT  
**Language**: Python  

#### Strengths
- **All-in-one solution**: ASR + diarization
- Word-level timestamps built-in
- Easy to use
- Good accuracy
- No separate ASR needed

#### Weaknesses
- Slower processing (runs ASR + diarization)
- Higher memory usage
- Requires both Whisper and pyannote models
- Less flexible than separate components

#### Use Cases
- Quick prototyping
- When you need word-level timestamps
- When you don't have existing ASR
- End-to-end transcription projects

#### Setup Requirements
```bash
pip install whisperx
# Accept model terms on Hugging Face
# Set HUGGING_FACE_TOKEN
```

#### Model Information
- **ASR**: OpenAI Whisper (base/large)
- **Diarization**: pyannote models
- **Size**: ~1-3GB total
- **Format**: PyTorch

---

### 3. SpeechBrain

**GitHub**: https://github.com/speechbrain/speechbrain  
**License**: Apache 2.0  
**Language**: Python  

#### Strengths
- End-to-end speech processing toolkit
- Excellent for speaker verification
- Good for known speaker identification
- Modular architecture
- Well-documented

#### Weaknesses
- No built-in diarization (requires custom pipeline)
- More complex for diarization use case
- Better suited for verification than diarization
- Requires more custom code

#### Use Cases
- Speaker verification systems
- Known speaker identification
- Voice authentication
- Custom diarization pipelines

#### Setup Requirements
```bash
pip install speechbrain
# Models download automatically
```

#### Model Information
- **Verification**: `speechbrain/spkrec-ecapa-voxceleb`
- **Size**: ~100MB
- **Format**: PyTorch

---

### 4. Resemblyzer

**GitHub**: https://github.com/resemble-ai/Resemblyzer  
**License**: MIT  
**Language**: Python  

#### Strengths
- Simple API
- Good for speaker verification
- Lightweight
- Easy to integrate

#### Weaknesses
- No diarization (verification only)
- Less actively maintained
- Limited documentation
- Requires custom diarization pipeline

#### Use Cases
- Speaker verification
- Voice similarity checking
- Simple speaker matching

#### Setup Requirements
```bash
pip install resemblyzer
```

#### Model Information
- **Embedding**: Pre-trained speaker encoder
- **Size**: ~50MB
- **Format**: PyTorch

---

## Recommendations by Use Case

### "I need word-level timestamps with speaker IDs"
**→ Use WhisperX**
- Simplest solution
- All-in-one package
- No separate ASR needed

### "I need highest accuracy for production"
**→ Use pyannote.audio + separate ASR (Whisper)**
- Best diarization accuracy
- More control
- Can optimize each component separately

### "I need to identify known speakers"
**→ Use SpeechBrain or Resemblyzer**
- Better suited for verification
- Can match against known speaker database
- Use with custom diarization pipeline

### "I need fastest processing"
**→ Use pyannote.audio (segment-level only)**
- Fastest diarization
- Skip word-level if not needed
- Lower memory usage

### "I need lowest memory usage"
**→ Use pyannote.audio or SpeechBrain**
- More efficient models
- Can run on CPU
- Lower resource requirements

## Performance Benchmarks

*Note: Actual performance depends on hardware, audio length, and number of speakers*

### Typical Performance (5-minute audio, 2 speakers, CPU)

| Solution | Processing Time | Memory Usage | Accuracy |
|----------|----------------|--------------|----------|
| pyannote.audio | 10-15s | 500-800 MB | 95%+ |
| WhisperX | 40-60s | 2-4 GB | 90-95% |
| SpeechBrain* | N/A | 200-400 MB | N/A |

*SpeechBrain requires custom diarization pipeline

### Typical Performance (5-minute audio, 2 speakers, GPU)

| Solution | Processing Time | Memory Usage | Accuracy |
|----------|----------------|--------------|----------|
| pyannote.audio | 3-5s | 1-2 GB | 95%+ |
| WhisperX | 15-25s | 3-6 GB | 90-95% |
| SpeechBrain* | N/A | 500 MB - 1 GB | N/A |

## Integration Examples

### pyannote.audio + Whisper
```python
# 1. Diarize with pyannote
diarization = pipeline(audio_path)

# 2. Transcribe with Whisper
transcription = whisper.transcribe(audio_path)

# 3. Align and assign speakers
# (requires custom alignment logic)
```

### WhisperX (All-in-one)
```python
# Single call does everything
result = whisperx.transcribe_with_diarization(audio_path)
# Result includes words with speaker IDs
```

### SpeechBrain (Verification)
```python
# 1. Extract speaker embeddings
embedding = model.encode_batch(audio)

# 2. Compare with known speakers
similarity = compare(embedding, known_speakers)

# 3. Identify speaker
speaker_id = find_best_match(similarity)
```

## Additional Resources

- [pyannote.audio Tutorial](https://github.com/pyannote/pyannote-audio#quick-start)
- [WhisperX Documentation](https://github.com/m-bain/whisperX#usage)
- [SpeechBrain Tutorials](https://speechbrain.github.io/tutorial_basics.html)
- [Speaker Diarization Survey Paper](https://arxiv.org/abs/2101.09624)
