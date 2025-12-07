import sys
from bs4 import BeautifulSoup
import re

def parse_transcript(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # The transcript seems to be in the article tag or identifiable blocks
    # Based on the snippet:
    # <div class="..."><strong ...>Stephen</strong><div><div ... id="t31"><a data-timestamp="31" ...>0:31</a></div></div></div>
    # <p ...>Well, that’s kind of true...</p>
    
    transcript_text = ""
    
    # Locate the main container for the transcript.
    # It seems to be under <div class="c248"> ... </div> or just searching for timestamp divs
    
    # We will look for elements that look like speaker blocks or timestamp blocks
    # A timestamp block has an 'id' starting with 't' and contains an 'a' with 'data-timestamp'
    
    # It seems the structure is roughly:
    # Div (Speaker) -> Div (Timestamp) -> P (Text)
    # OR
    # Div (Timestamp) -> P (Text) (continuation)
    
    # Let's iterate through all elements that might be relevanto
    
    # Find all divs with an id starting with 't' followed by digits
    timestamp_divs = soup.find_all("div", id=re.compile(r"^t\d+$"))
    
    last_speaker = None
    
    print(f"Found {len(timestamp_divs)} timestamp blocks.")
    
    for div in timestamp_divs:
        timestamp_id = div.get('id')
        seconds = int(timestamp_id[1:])
        
        # Format seconds to MM:SS
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h > 0:
            time_str = f"{h}:{m:02d}:{s:02d}"
        else:
            time_str = f"{m:02d}:{s:02d}"
            
        # The timestamp div is usually nested inside a container that *might* have the speaker name
        # <div class="..."><strong ...>Brandon</strong><div><div ... id="t5">...</div></div></div>
        
        # Check parent's previous sibling for speaker? 
        # Or check if the parent container has a 'strong' tag as a child
        
        # Let's see the structure around the timestamp div
        # The timestamp div is seemingly inside a wrapper div, which is inside a wrapper div that has the strong tag
        
        speaker = None
        
        # Go up to finding a container that has a strong tag
        parent = div.parent
        grandparent = parent.parent if parent else None
        
        if grandparent:
            strong = grandparent.find("strong")
            if strong:
                speaker = strong.get_text().strip()
                last_speaker = speaker
        
        # If no speaker found in this block, assume continued from last speaker
        current_speaker = speaker if speaker else (last_speaker if last_speaker else "Unknown")
        
        # The text/paragraphs associated with this timestamp are usually immediately following the container
        # The container is 'grandparent' in the case of speaker change, or just 'parent'/'div'?
        # Let's look at the example again:
        # <div class="..."> <strong...> ... <div><div id="t5">...</div></div> </div>
        # <p class="...">Today we are...</p>
        
        # So we need to find the specific container 'grandparent' (the flex/block container) and look for subsequent siblings that are 'p' tags or code blocks until the next timestamp block.
        
        current_node = grandparent if grandparent else div.parent
        
        # If the structure is simpler (no speaker name explicitly listed for this block, just timestamp), 
        # it might be: <div class="..."> <div><div id="t15">...</div></div> </div>
        # <p>...</p>
        
        content = []
        
        # We need to traverse following siblings until we hit a node that indicates a new section/timestamp
        if current_node:
            for sibling in current_node.next_siblings:
                if sibling.name == 'div':
                    # Check if this div contains a timestamp
                    if sibling.find("div", id=re.compile(r"^t\d+$")):
                        break # Start of next timestamp block
                    # Also check for "Unlock This Episode" or other interruptions
                    if "Unlock This Episode" in sibling.get_text():
                        break

                if sibling.name == 'p':
                    content.append(sibling.get_text().strip())
                elif sibling.name == 'pre':
                    code = sibling.get_text()
                    content.append(f"\n```\n{code}\n```\n")
                elif sibling.name == 'ul' or sibling.name == 'ol':
                     # simple list handling
                    for li in sibling.find_all('li'):
                        content.append(f"- {li.get_text().strip()}")
        
        text = "\n".join(content)
        if text.strip():
            transcript_text += f"[{time_str}] **{current_speaker}**: {text}\n\n"
            
    return transcript_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_pointfree.py <html_file>")
        sys.exit(1)
        
    html_file = sys.argv[1]
    transcript = parse_transcript(html_file)
    
    # determine output filename
    base_name = html_file.rsplit('.', 1)[0]
    out_file = base_name + "_transcript.md"
    
    with open(out_file, "w") as f:
        f.write(transcript)
    
    print(f"Transcript saved to {out_file}")
    print(transcript[:500] + "...")
