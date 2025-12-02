import os
import sys
import json
import subprocess
import yt_dlp
import argparse
from typing import List
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from apps.transcriber.extractors.youtube import YouTubeHistoryFetcher
from apps.transcriber.lib.models import VideoMetadata, Channel

class VideoProcessor:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.downloads_dir = os.path.join(base_dir, "downloads")
        self.transcriptions_dir = os.path.join(base_dir, "transcriptions")
        self.whisper_bin = os.path.join(base_dir, "whisper.cpp/build/bin/whisper-cli")
        self.model_path = os.path.join(base_dir, "whisper.cpp/models/ggml-medium.bin")
        
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.transcriptions_dir, exist_ok=True)
        
        if not os.path.exists(self.whisper_bin):
            # Fallback to 'main' if whisper-cli doesn't exist (older builds)
            fallback = os.path.join(base_dir, "whisper.cpp/build/bin/main")
            if os.path.exists(fallback):
                self.whisper_bin = fallback
            else:
                raise FileNotFoundError(f"Whisper binary not found at {self.whisper_bin}")
            
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Whisper model not found at {self.model_path}")

    def download_audio(self, video: VideoMetadata) -> str:
        """
        Download audio for a video. Returns path to the audio file.
        """
        output_template = os.path.join(self.downloads_dir, f"{video.id}.%(ext)s")
        final_path = os.path.join(self.downloads_dir, f"{video.id}.wav")
        
        if os.path.exists(final_path):
            print(f"Audio already exists for {video.id}")
            return final_path
            
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'postprocessor_args': [
                '-ar', '16000'
            ],
            'quiet': True,
        }
        
        print(f"Downloading audio for {video.title} ({video.id})...")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video.video_url])
            return final_path
        except Exception as e:
            print(f"Error downloading {video.id}: {e}")
            return None

    def transcribe(self, audio_path: str, video: VideoMetadata) -> bool:
        """
        Transcribe audio using whisper.cpp.
        """
        # Output base path (whisper.cpp adds extensions)
        output_base = os.path.join(self.transcriptions_dir, video.id)
        
        # Check if already transcribed (JSON existence)
        if os.path.exists(f"{output_base}.json"):
            print(f"Transcription already exists for {video.id}")
            return True
            
        print(f"Transcribing {video.id}...")
        
        # Command: ./whisper-cli -m model -f file -oj -of output_base
        # -oj: output JSON
        # -of: output file path (without extension)
        # -ml 1: max line length (optional, for formatting)
        cmd = [
            self.whisper_bin,
            "-m", self.model_path,
            "-f", audio_path,
            "-ojf", # Output JSON Full (with token timestamps)
            "-of", output_base,
            "--threads", "4" # Use 4 threads
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Generate Markdown from JSON
            self._generate_markdown(f"{output_base}.json", video)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error transcribing {video.id}: {e.stderr.decode()}")
            return False

    def _generate_markdown(self, json_path: str, video: VideoMetadata):
        """
        Create a Markdown file with metadata and transcription.
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            md_path = json_path.replace('.json', '.md')
            
            with open(md_path, 'w') as f:
                # Frontmatter / Metadata
                f.write(f"# {video.title}\n\n")
                f.write(f"**Channel:** [{video.channel.name}]({video.channel.url})\n")
                f.write(f"**Date:** {video.upload_date}\n")
                f.write(f"**URL:** {video.video_url}\n")
                f.write(f"**Duration:** {video.duration}s\n\n")
                f.write("## Description\n\n")
                f.write(f"{video.description}\n\n")
                f.write("## Transcription\n\n")
                
                # Transcription segments
                if 'transcription' in data:
                    segments = data['transcription']
                    for segment in segments:
                        # Whisper JSON format might vary, usually has 'offsets' or 'timestamps'
                        # Standard whisper.cpp JSON output:
                        # { "transcription": [ { "timestamps": { "from": "...", "to": "..." }, "text": "..." } ] }
                        
                        start = segment.get('timestamps', {}).get('from', '??')
                        text = segment.get('text', '').strip()
                        if text:
                            f.write(f"**[{start}]** {text}\n\n")
                            
            print(f"Generated Markdown at {md_path}")
            
        except Exception as e:
            print(f"Error generating markdown for {video.id}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process YouTube history: Download and Transcribe.")
    parser.add_argument("--limit", type=int, default=50, help="Number of videos to fetch")
    parser.add_argument("--cookies", type=str, help="Path to Netscape cookies file")
    parser.add_argument("--url", type=str, help="Process a specific video URL instead of history")
    
    args = parser.parse_args()
    
    history = []
    
    if args.url:
        # Create a dummy VideoMetadata for the single URL
        # We'll let yt-dlp fill in the details during download/extraction if possible, 
        # but for now we need a basic object. 
        # Actually, we should probably fetch metadata first.
        # But for simplicity, let's just use the URL and a dummy ID/Title, 
        # and let the downloader handle it?
        # The VideoProcessor expects a VideoMetadata object.
        
        # We can use the YouTubeHistoryFetcher's internal method or just create a dummy one
        # and let the download_audio method (which uses yt-dlp) work. 
        # But download_audio uses video.id for filename.
        # So we need to extract ID.
        
        try:
            # Quick extraction of ID
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(args.url, download=False)
                
            channel = Channel(name=info.get('uploader', 'Unknown'), id=info.get('channel_id'), url=info.get('uploader_url'))
            video = VideoMetadata(
                id=info['id'],
                title=info['title'],
                video_url=args.url,
                upload_date=info.get('upload_date'),
                description=info.get('description'),
                duration=info.get('duration'),
                view_count=info.get('view_count'),
                channel=channel
            )
            history = [video]
            print(f"Processing single video: {video.title}")
            
        except Exception as e:
            print(f"Error extracting info for {args.url}: {e}")
            return

    else:
        # Initialize Fetcher
        try:
            fetcher = YouTubeHistoryFetcher(cookie_file=args.cookies)
            history = fetcher.fetch_history(limit=args.limit)
        except Exception as e:
            print(f"Error initializing fetcher: {e}")
            return

    # Initialize Processor
    # Base dir is apps/transcriber
    base_dir = os.path.dirname(os.path.abspath(__file__))
    processor = VideoProcessor(base_dir)
    
    processed_count = 0
    
    for video in history:
        # Filter: Skip if > 3 hours (10800 seconds)
        if video.duration and video.duration > 10800:
            print(f"Skipping {video.title}: Duration {video.duration}s > 3 hours")
            continue
            
        print(f"\nProcessing {video.title}...")
        
        # Download
        audio_path = processor.download_audio(video)
        if not audio_path:
            continue
            
        # Transcribe
        success = processor.transcribe(audio_path, video)
        if success:
            processed_count += 1
            
    print(f"\nDone! Processed {processed_count} videos.")

if __name__ == "__main__":
    main()
