"""
Basic tests for the speaker diarization benchmark.

Note: These are unit tests that don't require actual audio files or models.
Integration tests would require real audio files and model downloads.
"""

import pytest
from pathlib import Path
from src.benchmark import (
    WordTimestamp,
    BenchmarkResult,
    BaseDiarizationPipeline,
)


def test_word_timestamp_creation():
    """Test WordTimestamp dataclass."""
    word = WordTimestamp(
        word="hello",
        start=0.5,
        end=0.8,
        speaker_id="SPEAKER_00",
        confidence=0.95,
    )
    
    assert word.word == "hello"
    assert word.start == 0.5
    assert word.end == 0.8
    assert word.speaker_id == "SPEAKER_00"
    assert word.confidence == 0.95


def test_benchmark_result_creation():
    """Test BenchmarkResult dataclass."""
    words = [
        WordTimestamp("hello", 0.0, 0.5, "SPEAKER_00"),
        WordTimestamp("world", 0.5, 1.0, "SPEAKER_01"),
    ]
    
    result = BenchmarkResult(
        solution_name="test",
        words=words,
        processing_time=1.5,
        memory_usage_mb=512.0,
    )
    
    assert result.solution_name == "test"
    assert len(result.words) == 2
    assert result.processing_time == 1.5
    assert result.memory_usage_mb == 512.0
    assert result.error is None


def test_base_pipeline():
    """Test BaseDiarizationPipeline."""
    class TestPipeline(BaseDiarizationPipeline):
        def process(self, audio_path: str, **kwargs):
            return BenchmarkResult(
                solution_name=self.name,
                words=[],
                processing_time=0.0,
            )
    
    pipeline = TestPipeline("test")
    assert pipeline.name == "test"
    
    # Test that process raises NotImplementedError for base class
    base = BaseDiarizationPipeline("base")
    with pytest.raises(NotImplementedError):
        base.process("test.wav")


def test_benchmark_result_serialization():
    """Test that BenchmarkResult can be converted to dict."""
    result = BenchmarkResult(
        solution_name="test",
        words=[
            WordTimestamp("hello", 0.0, 0.5, "SPEAKER_00", 0.95),
        ],
        processing_time=1.0,
        memory_usage_mb=512.0,
        metadata={"num_speakers": 1},
    )
    
    # Should be able to convert to dict
    result_dict = {
        "solution": result.solution_name,
        "words": [
            {
                "word": w.word,
                "start": w.start,
                "end": w.end,
                "speaker_id": w.speaker_id,
                "confidence": w.confidence,
            }
            for w in result.words
        ],
        "processing_time": result.processing_time,
        "memory_usage_mb": result.memory_usage_mb,
        "metadata": result.metadata,
    }
    
    assert result_dict["solution"] == "test"
    assert len(result_dict["words"]) == 1
    assert result_dict["words"][0]["word"] == "hello"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
