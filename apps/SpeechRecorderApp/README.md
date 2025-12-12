# SpeechRecorderApp

A macOS/iOS app for recording audio with real-time speech transcription, built using The Composable Architecture (TCA).

## 🎯 Purpose

SpeechRecorderApp enables users to record audio while simultaneously capturing live transcriptions. The app is designed to facilitate "chain of thought" recording - capturing spoken ideas with automatic transcription for later review and ingestion into other systems.

## 🏗️ Architecture

Built with [The Composable Architecture (TCA)](https://github.com/pointfreeco/swift-composable-architecture) following best practices from Point-Free.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              APP STRUCTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         AppFeature (Root)                              │  │
│  │  • Coordinates recording and recordings list                          │  │
│  │  • Manages modal presentation states                                   │  │
│  │  • Owns shared live transcription state                               │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                    │                              │                          │
│                    ▼                              ▼                          │
│  ┌─────────────────────────────┐   ┌─────────────────────────────────────┐  │
│  │     RecordingsListFeature   │   │        RecordingFeature             │  │
│  │  • List of saved recordings │   │  • Active recording session         │  │
│  │  • Playback presentation    │   │  • Real-time transcription          │  │
│  │  • Delete/manage recordings │   │  • Audio level monitoring           │  │
│  └─────────────────────────────┘   │  • Photo capture during recording   │  │
│              │                      └─────────────────────────────────────┘  │
│              ▼                                                               │
│  ┌─────────────────────────────┐                                            │
│  │      PlaybackFeature        │                                            │
│  │  • Audio playback           │                                            │
│  │  • Word-by-word highlighting│                                            │
│  │  • Seek to timestamp        │                                            │
│  └─────────────────────────────┘                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
SpeechRecorderApp/
├── SpeechRecorderApp/
│   ├── Features/                    # TCA Reducers
│   │   ├── AppFeature.swift         # Root feature coordinator
│   │   ├── RecordingFeature.swift   # Recording session logic
│   │   ├── RecordingsListFeature.swift
│   │   ├── PlaybackFeature.swift
│   │   ├── FullscreenImageFeature.swift
│   │   └── FullscreenTranscriptFeature.swift
│   │
│   ├── Views/                       # SwiftUI Views
│   │   ├── RecordingView.swift
│   │   ├── RecordingsListView.swift
│   │   ├── PlaybackView.swift
│   │   ├── TranscriptionDisplayView.swift
│   │   ├── AudioWaveformView.swift
│   │   ├── FloatingRecordingIndicator.swift
│   │   ├── LiveBadge.swift
│   │   └── ...
│   │
│   ├── Dependencies/                # TCA Dependency Clients
│   │   ├── AudioRecorderClient.swift
│   │   ├── LiveAudioRecorderClient.swift
│   │   ├── AudioPlayerClient.swift
│   │   ├── LiveAudioPlayerClient.swift
│   │   ├── SpeechClient.swift
│   │   ├── LiveSpeechClient.swift
│   │   ├── PhotoLibraryClient.swift
│   │   └── LivePhotoLibraryClient.swift
│   │
│   ├── Models/
│   │   ├── Recording.swift          # Recording data model
│   │   ├── Transcription.swift      # Transcription with words
│   │   ├── TimestampedWord.swift    # Word with timing info
│   │   └── TimestampedMedia.swift   # Photos captured during recording
│   │
│   ├── SharedKeys/
│   │   └── SharedKeys.swift         # @Shared state keys
│   │
│   └── Helpers/
│       ├── Helpers.swift
│       └── BufferConverter.swift
│
└── SpeechRecorderAppTests/          # Unit Tests
    ├── AppFeatureTests.swift
    ├── RecordingFeatureTests.swift
    ├── PlaybackFeatureTests.swift
    ├── RecordingsListFeatureTests.swift
    └── ...
```

## 🔧 Key Features

### Recording
- **Real-time transcription** using Apple's Speech framework
- **Audio level visualization** with waveform display
- **Photo capture** during recording with timestamp synchronization
- **Expandable/collapsible** recording modal
- **Floating indicator** when recording is minimized

### Playback
- **Word-by-word highlighting** synced to audio playback
- **Seek to word** by tapping on transcription
- **Fullscreen transcript** view
- **Fullscreen image** viewer for captured photos

### State Management
- **Persistent recordings** via `@Shared(.fileStorage)`
- **Live transcription** via `@Shared(.inMemory)`
- **Derived shared state** for playback editing

## 🚀 Getting Started

### Prerequisites
- Xcode 15.0+
- macOS 14.0+ / iOS 17.0+
- Swift 5.9+

### Build & Run

```bash
# Open in Xcode
open apps/SpeechRecorderApp/SpeechRecorderApp.xcodeproj

# Or build from command line
xcodebuild -project apps/SpeechRecorderApp/SpeechRecorderApp.xcodeproj \
  -scheme SpeechRecorderApp \
  -destination 'platform=macOS'
```

### Run Tests

```bash
xcodebuild test \
  -project apps/SpeechRecorderApp/SpeechRecorderApp.xcodeproj \
  -scheme SpeechRecorderApp \
  -destination 'platform=macOS'
```

## 📚 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| [swift-composable-architecture](https://github.com/pointfreeco/swift-composable-architecture) | 1.17+ | State management, effects, testing |
| [swift-sharing](https://github.com/pointfreeco/swift-sharing) | 2.0+ | Shared state across features |
| [swift-dependencies](https://github.com/pointfreeco/swift-dependencies) | 1.6+ | Dependency injection |

## 🔐 Permissions Required

The app requires the following permissions:

| Permission | Usage |
|------------|-------|
| Microphone | Audio recording |
| Speech Recognition | Real-time transcription |
| Photo Library | Capturing photos during recording |

## 🚧 Current Status

**Work in Progress** - The app is functional but undergoing architecture improvements:

- [ ] Move `@Shared(.liveTranscription)` to AppFeature level
- [ ] Implement Destination enum pattern for navigation
- [ ] Show active recording in recordings list with live indicator
- [ ] Add convenience initializers for dependency clients
- [ ] Improve effect lifecycle management with `.task` pattern

See [`plans/speech-recorder-tca-audit.md`](../../plans/speech-recorder-tca-audit.md) for detailed improvement plan.

## 📖 Related Documentation

- [`docs/speech-recorder-app-implementation-plan.md`](../../docs/speech-recorder-app-implementation-plan.md) - Original implementation plan
- [`docs/tca-best-practices-comprehensive-guide.md`](../../docs/tca-best-practices-comprehensive-guide.md) - TCA patterns reference
- [`plans/speech-recorder-tca-audit.md`](../../plans/speech-recorder-tca-audit.md) - Architecture audit and improvement plan