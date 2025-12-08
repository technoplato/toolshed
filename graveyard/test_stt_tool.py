import json
import logging
import subprocess
import re
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STT_TOOL_PATH = Path("stt_repo/.build/release/stt")
DATA_DIR = Path("data")
CLIPS_DIR = DATA_DIR / "clips"
MANIFEST_FILE = CLIPS_DIR / "manifest.json"

def parse_combined_output(file_path):
    """
    Parses the *_combined.txt output from stt tool.
    Format:
    [00:00.240 - 00:45.680] Speaker 1:
    I think we have finally got a real competitor for anthropic...
    """
    segments = []
    
    with open(file_path, 'r') as f:
        content = f.read()
        
    # Split by double newlines or look for the pattern
    # The format seems to be:
    # [START - END] SPEAKER:
    # TEXT
    
    # Regex to find the header
    pattern = re.compile(r'\[(\d{2}:\d{2}\.\d{3}) - (\d{2}:\d{2}\.\d{3})\] (Speaker \d+):')
    
    lines = content.split('\n')
    current_segment = None
    
    for i, line in enumerate(lines):
        match = pattern.match(line.strip())
        if match:
            if current_segment:
                segments.append(current_segment)
                
            start_str, end_str, speaker = match.groups()
            
            # Convert MM:SS.mmm to seconds
            def to_seconds(time_str):
                m, s = time_str.split(':')
                return float(m) * 60 + float(s)
                
            start = to_seconds(start_str)
            end = to_seconds(end_str)
            
            current_segment = {
                "start": start,
                "end": end,
                "speaker": speaker,
                "text": ""
            }
        elif current_segment and line.strip():
            # Append text to current segment
            if current_segment["text"]:
                current_segment["text"] += " " + line.strip()
            else:
                current_segment["text"] = line.strip()
                
    if current_segment:
        segments.append(current_segment)
        
    return segments

def main():
    clip_id = "clip_local_mssp-old-test-ep-1_0_60.wav"
    clip_path = CLIPS_DIR / clip_id
    
    if not clip_path.exists():
        logger.error(f"Clip not found: {clip_path}")
        return

    logger.info(f"Running stt tool on {clip_path}...")
    
    # Output directory
    output_dir = CLIPS_DIR / "stt_output"
    output_dir.mkdir(exist_ok=True)
    
    cmd = [
        str(STT_TOOL_PATH),
        str(clip_path),
        "--output", str(output_dir),
        "--verbose"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"stt tool failed: {e}")
        return
        
    # Find the output file
    # It should be named clip_youtube_jAlKYYr1bpY_0_60_combined.txt
    combined_file = output_dir / f"{clip_path.stem}_combined.txt"
    
    if not combined_file.exists():
        logger.error(f"Output file not found: {combined_file}")
        # List dir to see what happened
        logger.info(f"Contents of {output_dir}:")
        for f in output_dir.iterdir():
            logger.info(f.name)
        return
        
    logger.info(f"Parsing output from {combined_file}...")
    segments = parse_combined_output(combined_file)
    
    logger.info(f"Found {len(segments)} segments.")
    for seg in segments:
        logger.info(f"[{seg['start']:.2f}-{seg['end']:.2f}] {seg['speaker']}: {seg['text']}")
        
    # Update Manifest
    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)
        
    entry = next((e for e in manifest if e["id"] == clip_id), None)
    if entry:
        entry["transcriptions"]["stt_tool"] = segments
        # Optional: Set as main transcription to view in UI
        # entry["transcriptions"]["pywhispercpp.small"] = segments
        
        with open(MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=2)
            
        logger.info("Manifest updated!")

if __name__ == "__main__":
    main()
