"""
HOW:
  from ingestion.metrics import RunMetrics, track_run
  
  # Option 1: Context manager
  with track_run() as metrics:
      result = expensive_computation()
  print(f"Took {metrics.duration_seconds:.2f}s, peak memory: {metrics.peak_memory_mb:.1f}MB")
  
  # Option 2: Manual
  metrics = RunMetrics()
  metrics.start()
  result = expensive_computation()
  metrics.stop()

  [Inputs]
  - input_duration_seconds: Duration of audio being processed (optional)
  - cost_usd: API cost if applicable (optional)

  [Outputs]
  - RunMetrics object with duration, memory, cost

WHO:
  Claude AI, User
  (Context: Tracking run metrics for InstantDB)

WHAT:
  Utility for tracking processing metrics during transcription/diarization runs.
  Captures:
  - Wall clock processing time
  - Peak memory usage (via psutil)
  - Input audio duration (for real-time factor calculation)
  - API cost (when using paid services)

WHEN:
  2025-12-08
  Last Modified: 2025-12-08

WHERE:
  apps/speaker-diarization-benchmark/ingestion/metrics.py

WHY:
  To provide consistent metrics tracking across all pipeline steps.
  These metrics are stored in InstantDB for analysis:
  - Processing time helps optimize pipeline
  - Memory usage helps with resource planning
  - Cost tracking for API usage budgeting
  - Real-time factor (input_duration / processing_time) for benchmarking
"""

import time
import os
from dataclasses import dataclass, field
from typing import Optional
from contextlib import contextmanager

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class RunMetrics:
    """
    Metrics collected during a processing run.
    
    Attributes:
        input_duration_seconds: Duration of audio processed
        processing_time_seconds: Wall clock time for processing
        peak_memory_mb: Peak memory usage during processing
        cost_usd: API cost if using paid services
        start_time: Unix timestamp when run started
        end_time: Unix timestamp when run ended
    """
    
    input_duration_seconds: Optional[float] = None
    processing_time_seconds: Optional[float] = None
    peak_memory_mb: Optional[float] = None
    cost_usd: Optional[float] = None
    
    # Internal tracking
    _start_time: float = field(default=0.0, repr=False)
    _start_memory: float = field(default=0.0, repr=False)
    _process: Optional[object] = field(default=None, repr=False)
    _running: bool = field(default=False, repr=False)
    
    def start(self) -> "RunMetrics":
        """Start tracking metrics."""
        self._start_time = time.perf_counter()
        self._running = True
        
        if HAS_PSUTIL:
            self._process = psutil.Process(os.getpid())
            self._start_memory = self._process.memory_info().rss / (1024 * 1024)
            self.peak_memory_mb = self._start_memory
        
        return self
    
    def update_memory(self) -> None:
        """Update peak memory if current is higher."""
        if HAS_PSUTIL and self._process and self._running:
            current_mb = self._process.memory_info().rss / (1024 * 1024)
            if self.peak_memory_mb is None or current_mb > self.peak_memory_mb:
                self.peak_memory_mb = current_mb
    
    def stop(self) -> "RunMetrics":
        """Stop tracking and finalize metrics."""
        if not self._running:
            return self
            
        self._running = False
        self.processing_time_seconds = time.perf_counter() - self._start_time
        
        # Final memory check
        self.update_memory()
        
        return self
    
    @property
    def realtime_factor(self) -> Optional[float]:
        """
        Calculate real-time factor: input_duration / processing_time.
        
        A factor > 1 means faster than real-time.
        A factor < 1 means slower than real-time.
        """
        if self.input_duration_seconds and self.processing_time_seconds:
            return self.input_duration_seconds / self.processing_time_seconds
        return None
    
    def to_dict(self) -> dict:
        """Convert to dict for InstantDB storage."""
        return {
            "input_duration_seconds": self.input_duration_seconds,
            "processing_time_seconds": self.processing_time_seconds,
            "peak_memory_mb": self.peak_memory_mb,
            "cost_usd": self.cost_usd,
        }
    
    def __str__(self) -> str:
        parts = []
        if self.processing_time_seconds is not None:
            parts.append(f"{self.processing_time_seconds:.2f}s")
        if self.peak_memory_mb is not None:
            parts.append(f"{self.peak_memory_mb:.1f}MB")
        if self.cost_usd is not None:
            parts.append(f"${self.cost_usd:.4f}")
        if self.realtime_factor is not None:
            parts.append(f"{self.realtime_factor:.1f}x realtime")
        return " | ".join(parts) if parts else "no metrics"


@contextmanager
def track_run(input_duration_seconds: Optional[float] = None):
    """
    Context manager for tracking run metrics.
    
    Usage:
        with track_run(input_duration_seconds=60.0) as metrics:
            result = transcribe(audio_path)
        
        print(f"Processing: {metrics}")
        # "12.34s | 2048.5MB | 4.9x realtime"
    
    Args:
        input_duration_seconds: Duration of audio being processed (for realtime factor)
    
    Yields:
        RunMetrics object (metrics are populated after context exits)
    """
    metrics = RunMetrics(input_duration_seconds=input_duration_seconds)
    metrics.start()
    
    try:
        yield metrics
    finally:
        metrics.stop()


def estimate_api_cost(
    duration_seconds: float,
    service: str,
    model: Optional[str] = None,
) -> Optional[float]:
    """
    Estimate API cost based on audio duration and service.
    
    Args:
        duration_seconds: Duration of audio in seconds
        service: Service name ("openai", "pyannote_api", "assemblyai", "deepgram")
        model: Optional model name for more precise pricing
    
    Returns:
        Estimated cost in USD, or None if pricing unknown
    
    Note:
        These are approximate costs as of Dec 2025. 
        Always verify current pricing with the provider.
    """
    # Pricing per minute (approximate)
    PRICING = {
        # OpenAI Whisper API: $0.006 per minute
        "openai": 0.006 / 60,
        # PyAnnote AI API: ~$0.01 per minute (varies)
        "pyannote_api": 0.01 / 60,
        # AssemblyAI: $0.00025 per second ($0.015/min)
        "assemblyai": 0.00025,
        # Deepgram: $0.0043 per minute (Nova-2)
        "deepgram": 0.0043 / 60,
    }
    
    per_second_cost = PRICING.get(service.lower())
    if per_second_cost is not None:
        return duration_seconds * per_second_cost
    
    return None

