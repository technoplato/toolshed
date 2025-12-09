
"""
HOW:
  Run this migration to delete all "UNKNOWN" speakers from both InstantDB and PostgreSQL.
  
  cd apps/speaker-diarization-benchmark
  uv run python scripts/migrations/delete_unknown_speakers.py
  
  Or with dry-run to see what would be deleted:
  uv run python scripts/migrations/delete_unknown_speakers.py --dry-run

  [Inputs]
  - INSTANT_APP_ID (env): Required for InstantDB connection
  - INSTANT_ADMIN_SECRET (env): Required for InstantDB admin access
  - SPEAKER_DB_DSN (env): PostgreSQL connection string

  [Outputs]
  - Prints count of deleted records
  - Deletes UNKNOWN speakers from InstantDB
  - Deletes UNKNOWN embeddings from PostgreSQL

  [Side Effects]
  - Permanently deletes data from both databases

WHO:
  Claude AI, User
  (Context: Data cleanup migration)

WHAT:
  Migration script to remove "UNKNOWN" as a speaker entity.
  
  "UNKNOWN" is a placeholder label used by the diarization system when:
  - A segment hasn't been identified yet
  - Speaker identification failed
  - A segment was created from a split and hasn't been labeled
  
  It should NOT exist as a Speaker entity in InstantDB because:
  - It's not a real person
  - It pollutes the speaker autocomplete list
  - It can cause confusion in the UI

WHEN:
  2025-12-09

WHERE:
  apps/speaker-diarization-benchmark/scripts/migrations/delete_unknown_speakers.py

WHY:
  Clean up the database by removing placeholder "UNKNOWN" entries that
  were accidentally created as Speaker entities. This improves the
  Ground Truth UI experience by keeping the speaker list clean.
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

# Load .env from repo root
repo_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(repo_root / ".env")

import psycopg
import requests


def delete_from_postgres(pg_dsn: str, dry_run: bool = False) -> int:
    """Delete UNKNOWN embeddings from PostgreSQL."""
    print(f"\n📊 PostgreSQL: Checking for UNKNOWN embeddings...")
    
    try:
        conn = psycopg.connect(pg_dsn)
        cursor = conn.cursor()
        
        # Check count first
        cursor.execute("SELECT COUNT(*) FROM speaker_embeddings WHERE speaker_id = 'UNKNOWN'")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("   ✅ No 'UNKNOWN' embeddings found.")
            conn.close()
            return 0

        print(f"   ⚠️  Found {count} embeddings with speaker_id = 'UNKNOWN'")
        
        if dry_run:
            print(f"   🔍 DRY RUN: Would delete {count} rows")
            conn.close()
            return count
        
        # Execute DELETE
        cursor.execute("DELETE FROM speaker_embeddings WHERE speaker_id = 'UNKNOWN'")
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"   🗑️  Deleted {deleted_count} rows from PostgreSQL")
        conn.close()
        return deleted_count

    except Exception as e:
        print(f"   ❌ PostgreSQL Error: {e}")
        return 0


def delete_from_instantdb(dry_run: bool = False) -> int:
    """Delete UNKNOWN speaker entity from InstantDB via the TypeScript server."""
    print(f"\n📊 InstantDB: Checking for UNKNOWN speaker entity...")
    
    instant_server_url = os.getenv("INSTANT_SERVER_URL", "http://localhost:3001")
    
    try:
        # First, get all speakers to find UNKNOWN
        response = requests.get(f"{instant_server_url}/speakers", timeout=10)
        if response.status_code != 200:
            print(f"   ❌ Failed to fetch speakers: {response.status_code}")
            return 0
        
        data = response.json()
        speakers = data.get("speakers", [])
        
        # Find UNKNOWN speakers (case-insensitive)
        unknown_speakers = [s for s in speakers if s.get("name", "").upper() == "UNKNOWN"]
        
        if not unknown_speakers:
            print("   ✅ No 'UNKNOWN' speaker entity found.")
            return 0
        
        print(f"   ⚠️  Found {len(unknown_speakers)} UNKNOWN speaker(s)")
        
        if dry_run:
            for s in unknown_speakers:
                print(f"      - ID: {s.get('id')}, Name: {s.get('name')}")
            print(f"   🔍 DRY RUN: Would delete {len(unknown_speakers)} speaker(s)")
            return len(unknown_speakers)
        
        # Delete each UNKNOWN speaker via the DELETE endpoint
        deleted = 0
        for s in unknown_speakers:
            speaker_id = s.get("id")
            speaker_name = s.get("name")
            try:
                response = requests.delete(f"{instant_server_url}/speakers/{speaker_id}", timeout=10)
                if response.status_code == 200:
                    print(f"   🗑️  Deleted speaker: {speaker_name} ({speaker_id})")
                    deleted += 1
                else:
                    print(f"   ❌ Failed to delete {speaker_id}: {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error deleting {speaker_id}: {e}")
        
        return deleted

    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Could not connect to InstantDB server at {instant_server_url}")
        print(f"      Make sure the server is running: bun run apps/speaker-diarization-benchmark/ingestion/instant_proxy.ts")
        return 0
    except Exception as e:
        print(f"   ❌ InstantDB Error: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Delete UNKNOWN speakers from databases")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without actually deleting")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧹 Delete UNKNOWN Speakers Migration")
    print("=" * 60)
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    
    pg_dsn = os.getenv("SPEAKER_DB_DSN") or "postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings"
    
    # Delete from PostgreSQL
    pg_deleted = delete_from_postgres(pg_dsn, args.dry_run)
    
    # Delete from InstantDB
    instant_deleted = delete_from_instantdb(args.dry_run)
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Summary")
    print("=" * 60)
    print(f"   PostgreSQL: {pg_deleted} embeddings {'would be ' if args.dry_run else ''}deleted")
    print(f"   InstantDB:  {instant_deleted} speakers {'would be ' if args.dry_run else ''}deleted")
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to actually delete the records")


if __name__ == "__main__":
    main()
