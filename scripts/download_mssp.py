#!/usr/bin/env python3
"""
HOW:
  `uv run --with requests --with beautifulsoup4 scripts/download_mssp.py`
  
  Or with options:
  `uv run --with requests --with beautifulsoup4 scripts/download_mssp.py --dry-run`
  `uv run --with requests --with beautifulsoup4 scripts/download_mssp.py --limit 5`
  `uv run --with requests --with beautifulsoup4 scripts/download_mssp.py --skip-existing`

  [Inputs]
  - --dry-run: List episodes without downloading (preview mode)
  - --limit N: Download only first N episodes (useful for testing)
  - --skip-existing: Skip files that already exist (default: True)
  - --no-skip-existing: Force re-download of all files
  - --output-dir: Output directory (default: downloads/mssp)

  [Outputs]
  - MP3 files in downloads/mssp/ (e.g., "Inaugral Business.mp3")
  - JSON metadata files alongside each MP3 (e.g., "Inaugral Business.json")
  - Console output showing download progress

  [Side Effects]
  - Downloads ~11GB of MP3 files from msspoldt.b-cdn.net CDN
  - Creates JSON metadata files with episode info
  - Network requests to msspoldt.com for episode list
  - Network requests to CDN for MP3 files

WHO:
  Roo (AI Agent), User
  (Context: Archiving the legendary Old Testament era of Matt and Shane's Secret Podcast)

WHAT:
  A script to download all 145 episodes of Matt and Shane's Secret Podcast
  "Old Testament" era (Nov 2016 - Aug 2019) from msspoldt.com.
  
  The Old Testament represents the raw, unfiltered, no-limits era of MSSP before
  Shane got the SNL gig and subsequent firing. These episodes capture Matt and Shane
  at their most unhinged - recording in basements, going full throttle on every topic,
  and building the Dawg Pound from the ground up. Classic bits include:
  
  - The Inaugral Business (Ep. 1) - Where it all began
  - Special Guest Dan Soder (Ep. 11) - Early crossover with the comedy world
  - Boy Scouts with Rich Vos (Ep. 12) - Legendary guest appearance
  - The Night Cast (Ep. 23) - Late night unhinged energy
  - Our First Black Guest (Ep. 48) - Self-explanatory dawg
  - Live Cast #3 (Ep. 93) - Patreon exclusive chaos
  - SWAPCAST W Ya F#cked It (Ep. 126) - Podcast crossover madness
  - Live @ The Stand w Nick Mullen (Ep. 136) - NYC comedy scene collision
  
  This script:
  1. Scrapes the episode list from the main page
  2. Extracts metadata (title, date, description, URLs)
  3. Downloads MP3 files from the BunnyCDN
  4. Creates JSON metadata files for each episode
  5. Handles problematic URLs with special characters (#) via CDN URL construction

WHEN:
  2025-12-10
  Last Modified: 2025-12-10
  [Change Log:
    - 2025-12-10: Initial creation
    - 2025-12-10: Added CDN URL fallback for episodes with # in title (93, 126)
  ]

WHERE:
  scripts/download_mssp.py

WHY:
  The Old Testament episodes are hosted on a fan-run archive site (msspoldt.com)
  that could disappear at any time. These episodes represent comedy history -
  the raw, uncut, pre-fame era of what would become one of the biggest comedy
  podcasts. Archiving them locally ensures:
  
  1. Preservation of comedy history
  2. Offline access for true dawgs
  3. Potential future processing (transcription, speaker diarization, clip extraction)
  4. Protection against link rot and site takedowns
  
  Design decisions:
  - Uses BunnyCDN URLs directly when page fetch fails (handles # character issues)
  - Skips existing files by default (resumable downloads)
  - Creates JSON metadata for each episode (enables future indexing/search)
  - 1-second delay between downloads (respectful to the server)
  - Progress indicator for large file downloads
  
  Trade-offs:
  - Downloads are sequential (could be parallelized but we're being nice to the server)
  - ~11GB storage required (worth it for the dawgs)
"""

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, unquote, quote

import requests
from bs4 import BeautifulSoup


@dataclass
class Episode:
    """Represents a podcast episode with metadata."""
    episode_number: int
    title: str
    date: str
    description: str
    page_url: str
    mp3_url: str
    filename: str


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename.
    Removes or replaces characters that are invalid in filenames.
    """
    # Replace problematic characters
    name = name.replace("'", "'")
    name = name.replace('"', "")
    name = name.replace("/", "-")
    name = name.replace("\\", "-")
    name = name.replace(":", " -")
    name = name.replace("?", "")
    name = name.replace("*", "")
    name = name.replace("<", "")
    name = name.replace(">", "")
    name = name.replace("|", "-")
    
    # Remove .mp3 extension if present (we'll add it back)
    if name.lower().endswith(".mp3"):
        name = name[:-4]
    
    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()


def construct_cdn_url_from_page_url(page_url: str) -> str:
    """
    Construct the CDN URL directly from the page URL.
    
    The CDN URL pattern is:
    - Base: https://msspoldt.b-cdn.net/
    - Filename: The page URL path with:
      - .html removed
      - ' replaced with _
      - Properly URL-encoded (spaces, brackets, #, etc.)
    
    Example:
    Page: https://msspoldt.com/episodes/Matt and Shane's Secret Podcast Ep. 93 (Patreon) - LIVE CAST #3 [Aug. , 2018].mp3.html
    CDN:  https://msspoldt.b-cdn.net/Matt%20and%20Shane_s%20Secret%20Podcast%20Ep.%2093%20(Patreon)%20-%20LIVE%20CAST%20%233%20%5BAug.%20,%202018%5D.mp3
    """
    # Extract the filename from the page URL
    # Remove the base URL and .html extension
    if page_url.endswith('.html'):
        filename = page_url.rsplit('/', 1)[-1][:-5]  # Remove .html
    else:
        filename = page_url.rsplit('/', 1)[-1]
    
    # Replace ' with _ (CDN uses underscores for apostrophes)
    filename = filename.replace("'", "_")
    
    # URL-encode the filename properly
    # quote() encodes everything except alphanumerics and _.-~
    # We need to encode spaces, brackets, #, etc.
    encoded_filename = quote(filename, safe='')
    
    return f"https://msspoldt.b-cdn.net/{encoded_filename}"


def fetch_mp3_url_from_page(page_url: str) -> Optional[str]:
    """
    Fetch the actual MP3 URL from an episode page.
    
    The MP3 files are hosted on a CDN (msspoldt.b-cdn.net) and the URL
    is embedded in an <audio> tag's src attribute.
    
    If the page fetch fails (e.g., due to special characters in URL),
    we construct the CDN URL directly from the page URL pattern.
    """
    try:
        response = requests.get(page_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the audio tag
        audio_tag = soup.find('audio')
        if audio_tag and audio_tag.get('src'):
            return audio_tag.get('src')
        
        # If no audio tag found, try constructing the URL
        print(f"    No audio tag found, constructing CDN URL...")
        return construct_cdn_url_from_page_url(page_url)
        
    except requests.RequestException as e:
        print(f"    Page fetch failed ({e}), constructing CDN URL...")
        # Construct the CDN URL directly from the page URL pattern
        return construct_cdn_url_from_page_url(page_url)


def fetch_episode_list(base_url: str = "https://msspoldt.com/") -> list[Episode]:
    """
    Fetch the list of all episodes from the main page.
    
    Parses the HTML table containing episode information and extracts:
    - Episode number
    - Title
    - Date
    - Description
    - Links to episode pages
    
    Note: MP3 URLs are fetched lazily when downloading each episode,
    as they are hosted on a CDN and embedded in individual episode pages.
    """
    print(f"Fetching episode list from {base_url}...")
    
    response = requests.get(base_url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    episodes = []
    
    # Find the table with episodes
    table = soup.find('table')
    if not table:
        raise ValueError("Could not find episode table on page")
    
    rows = table.find_all('tr')
    
    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 4:
            continue
        
        # Extract episode number
        ep_num_text = cells[0].get_text(strip=True)
        try:
            episode_number = int(ep_num_text)
        except ValueError:
            continue
        
        # Extract title and link
        title_cell = cells[1]
        link = title_cell.find('a')
        if link:
            title = link.get_text(strip=True)
            page_url = urljoin(base_url, link.get('href', ''))
        else:
            title = title_cell.get_text(strip=True)
            page_url = ""
        
        # Extract date
        date = cells[2].get_text(strip=True)
        
        # Extract description
        description = cells[3].get_text(strip=True)
        
        # MP3 URL will be fetched from the episode page when downloading
        # (it's hosted on a CDN and embedded in the audio tag)
        mp3_url = ""
        
        # Create sanitized filename
        sanitized_title = sanitize_filename(title)
        filename = f"{sanitized_title}.mp3"
        
        episode = Episode(
            episode_number=episode_number,
            title=title,
            date=date,
            description=description,
            page_url=page_url,
            mp3_url=mp3_url,
            filename=filename
        )
        
        episodes.append(episode)
    
    print(f"Found {len(episodes)} episodes")
    return episodes


def download_episode(episode: Episode, output_dir: Path, skip_existing: bool = True) -> bool:
    """
    Download a single episode MP3 and create its metadata JSON file.
    
    First fetches the episode page to get the actual MP3 URL from the CDN,
    then downloads the MP3 file and creates a JSON metadata file.
    
    Returns True if download was successful, False otherwise.
    """
    mp3_path = output_dir / episode.filename
    json_path = output_dir / f"{episode.filename[:-4]}.json"
    
    # Check if already exists
    if skip_existing and mp3_path.exists() and json_path.exists():
        print(f"  Skipping (already exists): {episode.filename}")
        return True
    
    print(f"  Downloading: {episode.title}")
    
    try:
        # First, fetch the actual MP3 URL from the episode page
        print(f"    Fetching MP3 URL from episode page...")
        mp3_url = fetch_mp3_url_from_page(episode.page_url)
        
        if not mp3_url:
            print(f"    Error: Could not find MP3 URL on episode page")
            return False
        
        # Update the episode's mp3_url for metadata
        episode.mp3_url = mp3_url
        
        # Download MP3
        response = requests.get(mp3_url, stream=True, timeout=300)
        response.raise_for_status()
        
        # Get total size for progress
        total_size = int(response.headers.get('content-length', 0))
        
        # Write MP3 file
        with open(mp3_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r    Progress: {percent:.1f}%", end="", flush=True)
        
        print()  # New line after progress
        
        # Create metadata JSON
        metadata = {
            "episode_number": episode.episode_number,
            "title": episode.title,
            "date": episode.date,
            "description": episode.description,
            "page_url": episode.page_url,
            "mp3_url": episode.mp3_url,
            "filename": episode.filename,
            "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"    Saved metadata: {json_path.name}")
        return True
        
    except requests.RequestException as e:
        print(f"    Error downloading: {e}")
        # Clean up partial download
        if mp3_path.exists():
            mp3_path.unlink()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download Matt and Shane's Secret Podcast episodes from msspoldt.com"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List episodes without downloading"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Download only first N episodes"
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip files that already exist (default: True)"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_false",
        dest="skip_existing",
        help="Re-download files even if they exist"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("downloads/mssp"),
        help="Output directory (default: downloads/mssp)"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch episode list
    try:
        episodes = fetch_episode_list()
    except Exception as e:
        print(f"Error fetching episode list: {e}")
        sys.exit(1)
    
    # Apply limit if specified
    if args.limit:
        episodes = episodes[:args.limit]
        print(f"Limited to first {args.limit} episodes")
    
    # Dry run - just list episodes
    if args.dry_run:
        print("\n=== Episode List (Dry Run) ===\n")
        for ep in episodes:
            print(f"Ep. {ep.episode_number}: {ep.title}")
            print(f"  Date: {ep.date}")
            print(f"  Description: {ep.description[:100]}..." if len(ep.description) > 100 else f"  Description: {ep.description}")
            print(f"  MP3 URL: {ep.mp3_url}")
            print()
        print(f"Total: {len(episodes)} episodes")
        return
    
    # Download episodes
    print(f"\n=== Downloading {len(episodes)} episodes to {args.output_dir} ===\n")
    
    successful = 0
    failed = 0
    
    for i, episode in enumerate(episodes, 1):
        print(f"[{i}/{len(episodes)}] Episode {episode.episode_number}")
        
        if download_episode(episode, args.output_dir, args.skip_existing):
            successful += 1
        else:
            failed += 1
        
        # Small delay between downloads to be nice to the server
        if i < len(episodes):
            time.sleep(1)
    
    print(f"\n=== Download Complete ===")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()