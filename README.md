# Toolshed

A monorepo for various tools, experiments, and applications.

## Guiding Principles
*See [AGENTS.md](./AGENTS.md) for detailed guidelines.*

- **Instant Feedback**: We value rapid iteration and verification.
- **Agent-First**: This repository is structured to be friendly to AI agents.
- **Centralized Data**: We use InstantDB for data and logging.

## Project Structure

- **apps/**
    - `transcriber/`: Python-based video transcription and processing.
    - `swiss-army-knife/`: React application for general utilities (Coming Soon).
    - `log-watcher/`: TypeScript utility to tail InstantDB logs (Coming Soon).
- **packages/**
    - `schema/`: Shared InstantDB schema.

## Getting Started

1.  **Dependencies**:
    - Python: Install `uv`.
    - Node.js: Install dependencies with `npm install` (or `pnpm`/`yarn` as configured).

2.  **Documentation**:
    - Read [AGENTS.md](./AGENTS.md) for coding standards.
    - Check [TASKS.md](./TASKS.md) for current objectives.
    - Check [PROGRESS.md](./PROGRESS.md) for recent updates.
