"""
HOW:
  from embeddings.pyannote_extractor import PyAnnoteEmbeddingExtractor
  
  extractor = PyAnnoteEmbeddingExtractor()
  embedding = extractor.extract_embedding(
      audio_path="audio.wav",
      start_time=10.0,
      end_time=15.0,
  )  # Returns numpy array (512,) or None

  [Inputs]
  - audio_path: Path to audio file (wav, mp3, etc.)
  - start_time: Start time in seconds
  - end_time: End time in seconds
  - HF_TOKEN (env): Hugging Face token for pyannote model access

  [Outputs]
  - numpy array of shape (512,) representing the speaker embedding
  - Returns None if extraction fails (segment too short, audio error, etc.)

  [Side Effects]
  - Downloads pyannote model on first use (~400MB)
  - Uses GPU if available (CUDA/MPS), falls back to CPU

WHO:
  Claude AI, User
  (Context: Speaker embedding extraction for identification)

WHAT:
  A wrapper around pyannote's speaker embedding model that extracts 
  512-dimensional voice embeddings from audio segments. These embeddings
  can be compared using cosine similarity for speaker identification.

WHEN:
  2025-12-07

WHERE:
  apps/speaker-diarization-benchmark/src/embeddings/pyannote_extractor.py

WHY:
  To encapsulate the complexity of loading and using pyannote's embedding
  model, including safe_globals for torch deserialization, device selection,
  and audio preprocessing.
"""

import os
import logging
from typing import Optional
from pathlib import Path

import numpy as np
import torch

logger = logging.getLogger(__name__)


def get_safe_globals():
    """Get list of safe globals for torch.load deserialization."""
    import omegaconf
    import pytorch_lightning
    import typing
    import collections
    from pyannote.audio.core.task import Specifications, Problem, Resolution
    import pyannote.audio.core.model
    
    return [
        torch.torch_version.TorchVersion,
        omegaconf.listconfig.ListConfig,
        omegaconf.dictconfig.DictConfig,
        Specifications,
        Problem,
        Resolution,
        pyannote.audio.core.model.Introspection,
        pytorch_lightning.callbacks.early_stopping.EarlyStopping,
        pytorch_lightning.callbacks.model_checkpoint.ModelCheckpoint,
        omegaconf.base.ContainerMetadata,
        omegaconf.base.Metadata,
        omegaconf.nodes.AnyNode,
        omegaconf.nodes.StringNode,
        omegaconf.nodes.IntegerNode,
        omegaconf.nodes.FloatNode,
        omegaconf.nodes.BooleanNode,
        typing.Any,
        list,
        dict,
        collections.defaultdict,
        int,
        float,
        str,
        tuple,
        set,
    ]


class PyAnnoteEmbeddingExtractor:
    """Extracts 512-dimensional speaker embeddings using pyannote."""
    
    # Class-level model cache to avoid reloading
    _model = None
    _inference = None
    _audio_io = None
    
    def __init__(self, hf_token: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the embedding extractor.
        
        Args:
            hf_token: Hugging Face token (defaults to HF_TOKEN env var)
            device: Device to use ('cpu', 'cuda', 'mps'). Auto-detected if None.
        """
        self.hf_token = hf_token or os.environ.get("HF_TOKEN")
        if not self.hf_token:
            logger.warning("No HF_TOKEN found. pyannote models require authentication.")
        
        # Determine device
        if device:
            self.device = torch.device(device)
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            # MPS can be unstable with pyannote, use CPU for reliability
            self.device = torch.device("cpu")
        else:
            self.device = torch.device("cpu")
        
        self._ensure_loaded()
    
    def _ensure_loaded(self):
        """Ensure the model is loaded (lazy loading, shared across instances)."""
        if PyAnnoteEmbeddingExtractor._model is not None:
            return
        
        logger.info("Loading pyannote embedding model...")
        
        from pyannote.audio import Model, Inference
        from pyannote.audio.core.io import Audio
        
        try:
            with torch.serialization.safe_globals(get_safe_globals()):
                model = Model.from_pretrained(
                    "pyannote/embedding",
                    use_auth_token=self.hf_token
                )
            
            model.to(self.device)
            
            inference = Inference(model, window="whole")
            audio_io = Audio(sample_rate=16000, mono="downmix")
            
            # Cache at class level
            PyAnnoteEmbeddingExtractor._model = model
            PyAnnoteEmbeddingExtractor._inference = inference
            PyAnnoteEmbeddingExtractor._audio_io = audio_io
            
            logger.info(f"Loaded pyannote embedding model on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load pyannote model: {e}")
            raise
    
    def extract_embedding(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        min_duration: float = 0.1,
    ) -> Optional[np.ndarray]:
        """
        Extract a speaker embedding from an audio segment.
        
        Args:
            audio_path: Path to the audio file
            start_time: Start time in seconds
            end_time: End time in seconds
            min_duration: Minimum segment duration (default: 0.1s)
        
        Returns:
            numpy array of shape (512,) or None if extraction fails
        """
        duration = end_time - start_time
        if duration < min_duration:
            logger.debug(f"Segment too short ({duration:.3f}s < {min_duration}s)")
            return None
        
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return None
        
        try:
            from pyannote.core import Segment as PyannoteSegment
            
            # Crop audio to segment
            waveform, sample_rate = self._audio_io.crop(
                audio_path,
                PyannoteSegment(start_time, end_time)
            )
            
            # Extract embedding
            embedding = self._inference({"waveform": waveform, "sample_rate": sample_rate})
            
            # embedding is shape (1, 512), flatten to (512,)
            embedding_np = embedding.flatten()
            
            # Validate embedding
            if np.isnan(embedding_np).any() or np.isinf(embedding_np).any():
                logger.warning(f"Invalid embedding (NaN/Inf) for segment {start_time:.1f}-{end_time:.1f}s")
                return None
            
            return embedding_np
            
        except Exception as e:
            logger.warning(f"Failed to extract embedding for {start_time:.1f}-{end_time:.1f}s: {e}")
            return None
    
    def extract_embeddings_batch(
        self,
        audio_path: str,
        segments: list[tuple[float, float]],
        min_duration: float = 0.1,
    ) -> list[tuple[int, np.ndarray]]:
        """
        Extract embeddings for multiple segments.
        
        Args:
            audio_path: Path to the audio file
            segments: List of (start_time, end_time) tuples
            min_duration: Minimum segment duration
        
        Returns:
            List of (segment_index, embedding) tuples for successful extractions
        """
        results = []
        
        for i, (start, end) in enumerate(segments):
            embedding = self.extract_embedding(audio_path, start, end, min_duration)
            if embedding is not None:
                results.append((i, embedding))
        
        return results


if __name__ == "__main__":
    # Quick test
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python pyannote_extractor.py <audio_file> [start_time] [end_time]")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    start_time = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    end_time = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
    
    extractor = PyAnnoteEmbeddingExtractor()
    
    print(f"Extracting embedding from {audio_path} ({start_time:.1f}s - {end_time:.1f}s)...")
    embedding = extractor.extract_embedding(audio_path, start_time, end_time)
    
    if embedding is not None:
        print(f"✅ Embedding shape: {embedding.shape}")
        print(f"   First 5 values: {embedding[:5]}")
        print(f"   L2 norm: {np.linalg.norm(embedding):.4f}")
    else:
        print("❌ Failed to extract embedding")

