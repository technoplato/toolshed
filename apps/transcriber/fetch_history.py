import os
import sys
import json
import argparse
import yt_dlp
import requests
import re
from datetime import datetime

def parse_netscape_cookies(cookie_file):
    """Parse Netscape cookies file into a dictionary for requests."""
    cookies = {}
    try:
        with open(cookie_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    # domain = parts[0] # Not used for simple dict
                    name = parts[5]
                    value = parts[6]
                    cookies[name] = value
    except Exception as e:
        print(f"Warning: Failed to parse cookies for requests: {e}")
    return cookies

def get_video_details(url, cookies):
    """Fetch video page and extract metadata using regex."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
        if response.status_code != 200:
            return {}
        
        html = response.text
        data = {}
        
        # Description (og:description is usually good)
        og_desc = re.search(r'<meta property="og:description" content="([^"]+)">', html)
        if og_desc:
            data['description'] = og_desc.group(1)
        else:
             desc_match = re.search(r'<meta name="description" content="([^"]+)">', html)
             if desc_match:
                 data['description'] = desc_match.group(1)

        # Channel
        channel_match = re.search(r'<link itemprop="name" content="([^"]+)">', html)
        if channel_match:
            data['channel'] = channel_match.group(1)
            
        # Date
        date_match = re.search(r'<meta itemprop="datePublished" content="([^"]+)">', html)
        if date_match:
            data['upload_date'] = date_match.group(1)
            
        # Views
        views_match = re.search(r'<meta itemprop="interactionCount" content="([^"]+)">', html)
        if views_match:
            data['view_count'] = views_match.group(1)

        return data
    except Exception as e:
        print(f"Error fetching details for {url}: {e}")
        return {}

def fetch_history(limit=10, cookie_file=None):
    """
    Fetches YouTube watch history using yt-dlp.
    
    Args:
        limit (int): Number of most recent videos to fetch.
        cookie_file (str): Path to the Netscape formatted cookies file.
    """
    # Resolve cookie file path
    if not cookie_file:
        # Default locations to check relative to this script or CWD
        script_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_root = os.path.abspath(os.path.join(script_dir, "../../"))
        
        possible_paths = [
            os.path.join(workspace_root, "cookies/halfjew22-youtube-cookies.txt"),
            "cookies/halfjew22-youtube-cookies.txt",
            "cookies.txt"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                cookie_file = path
                break
    
    if not cookie_file or not os.path.exists(cookie_file):
        print("Error: Cookie file not found. Please provide a valid cookie file path using --cookies.")
        return

    print(f"Using cookies from: {cookie_file}")

    # Configure yt-dlp options
    ydl_opts = {
        'quiet': True,
        'ignoreerrors': True,
        'cookiefile': cookie_file,
        'playlistend': limit,
        'extract_flat': True, # Try flat extraction to avoid format errors
        'sleep_interval': 1,   # Be polite to YouTube
    }

    history_url = "https://www.youtube.com/feed/history"

    print(f"Fetching recent {limit} videos from watch history...")
    
    # Parse cookies for requests fallback
    cookie_dict = parse_netscape_cookies(cookie_file)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # extract_info with download=False fetches metadata
            info = ydl.extract_info(history_url, download=False)
        except Exception as e:
            print(f"Error fetching history: {e}")
            return

        if 'entries' in info:
            entries = list(info['entries']) # Convert generator to list
            print(f"\nFound {len(entries)} videos:")
            
            results = []
            
            for i, entry in enumerate(entries):
                if not entry:
                    continue
                
                # Extract relevant fields
                video_data = {
                    "title": entry.get('title'),
                    "channel": entry.get('uploader'),
                    "upload_date": entry.get('upload_date'),
                    "description": entry.get('description'),
                    "duration": entry.get('duration'),
                    "view_count": entry.get('view_count'),
                    "url": entry.get('webpage_url', entry.get('url')),
                    "id": entry.get('id')
                }
                
                # Fallback if description or channel is missing
                if not video_data.get('description') or not video_data.get('channel'):
                    # print(f"Fetching details for {video_data['url']}...")
                    details = get_video_details(video_data['url'], cookie_dict)
                    # Only update if we found something
                    for k, v in details.items():
                        if v:
                            video_data[k] = v

                results.append(video_data)
                
                # Print summary
                print(f"\n--- Video {i+1} ---")
                print(f"Title: {video_data.get('title', 'N/A')}")
                print(f"Channel: {video_data.get('channel', 'N/A')}")
                print(f"Date: {video_data.get('upload_date', 'N/A')}")
                print(f"Duration: {video_data.get('duration', 'N/A')}s")
                print(f"Views: {video_data.get('view_count', 'N/A')}")
                print(f"URL: {video_data.get('url', 'N/A')}")
                desc = video_data.get('description', '')
                desc_preview = desc[:100].replace('\n', ' ') if desc else "N/A"
                print(f"Description: {desc_preview}...")

            # Optional: Save to JSON for further processing
            output_file = "watch_history.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nSaved full metadata to {output_file}")
            
            return results
            
        else:
            print("No entries found. Ensure cookies are valid and logged in.")
            return []

def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube watch history.")
    parser.add_argument("--limit", type=int, default=5, help="Number of videos to fetch")
    parser.add_argument("--cookies", type=str, help="Path to Netscape cookies file")
    
    args = parser.parse_args()
    
    fetch_history(limit=args.limit, cookie_file=args.cookies)

if __name__ == "__main__":
    main()
