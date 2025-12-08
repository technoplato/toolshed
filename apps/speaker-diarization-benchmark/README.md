# Speaker Diarization Benchmark

A comprehensive system for speaker diarization, identification, and transcription benchmarking. Built for the Matt and Shane's Secret Podcast (MSSP) audio corpus.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ground_truth_instant.html     │  diarization_comparison.html               │
│  - Real-time transcript view   │  - Side-by-side ground truth vs model      │
│  - Speaker editing             │  - Speaker mapping                          │
│  - Keyboard shortcuts          │  - Time-synced playback                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                              HTTP (real-time sync)
                                      │
┌─────────────────────────────────────────────────────────────────────────────┐
│                                 DATABASES                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────┐   ┌───────────────────────────────────┐  │
│  │       InstantDB (Cloud)       │   │     PostgreSQL + pgvector        │  │
│  │                               │   │        (Docker: 5433)            │  │
│  │  • Videos, Speakers           │   │                                   │  │
│  │  • Transcription runs/words   │   │  • 512-dim speaker embeddings    │  │
│  │  • Diarization runs/segments  │   │  • IVFFlat cosine similarity     │  │
│  │  • Speaker assignments        │   │  • KNN search for identification │  │
│  │  • Real-time sync to UI       │   │                                   │  │
│  └───────────────────────────────┘   └───────────────────────────────────┘  │
│              │                                    │                          │
│              │ Admin SDK                          │ psycopg                  │
│              │                                    │                          │
│  ┌───────────────────────────────┐               │                          │
│  │  instant-server (Docker:3001) │               │                          │
│  │  TypeScript HTTP wrapper      │               │                          │
│  └───────────────────────────────┘               │                          │
│              │                                    │                          │
│              │ HTTP                               │                          │
│              └───────────────────────────────────┼──────────────────────────┤
│                                                  │                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        PYTHON SCRIPTS                                   ││
│  │                                                                         ││
│  │  identify_speakers.py    │  audio_ingestion.py   │  ingest_ground_truth ││
│  │  - KNN identification    │  - Pipeline orchestr. │  - Load labeled data ││
│  │  - Dry-run + execute     │  - Workflows          │                      ││
│  │  - Caching               │                       │                      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                      │                                       │
│                              pyannote.audio                                  │
│                                      │                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      EMBEDDING EXTRACTION                               ││
│  │  pyannote_extractor.py - Extract 512-dim voice embeddings from audio   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

## 🤔 Why This Architecture?

### Why Two Databases?

| Database | Purpose | Why Not Just One? |
|----------|---------|-------------------|
| **InstantDB** | Relational data, real-time sync | No vector type support |
| **PostgreSQL/pgvector** | Vector similarity search | No real-time sync to browser |

InstantDB provides real-time updates to the UI via WebSockets - when you change a speaker label, all connected browsers update instantly. PostgreSQL/pgvector provides O(√n) KNN search on 512-dimensional embeddings via IVFFlat indexing.

### Why a TypeScript Server for InstantDB?

```
                 ❌ BAD                              ✅ GOOD
┌─────────────────────────────────┐   ┌─────────────────────────────────┐
│  Python Script                  │   │  Python Script                  │
│         │                       │   │         │                       │
│         │ unofficial client     │   │         │ HTTP                  │
│         │ (unreliable)          │   │         ▼                       │
│         ▼                       │   │  ┌─────────────────────────┐   │
│  InstantDB                      │   │  │  instant-server (TS)    │   │
│  (frequent failures)            │   │  │  official Admin SDK     │   │
└─────────────────────────────────┘   │  └───────────┬─────────────┘   │
                                      │              │                 │
                                      │              ▼                 │
                                      │       InstantDB (reliable)     │
                                      └─────────────────────────────────┘
```

- **InstantDB's TypeScript SDK** is official, well-documented, and reliable
- **Python InstantDB clients** are unofficial, poorly maintained, and frequently break
- **HTTP** is a stable, debuggable interface between Python and TypeScript
- **Centralization** keeps all InstantDB logic in one file (`instant_server.ts`)

### Why Docker?

- **Reproducibility**: Same setup on any machine
- **Isolation**: No conflicts with local PostgreSQL
- **Easy cleanup**: `docker compose down -v` removes everything
- **Healthchecks**: Automatic service monitoring and restart

## 🚀 Quick Start

### Prerequisites

- Docker + Docker Compose
- Python 3.11+ with `uv` package manager
- Hugging Face token (for pyannote models): https://huggingface.co/settings/tokens

### 1. Environment Setup

Create/update `.env` in the **repository root** (`toolshed/.env`):

```bash
# InstantDB credentials (get from https://instantdb.com/dash)
INSTANT_APP_ID=your-app-id
INSTANT_ADMIN_SECRET=your-admin-secret

# Optional: Test instance
INSTANT_APP_ID_TEST=your-test-app-id
INSTANT_ADMIN_SECRET_TEST=your-test-admin-secret

# Hugging Face token for pyannote embedding model
HF_TOKEN=hf_your_token_here

# PostgreSQL (matches docker-compose defaults)
POSTGRES_DSN=postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings
```

### 2. Start Services

```bash
cd apps/speaker-diarization-benchmark

# Start all services (PostgreSQL + instant-server)
# IMPORTANT: Use --env-file to load credentials from repo root .env
docker compose --env-file ../../.env up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Or use the convenience script (recommended):
./start.sh
```

Expected output:
```
NAME                          STATUS                    PORTS
speaker-diarization-postgres  Up X seconds (healthy)    0.0.0.0:5433->5432/tcp
instant-server                Up X seconds (healthy)    0.0.0.0:3001->3001/tcp
```

> **Note**: The `--env-file ../../.env` flag is required because InstantDB credentials 
> are stored in the repo root `.env` file. Without this flag, the instant-server won't start.

### 3. Verify Services

```bash
# Check instant-server health
curl http://localhost:3001/health
# Expected: {"status":"ok","appId":"d4802f0a"}

# Check PostgreSQL
psql postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings -c "SELECT COUNT(*) FROM speaker_embeddings;"
# Expected: 207 (after migration)
```

### 4. Run Speaker Identification

```bash
# Dry run - preview what would happen
uv run scripts/one_off/identify_speakers.py \
  --video-id "20dbb029-5729-5072-8c6b-ef1f0a0cab0a" \
  --start-time 0 \
  --end-time 60

# Execute - save results to database
uv run scripts/one_off/identify_speakers.py \
  --video-id "20dbb029-5729-5072-8c6b-ef1f0a0cab0a" \
  --execute
```

## 📁 Project Structure

```
apps/speaker-diarization-benchmark/
├── docker-compose.yml          # PostgreSQL + instant-server
├── Dockerfile.instant-server   # TypeScript server container
├── README.md                   # This file
│
├── ingestion/
│   ├── instant_server.ts       # InstantDB HTTP wrapper (TypeScript)
│   ├── instant_client.py       # Python client for instant_server
│   └── server.py               # Legacy Python server (UI actions)
│
├── scripts/
│   ├── init-db.sql             # PostgreSQL schema + indexes
│   └── one_off/
│       ├── identify_speakers.py    # Main identification workflow
│       ├── migrate_embeddings_to_postgres.py
│       ├── ingest_ground_truth.py
│       └── ...
│
├── src/
│   ├── embeddings/
│   │   ├── pgvector_client.py      # PostgreSQL vector operations
│   │   └── pyannote_extractor.py   # Voice embedding extraction
│   └── data/
│       ├── models.py               # Pydantic models
│       └── impl/
│           └── instant_db_adapter.py
│
├── data/
│   ├── clips/                  # Audio files
│   │   ├── ground_truth_instant.html   # Main UI
│   │   └── diarization_comparison.html # Comparison UI
│   ├── cache/identify/         # Cached identification results
│   └── speaker_embeddings.json # Legacy embedding storage
│
└── tdd.identify.md             # Technical design doc
```

## 🔧 Services Reference

### PostgreSQL + pgvector (port 5433)

| Setting | Value |
|---------|-------|
| Host | `localhost` |
| Port | `5433` (not 5432 to avoid conflicts) |
| Database | `speaker_embeddings` |
| User | `diarization` |
| Password | `diarization_dev` |
| Connection String | `postgresql://diarization:diarization_dev@localhost:5433/speaker_embeddings` |

**Tables:**
- `speaker_embeddings`: 512-dim vectors with speaker labels, segment metadata

**Key Queries:**
```sql
-- Count embeddings per speaker
SELECT speaker_id, COUNT(*) FROM speaker_embeddings GROUP BY speaker_id;

-- KNN search (cosine similarity)
SELECT speaker_id, embedding <=> '[0.1, 0.2, ...]'::vector AS distance
FROM speaker_embeddings
ORDER BY distance
LIMIT 5;
```

### instant-server (port 3001)

TypeScript server wrapping InstantDB Admin SDK.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/query` | POST | Execute InstaQL query |
| `/transact` | POST | Execute transaction |
| `/videos/:id` | GET | Get video with runs/segments |
| `/diarization-segments` | GET | Get segments (with ?video_id, ?start_time, ?end_time) |
| `/speaker-assignments` | POST | Create speaker assignments (batch) |
| `/speakers` | GET | List all speakers |
| `/speakers` | POST | Get or create speaker by name |

**Example:**
```bash
# Get all speakers
curl http://localhost:3001/speakers

# Get diarization segments for a video
curl "http://localhost:3001/diarization-segments?video_id=20dbb029-..."
```

## 🎯 Common Tasks

### Run the Ground Truth UI

```bash
cd apps/speaker-diarization-benchmark

# Start the Python server (for audio serving + UI actions)
uv run python -m http.server 8000 --directory data/clips

# Open in browser
open http://localhost:8000/ground_truth_instant.html
```

### Add New Embeddings to PostgreSQL

```bash
# From speaker_embeddings.json
uv run scripts/one_off/migrate_embeddings_to_postgres.py
```

### Ingest Ground Truth Data

```bash
uv run scripts/one_off/ingest_ground_truth.py
```

### View Docker Logs

```bash
# All services
docker compose logs -f

# Just instant-server
docker compose logs -f instant-server

# Just PostgreSQL
docker compose logs -f postgres
```

### Reset Database

```bash
# Stop and remove volumes (deletes all data!)
docker compose down -v

# Start fresh
docker compose up -d
```

## 🐛 Troubleshooting

### instant-server won't start

```bash
# Check logs
./start.sh logs instant-server

# Verify .env file exists and has correct values
cat ../../.env | grep INSTANT

# Most common issue: forgot --env-file flag
# ❌ docker compose up -d
# ✅ docker compose --env-file ../../.env up -d
# ✅ ./start.sh  (recommended - handles this automatically)
```

Common issues:
- **Missing `--env-file` flag**: Use `./start.sh` or add `--env-file ../../.env`
- **Missing credentials**: Ensure `INSTANT_APP_ID` and `INSTANT_ADMIN_SECRET` are in `toolshed/.env`
- **Wrong .env location**: Must be at repo root (`toolshed/.env`), not in this directory

### PostgreSQL connection refused

```bash
# Check if postgres is running
docker compose ps

# Check if port 5433 is available
lsof -i :5433

# Restart postgres
docker compose restart postgres
```

### Python script can't connect to instant-server

```bash
# Verify server is running
curl http://localhost:3001/health

# If running locally (not in Docker), start it manually:
bun run ingestion/instant_server.ts
```

### Embedding extraction fails

```bash
# Verify HF_TOKEN is set
echo $HF_TOKEN

# First run downloads ~400MB model - check disk space
df -h
```

## 📚 Additional Documentation

- [`tdd.identify.md`](./tdd.identify.md) - Technical design for identification workflow
- [`packages/schema/instant.schema.ts`](../../packages/schema/instant.schema.ts) - InstantDB schema
- [`scripts/init-db.sql`](./scripts/init-db.sql) - PostgreSQL schema

## 📝 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `INSTANT_APP_ID` | ✅ | InstantDB application ID |
| `INSTANT_ADMIN_SECRET` | ✅ | InstantDB admin token |
| `HF_TOKEN` | For embeddings | Hugging Face token for pyannote |
| `POSTGRES_DSN` | Optional | Override PostgreSQL connection string |
| `PORT` | Optional | instant-server port (default: 3001) |
