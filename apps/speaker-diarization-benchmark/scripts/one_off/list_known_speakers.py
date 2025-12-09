
import sys
import os
from pathlib import Path
# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from src.embeddings.pgvector_client import PgVectorClient

def main():
    pg_dsn = os.getenv("SPEAKER_DB_DSN") or "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
    
    try:
        print(f"🔌 Connecting to Postgres...")
        client = PgVectorClient(pg_dsn)
        
        print("\n📢 Known Speakers in Database:")
        print(f"{'Speaker ID':<20} | {'Count':<6}")
        print("-" * 30)
        
        speakers = client.list_speakers() # Returns list of (speaker_id, count)
        
        total_embeddings = 0
        for speaker_id, count in speakers:
            print(f"{speaker_id:<20} | {count:<6}")
            total_embeddings += count
            
        print("-" * 30)
        print(f"Total Embeddings: {total_embeddings}")
        print(f"Total Speakers:   {len(speakers)}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
