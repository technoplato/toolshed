import os
import sys
import sqlite3
import json
import urllib.parse
import yt_dlp
from pywhispercpp.model import Model

DB_NAME = "transcriptions.db"

def init_db():
    """Initializes the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT DEFAULT 'youtube',
            external_id TEXT UNIQUE,
            url TEXT,
            title TEXT,
            audio_path TEXT,
            transcript_path TEXT,
            player_path TEXT,
            json_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Ensure columns exist (migrations)
    for col in ['json_path', 'player_path']:
        try:
            c.execute(f"ALTER TABLE videos ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn

def upsert_video_record(conn, external_id, platform, url, title, audio_path=None, transcript_path=None, player_path=None, json_path=None):
    c = conn.cursor()
    c.execute("SELECT id FROM videos WHERE external_id = ?", (external_id,))
    row = c.fetchone()
    
    if row:
        updates = []
        params = []
        if title: updates.append("title=?"); params.append(title)
        if audio_path: updates.append("audio_path=?"); params.append(audio_path)
        if transcript_path: updates.append("transcript_path=?"); params.append(transcript_path)
        if player_path: updates.append("player_path=?"); params.append(player_path)
        if json_path: updates.append("json_path=?"); params.append(json_path)
        if platform: updates.append("platform=?"); params.append(platform)
        
        if updates:
            sql = f"UPDATE videos SET {', '.join(updates)} WHERE external_id=?"
            params.append(external_id)
            c.execute(sql, tuple(params))
    else:
        c.execute('''INSERT INTO videos 
                     (platform, external_id, url, title, audio_path, transcript_path, player_path, json_path) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                  (platform, external_id, url, title, audio_path, transcript_path, player_path, json_path))
    conn.commit()

def download_audio(video_url, output_dir="downloads"):
    """Downloads audio using yt-dlp and returns platform/id info."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract info first to get platform (extractor) and ID
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
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
        return output_path, video_id, title, extractor

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
        
    return output_path, video_id, title, extractor

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

def generate_markdown(segments, video_id, platform, title, url, output_dir="transcriptions"):
    md_filename = os.path.join(output_dir, f"{platform}_{video_id}_transcript.md")
    
    markdown_content = f"# Transcription: {title}\n\n"
    markdown_content += f"**Video:** [{url}]({url})\n\n"
    # Initialize Fuse
    # The following JavaScript code snippet was provided in the instruction.
    # As this is a Python file, it's commented out to maintain syntactical correctness.
    # If this was intended for a template that generates JavaScript, it should be placed there.
    # const fuse = new Fuse(SEGMENTS, {
    #     keys: ['text'],
    #     includeMatches: true,
    #     threshold: 0.2,
    #     ignoreLocation: true,
    #     minMatchCharLength: 3
    # });
    
    for seg in segments:
        text = seg['text']
        if not text:
            continue
            
        timestamp_str = format_timestamp(seg['start'])
        # Deep links depend on platform. Currently only supporting YouTube deep links easily.
        link = ""
        if platform == 'youtube':
            link = f"https://youtu.be/{video_id}?t={int(seg['start'])}"
            markdown_content += f"[{timestamp_str}]({link})\n\n{text}\n\n"
        else:
            markdown_content += f"**{timestamp_str}**\n\n{text}\n\n"

    with open(md_filename, "w") as f:
        f.write(markdown_content)
    print(f"Saved transcription Markdown to {md_filename}")
    return md_filename

def update_index_html(conn, output_dir="transcriptions"):
    """Generates an index.html listing all videos."""
    c = conn.cursor()
    c.execute("SELECT platform, external_id, title, created_at FROM videos ORDER BY created_at DESC")
    videos = c.fetchall()
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Transcribed Videos</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .video-item { border: 1px solid #ddd; padding: 1rem; margin-bottom: 1rem; border-radius: 4px; }
        .video-item a { text-decoration: none; color: #1890ff; font-weight: bold; font-size: 1.1rem; }
        .meta { color: #666; font-size: 0.9rem; margin-top: 0.5rem; }
    </style>
</head>
<body>
    <h1>Transcribed Videos</h1>
    
    <div class="video-item" style="background: #f0f2f5; border-color: #d9d9d9;">
        <h3>Add New Video</h3>
        <form action="/submit" method="post" style="display: flex; gap: 10px;">
            <input type="text" name="url" placeholder="Paste YouTube URL here..." style="flex: 1; padding: 0.5rem; border: 1px solid #ccc; border-radius: 4px;" required>
            <button type="submit" style="padding: 0.5rem 1rem; background: #1890ff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">Transcribe</button>
        </form>
    </div>
"""
    
    for platform, vid_id, title, created_at in videos:
        # Link to the generic player with params
        player_link = f"player.html?id={vid_id}&platform={platform}&title={urllib.parse.quote(title)}"
        
        html += f"""
        <div class="video-item">
            <a href="{player_link}">{title}</a>
            <div class="meta">Platform: {platform} | ID: {vid_id} | {created_at}</div>
        </div>
        """
        
    html += "</body></html>"
    
    with open(os.path.join(output_dir, "index.html"), "w") as f:
        f.write(html)
    print("Updated index.html")

def process_video(url, conn):
    audio_path, vid_id, vid_title, platform = download_audio(url)
    
    segments, json_path = transcribe_audio(audio_path, vid_id, platform)
    
    if not segments:
        print("Failed to get segments.")
        return

    md_path = generate_markdown(segments, vid_id, platform, vid_title, url)
    
    # We no longer generate individual HTML players.
    # We rely on the generic player.html and the JSON file.
    
    upsert_video_record(conn, vid_id, platform, url, vid_title, audio_path, md_path, None, json_path)
    update_index_html(conn)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <video_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    
    conn = init_db()
    try:
        process_video(url, conn)
    finally:
        conn.close()
