# One-off Scripts

This directory contains scripts that are intended for one-time use or specific maintenance tasks. They are not part of the core application logic but are essential for data migration, analysis, or debugging.

## Scripts

### `migrate_clip.py`
**Who**: Antigravity, User
**What**: Migrates clip data from the legacy `manifest.json` file to InstantDB.
**When**: 2025-12-06
**Where**: `apps/speaker-diarization-benchmark/scripts/one_off/migrate_clip.py`
**Why**: To transition the Ground Truth UI and data storage from a local JSON file to a persistent InstantDB backend.
**How**:
```bash
# Run from repository root
source apps/speaker-diarization-benchmark/.venv/bin/activate
python3 apps/speaker-diarization-benchmark/scripts/one_off/migrate_clip.py
```
**Inputs**:
- `apps/speaker-diarization-benchmark/data/clips/manifest.json`: Source data.
- env vars `INSTANT_APP_ID`, `INSTANT_ADMIN_SECRET`: Destination DB credentials.

### `analyze_embeddings.py`
*Pending implementation*
**Who**: Antigravity
**What**: Verifies `PgVectorClient` functionality and migrates/analyzes embeddings.
**Why**: To ensure vector storage is working correctly before enabling active learning features.
