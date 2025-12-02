import os
import sys
import yt_dlp
from pathlib import Path

URLS = [
    "https://www.youtube.com/watch?v=Rni7Fz7208c",
    "https://www.youtube.com/watch?v=aR20FWCCjAs",
    # "https://www.youtube.com/watch?v=aR20FWCCjAs", # Duplicate
    "https://youtu.be/_IBDvROmdGU",
    "https://www.youtube.com/watch?v=mC43pZkpTec&pp=ygUMbGV4IGZyaWVkbWFu2AabLg%3D%3D",
    "https://www.youtube.com/watch?v=O4wBUysNe2k"
]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data/downloads")

def download_audio(video_url, output_dir="downloads"):
    """Downloads audio using yt-dlp and returns platform/id info."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Common options
    common_opts = {'quiet': True}
    
    # Extract info first to get platform (extractor) and ID
    print(f"Extracting metadata for {video_url}...")
    with yt_dlp.YoutubeDL(common_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        video_id = info['id']
        title = info.get('title', 'Unknown Title')
        extractor = info.get('extractor', 'unknown').lower()
        
        # Normalize youtube extractor names
        if 'youtube' in extractor:
            extractor = 'youtube'

    filename_base = f"{extractor}_{video_id}_sound"
    output_path = os.path.join(output_dir, f"{filename_base}.wav")
    
    if os.path.exists(output_path):
        print(f"Audio already exists at {output_path}")
        return output_path, video_id, title
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'postprocessor_args': [
            '-ar', '16000'
        ],
        # Use specific filename to avoid re-downloading with different ID formats
        'outtmpl': os.path.join(output_dir, f'{extractor}_%(id)s_sound.%(ext)s'),
        'quiet': True,
    }
    
    print(f"Downloading audio for {video_id} ({extractor})...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
        
    return output_path, video_id, title

def main():
    print(f"Downloading {len(URLS)} videos to {OUTPUT_DIR}...")
    
    for url in URLS:
        print(f"\nProcessing {url}...")
        try:
            output_path, video_id, title = download_audio(url, output_dir=OUTPUT_DIR)
            print(f"✓ Downloaded: {title}")
            print(f"  Path: {output_path}")
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")

if __name__ == "__main__":
    main()
