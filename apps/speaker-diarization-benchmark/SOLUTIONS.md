# Open Source Speaker Diarization Solutions

This document provides detailed information about each solution benchmarked in this tool.

## Solution Comparison Matrix

| Feature | pyannote.audio | WhisperX | SpeechBrain-Verification | SpeechBrain-Diarization | Resemblyzer | NeMo |
|---------|---------------|----------|--------------------------|------------------------|-------------|------|
| **Word-level timestamps** | ❌ (needs ASR) | ✅ | ❌ | ❌ | ❌ | ⚠️ (custom) |
| **Speaker diarization** | ✅ | ✅ | ⚠️ (custom) | ⚠️ (if available) | ⚠️ (custom) | ✅ |
| **Speaker identification** | ⚠️ (separate) | ⚠️ (separate) | ✅ | ⚠️ | ✅ | ⚠️ |
| **ASR included** | ❌ | ✅ | ❌ | ❌ | ❌ | ⚠️ |
| **Accuracy** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Memory usage** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Ease of use** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Documentation** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Active maintenance** | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ |

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

### 3. SpeechBrain-Verification

**GitHub**: https://github.com/speechbrain/speechbrain  
**License**: Apache 2.0  
**Language**: Python  

#### Strengths
- End-to-end speech processing toolkit
- Excellent speaker embeddings (ECAPA-TDNN)
- Good for known speaker identification
- Modular architecture
- Well-documented
- Fast inference

#### Weaknesses
- Requires custom segmentation pipeline
- Needs clustering (scikit-learn) for diarization
- Better suited for verification than diarization
- Segment-level output (not word-level)

#### Use Cases
- Speaker verification systems
- Known speaker identification
- Voice authentication
- Custom diarization pipelines with embeddings

#### Setup Requirements
```bash
pip install speechbrain scikit-learn
# Models download automatically
```

#### Model Information
- **Verification**: `speechbrain/spkrec-ecapa-voxceleb`
- **Size**: ~100MB
- **Format**: PyTorch
- **Implementation**: Uses speaker embeddings + AgglomerativeClustering

### 4. SpeechBrain-Diarization

**GitHub**: https://github.com/speechbrain/speechbrain  
**License**: Apache 2.0  
**Language**: Python  

#### Strengths
- Integrated with SpeechBrain ecosystem
- May have built-in diarization models
- Well-documented

#### Weaknesses
- May require additional setup/configuration
- Availability depends on SpeechBrain version
- May not be available in all installations

#### Use Cases
- When SpeechBrain diarization models are available
- Integrated SpeechBrain workflows

#### Setup Requirements
```bash
pip install speechbrain
# Check SpeechBrain documentation for diarization models
```

#### Model Information
- **Status**: Depends on SpeechBrain version and available models
- **Note**: This pipeline checks for availability but may require additional setup

---

### 5. Resemblyzer

**GitHub**: https://github.com/resemble-ai/Resemblyzer  
**License**: MIT  
**Language**: Python  

#### Strengths
- Simple API
- Good speaker embeddings
- Lightweight (~50MB model)
- Easy to integrate
- Fast inference

#### Weaknesses
- Requires custom segmentation pipeline
- Needs clustering for diarization
- Less actively maintained
- Limited documentation
- Segment-level output (not word-level)

#### Use Cases
- Speaker verification
- Voice similarity checking
- Simple speaker matching
- Lightweight diarization with clustering

#### Setup Requirements
```bash
pip install resemblyzer scikit-learn
```

#### Model Information
- **Embedding**: Pre-trained speaker encoder
- **Size**: ~50MB
- **Format**: PyTorch
- **Implementation**: Uses VoiceEncoder + AgglomerativeClustering with cosine similarity

### 6. NeMo (NVIDIA)

**GitHub**: https://github.com/NVIDIA/NeMo  
**License**: Apache 2.0  
**Language**: Python  

#### Strengths
- Enterprise-grade toolkit
- NVIDIA's production solution
- Well-optimized for GPU
- Comprehensive documentation
- Active development

#### Weaknesses
- Complex setup
- Requires NeMo toolkit installation
- Larger dependency footprint
- May require additional configuration

#### Use Cases
- Enterprise speaker diarization
- Production systems
- GPU-accelerated processing
- When using other NeMo components

#### Setup Requirements
```bash
pip install nemo_toolkit[all]
# Additional setup may be required - see NeMo documentation
```

#### Model Information
- **Models**: Various NeMo diarization models available
- **Size**: Varies by model
- **Format**: PyTorch
- **Note**: Requires proper NeMo configuration and model paths

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
**→ Use SpeechBrain-Verification or Resemblyzer**
- Better suited for verification
- Can match against known speaker database
- Use with custom diarization pipeline
- Resemblyzer is simpler, SpeechBrain-Verification is more accurate

### "I need fastest processing"
**→ Use pyannote.audio (segment-level only)**
- Fastest diarization
- Skip word-level if not needed
- Lower memory usage

### "I need lowest memory usage"
**→ Use Resemblyzer or SpeechBrain-Verification**
- More efficient models
- Can run on CPU
- Lower resource requirements
- Resemblyzer is smallest (~50MB)

### "I need lightweight speaker identification"
**→ Use Resemblyzer**
- Smallest model size
- Simple API
- Fast inference
- Good for verification tasks

### "I need enterprise-grade solution"
**→ Use NeMo**
- NVIDIA's production toolkit
- Well-optimized
- Comprehensive features
- Requires more setup

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
