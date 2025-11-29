import os
import sys
import json
import urllib.parse
import yt_dlp
import asyncio
from datetime import datetime
from pywhispercpp.model import Model

# Add parent directory to path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from instantdb_admin_client import InstantDBAdminAPI, Link, Update

APP_ID = "979844fa-8b96-4a83-9906-2445928f1e0d"
ADMIN_TOKEN = "b11e3fbe-e3d3-4e1e-a2d0-41bf2296ea0a"

import logging

logger = logging.getLogger(__name__)

def download_audio(video_url, output_dir="downloads"):
    """Downloads audio using yt-dlp and returns platform/id info."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Debug: Print CWD and check for cookies
    logger.info(f"DEBUG: CWD is {os.getcwd()}")
    
    # Common options including cookies
    common_opts = {'quiet': True}
    
    # Check for cookies.txt in the persistent volume
    cookie_path = "transcriptions/cookies.txt"
    if os.path.exists(cookie_path):
        logger.info(f"DEBUG: Found cookies at {cookie_path}")
        common_opts['cookiefile'] = cookie_path
    else:
        logger.info(f"DEBUG: Cookies NOT found at {cookie_path}")
        # Fallback check
        if os.path.exists("cookies.txt"):
             logger.info(f"DEBUG: Found cookies at ./cookies.txt")
             common_opts['cookiefile'] = "cookies.txt"

    # Extract info first to get platform (extractor) and ID
    logger.info("Extracting video metadata...")
    with yt_dlp.YoutubeDL(common_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        video_id = info['id']
        title = info.get('title', 'Unknown Title')
        extractor = info.get('extractor', 'unknown').lower()
        duration = info.get('duration')
        upload_date = info.get('upload_date')
        channel = info.get('uploader')
        
        # Normalize youtube extractor names
        if 'youtube' in extractor:
            extractor = 'youtube'

    filename_base = f"{extractor}_{video_id}_sound"
    output_path = os.path.join(output_dir, f"{filename_base}.wav")
    
    if os.path.exists(output_path):
        logger.info(f"Audio already exists at {output_path}")
        return output_path, video_id, title, extractor, duration, upload_date, channel

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
    
    # Add cookiefile to download options if present
    if 'cookiefile' in common_opts:
        ydl_opts['cookiefile'] = common_opts['cookiefile']

    logger.info(f"DEBUG: ydl_opts: {ydl_opts}")
    logger.info(f"Downloading audio for {video_id} ({extractor})...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
        
    return output_path, video_id, title, extractor, duration, upload_date, channel

def format_timestamp(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def transcribe_audio(audio_path, video_id, platform, output_dir="transcriptions"):
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, f"{platform}_{video_id}_transcript.json")
    
    if os.path.exists(json_path):
        print(f"Loading existing transcription from {json_path}")
        with open(json_path, 'r') as f:
            return json.load(f), json_path

    print(f"Loading whisper.cpp model (base)...")
    try:
        model = Model('base', print_realtime=True, print_progress=True)
    except Exception as e:
        print(f"Error loading model: {e}")
        return [], None

    print(f"Transcribing {audio_path}...")
    segments = model.transcribe(audio_path, n_threads=4)
    
    json_segments = []
    for s in segments:
        json_segments.append({
            "start": s.t0 / 100.0,
            "end": s.t1 / 100.0,
            "text": s.text.strip()
        })
        
    with open(json_path, 'w') as f:
        json.dump(json_segments, f, indent=2)
    print(f"Saved transcription JSON to {json_path}")
    
    return json_segments, json_path

async def upsert_video_record(video_id, platform, url, title, audio_path, json_path, duration, upload_date, channel, video_uuid=None):
    db = InstantDBAdminAPI(app_id=APP_ID, admin_token=ADMIN_TOKEN)
    
    if not video_uuid:
        # Try to find by external_id if no UUID provided
        existing = await db.query({
            "videos": {
                "$": {
                    "where": {"external_id": video_id}
                }
            }
        })
        
        if existing.get("videos"):
            video_uuid = existing["videos"][0]["id"]
            print(f"Found existing video with ID: {video_uuid}")
        else:
            import uuid
            video_uuid = str(uuid.uuid4())
            print(f"Creating new video with ID: {video_uuid}")
    else:
        print(f"Updating existing video with UUID: {video_uuid}")
        # Check for conflict: Does another video have this external_id?
        conflict = await db.query({
            "videos": {
                "$": {
                    "where": {"external_id": video_id}
                }
            }
        })
        conflicting_videos = conflict.get("videos", [])
        for cv in conflicting_videos:
            if cv["id"] != video_uuid:
                print(f"Found conflicting video {cv['id']} with same external_id. Deleting it.")
                # We need to delete it to free up the external_id
                # But wait, if we delete it, we might leave orphan transcriptions?
                # Transcriptions are linked, so we should delete them too or rely on cascade?
                # InstantDB doesn't cascade delete by default.
                # For now, just delete the video.
                from instantdb_admin_client import Delete
                await db.transact([Delete(collection="videos", id=cv["id"])])

    # Create/Update Video
    video_data = {
        "platform": platform,
        "external_id": video_id,
        "original_url": url,
        "title": title,
        "audio_path": audio_path,
        "duration": duration,
        "upload_date": upload_date,
        "channel": channel,
        "created_at": datetime.now().isoformat()
    }
    
    steps = [
        Update(collection="videos", id=video_uuid, data=video_data)
    ]
    
    # Create Transcription entity
    if json_path:
        import uuid
        transcription_uuid = str(uuid.uuid4())
        transcription_data = {
            "path": json_path,
            "created_at": datetime.now().isoformat(),
            "model": "base",
            "tool": "whisper.cpp"
        }
        steps.append(Update(collection="transcriptions", id=transcription_uuid, data=transcription_data))
        steps.append(Link(collection="videos", id=video_uuid, links={"transcriptions": transcription_uuid}))
        
    await db.transact(steps)
    print("Upserted video and transcription to InstantDB.")

async def process_video(url, video_uuid=None):
    # Download
    audio_path, vid_id, vid_title, platform, duration, upload_date, channel = download_audio(url)
    
    # Transcribe
    segments, json_path = transcribe_audio(audio_path, vid_id, platform)
    
    if not segments:
        print("Failed to get segments.")
        return

    # Upsert to InstantDB
    await upsert_video_record(vid_id, platform, url, vid_title, audio_path, json_path, duration, upload_date, channel, video_uuid)

def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <video_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    asyncio.run(process_video(url))

if __name__ == "__main__":
    main()
