import http.server
import socketserver
import json
import os
import re

PORT = 8000
MANIFEST_FILE = "manifest.json"

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
            super().copyfile(source, outputfile)
            return

        start, end = self.range
        start = int(start)
        if end:
            end = int(end)
        else:
            # We don't know the end if we didn't calculate it in send_head, 
            # but send_head calculates it.
            # However, send_head returns the file object positioned at start.
            # We just need to read the correct amount.
            # But wait, send_head logic above sets 'end' correctly if missing.
            # But self.range is the raw parsed groups.
            # We need to re-calculate length to know how much to copy.
            # Let's just read until EOF if end is missing? 
            # No, Content-Length was set.
            pass
            
        # Re-calculate length to copy
        # We need the file size again? Or just trust Content-Length?
        # copyfile doesn't know Content-Length sent.
        # But source is already seeked.
        
        # Simpler: just read/write in chunks until limit
        # But we need to know the limit.
        # Let's assume send_head did the seek.
        
        # Actually, let's look at how we can get the length.
        # We can stat the source file again.
        try:
            fs = os.fstat(source.fileno())
            file_len = fs[6]
            if not end:
                end = file_len - 1
            else:
                end = int(end)
            
            length = end - start + 1
            
            # Copy 'length' bytes
            import shutil
            shutil.copyfileobj(source, outputfile, length)
        except:
            super().copyfile(source, outputfile)

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
                cache_path = f"../cache/embeddings/{clip_id}.json"
                if not os.path.exists(cache_path):
                    raise FileNotFoundError(f"Cache not found: {cache_path}")
                    
                with open(cache_path) as f:
                    cache = json.load(f)
                
                # Load DB
                db_path = "../speaker_embeddings.json"
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
                cache_path = f"../cache/embeddings/{clip_id}.json"
                if os.path.exists(cache_path):
                    with open(cache_path) as f:
                        cache = json.load(f)
                    
                    # Cache keys are strings of indices
                    seg_key = str(segment_index)
                    if seg_key in cache:
                        embedding = cache[seg_key]
                        
                        # Load DB
                        db_path = "../speaker_embeddings.json"
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
        else:
            self.send_error(404)

print(f"Starting server at http://localhost:{PORT}")
# Allow address reuse to avoid "Address already in use" errors during restarts
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
