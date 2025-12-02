import os
import json
from bs4 import BeautifulSoup

def parse_history_html(file_path):
    """Parses the YouTube history HTML file."""
    print(f"Parsing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    videos = []
    
    # YouTube history structure often uses ytd-video-renderer
    # But in a raw HTML dump, it might be different depending on how it was saved.
    # Let's look for the main video containers.
    
    # Strategy 1: Look for ytd-video-renderer tags (if it's a full DOM dump)
    renderers = soup.find_all('ytd-video-renderer')
    
    if not renderers:
        print("No ytd-video-renderer tags found. Trying alternative selectors...")
        # Strategy 2: Look for video-title ids or classes
        titles = soup.find_all(id='video-title')
        if titles:
            print(f"Found {len(titles)} video titles by ID. Attempting to infer parents.")
            # This is riskier but might work if the custom element tags are stripped or not parsed correctly
            for title in titles:
                # Go up to find the container
                renderer = title.find_parent('ytd-video-renderer')
                if renderer and renderer not in renderers:
                    renderers.append(renderer)
    
    print(f"Found {len(renderers)} video renderers.")
    
    for i, renderer in enumerate(renderers):
        try:
            # Title & URL
            title_el = renderer.find(id='video-title')
            title = title_el.get_text(strip=True) if title_el else "Unknown"
            url = title_el.get('href') if title_el else None
            if url and not url.startswith('http'):
                url = 'https://www.youtube.com' + url
                
            # Channel
            channel_el = renderer.find('ytd-channel-name')
            channel = channel_el.get_text(strip=True) if channel_el else "Unknown"
            
            # Description
            desc_el = renderer.find(id='description-text')
            description = desc_el.get_text(strip=True) if desc_el else ""
            
            # Metadata (Views, Time)
            # Usually in ytd-video-meta-block or similar
            # The "Watched on" date might be in a header above the video or in the metadata line
            
            # Check for specific history metadata
            # In /feed/history, there's often a "Watched" badge or text.
            # But the DATE is often a section header (e.g. "Today", "Yesterday").
            # We need to find which section this video belongs to.
            
            # Find parent section if possible
            # Structure: ytd-section-list-renderer -> ytd-item-section-renderer -> ytd-video-renderer
            section = renderer.find_parent('ytd-item-section-renderer')
            section_title = "Unknown Date"
            if section:
                header = section.find('div', id='title') # or similar for section header
                # Often it's in a ytd-item-section-header-renderer
                header_renderer = section.find('ytd-item-section-header-renderer')
                if header_renderer:
                    header_text = header_renderer.get_text(strip=True)
                    if header_text:
                        section_title = header_text
            
            video_data = {
                "title": title,
                "url": url,
                "channel": channel,
                "description": description[:100] + "..." if description else "",
                "section_date": section_title
            }
            videos.append(video_data)
            
        except Exception as e:
            print(f"Error parsing video {i}: {e}")
            
    return videos

def main():
    # Default to the dump file in the parent directory
    dump_file = "../../history_dump.html"
    if not os.path.exists(dump_file):
        print(f"Error: {dump_file} not found.")
        return
        
    results = parse_history_html(dump_file)
    
    print(f"\nParsed {len(results)} videos.")
    if results:
        print("\nSample (first 3):")
        print(json.dumps(results[:3], indent=2))
        
        # Save to JSON
        with open("parsed_history.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\nSaved to parsed_history.json")

if __name__ == "__main__":
    main()
