"""
Generate HTML verification page for speaker diarization results.

This script creates an interactive web page that allows users to:
1. Review diarized segments with audio playback
2. Verify and correct speaker assignments
3. Use autocomplete to assign speakers from a database
4. Save updated speaker assignments
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Segment:
    """Represents a diarized segment."""
    start: float
    end: float
    speaker_id: str
    word: Optional[str] = None
    confidence: Optional[float] = None
    assigned_speaker: Optional[str] = None  # User-assigned speaker name


def load_results(results_path: str) -> Dict:
    """Load benchmark results from JSON file."""
    with open(results_path, 'r') as f:
        return json.load(f)


def load_speaker_database(db_path: Optional[str] = None) -> List[str]:
    """Load speaker database (list of known speaker names)."""
    if db_path and Path(db_path).exists():
        with open(db_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'speakers' in data:
                return data['speakers']
            elif isinstance(data, dict):
                # Extract unique speaker names from dict
                return list(set(data.values()))
    return []


def create_verification_page(
    results_path: str,
    audio_path: str,
    output_path: str,
    speaker_db_path: Optional[str] = None,
    solution_name: Optional[str] = None,
) -> str:
    """Generate HTML verification page."""
    
    # Load data
    results_data = load_results(results_path)
    speaker_database = load_speaker_database(speaker_db_path)
    
    # Select solution (use first if not specified)
    if solution_name:
        solution_results = next(
            (r for r in results_data['results'] if r['solution'] == solution_name),
            None
        )
    else:
        solution_results = results_data['results'][0] if results_data['results'] else None
    
    if not solution_results:
        raise ValueError("No results found for the specified solution")
    
    words = solution_results.get('words', [])
    audio_file = Path(audio_path).name
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speaker Verification - {Path(results_path).stem}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 28px;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        
        .controls {{
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .control-group {{
            display: flex;
            flex-direction: column;
            gap: 5px;
        }}
        
        label {{
            font-size: 12px;
            font-weight: 600;
            color: #555;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        input, select, button {{
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        input:focus, select:focus {{
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }}
        
        button {{
            background: #3498db;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }}
        
        button:hover {{
            background: #2980b9;
        }}
        
        button:disabled {{
            background: #bdc3c7;
            cursor: not-allowed;
        }}
        
        .save-btn {{
            background: #27ae60;
        }}
        
        .save-btn:hover {{
            background: #229954;
        }}
        
        .segments {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}
        
        .segment {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #3498db;
            transition: all 0.2s;
        }}
        
        .segment:hover {{
            background: #e9ecef;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .segment.verified {{
            border-left-color: #27ae60;
            background: #d4edda;
        }}
        
        .segment-time {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #7f8c8d;
            min-width: 120px;
        }}
        
        .segment-word {{
            flex: 1;
            font-size: 15px;
            color: #2c3e50;
        }}
        
        .segment-speaker {{
            display: flex;
            align-items: center;
            gap: 10px;
            min-width: 200px;
        }}
        
        .speaker-id {{
            font-size: 12px;
            color: #7f8c8d;
            background: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        
        .autocomplete-wrapper {{
            position: relative;
            flex: 1;
        }}
        
        .autocomplete-input {{
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .autocomplete-dropdown {{
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 4px 4px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .autocomplete-dropdown.show {{
            display: block;
        }}
        
        .autocomplete-item {{
            padding: 10px 12px;
            cursor: pointer;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        .autocomplete-item:hover {{
            background: #f8f9fa;
        }}
        
        .autocomplete-item:last-child {{
            border-bottom: none;
        }}
        
        .play-btn {{
            background: #9b59b6;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: background 0.2s;
        }}
        
        .play-btn:hover {{
            background: #8e44ad;
        }}
        
        .play-btn.playing {{
            background: #e74c3c;
        }}
        
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding: 15px;
            background: #e8f4f8;
            border-radius: 6px;
        }}
        
        .stat {{
            display: flex;
            flex-direction: column;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #2c3e50;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
        
        .audio-player {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Speaker Verification</h1>
        <div class="subtitle">
            Audio: <strong>{audio_file}</strong> | 
            Solution: <strong>{solution_results['solution']}</strong> | 
            Segments: <strong>{len(words)}</strong>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value" id="total-segments">{len(words)}</div>
                <div class="stat-label">Total Segments</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="verified-segments">0</div>
                <div class="stat-label">Verified</div>
            </div>
            <div class="stat">
                <div class="stat-value" id="unique-speakers">0</div>
                <div class="stat-label">Unique Speakers</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label>Audio File</label>
                <input type="file" id="audio-file" accept="audio/*">
            </div>
            <div class="control-group">
                <label>Filter</label>
                <select id="filter-speaker">
                    <option value="">All Speakers</option>
                </select>
            </div>
            <button class="save-btn" onclick="saveResults()">💾 Save Changes</button>
            <button onclick="exportCSV()">📥 Export CSV</button>
        </div>
        
        <div class="segments" id="segments-container">
            {generate_segments_html(words, audio_file)}
        </div>
    </div>
    
    <audio id="audio-player" class="audio-player" preload="none"></audio>
    
    <script>
        // Data
        const segments = {json.dumps(words, indent=8)};
        const speakerDatabase = {json.dumps(speaker_database)};
        const audioFile = {json.dumps(audio_file)};
        const audioPath = {json.dumps(str(Path(audio_path).absolute()))};
        let currentAudio = null;
        let playingSegment = null;
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            initializeAutocomplete();
            updateStats();
            populateFilter();
        }});
        
        // Autocomplete functionality
        function initializeAutocomplete() {{
            document.querySelectorAll('.autocomplete-input').forEach(input => {{
                const dropdown = input.nextElementSibling;
                
                input.addEventListener('input', function() {{
                    const value = this.value.toLowerCase();
                    const segment = this.closest('.segment');
                    
                    if (value.length === 0) {{
                        dropdown.classList.remove('show');
                        return;
                    }}
                    
                    const matches = speakerDatabase.filter(speaker =>
                        speaker.toLowerCase().includes(value)
                    );
                    
                    if (matches.length > 0) {{
                        dropdown.innerHTML = matches.map(speaker => `
                            <div class="autocomplete-item" onclick="selectSpeaker(this, '${{speaker}}')">${{speaker}}</div>
                        `).join('');
                        dropdown.classList.add('show');
                    }} else {{
                        dropdown.classList.remove('show');
                    }}
                }});
                
                input.addEventListener('blur', function() {{
                    setTimeout(() => {{
                        dropdown.classList.remove('show');
                    }}, 200);
                }});
                
                input.addEventListener('keydown', function(e) {{
                    if (e.key === 'Enter') {{
                        const firstItem = dropdown.querySelector('.autocomplete-item');
                        if (firstItem) {{
                            firstItem.click();
                        }}
                    }}
                }});
            }});
        }}
        
        function selectSpeaker(element, speaker) {{
            const input = element.closest('.autocomplete-wrapper').querySelector('.autocomplete-input');
            input.value = speaker;
            
            // Mark segment as verified
            const segment = input.closest('.segment');
            segment.classList.add('verified');
            
            // Update segment data
            const index = parseInt(segment.dataset.index);
            if (segments[index]) {{
                segments[index].assigned_speaker = speaker;
            }}
            
            // Trigger change event
            input.dispatchEvent(new Event('change'));
            element.closest('.autocomplete-dropdown').classList.remove('show');
            
            updateStats();
        }}
        
        // Audio playback
        function playSegment(index, start, end) {{
            const audio = document.getElementById('audio-player');
            const playBtn = event.target;
            
            // Stop current playback
            if (playingSegment !== null && playingSegment !== index) {{
                const prevBtn = document.querySelector(`[data-segment-index="${{playingSegment}}"]`);
                if (prevBtn) {{
                    prevBtn.classList.remove('playing');
                    prevBtn.textContent = '▶ Play';
                }}
            }}
            
            // Toggle playback
            if (playingSegment === index && !audio.paused) {{
                audio.pause();
                playBtn.classList.remove('playing');
                playBtn.textContent = '▶ Play';
                playingSegment = null;
                return;
            }}
            
            // Set audio source
            const audioFileInput = document.getElementById('audio-file');
            let audioSrc = audioPath;
            
            // Try file input first, then fall back to original path
            if (audioFileInput && audioFileInput.files.length > 0) {{
                audioSrc = URL.createObjectURL(audioFileInput.files[0]);
            }} else {{
                // Use file:// protocol for local paths
                if (!audioSrc.startsWith('http') && !audioSrc.startsWith('file://')) {{
                    audioSrc = 'file://' + audioSrc;
                }}
            }}
            
            audio.src = audioSrc;
            audio.currentTime = start;
            
            // Play
            audio.play().then(() => {{
                playBtn.classList.add('playing');
                playBtn.textContent = '⏸ Stop';
                playingSegment = index;
                
                // Stop at end time
                const checkTime = setInterval(() => {{
                    if (audio.currentTime >= end || audio.paused) {{
                        audio.pause();
                        playBtn.classList.remove('playing');
                        playBtn.textContent = '▶ Play';
                        playingSegment = null;
                        clearInterval(checkTime);
                    }}
                }}, 100);
            }}).catch(err => {{
                console.error('Playback error:', err);
                alert('Error playing audio. Please select an audio file using the file input.');
            }});
        }}
        
        // Stats
        function updateStats() {{
            const verified = segments.filter(s => s.assigned_speaker).length;
            const uniqueSpeakers = new Set(segments.filter(s => s.assigned_speaker).map(s => s.assigned_speaker));
            
            document.getElementById('verified-segments').textContent = verified;
            document.getElementById('unique-speakers').textContent = uniqueSpeakers.size;
        }}
        
        // Filter
        function populateFilter() {{
            const filter = document.getElementById('filter-speaker');
            const speakers = new Set(segments.map(s => s.speaker_id));
            
            speakers.forEach(speaker => {{
                const option = document.createElement('option');
                option.value = speaker;
                option.textContent = speaker;
                filter.appendChild(option);
            }});
            
            filter.addEventListener('change', function() {{
                const value = this.value;
                document.querySelectorAll('.segment').forEach(segment => {{
                    const speakerId = segment.querySelector('.speaker-id').textContent;
                    if (!value || speakerId === value) {{
                        segment.style.display = 'flex';
                    }} else {{
                        segment.style.display = 'none';
                    }}
                }});
            }});
        }}
        
        // Save results
        function saveResults() {{
            const data = {{
                segments: segments,
                metadata: {{
                    audio_file: audioFile,
                    solution: '{solution_results['solution']}',
                    updated_at: new Date().toISOString()
                }}
            }};
            
            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{Path(results_path).stem}_verified.json';
            a.click();
            URL.revokeObjectURL(url);
            
            alert('Results saved!');
        }}
        
        // Export CSV
        function exportCSV() {{
            const headers = ['start', 'end', 'word', 'speaker_id', 'assigned_speaker', 'confidence'];
            const rows = segments.map(s => [
                s.start,
                s.end,
                s.word || '',
                s.speaker_id,
                s.assigned_speaker || '',
                s.confidence || ''
            ]);
            
            const csv = [
                headers.join(','),
                ...rows.map(r => r.map(v => `"${{v}}"`).join(','))
            ].join('\\n');
            
            const blob = new Blob([csv], {{type: 'text/csv'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = '{Path(results_path).stem}_verified.csv';
            a.click();
            URL.revokeObjectURL(url);
        }}
    </script>
</body>
</html>
"""
    
    return html


def generate_segments_html(words: List[Dict], audio_file: str) -> str:
    """Generate HTML for segments."""
    segments_html = []
    
    for i, word in enumerate(words):
        start = word.get('start', 0)
        end = word.get('end', 0)
        speaker_id = word.get('speaker_id', 'UNKNOWN')
        word_text = word.get('word', '')
        confidence = word.get('confidence', None)
        
        # Format time (MM:SS.mm)
        start_min = int(start // 60)
        start_sec = int(start % 60)
        start_ms = int((start % 1) * 100)
        start_str = f"{start_min}:{start_sec:02d}.{start_ms:02d}"
        
        end_min = int(end // 60)
        end_sec = int(end % 60)
        end_ms = int((end % 1) * 100)
        end_str = f"{end_min}:{end_sec:02d}.{end_ms:02d}"
        
        assigned_speaker = word.get('assigned_speaker', '')
        verified_class = 'verified' if assigned_speaker else ''
        
        segments_html.append(f"""
            <div class="segment {verified_class}" data-index="{i}">
                <div class="segment-time">
                    {start_str} - {end_str}
                </div>
                <div class="segment-word">
                    {word_text}
                </div>
                <div class="segment-speaker">
                    <span class="speaker-id">{speaker_id}</span>
                    <div class="autocomplete-wrapper">
                        <input 
                            type="text" 
                            class="autocomplete-input" 
                            placeholder="Assign speaker..."
                            value="{assigned_speaker}"
                            onchange="segments[{i}].assigned_speaker = this.value; this.closest('.segment').classList.toggle('verified', this.value.length > 0); updateStats();"
                        >
                        <div class="autocomplete-dropdown"></div>
                    </div>
                </div>
                <button 
                    class="play-btn" 
                    onclick="playSegment({i}, {start}, {end})"
                    data-segment-index="{i}"
                >
                    ▶ Play
                </button>
            </div>
        """)
    
    return ''.join(segments_html)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate HTML verification page for speaker diarization results"
    )
    parser.add_argument(
        "results_path",
        type=str,
        help="Path to benchmark results JSON file",
    )
    parser.add_argument(
        "audio_path",
        type=str,
        help="Path to audio file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output HTML file path (default: <results_path>_verification.html)",
    )
    parser.add_argument(
        "--speaker-db",
        type=str,
        default=None,
        help="Path to speaker database JSON file",
    )
    parser.add_argument(
        "--solution",
        type=str,
        default=None,
        help="Solution name to use (default: first solution in results)",
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        results_stem = Path(args.results_path).stem
        output_path = str(Path(args.results_path).parent / f"{results_stem}_verification.html")
    
    # Generate HTML
    logger.info(f"Generating verification page...")
    logger.info(f"Results: {args.results_path}")
    logger.info(f"Audio: {args.audio_path}")
    logger.info(f"Output: {output_path}")
    
    html = create_verification_page(
        results_path=args.results_path,
        audio_path=args.audio_path,
        output_path=output_path,
        speaker_db_path=args.speaker_db,
        solution_name=args.solution,
    )
    
    # Save HTML
    with open(output_path, 'w') as f:
        f.write(html)
    
    logger.info(f"✓ Verification page generated: {output_path}")
    logger.info(f"Open {output_path} in your browser to verify speakers")


if __name__ == "__main__":
    main()
