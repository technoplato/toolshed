"""
HOW:
  Run from the speaker-diarization-benchmark directory:
  `uv run python scripts/one_off/test_new_schema.py`

  [Inputs]
  - INSTANT_APP_ID (env): The InstantDB Application ID
  - INSTANT_ADMIN_SECRET (env): The Admin Secret for the app

  [Outputs]
  - Creates test entities in InstantDB
  - Verifies they can be queried back

  [Side Effects]
  - Creates data in InstantDB (test entities)

WHO:
  Antigravity, User
  (Context: Verifying new schema implementation)

WHAT:
  Test script to verify the new InstantDB schema and adapter work correctly.
  Tests:
  1. Save a publication
  2. Save a video linked to publication
  3. Save a transcription run with words
  4. Save a diarization run with segments
  5. Save speaker assignments
  6. Query everything back

WHEN:
  Created: 2025-12-07
  Last Modified: 2025-12-07

WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/test_new_schema.py

WHY:
  To verify the Python adapter correctly implements the new schema
  before running the full audio ingestion pipeline.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directories to path
repo_root = Path(__file__).resolve().parents[4]
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Load .env from repo root
load_dotenv(repo_root / ".env")

from src.data.impl.instant_db_adapter import InstantDBVideoRepository
from src.data.models import (
    Publication,
    Video,
    Speaker,
    TranscriptionRun,
    TranscriptionConfig,
    DiarizationRun,
    DiarizationConfig,
    Word,
    DiarizationSegment,
)


def test_new_schema():
    """Test the new schema implementation."""
    
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set")
        return False
    
    print(f"Using App ID: {app_id[:8]}...")
    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    try:
        # 1. Test Publication
        print("\n1. Testing Publication...")
        publication = Publication(
            name="Test Podcast",
            publication_type="youtube_channel",
            url="https://www.youtube.com/test-channel",
            external_id="test-channel-id",
        )
        pub_id = repo.save_publication(publication)
        print(f"   ✓ Saved publication: {pub_id}")
        
        pub_back = repo.get_publication_by_url(publication.url)
        assert pub_back is not None, "Failed to retrieve publication"
        assert pub_back.name == publication.name
        print(f"   ✓ Retrieved publication: {pub_back.name}")
        
        # 2. Test Video
        print("\n2. Testing Video...")
        video = Video(
            title="Test Video - Schema Verification",
            url="https://www.youtube.com/watch?v=test123",
            filepath="/data/test/test123.wav",
            duration=60.0,
            description="A test video for schema verification",
        )
        video_id = repo.save_video(video, publication_id=pub_id)
        print(f"   ✓ Saved video: {video_id}")
        
        video_back = repo.get_video_by_url(video.url)
        assert video_back is not None, "Failed to retrieve video"
        assert video_back.title == video.title
        print(f"   ✓ Retrieved video: {video_back.title}")
        
        # 3. Test Speaker
        print("\n3. Testing Speaker...")
        speaker = Speaker(
            name="Test Speaker",
            is_human=True,
            metadata={"role": "host"},
        )
        speaker_id = repo.save_speaker(speaker)
        print(f"   ✓ Saved speaker: {speaker_id}")
        
        speaker_back = repo.get_speaker_by_name(speaker.name)
        assert speaker_back is not None, "Failed to retrieve speaker"
        print(f"   ✓ Retrieved speaker: {speaker_back.name}")
        
        # 4. Test Transcription Run with Words
        print("\n4. Testing Transcription Run with Words...")
        config = TranscriptionConfig(
            model="whisper-large-v3",
            tool="mlx-whisper",
            language="en",
            word_timestamps=True,
        )
        
        run = TranscriptionRun(
            video_id=video_id,
            config=config,
            tool_version="mlx-whisper-0.4.1",
            is_preferred=True,
            pipeline_script="test_new_schema.py",
        )
        
        words = [
            Word(text="Hello", start_time=0.0, end_time=0.5, confidence=0.95, transcription_segment_index=0),
            Word(text="world", start_time=0.5, end_time=1.0, confidence=0.92, transcription_segment_index=0),
            Word(text="this", start_time=1.5, end_time=1.8, confidence=0.88, transcription_segment_index=1),
            Word(text="is", start_time=1.8, end_time=2.0, confidence=0.90, transcription_segment_index=1),
            Word(text="a", start_time=2.0, end_time=2.2, confidence=0.85, transcription_segment_index=1),
            Word(text="test", start_time=2.2, end_time=2.7, confidence=0.93, transcription_segment_index=1),
        ]
        
        run_id = repo.save_transcription_run(run, words)
        print(f"   ✓ Saved transcription run: {run_id}")
        print(f"   ✓ Saved {len(words)} words")
        
        words_back = repo.get_words_by_run_id(run_id)
        assert len(words_back) == len(words), f"Expected {len(words)} words, got {len(words_back)}"
        print(f"   ✓ Retrieved {len(words_back)} words")
        
        # 5. Test Diarization Run with Segments
        print("\n5. Testing Diarization Run with Segments...")
        diar_config = DiarizationConfig(
            embedding_model="pyannote/wespeaker-voxceleb-resnet34",
            tool="pyannote-local",
            clustering_method="AgglomerativeClustering",
        )
        
        diar_run = DiarizationRun(
            video_id=video_id,
            config=diar_config,
            workflow="pyannote",
            is_preferred=True,
            num_speakers_detected=2,
        )
        
        segments = [
            DiarizationSegment(
                start_time=0.0,
                end_time=1.0,
                speaker_label="SPEAKER_0",
                confidence=0.85,
            ),
            DiarizationSegment(
                start_time=1.5,
                end_time=3.0,
                speaker_label="SPEAKER_1",
                confidence=0.90,
            ),
        ]
        
        diar_run_id = repo.save_diarization_run(diar_run, segments)
        print(f"   ✓ Saved diarization run: {diar_run_id}")
        print(f"   ✓ Saved {len(segments)} segments")
        
        segments_back = repo.get_diarization_segments_by_run_id(diar_run_id)
        assert len(segments_back) == len(segments), f"Expected {len(segments)} segments, got {len(segments_back)}"
        print(f"   ✓ Retrieved {len(segments_back)} segments")
        
        # 6. Test Speaker Assignment
        print("\n6. Testing Speaker Assignment...")
        segment_id = segments_back[0].id
        assignment_id = repo.save_speaker_assignment(
            segment_id=segment_id,
            speaker_id=speaker_id,
            source="model",
            assigned_by="test_script",
            confidence=0.87,
            note="Test assignment",
        )
        print(f"   ✓ Saved speaker assignment: {assignment_id}")
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! New schema is working correctly.")
        print("=" * 50)
        
        # Summary
        print("\nCreated entities:")
        print(f"  - Publication: {pub_id}")
        print(f"  - Video: {video_id}")
        print(f"  - Speaker: {speaker_id}")
        print(f"  - Transcription Run: {run_id} (with {len(words)} words)")
        print(f"  - Diarization Run: {diar_run_id} (with {len(segments)} segments)")
        print(f"  - Speaker Assignment: {assignment_id}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_new_schema()
    sys.exit(0 if success else 1)








