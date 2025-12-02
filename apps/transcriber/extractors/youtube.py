"""
YouTube History Fetcher
=======================

This script fetches the most recent watch history from a user's YouTube account.
It uses `yt-dlp` to retrieve the history feed and extracts detailed metadata
for each video, including Channel ID, Channel URL, Upload Date, and Description.

It is designed to be robust against missing metadata in the initial feed by
falling back to scraping the individual video pages (using the same authenticated session)
to enrich the data.

Usage
-----
Run with `uv` to manage dependencies automatically:

```bash
uv run --with yt-dlp --with requests --with pydantic apps/transcriber/extractors/youtube.py --limit 5 --browser chrome
```

Options
-------
- `--limit`: Number of videos to fetch (default: 5).
- `--browser`: Browser to extract cookies from (default: 'chrome'). Options: chrome, firefox, safari, opera, edge.
- `--cookies`: Path to a Netscape-formatted cookies file (optional, overrides --browser).

Example Output
--------------
Fetched 2 videos:

--- Video 1 ---
Title: Rainy Mood
Channel: Rainy Mood - Topic (ID: UC90fOsOqo5_0HkBiPqCj5hg)
Channel URL: https://www.youtube.com/channel/UC90fOsOqo5_0HkBiPqCj5hg
Date: 2023-01-05T10:43:46-08:00
URL: https://www.youtube.com/watch?v=t0qpleYxQNs
Description: Provided to YouTube by CDBabyRainy Mood · Rainy MoodRainy Mood℗ 2023 Plain TheoryReleased on: 2023-0...

--- Video 2 ---
Title: Friends - Joey eats Rachel's dessert
Channel: martin zet (ID: None)
Channel URL: http://www.youtube.com/@martinzet7790
Date: 2014-05-28T12:34:22-07:00
URL: https://www.youtube.com/watch?v=TSFgDZJVYbo
Description: custard? good! jam? good! beef? GOOD!!!!...
"""

import os
import sys
import json
import re
import requests
import yt_dlp
from typing import List, Optional
from datetime import datetime, timedelta

# Add parent directory to path to allow imports if running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from apps.transcriber.lib.models import VideoMetadata, Channel
from apps.transcriber.lib.cookies import parse_netscape_cookies, find_cookie_file

class YouTubeHistoryFetcher:
    """
    Fetcher for YouTube watch history.
    """
    
    def __init__(self, cookie_file: str = None, browser: str = 'chrome'):
        self.cookie_file = cookie_file
        self.browser = browser
        self.cookies = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # Load cookies immediately to be used by requests
        self._load_cookies()

    def _load_cookies(self):
        """
        Load cookies from file or browser into a format requests can use.
        """
        if self.cookie_file:
            self.cookie_file = find_cookie_file(self.cookie_file)
            if self.cookie_file:
                print(f"Using cookies from file: {self.cookie_file}")
                self.cookies = parse_netscape_cookies(self.cookie_file)
                return

        if self.browser:
            print(f"Extracting cookies from {self.browser}...")
            opts = {
                'cookiesfrombrowser': (self.browser, ), 
                'quiet': True,
                'skip_download': True
            }
            with yt_dlp.YoutubeDL(opts) as ydl:
                self.cookies = ydl.cookiejar
                
    def fetch_history(self, limit: int = 10) -> List[VideoMetadata]:
        """
        Fetch the most recent watch history.
        """
        ydl_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'playlistend': limit,
            'extract_flat': True,
            'sleep_interval': 1,
        }
        
        if self.cookie_file:
            ydl_opts['cookiefile'] = self.cookie_file
        elif self.browser:
            ydl_opts['cookiesfrombrowser'] = (self.browser, )
        
        history_url = "https://www.youtube.com/feed/history"
        results = []

        print(f"Fetching recent {limit} videos from YouTube history...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(history_url, download=False)
            except Exception as e:
                print(f"Error fetching history list: {e}")
                return []

            if 'entries' not in info:
                print("No entries found.")
                return []

            entries = list(info['entries'])
            print(f"Found {len(entries)} entries. Processing metadata...")

            for entry in entries:
                if not entry:
                    continue
                
                video_id = entry.get('id')
                url = entry.get('webpage_url', entry.get('url'))
                title = entry.get('title')
                
                # Basic info from yt-dlp flat extraction
                channel_name = entry.get('uploader')
                channel_id = entry.get('channel_id') or entry.get('uploader_id')
                channel_url = entry.get('channel_url') or entry.get('uploader_url')
                duration = entry.get('duration')
                view_count = entry.get('view_count')
                upload_date = entry.get('upload_date')
                description = entry.get('description')
                
                # We need more details (Description, Channel ID, Channel URL)
                # We'll fetch the video page to get these if missing or to enrich
                # Only fetch if we are missing critical info or description
                if not description or not channel_id or not channel_url or not view_count:
                    details = self._get_video_details(url)
                    
                    description = details.get('description', description)
                    channel_id = channel_id or details.get('channel_id')
                    channel_url = channel_url or details.get('channel_url')
                    view_count = view_count or details.get('view_count')
                    
                    # Prefer details for channel name if yt-dlp missed it
                    if not channel_name and details.get('channel_name'):
                        channel_name = details.get('channel_name')
                    
                    # Prefer details for upload date if yt-dlp missed it
                    if not upload_date and details.get('upload_date'):
                        upload_date = details.get('upload_date')

                # Create Channel object
                channel = Channel(
                    name=channel_name or "Unknown",
                    id=channel_id,
                    url=channel_url
                )
                
                # Create VideoMetadata object
                video = VideoMetadata(
                    id=video_id,
                    title=title or "Unknown",
                    video_url=url,
                    upload_date=upload_date,
                    description=description,
                    duration=duration,
                    view_count=view_count,
                    channel=channel
                )
                
                results.append(video)
                
        return results

    def _get_video_details(self, url: str) -> dict:
        """
        Fetch video page and extract metadata using regex.
        """
        data = {}
        start_time = datetime.now()
        print(f"[{start_time.strftime('%H:%M:%S')}] Fetching details for {url}...")
        
        try:
            # Update headers to match a modern Chrome
            self.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            
            response = requests.get(url, cookies=self.cookies, headers=self.headers, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch {url}: Status {response.status_code}")
                return data
            
            html = response.text
            
            # Description
            og_desc = re.search(r'<meta property="og:description" content="([^"]+)">', html)
            if og_desc:
                data['description'] = og_desc.group(1)
            
            # Channel ID
            # <meta itemprop="channelId" content="UC...">
            chan_id_match = re.search(r'<meta itemprop="channelId" content="([^"]+)">', html)
            if chan_id_match:
                data['channel_id'] = chan_id_match.group(1)
            else:
                # Try finding in link tags
                # <link itemprop="url" href="http://www.youtube.com/channel/UC...">
                chan_url_match = re.search(r'<link itemprop="url" href="https?://www\.youtube\.com/channel/(UC[^"]+)">', html)
                if chan_url_match:
                    data['channel_id'] = chan_url_match.group(1)
            
            # Channel URL
            if data.get('channel_id'):
                data['channel_url'] = f"https://www.youtube.com/channel/{data['channel_id']}"
            else:
                # Try to find user/custom URL
                # <link itemprop="url" href="http://www.youtube.com/@UserName">
                user_url_match = re.search(r'<link itemprop="url" href="(https?://www\.youtube\.com/@[^"]+)">', html)
                if user_url_match:
                    data['channel_url'] = user_url_match.group(1)

            # Channel Name
            # <link itemprop="name" content="...">
            chan_name_match = re.search(r'<link itemprop="name" content="([^"]+)">', html)
            if chan_name_match:
                data['channel_name'] = chan_name_match.group(1)
                
            # Upload Date
            date_match = re.search(r'<meta itemprop="datePublished" content="([^"]+)">', html)
            if date_match:
                data['upload_date'] = date_match.group(1)

            # View Count
            # <meta itemprop="interactionCount" content="12345">
            views_match = re.search(r'<meta itemprop="interactionCount" content="(\d+)">', html)
            if views_match:
                data['view_count'] = int(views_match.group(1))
            else:
                # Try looking for "x views" text if meta tag missing (less reliable)
                # "viewCount":"12345" in JSON blobs
                json_views = re.search(r'"viewCount":"(\d+)"', html)
                if json_views:
                    data['view_count'] = int(json_views.group(1))

            return data
        except Exception as e:
            print(f"Warning: Failed to fetch details for {url}: {e}")
            return data

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch YouTube watch history.")
    parser.add_argument("--limit", type=int, default=5, help="Number of videos to fetch")
    parser.add_argument("--cookies", type=str, help="Path to Netscape cookies file")
    parser.add_argument("--browser", type=str, default="chrome", help="Browser to extract cookies from (chrome, firefox, safari)")
    
    args = parser.parse_args()
    
    try:
        fetcher = YouTubeHistoryFetcher(cookie_file=args.cookies, browser=args.browser)
        history = fetcher.fetch_history(limit=args.limit)
        
        print(f"\nFetched {len(history)} videos:")
        for i, video in enumerate(history):
            print(f"\n--- Video {i+1} ---")
            print(f"Title: {video.title}")
            print(f"Channel: {video.channel.name} (ID: {video.channel.id})")
            print(f"Channel URL: {video.channel.url}")
            print(f"Date: {video.upload_date}")
            print(f"URL: {video.video_url}")
            desc_preview = video.description[:100].replace('\n', ' ') if video.description else "N/A"
            print(f"Description: {desc_preview}...")
            
        # Save to JSON
        output_file = "youtube_history.json"
        with open(output_file, 'w') as f:
            # Pydantic v2 model_dump, v1 dict()
            # Assuming v2 or v1 compatibility
            try:
                json_data = [v.model_dump() for v in history]
            except AttributeError:
                json_data = [v.dict() for v in history]
                
            json.dump(json_data, f, indent=2)
        print(f"\nSaved to {output_file}")
            
    except Exception as e:
        print(f"Error: {e}")
