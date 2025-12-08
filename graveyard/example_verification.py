"""
Example script showing how to use the verification page.

This demonstrates the complete workflow:
1. Run benchmark
2. Generate verification page
3. (User verifies in browser)
4. Load verified results
"""

import json
from pathlib import Path
from src.generate_verification_page import create_verification_page


def example_workflow():
    """Example workflow for speaker verification."""
    
    # Example paths (adjust to your actual paths)
    results_path = "data/results/sample_audio_results.json"
    audio_path = "data/sample_audio.wav"
    speaker_db_path = "data/speaker_database.json"
    output_path = "data/results/sample_audio_verification.html"
    
    print("=" * 60)
    print("Speaker Verification Workflow Example")
    print("=" * 60)
    
    # Step 1: Check if results exist
    if not Path(results_path).exists():
        print(f"\n⚠️  Results file not found: {results_path}")
        print("   Run the benchmark first:")
        print(f"   uv run python src/benchmark.py {audio_path}")
        return
    
    # Step 2: Generate verification page
    print(f"\n📄 Generating verification page...")
    print(f"   Results: {results_path}")
    print(f"   Audio: {audio_path}")
    print(f"   Speaker DB: {speaker_db_path}")
    
    try:
        html = create_verification_page(
            results_path=results_path,
            audio_path=audio_path,
            output_path=output_path,
            speaker_db_path=speaker_db_path if Path(speaker_db_path).exists() else None,
        )
        
        # Save HTML
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"   ✓ Verification page generated: {output_path}")
        print(f"\n🌐 Open in browser:")
        print(f"   open {output_path}  # macOS")
        print(f"   xdg-open {output_path}  # Linux")
        print(f"   start {output_path}  # Windows")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Step 3: Example of loading verified results
    print(f"\n📥 Example: Loading verified results")
    verified_path = output_path.replace('.html', '_verified.json')
    
    if Path(verified_path).exists():
        with open(verified_path) as f:
            verified = json.load(f)
        
        print(f"   Loaded {len(verified['segments'])} segments")
        
        # Count verified speakers
        verified_speakers = {}
        for segment in verified['segments']:
            speaker = segment.get('assigned_speaker')
            if speaker:
                verified_speakers[speaker] = verified_speakers.get(speaker, 0) + 1
        
        print(f"   Verified speakers: {len(verified_speakers)}")
        for speaker, count in verified_speakers.items():
            print(f"     - {speaker}: {count} segments")
        
        # Example: Map to user IDs
        print(f"\n🔗 Example: Mapping to user records")
        user_mapping = {
            "Alice Johnson": "user_123",
            "Bob Smith": "user_456",
        }
        
        for segment in verified['segments'][:5]:  # Show first 5
            speaker = segment.get('assigned_speaker')
            if speaker:
                user_id = user_mapping.get(speaker, "unknown_user")
                print(f"   {speaker} → {user_id}")
    else:
        print(f"   ⚠️  Verified results not found: {verified_path}")
        print(f"   (Save results from the verification page first)")


if __name__ == "__main__":
    example_workflow()
