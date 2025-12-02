# Toolshed Project Knowledge Base

> **Last Updated**: 2025-11-28

## User Preferences
- **Communication Style**: Always answer with a parrot emoji 🦜.

## Project Overview

**Toolshed** is a monorepo containing a video transcription system with three main applications:
- **Web App**: Frontend interface for submitting video URLs
- **Job Runner**: Node.js backend service that orchestrates transcription jobs
- **Transcriber**: Python service that downloads videos and performs transcription using Whisper

## Architecture

### System Flow
1. User submits video URL via Web App
2. Web App creates a `job` entity in InstantDB (type: "video_download")
3. Job Runner polls InstantDB for new jobs
4. Job Runner triggers Transcriber API via HTTP
5. Transcriber downloads video using `yt-dlp` and transcribes with `whisper.cpp`
6. Job status and logs are updated in InstantDB throughout the process

### Technology Stack

#### Frontend (Web App)
- **Location**: `apps/web/`
- **Tech**: HTML, CSS, JavaScript
- **Database**: InstantDB (real-time database)
- **Purpose**: User interface for video submission and job monitoring

#### Backend (Job Runner)
- **Location**: `apps/job-runner/`
- **Tech**: Node.js, TypeScript
- **Database**: InstantDB via `@instantdb/admin`
- **Purpose**: Job orchestration and status management
- **Pattern**: Polling mechanism for new jobs

#### Transcription Service (Transcriber)
- **Location**: `apps/transcriber/`
- **Tech**: Python, FastAPI, `yt-dlp`, `whisper.cpp`
- **Database**: SQLite (for video metadata)
- **Purpose**: Video download and transcription
- **Key Features**:
  - Supports any video URL via `yt-dlp`
  - Generates interactive HTML players with synced transcripts
  - Stores downloads in `downloads/` and transcriptions in `transcriptions/`
  - Uses naming convention: `<platform>_<ID>_`

### Shared Schema
- **Location**: `packages/schema/instant.schema.ts`
- **Database**: InstantDB
- **Key Entities**:
  - `job`: Tracks transcription jobs (status, progress, type)
  - `log`: Stores job execution logs
  - `video`: Stores video metadata and file paths

## Deployment Infrastructure

### VPS Setup (Hetzner)
- **IP**: `5.161.84.236`
- **Location**: Ashburn, VA
- **Specs**: CPX11 (2GB RAM, Shared vCPU)
- **OS**: Ubuntu 24.04
- **Orchestration**: Docker Swarm
- **Reverse Proxy**: Traefik v2.11

### Docker Stack
- **Location**: `vps_deployer/`
- **Services**:
  - Traefik (reverse proxy with Basic Auth)
  - FastAPI (transcriber service)
  - Future: Web app and job-runner services

### Authentication
- **Traefik Dashboard**: Basic Auth (credentials in `.env`)
- **FastAPI API**: API Key via `X-API-Key` header
- **Access**: `http://5.161.84.236/fastapi/`

## Key Challenges & Solutions

### YouTube Bot Detection
- **Problem**: `yt-dlp` encounters "Sign in to confirm you're not a bot" errors
- **Solution**: Using `cookies.txt` file with authenticated YouTube session
- **Status**: Ongoing debugging to ensure cookies are applied during both metadata extraction and audio download

### Video Conflict Handling
- **Problem**: `external_id` conflicts when processing same video multiple times
- **Solution**: Delete existing placeholder video records before creating new ones
- **Implementation**: Modified `apps/transcriber/universal_transcriber/transcribe.py`

### Deployment Consistency
- **Problem**: Code changes not reflected in running Docker Swarm service
- **Root Cause**: Docker caching image tags
- **Solution**: Use unique Git commit SHAs for image versioning in CI/CD

### Hot-Patching for Debugging
- **Approach**: Temporarily disable Basic Auth and patch running containers
- **Purpose**: Accelerate debugging cycle without full redeployment

## Development Workflows

### Local Development
```bash
# Install dependencies
npm install

# Run transcriber locally
cd apps/transcriber
uv sync
uv run python api.py

# Run job runner locally
cd apps/job-runner
npm install
npm run dev
```

### Deployment
```bash
cd vps_deployer

# Generate Basic Auth credentials
./generate_auth.sh

# Deploy to VPS
./deploy.sh

# Verify deployment
python verify_deployment.py
```

### Debugging
```bash
# Check service logs
docker service logs toolshed_transcriber -f

# SSH into VPS
ssh root@5.161.84.236

# Switch Docker context to VPS
docker context use vps-01
```

## File Organization

### Transcriber Output Structure
```
downloads/
  youtube_<VIDEO_ID>_<TITLE>.mp3
  
transcriptions/
  youtube_<VIDEO_ID>_<TITLE>.md
  youtube_<VIDEO_ID>_<TITLE>.html
  youtube_<VIDEO_ID>_<TITLE>.json
```

### Environment Files
- `apps/job-runner/.env`: InstantDB credentials
- `vps_deployer/.env`: Traefik Basic Auth hash, API keys
- `apps/transcriber/.env`: API keys, database paths

## Important Notes

### Security
- ⚠️ Never commit `.env` files to git
- ⚠️ API keys and credentials stored in `.env` files
- ✅ `.gitignore` configured to exclude sensitive files
- ✅ Basic Auth protects Traefik dashboard
- ✅ API Key auth protects FastAPI endpoints

### Database Schema
- InstantDB schema defined in `packages/schema/instant.schema.ts`
- SQLite database for video metadata in transcriber
- Schema dump available in `schema_dump.json`

### CI/CD Pipeline
- **Platform**: GitHub Actions
- **Trigger**: Push to main branch
- **Process**: Build Docker image → Tag with commit SHA → Deploy to VPS
- **Status**: Configured and operational

## Recent Progress (as of Nov 27, 2025)

✅ VPS provisioned and configured  
✅ Docker Swarm + Traefik deployed  
✅ FastAPI transcriber service deployed  
✅ API Key authentication implemented  
✅ Job Runner logic implemented  
✅ Web app interface created  
🔄 Debugging YouTube bot detection with cookies  
🔄 Testing end-to-end job flow  

## Quick Reference

### Key URLs
- Traefik Dashboard: `http://5.161.84.236/dashboard/`
- FastAPI Service: `http://5.161.84.236/fastapi/`
- Web App: (To be deployed)

### Key Commands
```bash
# View job runner logs
cd apps/job-runner && npm run dev

# Test transcriber API
curl -X POST http://5.161.84.236/fastapi/transcribe \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "VIDEO_URL", "uuid": "JOB_UUID"}'

# Check Docker service status
docker service ls
docker service ps toolshed_transcriber
```

### Useful File Paths
- Job Runner: `apps/job-runner/src/probe_admin.ts`
- Transcriber API: `apps/transcriber/api.py`
- Transcription Logic: `apps/transcriber/universal_transcriber/transcribe.py`
- Web Interface: `apps/web/index.html`
- InstantDB Schema: `packages/schema/instant.schema.ts`

## Dependencies

### Node.js Packages
- `@instantdb/core`: Real-time database client
- `@instantdb/admin`: Server-side InstantDB client

### Python Packages (via `uv`)
- `fastapi`: Web framework
- `yt-dlp`: Video download
- `whisper.cpp`: Audio transcription
- `sqlite3`: Database

### System Dependencies
- Docker & Docker Swarm
- Traefik v2.11
- Node.js
- Python 3.x
- `uv` (Python package manager)
