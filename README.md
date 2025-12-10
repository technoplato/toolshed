# Toolshed

A monorepo for various tools, experiments, and applications.

## Guiding Principles

_See [AGENTS.md](./AGENTS.md) for detailed guidelines._

- **Instant Feedback**: We value rapid iteration and verification.
- **Agent-First**: This repository is structured to be friendly to AI agents.
- **Centralized Data**: We use InstantDB for data and logging.

## Project Structure

- **apps/**
  - `speaker-diarization-benchmark/`: Python-based speaker diarization and transcription benchmarking.
  - `transcriber/`: Python-based video transcription and processing.
- **references/** (git submodules)
  - `swift-composable-architecture/`: Point-Free's TCA library for building Swift applications.
  - `swift-sharing/`: Point-Free's library for sharing state across features.
- **packages/**
  - `schema/`: Shared InstantDB schema.

## References (Submodules)

This repository includes reference implementations as git submodules for agents to explore:

- **[swift-composable-architecture](https://github.com/pointfreeco/swift-composable-architecture)**: A library for building applications in a consistent and understandable way, with composition, testing, and ergonomics in mind.
- **[swift-sharing](https://github.com/pointfreeco/swift-sharing)**: A library for sharing state across features in a composable way.

To initialize submodules after cloning:

```bash
git submodule update --init --recursive
```

## Getting Started

1.  **Dependencies**:
    - Python: Install `uv`.
    - Node.js: Install dependencies with `npm install` (or `pnpm`/`yarn` as configured).

2.  **Documentation**:
    - Read [AGENTS.md](./AGENTS.md) for coding standards.
    - Check [TASKS.md](./TASKS.md) for current objectives.
    - Check [progress.md](./progress.md) for recent updates.
