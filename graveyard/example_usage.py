"""
Example usage of the speaker diarization benchmark.

This script demonstrates how to:
1. Run benchmarks programmatically
2. Process results
3. Map speaker IDs to user records
"""

import json
from pathlib import Path
from src.benchmark import BenchmarkRunner, WordTimestamp


def example_basic_usage():
    """Basic usage example."""
    print("=" * 60)
    print("Example 1: Basic Benchmark Usage")
    print("=" * 60)
    
    # Initialize runner (will auto-detect HF token from env)
    import os
    runner = BenchmarkRunner(hf_token=os.getenv("HF_TOKEN"))
    
    # Run benchmark on audio file
    audio_path = "/Users/laptop/Development/Personal/psuedonymous/toolshed/downloads/youtube_-pGs0btGmgY_sound.wav"
    
    if not Path(audio_path).exists():
        print(f"⚠️  Audio file not found: {audio_path}")
        print("Please provide a valid audio file path.")
        return
    
    results = runner.run_benchmark(
        audio_path=audio_path,
        output_dir="data/results",
        device="cpu",  # or "cuda" if GPU available
    )
    
    # Print summary
    runner.print_summary(results)
    
    return results


def example_process_results():
    """Example of processing and using results."""
    print("\n" + "=" * 60)
    print("Example 2: Processing Results")
    print("=" * 60)
    
    # Load results from JSON
    results_file = Path("data/results/sample_audio_results.json")
    
    if not results_file.exists():
        print(f"⚠️  Results file not found: {results_file}")
        return
    
    with open(results_file) as f:
        data = json.load(f)
    
    # Process each solution's results
    for result_data in data["results"]:
        solution_name = result_data["solution"]
        words = result_data["words"]
        
        print(f"\n📊 {solution_name}:")
        print(f"   Total words: {len(words)}")
        
        # Group by speaker
        speakers = {}
        for word_data in words:
            speaker_id = word_data["speaker_id"]
            if speaker_id not in speakers:
                speakers[speaker_id] = []
            speakers[speaker_id].append(word_data)
        
        print(f"   Speakers detected: {len(speakers)}")
        for speaker_id, speaker_words in speakers.items():
            print(f"   - {speaker_id}: {len(speaker_words)} words")


def example_map_speakers_to_users():
    """Example of mapping speaker IDs to user records."""
    print("\n" + "=" * 60)
    print("Example 3: Mapping Speakers to User Records")
    print("=" * 60)
    
    # Example user database (in production, this would be a real database)
    user_database = {
        "user_123": {
            "name": "Alice",
            "voice_fingerprint": "abc123",  # Would be actual voice embedding
        },
        "user_456": {
            "name": "Bob",
            "voice_fingerprint": "def456",
        },
    }
    
    # Example: Simple mapping based on speaker order
    # In production, you'd use voice fingerprinting/matching
    def map_speaker_to_user(speaker_id: str, audio_metadata: dict) -> str:
        """Map speaker ID to user record."""
        # This is a simplified example
        # Real implementation would use:
        # - Voice embeddings comparison
        # - Speaker verification models
        # - Known speaker database
        
        mapping = {
            "SPEAKER_00": "user_123",  # Alice
            "SPEAKER_01": "user_456",  # Bob
        }
        
        return mapping.get(speaker_id, "unknown_user")
    
    # Load results
    results_file = Path("data/results/sample_audio_results.json")
    if not results_file.exists():
        print(f"⚠️  Results file not found: {results_file}")
        return
    
    with open(results_file) as f:
        data = json.load(f)
    
    # Process WhisperX results (has word-level timestamps)
    whisperx_result = next(
        (r for r in data["results"] if r["solution"] == "WhisperX"),
        None
    )
    
    if not whisperx_result:
        print("⚠️  WhisperX results not found")
        return
    
    # Map speakers to users
    speaker_to_user = {}
    for word_data in whisperx_result["words"]:
        speaker_id = word_data["speaker_id"]
        if speaker_id not in speaker_to_user:
            user_id = map_speaker_to_user(speaker_id, {})
            speaker_to_user[speaker_id] = user_id
            print(f"   {speaker_id} → {user_id} ({user_database.get(user_id, {}).get('name', 'Unknown')})")
    
    # Create output with user IDs
    output_words = []
    for word_data in whisperx_result["words"]:
        speaker_id = word_data["speaker_id"]
        user_id = speaker_to_user.get(speaker_id, "unknown_user")
        
        output_words.append({
            **word_data,
            "user_id": user_id,
            "user_name": user_database.get(user_id, {}).get("name", "Unknown"),
        })
    
    # Save mapped results
    output_file = Path("data/results/sample_audio_mapped.json")
    with open(output_file, "w") as f:
        json.dump({"words": output_words}, f, indent=2)
    
    print(f"\n✓ Mapped results saved to: {output_file}")


def example_custom_pipeline():
    """Example of creating a custom pipeline."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Pipeline (Template)")
    print("=" * 60)
    
    print("""
To add a custom pipeline, create a class like this:

from src.benchmark import BaseDiarizationPipeline, BenchmarkResult, WordTimestamp

class MyCustomPipeline(BaseDiarizationPipeline):
    def __init__(self):
        super().__init__("MyCustomSolution")
        # Initialize your model here
    
    def process(self, audio_path: str, **kwargs) -> BenchmarkResult:
        start_time = time.time()
        words = []
        
        # Your processing logic here
        # Extract words with timestamps and speaker IDs
        
        return BenchmarkResult(
            solution_name=self.name,
            words=words,
            processing_time=time.time() - start_time,
            memory_usage_mb=self._get_memory_usage(),
        )

Then add it to BenchmarkRunner._initialize_pipelines():
    try:
        self.pipelines.append(MyCustomPipeline())
    except Exception as e:
        logger.warning(f"Could not initialize MyCustomSolution: {e}")
""")


if __name__ == "__main__":
    print("🎤 Speaker Diarization Benchmark - Examples\n")
    
    # Run examples
    # Uncomment the ones you want to run:
    
    example_basic_usage()
    # example_process_results()
    # example_map_speakers_to_users()
    # example_custom_pipeline()
    
    print("\n" + "=" * 60)
    print("For more examples, see the README.md file")
    print("=" * 60)
