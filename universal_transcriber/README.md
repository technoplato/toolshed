## Universal Transcriber

The Universal Transcriber is a small web service for generating, storing, and playing back transcripts for YouTube (and potentially other) videos. It includes a backend for managing transcriptions, a simple web player UI, and deployment tooling for running the service on a VPS.

### Current State

- **Core transcription flow**: Transcripts can be generated and saved locally (HTML and JSON files, plus a SQLite database).
- **Web player**: A basic player page can load a transcript by ID and display it in the browser.
- **Deployment**: A deployment pipeline exists and is verified via homepage title changes.
- **Observability**: Logging has been improved recently (moving from `print` statements to a logger and adding debug logs around cookie handling).

### Desired End State

- **Centralized realtime storage**: All transcriptions are stored in InstantDB for realtime access and synchronization across clients.
- **Richer admin tooling**: An admin dashboard for viewing, searching, and managing transcriptions and their metadata.
- **Robust deployment pipeline**: Fully automated, observable deployments with clear health checks and rollbacks.
- **Multi-platform support**: Support for additional platforms beyond YouTube (e.g., locally uploaded files or other video platforms).
- **Clear documentation**: Up-to-date docs for setup, deployment, and day-to-day operations.

### High-Level Tasks / Roadmap

- **InstantDB integration**
  - Design a schema in InstantDB for transcripts, segments, and metadata.
  - Implement a sync job or service to push existing SQLite/HTML/JSON transcriptions into InstantDB.
  - Update the web player and backend to read/write from InstantDB instead of (or in addition to) local storage.

- **Admin & operations**
  - Create an authenticated admin UI for listing, searching, and inspecting transcriptions.
  - Document key operational URLs and credentials setup (see `admin.md` at the repo root).

- **Developer experience & testing**
  - Add end-to-end tests covering the full transcription -> storage -> playback flow.
  - Flesh out unit/integration tests for the transcription pipeline and search behavior.

- **Platform and feature expansion**
  - Abstract platform-specific logic so the system can support new video sources.
  - Add features like bookmarking, sharing, and improved search within transcripts.
