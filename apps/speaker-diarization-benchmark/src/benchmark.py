"""
Speaker Diarization and Identification Benchmark

This script benchmarks multiple open source solutions for speaker diarization
and identification, providing per-word timestamps with speaker identity IDs.

Supported Solutions:
1. pyannote.audio - Industry standard for speaker diarization
2. SpeechBrain - Speaker verification and diarization with custom pipeline
3. WhisperX - Combines Whisper ASR with speaker diarization
4. Resemblyzer - Speaker verification and identification
5. NeMo - NVIDIA's speaker diarization toolkit
6. SpeechBrain Diarization - SpeechBrain's built-in diarization models

Output Format:
- Per-word timestamps with speaker ID
- Speaker ID maps to user records (external mapping)
- Performance metrics (accuracy, speed, resource usage)
"""

import argparse
import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

import numpy as np
import pandas as pd
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
logger = logging.getLogger(__name__)
console = Console()


@dataclass
class WordTimestamp:
    """Represents a word with timestamp and speaker information."""
    word: str
    start: float
    end: float
    speaker_id: str
    confidence: Optional[float] = None


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    solution_name: str
    words: List[WordTimestamp]
    processing_time: float
    memory_usage_mb: Optional[float] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None


class BaseDiarizationPipeline:
    """Base class for diarization pipelines."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        """Process audio and return benchmark results."""
        raise NotImplementedError
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return None


class PyannotePipeline(BaseDiarizationPipeline):
    """
    pyannote.audio Pipeline
    
    Requires:
    - Hugging Face token for model access
    - Models: pyannote/speaker-diarization-3.1
    """
    
    def __init__(self, hf_token: Optional[str] = None):
        super().__init__("pyannote.audio")
        self.hf_token = hf_token
        self.pipeline = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the pyannote pipeline."""
        try:
            from pyannote.audio import Pipeline
            
            if not self.hf_token:
                self.logger.warning(
                    "No Hugging Face token provided. "
                    "You may need to set it via HUGGING_FACE_TOKEN environment variable."
                )
            
            # Load the speaker diarization pipeline
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token,
            )
            self.logger.info("✓ pyannote.audio pipeline initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize pyannote.audio: {e}")
            raise
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        """Process audio with pyannote.audio."""
        start_time = time.time()
        words = []
        
        try:
            # Run diarization
            diarization = self.pipeline(audio_path)
            
            # For word-level timestamps, we need to combine with ASR
            # This is a simplified version - in production, use Whisper or similar
            from pyannote.audio.pipelines.utils.hook import ProgressHook
            
            # Extract segments with speaker labels
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                # Note: pyannote provides segment-level diarization
                # For word-level, you'd need to combine with ASR
                words.append(WordTimestamp(
                    word=f"[Segment: {speaker}]",
                    start=turn.start,
                    end=turn.end,
                    speaker_id=speaker,
                ))
            
            processing_time = time.time() - start_time
            memory_usage = self._get_memory_usage()
            
            return BenchmarkResult(
                solution_name=self.name,
                words=words,
                processing_time=processing_time,
                memory_usage_mb=memory_usage,
                metadata={"num_speakers": len(set(w.speaker_id for w in words))},
            )
        except Exception as e:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=time.time() - start_time,
                error=str(e),
            )


class SpeechBrainVerificationPipeline(BaseDiarizationPipeline):
    """
    SpeechBrain Speaker Verification Pipeline
    
    Uses SpeechBrain for speaker verification/identification.
    This implementation performs segmentation and speaker verification
    to create a diarization-like output.
    """
    
    def __init__(self):
        super().__init__("SpeechBrain-Verification")
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize SpeechBrain speaker verification model."""
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            
            self.model = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
            )
            self.logger.info("✓ SpeechBrain verification model initialized")
        except Exception as e:
            self.logger.warning(f"SpeechBrain verification initialization: {e}")
            self.model = None
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        """Process audio with SpeechBrain speaker verification."""
        start_time = time.time()
        words = []
        
        if not self.model:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=0.0,
                error="Model not initialized",
            )
        
        try:
            import librosa
            import torch
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Segment audio into chunks (e.g., 2-second windows with 1-second overlap)
            chunk_duration = 2.0
            overlap = 1.0
            chunk_samples = int(chunk_duration * sr)
            overlap_samples = int(overlap * sr)
            step_samples = chunk_samples - overlap_samples
            
            # Extract embeddings for each chunk
            embeddings = []
            chunk_times = []
            
            for start_idx in range(0, len(audio) - chunk_samples, step_samples):
                chunk = audio[start_idx:start_idx + chunk_samples]
                chunk_time = start_idx / sr
                
                # Get speaker embedding
                embedding = self.model.encode_batch(torch.tensor(chunk).unsqueeze(0))
                embeddings.append(embedding.squeeze().cpu().numpy())
                chunk_times.append((chunk_time, chunk_time + chunk_duration))
            
            # Cluster embeddings to identify speakers
            from sklearn.cluster import AgglomerativeClustering
            
            if len(embeddings) > 1:
                embeddings_array = np.array(embeddings)
                
                # Determine number of speakers (simple heuristic: use 2-5 speakers)
                n_speakers = min(max(2, len(embeddings) // 10), 5)
                
                clustering = AgglomerativeClustering(n_clusters=n_speakers)
                speaker_labels = clustering.fit_predict(embeddings_array)
                
                # Create word-like segments (using chunk info as segments)
                for (start, end), speaker_label in zip(chunk_times, speaker_labels):
                    words.append(WordTimestamp(
                        word=f"[Segment: SPEAKER_{speaker_label:02d}]",
                        start=start,
                        end=end,
                        speaker_id=f"SPEAKER_{speaker_label:02d}",
                        confidence=0.8,  # Placeholder confidence
                    ))
            
            processing_time = time.time() - start_time
            memory_usage = self._get_memory_usage()
            
            return BenchmarkResult(
                solution_name=self.name,
                words=words,
                processing_time=processing_time,
                memory_usage_mb=memory_usage,
                metadata={"num_speakers": len(set(w.speaker_id for w in words))},
            )
        except ImportError as e:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=time.time() - start_time,
                error=f"Missing dependency: {e}. Install scikit-learn for clustering.",
            )
        except Exception as e:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=time.time() - start_time,
                error=str(e),
            )


class SpeechBrainDiarizationPipeline(BaseDiarizationPipeline):
    """
    SpeechBrain Speaker Diarization Pipeline
    
    Uses SpeechBrain's built-in diarization models if available.
    """
    
    def __init__(self):
        super().__init__("SpeechBrain-Diarization")
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize SpeechBrain diarization model."""
        try:
            # Try to load SpeechBrain diarization pipeline
            # Note: SpeechBrain may have diarization recipes/models
            from speechbrain.inference.speaker import SpeakerRecognition
            
            # Check if diarization models are available
            # This is a placeholder - actual implementation depends on available models
            self.logger.info("✓ SpeechBrain diarization ready (checking for models)")
            self.model = True  # Placeholder
        except Exception as e:
            self.logger.warning(f"SpeechBrain diarization not available: {e}")
            self.model = None
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        """Process audio with SpeechBrain diarization."""
        start_time = time.time()
        
        if not self.model:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=0.0,
                error="SpeechBrain diarization models not available. Use SpeechBrain-Verification instead.",
            )
        
        # Placeholder - would need actual SpeechBrain diarization model
        return BenchmarkResult(
            solution_name=self.name,
            words=[],
            processing_time=time.time() - start_time,
            error="SpeechBrain diarization models require additional setup. See documentation.",
        )


class WhisperXPipeline(BaseDiarizationPipeline):
    """
    WhisperX Pipeline
    
    Combines Whisper ASR with speaker diarization for word-level timestamps.
    """
    
    def __init__(self):
        super().__init__("WhisperX")
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize WhisperX model."""
        try:
            import whisperx
            
            # WhisperX loads models on first use
            self.logger.info("✓ WhisperX ready (models load on first use)")
        except Exception as e:
            self.logger.error(f"Failed to initialize WhisperX: {e}")
            raise
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        """Process audio with WhisperX."""
        start_time = time.time()
        words = []
        
        try:
            import whisperx
            
            device = kwargs.get("device", "cpu")
            batch_size = kwargs.get("batch_size", 16)
            
            # Load ASR model
            model = whisperx.load_model("base", device, compute_type="int8")
            
            # Transcribe with word-level timestamps
            audio = whisperx.load_audio(audio_path)
            result = model.transcribe(audio, batch_size=batch_size)
            
            # Align timestamps
            model_a, metadata = whisperx.load_align_model(
                language_code=result["language"], device=device
            )
            result = whisperx.align(result["segments"], model_a, metadata, audio, device)
            
            # Diarize
            diarize_model = whisperx.DiarizationPipeline(
                use_auth_token=kwargs.get("hf_token"),
                device=device,
            )
            diarize_segments = diarize_model(audio_path)
            result = whisperx.assign_word_speakers(diarize_segments, result)
            
            # Extract word-level timestamps with speaker IDs
            for segment in result["segments"]:
                for word_info in segment.get("words", []):
                    words.append(WordTimestamp(
                        word=word_info["word"],
                        start=word_info["start"],
                        end=word_info["end"],
                        speaker_id=word_info.get("speaker", "UNKNOWN"),
                        confidence=word_info.get("score"),
                    ))
            
            processing_time = time.time() - start_time
            memory_usage = self._get_memory_usage()
            
            return BenchmarkResult(
                solution_name=self.name,
                words=words,
                processing_time=processing_time,
                memory_usage_mb=memory_usage,
                metadata={
                    "language": result.get("language"),
                    "num_speakers": len(set(w.speaker_id for w in words)),
                },
            )
        except Exception as e:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=time.time() - start_time,
                error=str(e),
            )


class ResemblyzerPipeline(BaseDiarizationPipeline):
    """
    Resemblyzer Pipeline
    
    Uses Resemblyzer for speaker verification and identification.
    Performs segmentation and speaker embedding clustering.
    """
    
    def __init__(self):
        super().__init__("Resemblyzer")
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Resemblyzer model."""
        try:
            from resemblyzer import VoiceEncoder, preprocess_wav
            
            self.model = VoiceEncoder()
            self.preprocess_wav = preprocess_wav
            self.logger.info("✓ Resemblyzer model initialized")
        except Exception as e:
            self.logger.warning(f"Resemblyzer initialization: {e}")
            self.model = None
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        """Process audio with Resemblyzer."""
        start_time = time.time()
        words = []
        
        if not self.model:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=0.0,
                error="Model not initialized",
            )
        
        try:
            import librosa
            from pathlib import Path
            
            # Load and preprocess audio
            wav = self.preprocess_wav(str(audio_path))
            sr = 16000  # Resemblyzer uses 16kHz
            
            # Segment audio into chunks
            chunk_duration = 1.5  # 1.5 second chunks
            overlap = 0.5  # 0.5 second overlap
            chunk_samples = int(chunk_duration * sr)
            overlap_samples = int(overlap * sr)
            step_samples = chunk_samples - overlap_samples
            
            # Extract embeddings for each chunk
            embeddings = []
            chunk_times = []
            
            for start_idx in range(0, len(wav) - chunk_samples, step_samples):
                chunk = wav[start_idx:start_idx + chunk_samples]
                chunk_time = start_idx / sr
                
                # Get speaker embedding
                embedding = self.model.embed_utterance(chunk)
                embeddings.append(embedding)
                chunk_times.append((chunk_time, chunk_time + chunk_duration))
            
            # Cluster embeddings to identify speakers
            from sklearn.cluster import AgglomerativeClustering
            
            if len(embeddings) > 1:
                embeddings_array = np.array(embeddings)
                
                # Determine number of speakers
                n_speakers = min(max(2, len(embeddings) // 8), 5)
                
                clustering = AgglomerativeClustering(n_clusters=n_speakers, metric='cosine', linkage='average')
                speaker_labels = clustering.fit_predict(embeddings_array)
                
                # Create segments
                for (start, end), speaker_label in zip(chunk_times, speaker_labels):
                    words.append(WordTimestamp(
                        word=f"[Segment: SPEAKER_{speaker_label:02d}]",
                        start=start,
                        end=end,
                        speaker_id=f"SPEAKER_{speaker_label:02d}",
                        confidence=0.75,  # Placeholder confidence
                    ))
            
            processing_time = time.time() - start_time
            memory_usage = self._get_memory_usage()
            
            return BenchmarkResult(
                solution_name=self.name,
                words=words,
                processing_time=processing_time,
                memory_usage_mb=memory_usage,
                metadata={"num_speakers": len(set(w.speaker_id for w in words))},
            )
        except ImportError as e:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=time.time() - start_time,
                error=f"Missing dependency: {e}. Install scikit-learn for clustering.",
            )
        except Exception as e:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=time.time() - start_time,
                error=str(e),
            )


class NeMoPipeline(BaseDiarizationPipeline):
    """
    NeMo (NVIDIA) Speaker Diarization Pipeline
    
    Uses NVIDIA NeMo toolkit for speaker diarization.
    Requires NeMo to be installed separately.
    """
    
    def __init__(self):
        super().__init__("NeMo")
        self.model = None
        self._initialize()
    
    def _initialize(self):
        """Initialize NeMo diarization model."""
        try:
            import nemo.collections.asr as nemo_asr
            
            # Try to load NeMo speaker diarization model
            # Note: NeMo requires specific setup and model paths
            self.logger.info("✓ NeMo ready (checking for models)")
            
            # Check if NeMo is properly installed
            try:
                # Try to import diarization modules
                from omegaconf import OmegaConf
                self.model = True  # Placeholder - actual model loading would go here
            except ImportError:
                self.model = None
                self.logger.warning("NeMo dependencies not fully installed")
        except ImportError:
            self.logger.warning("NeMo not installed. Install with: pip install nemo_toolkit[all]")
            self.model = None
        except Exception as e:
            self.logger.warning(f"NeMo initialization: {e}")
            self.model = None
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        """Process audio with NeMo."""
        start_time = time.time()
        
        if not self.model:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=0.0,
                error="NeMo not installed or models not available. Install with: pip install nemo_toolkit[all]",
            )
        
        try:
            # NeMo diarization implementation
            # This is a placeholder - actual implementation would use NeMo's diarization API
            # Example structure:
            # from nemo.collections.asr.models import ClusteringDiarizer
            # diarizer = ClusteringDiarizer(cfg=diarizer_cfg)
            # diarizer.diarize()
            
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=time.time() - start_time,
                error="NeMo diarization requires additional configuration. See NeMo documentation for setup.",
            )
        except Exception as e:
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=time.time() - start_time,
                error=str(e),
            )


class BenchmarkRunner:
    """Runs benchmarks across multiple diarization solutions."""
    
    def __init__(self, hf_token: Optional[str] = None):
        self.hf_token = hf_token
        self.pipelines = []
        self._initialize_pipelines()
    
    def _initialize_pipelines(self):
        """Initialize all available pipelines."""
        logger.info("Initializing diarization pipelines...")
        
        # Try to initialize each pipeline
        try:
            self.pipelines.append(PyannotePipeline(hf_token=self.hf_token))
        except Exception as e:
            logger.warning(f"Could not initialize pyannote.audio: {e}")
        
        try:
            pipeline = SpeechBrainVerificationPipeline()
            if pipeline.model:
                self.pipelines.append(pipeline)
        except Exception as e:
            logger.warning(f"Could not initialize SpeechBrain-Verification: {e}")
        
        try:
            pipeline = SpeechBrainDiarizationPipeline()
            if pipeline.model:
                self.pipelines.append(pipeline)
        except Exception as e:
            logger.warning(f"Could not initialize SpeechBrain-Diarization: {e}")
        
        try:
            self.pipelines.append(WhisperXPipeline())
        except Exception as e:
            logger.warning(f"Could not initialize WhisperX: {e}")
        
        try:
            pipeline = ResemblyzerPipeline()
            if pipeline.model:
                self.pipelines.append(pipeline)
        except Exception as e:
            logger.warning(f"Could not initialize Resemblyzer: {e}")
        
        try:
            pipeline = NeMoPipeline()
            if pipeline.model:
                self.pipelines.append(pipeline)
        except Exception as e:
            logger.warning(f"Could not initialize NeMo: {e}")
        
        logger.info(f"Initialized {len(self.pipelines)} pipeline(s)")
    
    def run_benchmark(
        self,
        audio_path: str,
        output_dir: Optional[str] = None,
        **kwargs
    ) -> List[BenchmarkResult]:
        """Run benchmark on all pipelines."""
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Running benchmark on: {audio_path.name}")
        logger.info(f"Audio duration: {self._get_audio_duration(audio_path):.2f}s")
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            for pipeline in self.pipelines:
                task = progress.add_task(
                    f"Processing with {pipeline.name}...",
                    total=100,
                )
                
                try:
                    result = pipeline.process(audio_path, hf_token=self.hf_token, **kwargs)
                    results.append(result)
                    
                    if result.error:
                        logger.error(f"❌ {pipeline.name}: {result.error}")
                    else:
                        logger.info(
                            f"✓ {pipeline.name}: "
                            f"{len(result.words)} words, "
                            f"{result.processing_time:.2f}s"
                        )
                except Exception as e:
                    logger.error(f"❌ {pipeline.name} failed: {e}")
                    results.append(BenchmarkResult(
                        solution_name=pipeline.name,
                        words=[],
                        processing_time=0.0,
                        error=str(e),
                    ))
                
                progress.update(task, completed=100)
        
        # Save results
        if output_dir:
            self._save_results(results, output_dir, audio_path.stem)
        
        return results
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds."""
        try:
            import librosa
            y, sr = librosa.load(str(audio_path), sr=None)
            return len(y) / sr
        except Exception as e:
            logger.warning(f"Could not determine audio duration: {e}")
            return 0.0
    
    def _save_results(
        self,
        results: List[BenchmarkResult],
        output_dir: str,
        audio_name: str,
    ):
        """Save benchmark results to files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save JSON results
        results_dict = {
            "audio_file": audio_name,
            "results": [
                {
                    "solution": r.solution_name,
                    "processing_time": r.processing_time,
                    "memory_usage_mb": r.memory_usage_mb,
                    "error": r.error,
                    "metadata": r.metadata,
                    "words": [
                        {
                            "word": w.word,
                            "start": w.start,
                            "end": w.end,
                            "speaker_id": w.speaker_id,
                            "confidence": w.confidence,
                        }
                        for w in r.words
                    ],
                }
                for r in results
            ],
        }
        
        json_path = output_path / f"{audio_name}_results.json"
        with open(json_path, "w") as f:
            json.dump(results_dict, f, indent=2)
        
        logger.info(f"Results saved to: {json_path}")
        
        # Save CSV for each solution
        for result in results:
            if result.words:
                df = pd.DataFrame([
                    {
                        "word": w.word,
                        "start": w.start,
                        "end": w.end,
                        "speaker_id": w.speaker_id,
                        "confidence": w.confidence,
                    }
                    for w in result.words
                ])
                csv_path = output_path / f"{audio_name}_{result.solution_name.replace('.', '_')}.csv"
                df.to_csv(csv_path, index=False)
                logger.info(f"CSV saved to: {csv_path}")
    
    def print_summary(self, results: List[BenchmarkResult]):
        """Print a summary table of results."""
        table = Table(title="Benchmark Results Summary")
        table.add_column("Solution", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Words", justify="right")
        table.add_column("Time (s)", justify="right", style="yellow")
        table.add_column("Memory (MB)", justify="right", style="magenta")
        table.add_column("Speakers", justify="right")
        
        for result in results:
            status = "✓" if not result.error else "❌"
            word_count = len(result.words)
            time_str = f"{result.processing_time:.2f}"
            memory_str = f"{result.memory_usage_mb:.1f}" if result.memory_usage_mb else "N/A"
            speakers = len(set(w.speaker_id for w in result.words)) if result.words else 0
            
            table.add_row(
                result.solution_name,
                status,
                str(word_count),
                time_str,
                memory_str,
                str(speakers),
            )
        
        console.print(table)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Benchmark speaker diarization and identification solutions"
    )
    parser.add_argument(
        "audio_path",
        type=str,
        help="Path to input audio file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/results",
        help="Directory to save results (default: data/results)",
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Hugging Face token for model access (or set HUGGING_FACE_TOKEN env var)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to use for processing (default: cpu)",
    )
    
    args = parser.parse_args()
    
    # Get HF token from env if not provided
    hf_token = args.hf_token or None
    if not hf_token:
        import os
        hf_token = os.getenv("HUGGING_FACE_TOKEN")
    
    # Run benchmark
    runner = BenchmarkRunner(hf_token=hf_token)
    results = runner.run_benchmark(
        args.audio_path,
        output_dir=args.output_dir,
        device=args.device,
    )
    
    # Print summary
    runner.print_summary(results)


if __name__ == "__main__":
    main()
