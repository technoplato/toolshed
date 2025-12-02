from enum import Enum
from pydantic import BaseModel, Field

class WhisperModel(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class WhisperConfig(BaseModel):
    """Configuration for the whisper.cpp transcriber."""
    model: WhisperModel = Field(default=WhisperModel.BASE, description="Whisper model to use")
    n_threads: int = Field(default=4, description="Number of threads to use for transcription")
    print_realtime: bool = Field(default=True, description="Whether to print transcription in real-time")
    print_progress: bool = Field(default=True, description="Whether to print progress bar")

class BatchConfig(BaseModel):
    """Configuration for the batch processing workflow."""
    limit: int = Field(default=5, description="Number of videos to fetch from history")
    max_concurrent: int = Field(default=3, description="Maximum number of concurrent processings")
    max_duration_hours: int = Field(default=5, description="Maximum duration of videos to process in hours")
    whisper_config: WhisperConfig = Field(default_factory=WhisperConfig, description="Whisper configuration")
