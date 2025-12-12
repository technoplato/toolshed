#!/usr/bin/env python3
"""
HOW:
  uv run python scripts/one_off/inspect_run_embeddings.py --run-id <diarization_run_id>
  
  Example:
  uv run python scripts/one_off/inspect_run_embeddings.py --run-id e2418a71-6b20-4a47-9484-095284a1f63b

  [Inputs]
  - --run-id: The diarization run ID to inspect

  [Outputs]
  - Console output showing embedding summary and details

WHO:
  Claude (Code mode)
  (Context: Verifying speaker labels are correctly saved to PostgreSQL)

WHAT:
  Inspects embeddings in PostgreSQL for a specific diarization run.
  Shows summary statistics and detailed listing of all embeddings.

WHEN:
  2025-12-09
  Last Modified: 2025-12-09

WHERE:
  apps/speaker-diarization-benchmark/scripts/one_off/inspect_run_embeddings.py

WHY:
  To verify that when users label segments in the Ground Truth UI,
  the speaker_id is correctly updated in the PostgreSQL embeddings table.
"""

import argparse
import os
import sys
from collections import Counter

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.embeddings.pgvector_client import PgVectorClient


def main():
    parser = argparse.ArgumentParser(description="Inspect embeddings for a diarization run")
    parser.add_argument("--run-id", required=True, help="Diarization run ID to inspect")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all embedding details")
    args = parser.parse_args()
    
    # Connect to PostgreSQL
    client = PgVectorClient()
    
    # Query embeddings for this run
    # We need to use a raw query since get_embeddings_by_run only returns unlabeled
    with client._get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, external_id, speaker_id, diarization_run_id, created_at
                FROM speaker_embeddings
                WHERE diarization_run_id = %s
                ORDER BY created_at
            """, (args.run_id,))
            
            rows = cur.fetchall()
    
    if not rows:
        print(f"❌ No embeddings found for run {args.run_id}")
        return
    
    # Summary statistics
    print(f"\n📊 EMBEDDINGS FOR RUN: {args.run_id}")
    print(f"{'='*60}")
    print(f"Total embeddings: {len(rows)}")
    
    # Count by speaker_id
    speaker_counts = Counter(row[2] for row in rows)  # row[2] is speaker_id
    
    print(f"\n📈 BY SPEAKER:")
    for speaker_id, count in sorted(speaker_counts.items(), key=lambda x: (x[0] is None, x[0] or "")):
        label = speaker_id if speaker_id else "(unlabeled/NULL)"
        print(f"   {label}: {count}")
    
    # Labeled vs unlabeled
    labeled = sum(1 for row in rows if row[2] is not None)
    unlabeled = len(rows) - labeled
    print(f"\n📋 SUMMARY:")
    print(f"   Labeled: {labeled}")
    print(f"   Unlabeled: {unlabeled}")
    
    if args.verbose:
        print(f"\n📝 ALL EMBEDDINGS:")
        print(f"{'ID':<40} {'Segment ID':<40} {'Speaker':<20} {'Created'}")
        print("-" * 120)
        for row in rows:
            emb_id, seg_id, speaker, run_id, created = row
            speaker_display = speaker if speaker else "(NULL)"
            created_str = created.strftime("%Y-%m-%d %H:%M") if created else "N/A"
            print(f"{emb_id:<40} {seg_id:<40} {speaker_display:<20} {created_str}")
    
    print()


if __name__ == "__main__":
    main()