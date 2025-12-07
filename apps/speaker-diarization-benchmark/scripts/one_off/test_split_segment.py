"""
HOW:
  Run from the speaker-diarization-benchmark directory:
  `uv run python scripts/one_off/test_split_segment.py`

  [Inputs]
  - INSTANT_APP_ID (env): The InstantDB Application ID
  - INSTANT_ADMIN_SECRET (env): The Admin Secret for the app

  [Outputs]
  - Creates test entities, performs split, verifies results, cleans up

  [Side Effects]
  - Creates and deletes test data in InstantDB

WHO:
  Antigravity, User
  (Context: Testing segment split functionality)

WHAT:
  Test script to verify the segment splitting works correctly.
  
  Tests:
  1. Create test video, diarization run, and segment
  2. Simulate the /split_segment request logic
  3. Verify:
     - SegmentSplit record created with correct fields
     - Original segment marked is_invalidated=true
     - New segments created with SPLIT_X labels
     - Links established: split → original, split → resulting segments
  4. Clean up all test data

WHEN:
  Created: 2025-12-07
  Last Modified: 2025-12-07

WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/test_split_segment.py

WHY:
  To verify the segment split logic works correctly before testing in UI.
"""

import sys
import os
import uuid
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add parent directories to path
repo_root = Path(__file__).resolve().parents[4]
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Load .env from repo root
load_dotenv(repo_root / ".env")


def test_split_segment():
    """Test the segment splitting functionality."""
    
    app_id = os.getenv("INSTANT_APP_ID")
    admin_secret = os.getenv("INSTANT_ADMIN_SECRET")
    
    if not app_id or not admin_secret:
        print("Error: INSTANT_APP_ID and INSTANT_ADMIN_SECRET must be set")
        return False
    
    print(f"Using App ID: {app_id[:8]}...")
    
    from src.data.impl.instant_db_adapter import InstantDBVideoRepository
    repo = InstantDBVideoRepository(app_id, admin_secret)
    
    # Track entities for cleanup
    entities_to_cleanup = {
        "videos": [],
        "diarizationRuns": [],
        "diarizationSegments": [],
        "segmentSplits": [],
        "diarizationConfigs": [],
    }
    
    try:
        print("\n" + "=" * 60)
        print("TEST: Segment Splitting")
        print("=" * 60)
        
        # =====================================================================
        # 1. Create test data
        # =====================================================================
        print("\n1. Creating test data...")
        
        # Create test video
        video_id = str(uuid.uuid4())
        repo._transact([
            ["update", "videos", video_id, {
                "title": "Split Test Video",
                "url": f"https://test.com/split-test-{video_id}",
                "duration": 60.0,
                "ingested_at": datetime.now().isoformat(),
            }]
        ])
        entities_to_cleanup["videos"].append(video_id)
        print(f"   ✓ Created video: {video_id}")
        
        # Create diarization config
        config_id = str(uuid.uuid4())
        repo._transact([
            ["update", "diarizationConfigs", config_id, {
                "embedding_model": "test-model",
                "tool": "test-tool",
                "created_at": datetime.now().isoformat(),
            }]
        ])
        entities_to_cleanup["diarizationConfigs"].append(config_id)
        print(f"   ✓ Created config: {config_id}")
        
        # Create diarization run
        run_id = str(uuid.uuid4())
        repo._transact([
            ["update", "diarizationRuns", run_id, {
                "workflow": "test-workflow",
                "is_preferred": True,
                "executed_at": datetime.now().isoformat(),
            }],
            ["link", "videos", video_id, {"diarizationRuns": run_id}],
            ["link", "diarizationRuns", run_id, {"config": config_id}],
        ])
        entities_to_cleanup["diarizationRuns"].append(run_id)
        print(f"   ✓ Created diarization run: {run_id}")
        
        # Create original segment (0.0s - 3.0s)
        original_segment_id = str(uuid.uuid4())
        repo._transact([
            ["update", "diarizationSegments", original_segment_id, {
                "start_time": 0.0,
                "end_time": 3.0,
                "speaker_label": "SPEAKER_0",
                "is_invalidated": False,
                "created_at": datetime.now().isoformat(),
            }],
            ["link", "diarizationRuns", run_id, {"diarizationSegments": original_segment_id}],
        ])
        entities_to_cleanup["diarizationSegments"].append(original_segment_id)
        print(f"   ✓ Created original segment: {original_segment_id}")
        print(f"     Time range: 0.0s - 3.0s, Speaker: SPEAKER_0")
        
        # =====================================================================
        # 2. Perform the split (simulating /split_segment endpoint logic)
        # =====================================================================
        print("\n2. Performing segment split...")
        
        # Input: User wants to split into 2 parts
        lines = ["Hello world", "this is a test"]  # 11 chars, 14 chars
        start_time = 0.0
        end_time = 3.0
        split_by = "test_script"
        
        # Calculate split times (proportional to character count)
        total_chars = sum(len(line) for line in lines)
        duration = end_time - start_time
        
        split_times = []
        current_time = start_time
        for i, line in enumerate(lines[:-1]):
            prop = len(line) / total_chars
            current_time += duration * prop
            split_times.append(current_time)
        
        print(f"   Split times calculated: {split_times}")
        primary_split_time = split_times[0]
        
        # Create SegmentSplit record
        split_id = str(uuid.uuid4())
        new_segment_ids = []
        
        steps = [
            # 1. Create SegmentSplit record
            ["update", "segmentSplits", split_id, {
                "split_time": primary_split_time,
                "split_by": split_by,
                "split_at": datetime.now().isoformat(),
            }],
            # 2. Link split to original segment
            ["link", "segmentSplits", split_id, {"originalSegment": original_segment_id}],
            # 3. Mark original segment as invalidated
            ["update", "diarizationSegments", original_segment_id, {
                "is_invalidated": True
            }],
        ]
        
        # 4. Create new segments
        current_start = start_time
        for idx, line in enumerate(lines):
            seg_end = split_times[idx] if idx < len(split_times) else end_time
            
            new_seg_id = str(uuid.uuid4())
            new_segment_ids.append(new_seg_id)
            
            steps.extend([
                ["update", "diarizationSegments", new_seg_id, {
                    "start_time": current_start,
                    "end_time": seg_end,
                    "speaker_label": f"SPLIT_{idx}",
                    "is_invalidated": False,
                    "created_at": datetime.now().isoformat(),
                }],
                # Link to split record
                ["link", "segmentSplits", split_id, {"resultingSegments": new_seg_id}],
                # Link to run
                ["link", "diarizationRuns", run_id, {"diarizationSegments": new_seg_id}],
            ])
            
            current_start = seg_end
        
        entities_to_cleanup["segmentSplits"].append(split_id)
        entities_to_cleanup["diarizationSegments"].extend(new_segment_ids)
        
        # Execute transaction
        repo._transact(steps)
        print(f"   ✓ Created SegmentSplit: {split_id}")
        print(f"   ✓ Created {len(new_segment_ids)} new segments")
        
        # =====================================================================
        # 3. Verify the results
        # =====================================================================
        print("\n3. Verifying results...")
        
        # Query the split record
        q_split = {
            "segmentSplits": {
                "$": {"where": {"id": split_id}},
                "originalSegment": {},
                "resultingSegments": {},
            }
        }
        split_result = repo._query(q_split)
        splits = split_result.get("segmentSplits", [])
        
        if not splits:
            print("   ✗ FAILED: SegmentSplit not found!")
            return False
        
        split_record = splits[0]
        print(f"   ✓ SegmentSplit found")
        print(f"     split_time: {split_record.get('split_time')}")
        print(f"     split_by: {split_record.get('split_by')}")
        
        # Verify original segment link
        original_segments = split_record.get("originalSegment", [])
        if not original_segments:
            print("   ✗ FAILED: originalSegment link not found!")
            return False
        print(f"   ✓ originalSegment link exists ({len(original_segments)} segment)")
        
        # Verify resulting segments link
        resulting_segments = split_record.get("resultingSegments", [])
        if len(resulting_segments) != len(lines):
            print(f"   ✗ FAILED: Expected {len(lines)} resulting segments, got {len(resulting_segments)}")
            return False
        print(f"   ✓ resultingSegments link exists ({len(resulting_segments)} segments)")
        
        # Query original segment to verify it's invalidated
        q_original = {
            "diarizationSegments": {
                "$": {"where": {"id": original_segment_id}},
            }
        }
        original_result = repo._query(q_original)
        original_segs = original_result.get("diarizationSegments", [])
        
        if not original_segs:
            print("   ✗ FAILED: Original segment not found!")
            return False
        
        if not original_segs[0].get("is_invalidated"):
            print("   ✗ FAILED: Original segment not marked as invalidated!")
            return False
        print(f"   ✓ Original segment is_invalidated=true")
        
        # Query new segments
        q_new = {
            "diarizationSegments": {
                "$": {"where": {"id": {"$in": new_segment_ids}}},
            }
        }
        new_result = repo._query(q_new)
        new_segs = new_result.get("diarizationSegments", [])
        
        if len(new_segs) != len(new_segment_ids):
            print(f"   ✗ FAILED: Expected {len(new_segment_ids)} new segments, got {len(new_segs)}")
            return False
        
        print(f"   ✓ All {len(new_segs)} new segments found:")
        for seg in sorted(new_segs, key=lambda s: s.get("start_time", 0)):
            print(f"     - {seg.get('speaker_label')}: {seg.get('start_time'):.2f}s - {seg.get('end_time'):.2f}s")
        
        # Verify time ranges are correct
        new_segs_sorted = sorted(new_segs, key=lambda s: s.get("start_time", 0))
        expected_times = [
            (0.0, split_times[0]),
            (split_times[0], 3.0),
        ]
        
        for i, (seg, (exp_start, exp_end)) in enumerate(zip(new_segs_sorted, expected_times)):
            actual_start = seg.get("start_time")
            actual_end = seg.get("end_time")
            if abs(actual_start - exp_start) > 0.01 or abs(actual_end - exp_end) > 0.01:
                print(f"   ✗ FAILED: Segment {i} times incorrect!")
                print(f"     Expected: {exp_start:.2f} - {exp_end:.2f}")
                print(f"     Got: {actual_start:.2f} - {actual_end:.2f}")
                return False
        
        print(f"   ✓ All time ranges correct")
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # =====================================================================
        # 4. Clean up test data
        # =====================================================================
        print("\n4. Cleaning up test data...")
        
        cleanup_steps = []
        
        # Delete in reverse order of dependencies
        for seg_id in entities_to_cleanup["diarizationSegments"]:
            cleanup_steps.append(["delete", "diarizationSegments", seg_id])
        
        for split_id in entities_to_cleanup["segmentSplits"]:
            cleanup_steps.append(["delete", "segmentSplits", split_id])
        
        for run_id in entities_to_cleanup["diarizationRuns"]:
            cleanup_steps.append(["delete", "diarizationRuns", run_id])
        
        for config_id in entities_to_cleanup["diarizationConfigs"]:
            cleanup_steps.append(["delete", "diarizationConfigs", config_id])
        
        for video_id in entities_to_cleanup["videos"]:
            cleanup_steps.append(["delete", "videos", video_id])
        
        if cleanup_steps:
            try:
                repo._transact(cleanup_steps)
                total = sum(len(v) for v in entities_to_cleanup.values())
                print(f"   ✓ Cleaned up {total} test entities")
            except Exception as e:
                print(f"   Warning: Cleanup failed: {e}")


if __name__ == "__main__":
    success = test_split_segment()
    sys.exit(0 if success else 1)

