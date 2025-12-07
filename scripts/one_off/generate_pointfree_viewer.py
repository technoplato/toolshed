import sys
from bs4 import BeautifulSoup
import re
import json
import os
import urllib.request
import urllib.error

def fetch_github_content(url):
    """
    Attempts to fetch raw content or diffs from GitHub URLs.
    Returns (content, language/type) or (None, None).
    """
    # 1. Commits / Pull Requests -> .diff
    # 2. Blobs -> raw content
    
    target_url = None
    content_type = "text"
    
    if "github.com" not in url:
        return None, None
        
    # Clean URL: remove fragment and trailing slash
    clean_url = url.split('#')[0].rstrip('/')
    
    # Remove /files suffix commonly found in PR review links
    if clean_url.endswith("/files"):
        clean_url = clean_url[:-6]

    try:
        if "/commit/" in clean_url or "/pull/" in clean_url:
            # Append .diff if not present
            if not clean_url.endswith(".diff") and not clean_url.endswith(".patch"):
                target_url = clean_url + ".diff"
                content_type = "diff"
            else:
                target_url = clean_url
                content_type = "diff"
        elif "/blob/" in clean_url:
            # Convert to raw.githubusercontent.com
            # https://github.com/user/repo/blob/branch/file.swift
            # -> https://raw.githubusercontent.com/user/repo/branch/file.swift
            target_url = clean_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            # Guess language
            if target_url.endswith(".swift"): content_type = "swift"
            elif target_url.endswith(".py"): content_type = "python"
            else: content_type = "code"
        
        if target_url:
            print(f"Fetching: {target_url}")
            req = urllib.request.Request(
                target_url, 
                data=None, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8'), content_type
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None, None
        
    return None, None

def parse_episode(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    transcript_data = []
    all_references = {} # URL -> {text, timestamps: set(), content: str, type: str}
    
    # 1. Parse Transcript
    timestamp_divs = soup.find_all("div", id=re.compile(r"^t\d+$"))
    
    last_speaker = "Unknown"
    
    for div in timestamp_divs:
        timestamp_id = div.get('id')
        seconds = int(timestamp_id[1:])
        
        # Format seconds
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        time_str = f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
            
        speaker = None
        parent = div.parent
        grandparent = parent.parent if parent else None
        
        if grandparent:
            strong = grandparent.find("strong")
            if strong:
                speaker = strong.get_text().strip()
                last_speaker = speaker
        
        current_speaker = speaker if speaker else last_speaker
        current_node = grandparent if grandparent else div.parent
        content_html = ""
        
        if current_node:
            for sibling in current_node.next_siblings:
                if sibling.name == 'div':
                    if sibling.find("div", id=re.compile(r"^t\d+$")) or "Unlock This Episode" in sibling.get_text():
                        break

                if sibling.name in ['p', 'ul', 'ol', 'pre']:
                    # Extract links before cleaning
                    for link in sibling.find_all('a'):
                        href = link.get('href')
                        text = link.get_text().strip()
                        if href and not href.startswith('#'):
                            if href not in all_references:
                                all_references[href] = {"text": text, "timestamps": set(), "content": None, "type": None}
                            all_references[href]["timestamps"].add((seconds, time_str))

                    if hasattr(sibling, 'attrs'):
                        # Keep minimal attributes for viewer
                        new_attrs = {}
                        if 'href' in sibling.attrs: new_attrs['href'] = sibling.attrs['href']
                        sibling.attrs = new_attrs

                        for child in sibling.find_all(True):
                             child_new_attrs = {}
                             if 'href' in child.attrs: child_new_attrs['href'] = child.attrs['href']
                             child.attrs = child_new_attrs
                    
                    content_html += str(sibling)
        
        if content_html.strip():
            transcript_data.append({
                "timestamp": seconds,
                "time_display": time_str,
                "speaker": current_speaker,
                "content": content_html
            })

    # 1.5 Fetch Content for References
    print(f"Processing {len(all_references)} references...")
    for url, data in all_references.items():
        # Only fetch if it looks like code
        if "github.com" in url:
            content, ctype = fetch_github_content(url)
            if content:
                data["content"] = content
                data["type"] = ctype

    # 2. Extract Downloads
    downloads = []
    downloads_header = soup.find("h4", id="downloads")
    if downloads_header:
        container = downloads_header.parent.parent 
        if container:
            for link in container.find_all("a"):
                href = link.get('href')
                text = link.get_text().strip()
                if "gh-icon" not in text and href:
                     downloads.append({"text": text, "url": href})

    return transcript_data, downloads, all_references

def generate_viewer(html_path, video_filename):
    transcript, downloads, references = parse_episode(html_path)
    
    episode_title = "Episode Playback"
    
    css = """
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; height: 100vh; display: flex; flex-direction: column; background: #f9f9f9; }
    header { background: #121212; color: white; padding: 1rem; flex-shrink: 0; }
    main { display: flex; flex: 1; overflow: hidden; }
    #video-container { flex: 0 0 50%; background: black; display: flex; align-items: center; justify-content: center; }
    video { width: 100%; max-height: 100%; }
    #transcript-container { flex: 1; overflow-y: auto; padding: 2rem; background: white; border-left: 1px solid #eee; }
    .transcript-block { display: flex; margin-bottom: 1.5rem; }
    .timestamp { font-family: monospace; color: #999; margin-right: 1rem; cursor: pointer; user-select: none; }
    .timestamp:hover { color: #007aff; text-decoration: underline; }
    .speaker { font-weight: bold; margin-bottom: 0.25rem; color: #333; }
    .content p { margin: 0 0 0.5rem 0; line-height: 1.6; }
    .content pre { background: #f6f8fa; padding: 1rem; border-radius: 6px; overflow-x: auto; }
    .active-block { background-color: #fffbdd; transition: background-color 0.3s; padding: 0.5rem; margin: -0.5rem; border-radius: 4px; }
    
    #sidebar { width: 450px; padding: 1rem; border-left: 1px solid #ddd; background: #fafafa; overflow-y: auto; font-size: 0.9em; flex-shrink: 0; }
    h3 { font-size: 1.1em; margin-top: 1rem; border-bottom: 1px solid #ddd; padding-bottom: 0.5rem; code-weight: 600; }
    ul { list-style: none; padding: 0; }
    li { margin-bottom: 1rem; word-break: break-word; border-bottom: 1px solid #eee; padding-bottom: 1rem; }
    a { color: #007aff; text-decoration: none; }
    a:hover { text-decoration: underline; }
    
    .ref-timestamps { margin-top: 0.25rem; font-size: 0.85em; color: #666; }
    .ts-link { margin-right: 0.5rem; cursor: pointer; background: #e0e0e0; padding: 1px 5px; border-radius: 3px; font-family: monospace; }
    .ts-link:hover { background: #d0d0d0; color: #000; }
    
    details { margin-top: 0.5rem; border: 1px solid #ccc; border-radius: 4px; background: white; overflow: hidden; }
    summary { padding: 0.5rem; cursor: pointer; background: #f0f0f0; font-weight: 500; font-size: 0.85em; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
    summary:after { content: "▼"; font-size: 0.8em; color: #666; }
    details[open] summary:after { content: "▲"; }
    
    .code-preview { padding: 0.5rem; overflow-x: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.8em; white-space: pre; background: #fff; max-height: 500px; overflow-y: auto; color: #24292e; border-top: 1px solid #eee; }
    """
    
    lines = []
    for item in transcript:
        lines.append(f"""
        <div class="transcript-block" data-timestamp="{item['timestamp']}">
            <div class="timestamp" onclick="seekTo({item['timestamp']})">[{item['time_display']}]</div>
            <div>
                <div class="speaker">{item['speaker']}</div>
                <div class="content">{item['content']}</div>
            </div>
        </div>
        """)
    transcript_html = "\n".join(lines)
    
    download_links = ""
    if downloads:
        download_links = "<ul>" + "".join([f'<li><a href="{d["url"]}" target="_blank">{d["text"]}</a></li>' for d in downloads]) + "</ul>"
        
    ref_links = ""
    if references:
        ref_list_items = []
        for url, data in references.items():
            ts_html = ""
            sorted_ts = sorted(list(data["timestamps"]), key=lambda x: x[0])
            for sec, disp in sorted_ts:
                ts_html += f'<span class="ts-link" onclick="seekTo({sec})">{disp}</span> '
            
            content_block = ""
            if data["content"]:
                summary_text = f"Show {data['type'].upper()} content"
                # Basic escaping
                safe_content = data['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                content_block = f"""
                <details>
                    <summary>{summary_text}</summary>
                    <div class="code-preview">{safe_content}</div>
                </details>
                """
            
            ref_list_items.append(f"""
            <li>
                <div style="font-weight:500; margin-bottom: 0.25rem;"><a href="{url}" target="_blank">{data['text']}</a></div>
                <div class="ref-timestamps" style="margin-bottom:0.25rem;">Mentioned at: {ts_html}</div>
                {content_block}
            </li>
            """)
        ref_links = "<ul>" + "".join(ref_list_items) + "</ul>"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{episode_title}</title>
        <style>{css}</style>
    </head>
    <body>
        <header>
            <h1>{episode_title}</h1>
        </header>
        <main>
            <div id="video-container">
                <video id="player" controls>
                    <source src="{video_filename}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            </div>
            <div id="transcript-container">
                {transcript_html}
            </div>
            <div id="sidebar">
                <h3>Downloads</h3>
                {download_links}
                
                <h3>References & Links</h3>
                {ref_links}
            </div>
        </main>
        <script>
            const player = document.getElementById('player');
            const blocks = document.querySelectorAll('.transcript-block');
            let lastActiveBlock = null;
            
            function seekTo(seconds) {{
                player.currentTime = seconds;
                player.play();
            }}
            
            player.addEventListener('timeupdate', () => {{
                const t = player.currentTime;
                let activeBlock = null;
                
                blocks.forEach(block => {{
                    const blockTime = parseFloat(block.dataset.timestamp);
                    if (blockTime <= t) {{
                        activeBlock = block;
                    }}
                    block.classList.remove('active-block');
                }});
                
                if (activeBlock) {{
                    activeBlock.classList.add('active-block');
                    if (activeBlock !== lastActiveBlock) {{
                        activeBlock.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        lastActiveBlock = activeBlock;
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    output_path = html_path.rsplit('.', 1)[0] + "_viewer.html"
    if "_viewer" in html_path:
        output_path = html_path
    
    with open(output_path, "w") as f:
        f.write(html_content)
    
    print(f"Viewer generated at: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_viewer.py <html_file> <video_file_name>")
        sys.exit(1)
        
    generate_viewer(sys.argv[1], sys.argv[2])
