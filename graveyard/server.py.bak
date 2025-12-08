import http.server
import socketserver
import json
import os
import re
import sys

# --- CONFIGURATION & VALIDATION ---
# This server must be run from the 'apps/speaker-diarization-benchmark' directory.
# It relies on relative paths to 'data/clips/manifest.json' and 'data/cache/'.

REQUIRED_FILE = "data/clips/manifest.json"
if not os.path.exists(REQUIRED_FILE):
    print("\n" + "!" * 80)
    print("ERROR: server.py is running in the wrong directory!")
    print("!" * 80)
    print(f"\nCurrent Directory: {os.getcwd()}")
    print(f"Missing File:      {REQUIRED_FILE}")
    print("\nCORRECT USAGE:")
    print("  You must run this script from the 'apps/speaker-diarization-benchmark' directory.")
    print("\n  Example:")
    print("    cd apps/speaker-diarization-benchmark")
    print("    python3 server.py")
    print("\n" + "!" * 80 + "\n")
    sys.exit(1)

PORT = 8000
MANIFEST_FILE = "data/clips/manifest.json"

# Minimal RangeRequestHandler to support seeking
class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        if 'Range' not in self.headers:
            self.range = None
            return super().send_head()
        
        try:
            self.range = re.search(r'bytes=(\d+)-(\d*)', self.headers['Range']).groups()
        except:
            self.range = None
            return super().send_head()
            
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            return super().send_head()
            
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404, "File not found")
            return None

        ctype = self.guess_type(path)
        try:
            fs = os.fstat(f.fileno())
            file_len = fs[6]
            
            start, end = self.range
            start = int(start)
            if end:
                end = int(end)
            else:
                end = file_len - 1
                
            if start >= file_len:
                self.send_error(416, "Requested Range Not Satisfiable")
                return None
                
            self.send_response(206)
            self.send_header("Content-type", ctype)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_len}")
            self.send_header("Content-Length", str(end - start + 1))
            self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
            self.end_headers()
            
            f.seek(start)
            return f
        except:
            f.close()
            raise

    def copyfile(self, source, outputfile):
        if not self.range:
            try:
                super().copyfile(source, outputfile)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        start, end = self.range
        start = int(start)
        if end:
            end = int(end)
        
        try:
            fs = os.fstat(source.fileno())
            file_len = fs[6]
            if not end:
                end = file_len - 1
            
            length = end - start + 1
            
            import shutil
            shutil.copyfileobj(source, outputfile, length)
        except (BrokenPipeError, ConnectionResetError):
            # Client closed connection, this is normal during streaming
            pass
        except Exception:
            # For other errors, try fallback but ignore connection errors
            try:
                super().copyfile(source, outputfile)
            except (BrokenPipeError, ConnectionResetError):
                pass

class Handler(RangeRequestHandler):
    def do_POST(self):
        if self.path == '/enroll':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data)
                clip_id = payload.get('clip_id')
                mapping = payload.get('mapping') # {"SPEAKER_00": "Ilya"}
                
                print(f"Enrolling speakers for {clip_id}: {mapping}")
                
                # Load cache
                cache_path = f"data/cache/embeddings/{clip_id}.json"
                if not os.path.exists(cache_path):
                    raise FileNotFoundError(f"Cache not found: {cache_path}")
                    
                with open(cache_path) as f:
                    cache = json.load(f)
                
                # Load DB
                db_path = "speaker_embeddings.json"
                if os.path.exists(db_path):
                    with open(db_path) as f:
                        db = json.load(f)
                else:
                    db = {}
                
                # Update DB
                for spk_label, real_name in mapping.items():
                    if spk_label in cache:
                        if real_name not in db:
                            db[real_name] = []
                        # Avoid duplicates? Ideally yes, but for now just append.
                        # We might want to limit history size.
                        db[real_name].append(cache[spk_label])
                        print(f"  Added embedding for {real_name}")
                
                with open(db_path, 'w') as f:
                    json.dump(db, f)
                    
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Enrolled successfully")
            except Exception as e:
                print(f"Error enrolling: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                print(f"Saving manifest with {len(data)} entries...")
                with open(MANIFEST_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Saved successfully")
            except Exception as e:
                print(f"Error saving: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        elif self.path == '/correct_segment':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data)
                clip_id = payload.get('clip_id')
                segment_index = payload.get('segment_index') # Integer index in mlx_whisper_turbo_seg_level
                new_label = payload.get('new_label') # e.g. "Shane Gillis"
                
                print(f"Correcting segment {segment_index} in {clip_id} to {new_label}")
                
                # 1. Update Manifest
                with open(MANIFEST_FILE, 'r') as f:
                    manifest = json.load(f)
                
                clip_entry = next((c for c in manifest if c['id'] == clip_id), None)
                if not clip_entry:
                    raise ValueError(f"Clip {clip_id} not found")
                    
                segments = clip_entry['transcriptions'].get('mlx_whisper_turbo_seg_level', [])
                if segment_index < 0 or segment_index >= len(segments):
                    raise ValueError(f"Invalid segment index {segment_index}")
                    
                old_label = segments[segment_index].get('speaker')
                segments[segment_index]['speaker'] = new_label
                
                with open(MANIFEST_FILE, 'w') as f:
                    json.dump(manifest, f, indent=2)
                    
                # 2. Active Learning: Add embedding to speaker_embeddings.json
                # Load cache
                cache_path = f"data/cache/embeddings/{clip_id}.json"
                if os.path.exists(cache_path):
                    with open(cache_path) as f:
                        cache = json.load(f)
                    
                    # Cache keys are strings of indices
                    seg_key = str(segment_index)
                    if seg_key in cache:
                        embedding = cache[seg_key]
                        
                        # Load DB
                        db_path = "speaker_embeddings.json"
                        if os.path.exists(db_path):
                            with open(db_path) as f:
                                db = json.load(f)
                        else:
                            db = {}
                            
                        # Remove from old label if exists
                        if old_label and old_label in db:
                            try:
                                # Embeddings are lists of floats, so we can try to remove by value
                                # This removes the first occurrence of this exact embedding list
                                db[old_label].remove(embedding)
                                print(f"  Removed embedding from {old_label}")
                                # If list is empty, maybe remove the key? Optional.
                                if not db[old_label]:
                                    del db[old_label]
                            except ValueError:
                                print(f"  Warning: Embedding not found in {old_label} to remove")

                        if new_label not in db:
                            db[new_label] = []
                            
                        db[new_label].append(embedding)
                        
                        with open(db_path, 'w') as f:
                            json.dump(db, f)
                        print(f"  Added embedding to {new_label}")
                    else:
                        print(f"  Warning: No embedding found in cache for segment {segment_index}")
                else:
                    print(f"  Warning: No cache file found at {cache_path}")

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Correction applied")
            except Exception as e:
                print(f"Error correcting: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        elif self.path == '/split_segment':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data)
                clip_id = payload.get('clip_id')
                segment_index = payload.get('segment_index')
                lines = payload.get('lines') # List of strings
                model_name = payload.get('model_name')
                
                print(f"Splitting segment {segment_index} in {clip_id} into {len(lines)} parts")
                
                # 1. Load Manifest
                with open(MANIFEST_FILE, 'r') as f:
                    manifest = json.load(f)
                
                clip_entry = next((c for c in manifest if c['id'] == clip_id), None)
                if not clip_entry:
                    raise ValueError(f"Clip {clip_id} not found")
                    
                segments = clip_entry['transcriptions'].get(model_name, [])
                if segment_index < 0 or segment_index >= len(segments):
                    raise ValueError(f"Invalid segment index {segment_index}")
                
                original_segment = segments[segment_index]
                start_time = original_segment['start']
                end_time = original_segment['end']
                
                # 2. Load Word-Level Transcription
                # Try to find the cache file. clip_id usually has extension, cache file might not.
                base_id = os.path.splitext(clip_id)[0]
                cache_path = f"data/cache/transcriptions/{base_id}.json"
                
                words = []
                if os.path.exists(cache_path):
                    with open(cache_path) as f:
                        cache_data = json.load(f)
                        # Flatten segments to words
                        for seg in cache_data.get('segments', []):
                            for w in seg.get('words', []):
                                if w['start'] >= start_time - 0.1 and w['end'] <= end_time + 0.1:
                                    words.append(w)
                else:
                    print(f"Warning: Word-level cache not found at {cache_path}. Falling back to proportional split.")
                
                # 3. Align Lines to Words
                new_segments = []
                current_word_idx = 0
                current_seg_start = start_time
                
                if words:
                    for i, line in enumerate(lines):
                        # Simple character count alignment
                        target_chars = len(line.replace(" ", ""))
                        accumulated_chars = 0
                        matched_words = []
                        
                        # If it's the last line, take all remaining words
                        if i == len(lines) - 1:
                            matched_words = words[current_word_idx:]
                            seg_end = end_time # Force end to match original
                        else:
                            while current_word_idx < len(words):
                                w = words[current_word_idx]
                                w_chars = len(w['word'].replace(" ", ""))
                                
                                # Heuristic: if adding this word makes us exceed target significantly, stop?
                                # Or just greedy: add until we meet or exceed?
                                # Let's try to get closest.
                                if accumulated_chars + w_chars > target_chars + 5: # Tolerance
                                    break
                                
                                matched_words.append(w)
                                accumulated_chars += w_chars
                                current_word_idx += 1
                                
                                if accumulated_chars >= target_chars - 2: # Close enough
                                    break
                            
                            if matched_words:
                                seg_end = matched_words[-1]['end']
                            else:
                                # Fallback if no words matched (e.g. silence or mismatch)
                                seg_end = current_seg_start + (end_time - current_seg_start) / (len(lines) - i)
                        
                        # Ensure continuity
                        if i > 0:
                            current_seg_start = new_segments[-1]['end']
                        
                        new_segments.append({
                            "start": current_seg_start,
                            "end": seg_end,
                            "text": line,
                            "speaker": "UNKNOWN" # All new segments are UNKNOWN
                        })
                else:
                    # Fallback: Proportional Split
                    total_chars = sum(len(l) for l in lines)
                    total_duration = end_time - start_time
                    current_start = start_time
                    
                    for i, line in enumerate(lines):
                        proportion = len(line) / total_chars if total_chars > 0 else 1/len(lines)
                        duration = total_duration * proportion
                        seg_end = current_start + duration
                        
                        new_segments.append({
                            "start": current_start,
                            "end": seg_end,
                            "text": line,
                            "speaker": "UNKNOWN"
                        })
                        current_start = seg_end

                # 4. Update Manifest
                # Python list replacement
                segments[segment_index:segment_index+1] = new_segments
                
                with open(MANIFEST_FILE, 'w') as f:
                    json.dump(manifest, f, indent=2)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"segments": new_segments}).encode())

            except Exception as e:
                print(f"Error splitting: {e}")
                import traceback
                traceback.print_exc()
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        else:
            self.send_error(404)

print(f"Starting server at http://localhost:{PORT}")
# Allow address reuse to avoid "Address already in use" errors during restarts
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
