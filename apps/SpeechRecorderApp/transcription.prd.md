# SpeechRecorderApp Product Requirements Document

## Overview

SpeechRecorderApp is a speech transcription, recognition, recording, and playback application that aspires to be the **platonic ideal of a speech recording application**. It represents a complete speech recording archetype with a comprehensive feature set that prioritizes user experience, real-time feedback, and seamless interaction patterns.

The application is built entirely with Point-Free's library ecosystem, leveraging The Composable Architecture (TCA), Swift Sharing, and Swift Dependencies to create a robust, testable, and maintainable codebase.

---

## Core Features Summary

| Feature | Description |
|---------|-------------|
| **Recording** | Capture audio with real-time speech-to-text transcription |
| **Playback** | Play recordings with synchronized word highlighting |
| **Recordings Library** | Browse, manage, and organize persisted recordings |
| **Media Embedding** | Capture and embed screenshots/photos inline with transcription |
| **Fullscreen Mode** | Distraction-free viewing with pinch-to-zoom text sizing |
| **Collapsible Recording** | Minimize recording to floating indicator while browsing |

---

## Technical Architecture

### Point-Free Library Stack

The application is built exclusively with Point-Free's Swift libraries:

| Library | Purpose |
|---------|---------|
| **swift-composable-architecture** | State management, effects, and feature composition |
| **swift-sharing** | Shared state across features with automatic synchronization |
| **swift-dependencies** | Dependency injection for live, test, and preview environments |

### Feature Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AppFeature (Root)                               │
│  • Coordinates recording and recordings list                                 │
│  • Manages modal presentation states                                         │
│  • Owns shared live transcription state                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                   │                              │
                   ▼                              ▼
┌─────────────────────────────┐   ┌─────────────────────────────────────────┐
│     RecordingsListFeature   │   │        RecordingFeature                 │
│  • List of saved recordings │   │  • Active recording session             │
│  • Playback presentation    │   │  • Real-time transcription              │
│  • Delete/manage recordings │   │  • Audio level monitoring               │
└─────────────────────────────┘   │  • Photo capture during recording       │
             │                     └─────────────────────────────────────────┘
             ▼                                    │
┌─────────────────────────────┐                   ▼
│      PlaybackFeature        │   ┌─────────────────────────────────────────┐
│  • Audio playback           │   │     FullscreenTranscriptFeature         │
│  • Word-by-word highlighting│   │  • Pinch-to-zoom text sizing            │
│  • Seek to timestamp        │   │  • Distraction-free viewing             │
└─────────────────────────────┘   └─────────────────────────────────────────┘
```

### Shared State Architecture

The application uses `@Shared` property wrappers for state that needs to be synchronized across features:

| Shared Key | Storage | Purpose |
|------------|---------|---------|
| `.recordings` | File Storage | Persisted list of all recordings |
| `.liveTranscription` | In-Memory | Real-time transcription during recording |
| `.activeRecording` | In-Memory | Currently active recording (for list display) |
| `.fullscreenTextSize` | App Storage | User's preferred text size (persisted) |

---

## Feature Specifications

### 1. Recordings Library

**Purpose:** Central hub for viewing and managing all saved recordings.

**Behavior:**
- Displays a scrollable list of all recordings persisted to disk
- Each recording row shows:
  - Title (user-editable or auto-generated from date)
  - Recording date and time
  - Duration
  - Transcription preview (first 2 lines)
  - Media count indicator (if photos/screenshots exist)
  - Thumbnail previews of embedded media
- Tap a recording to open playback view
- Swipe to delete recordings (removes audio file from disk)
- Large record button at bottom to start new recording

**Active Recording Display:**
- When a recording is in progress, it appears at the top of the list
- Shows a pulsing red "LIVE" indicator
- Displays real-time duration counter
- Shows live transcription preview (most recent segment)
- Allows browsing other recordings while recording continues

---

### 2. Recording Session

**Purpose:** Capture audio with real-time speech-to-text transcription.

**Behavior:**

#### Recording Controls
- **Record Button:** Large circular button to start recording
- **Stop Button:** Square icon replaces record button during recording
- **Pause/Resume Button:** 
  - Shows pause icon during active recording
  - Shows microphone icon when paused (indicating "tap to resume")
- **Duration Display:** Shows elapsed time in `HH:MM:SS.ms` format with zero-padded segments

#### Live Transcription Display
- Words appear in real-time as speech is recognized
- Finalized segments show with timestamps
- Volatile (in-progress) text appears in purple
- Segments are separated by natural pauses in speech
- Auto-scrolls to keep latest content visible

#### Auto-Scroll Behavior
- **Follow Mode:** Automatically scrolls to the bottom as new content appears
- **Manual Scroll:** Scrolling away from the bottom disables auto-scroll
- **Resume Button:** A floating "Resume auto-scroll" button appears when auto-scroll is disabled
- **Liquid Glass Preview:** When scrolled away, a preview of the current recording segment appears (planned)

#### Audio Visualization
- Rolling waveform visualization shows audio levels
- Waveform pauses when recording is paused
- Visual feedback confirms microphone is capturing audio

#### Title Editing
- Default title is human-readable date (e.g., "December 12, 2025 at 3:45 PM")
- Tap title to edit inline
- Title can be changed during or after recording

---

### 3. Collapsible Recording Modal

**Purpose:** Allow users to browse the app while recording continues in the background.

**Behavior:**
- Swipe down on the recording view to minimize
- Recording continues in the background (timer, transcription, audio capture)
- A floating indicator appears at the bottom of the screen showing:
  - Pulsing red dot (or orange when paused)
  - Current duration
  - "Recording" or "Paused" status
  - Chevron indicating tap to expand
- Tap the floating indicator to return to full recording view
- Can interact with recordings list, play back previous recordings, etc.

---

### 4. Playback

**Purpose:** Review recordings with synchronized word highlighting and media display.

**Behavior:**

#### Audio Playback
- Play/Pause button with standard controls
- Skip forward/backward 10 seconds
- Scrubber bar for seeking to any position
- Current time and total duration display

#### Word Highlighting
- The currently spoken word is highlighted in yellow
- Highlighting moves in sync with audio playback
- Tap any word to jump audio playback to that word's timestamp
- Smooth scrolling keeps the current word visible

#### Media Display
- Photos and screenshots captured during recording appear inline
- Media is positioned at the timestamp where it was captured
- Tap media to jump playback to that timestamp
- Double-tap media to view fullscreen
- Media timeline shows all captured media with thumbnails

#### Segment Display
- Transcription is organized into segments with timestamps
- Each segment shows its start time
- Active segment is subtly highlighted during playback

---

### 5. Media Embedding

**Purpose:** Capture and embed visual context alongside audio transcription.

**Behavior:**

#### During Recording
- App observes the photo library for new photos/screenshots
- When a photo or screenshot is taken, it's automatically embedded
- Media is timestamped relative to recording start time
- Thumbnails appear inline with the transcription
- Screenshots show blue border, photos show green border

#### During Playback
- Media appears at the position in the transcription where it was captured
- Tap media to seek playback to that timestamp
- Double-tap to view media fullscreen
- Media timeline provides quick navigation to all captured media

---

### 6. Fullscreen Transcript Mode

**Purpose:** Distraction-free reading experience for transcripts.

**Behavior:**

#### Entry/Exit
- Double-tap with two fingers to enter fullscreen mode
- Double-tap with two fingers again to exit
- Works in both recording and playback views

#### Display
- Black background for reduced eye strain
- White text for high contrast
- Timestamps shown in gray
- Current word highlighted in yellow (during playback)
- Volatile text shown in purple (during recording)

#### Text Size
- Pinch-to-zoom gesture adjusts text size
- Text size range: 16pt to 48pt
- Default size: 24pt
- Size preference is persisted to disk

#### Auto-Scroll
- Same behavior as recording view
- Manual scroll disables auto-scroll
- Floating button to resume auto-scroll

---

### 7. Gesture Support

**Purpose:** Enable chrome-free interaction in fullscreen and recording views.

| Gesture | Context | Action |
|---------|---------|--------|
| Two-finger double-tap | Recording/Playback | Toggle fullscreen mode |
| Pinch | Fullscreen | Adjust text size |
| Swipe down | Recording modal | Minimize to floating indicator |
| Tap word | Playback | Seek to word timestamp |
| Tap media | Playback | Seek to media timestamp |
| Double-tap media | Playback | View media fullscreen |

---

## Data Models

### Recording

```swift
struct Recording {
    let id: UUID
    var title: String
    var date: Date
    var duration: TimeInterval
    var audioURL: URL
    var transcription: Transcription
    var media: [TimestampedMedia]
}
```

### Transcription

```swift
struct Transcription {
    var text: String
    var words: [TimestampedWord]
    var segments: [TranscriptionSegment]
    var isFinal: Bool
}
```

### TimestampedWord

```swift
struct TimestampedWord {
    let id: UUID
    var text: String
    var startTime: TimeInterval
    var endTime: TimeInterval
}
```

### TimestampedMedia

```swift
struct TimestampedMedia {
    let id: UUID
    var timestamp: TimeInterval
    var assetIdentifier: String
    var mediaType: MediaType  // .photo or .screenshot
    var creationDate: Date
}
```

---

## Permissions Required

| Permission | Usage |
|------------|-------|
| Microphone | Audio recording |
| Speech Recognition | Real-time transcription |
| Photo Library | Capturing and embedding photos/screenshots |

---

## Platform Support

- **iOS:** 17.0+
- **macOS:** 14.0+
- **Swift:** 5.9+
- **Xcode:** 15.0+

---

## Current Implementation Status

### Implemented Features ✅

- [x] Recording with real-time transcription
- [x] Playback with word highlighting
- [x] Recordings list with persistence
- [x] Collapsible recording modal with floating indicator
- [x] Media embedding (photos/screenshots)
- [x] Fullscreen transcript mode
- [x] Pinch-to-zoom text sizing
- [x] Two-finger double-tap gestures
- [x] Auto-scroll with resume button
- [x] Pause/resume recording
- [x] Editable recording titles
- [x] Active recording display in list with LIVE indicator
- [x] Playback while recording (other recordings)

### Known Issues / In Progress 🚧

- [ ] Scrolling behavior needs refinement in some views
- [ ] Pinch-to-zoom in fullscreen may need gesture conflict resolution
- [ ] Liquid glass preview for scrolled-away recording segment (planned)
- [ ] Background recording support (audio continues when app backgrounded)

---

## Design Philosophy

### Platonic Ideal

This application strives to be the archetypal speech recording app—not by being minimal, but by being **complete**. Every feature that a user might reasonably expect from a speech recording application should be present and polished.

### Non-Dumbed-Down

The interface respects user intelligence. Features are discoverable but not hidden behind excessive tutorials or hand-holding. Power users can access advanced features through gestures and shortcuts.

### Real-Time Feedback

Every action provides immediate feedback:
- Words appear as they're spoken
- Audio levels visualize in real-time
- Media embeds instantly when captured
- Playback highlighting syncs precisely with audio

### Composable Architecture

The TCA foundation ensures:
- **Testability:** Every feature can be tested in isolation
- **Predictability:** State changes are explicit and traceable
- **Composability:** Features can be combined and reused
- **Ergonomics:** SwiftUI integration is seamless

---

## File Structure

```
SpeechRecorderApp/
├── Features/
│   ├── AppFeature.swift              # Root coordinator
│   ├── RecordingFeature.swift        # Recording session logic
│   ├── RecordingsListFeature.swift   # Recordings list management
│   ├── PlaybackFeature.swift         # Audio playback with highlighting
│   ├── FullscreenTranscriptFeature.swift
│   └── FullscreenImageFeature.swift
├── Views/
│   ├── ContentView.swift             # Root view
│   ├── RecordingView.swift           # Recording interface
│   ├── RecordingsListView.swift      # Recordings list
│   ├── PlaybackView.swift            # Playback interface
│   ├── TranscriptionDisplayView.swift # Shared transcription display
│   ├── FullscreenTranscriptView.swift
│   ├── FloatingRecordingIndicator.swift
│   └── AudioWaveformView.swift
├── Dependencies/
│   ├── AudioRecorderClient.swift
│   ├── AudioPlayerClient.swift
│   ├── SpeechClient.swift
│   └── PhotoLibraryClient.swift
├── Models/
│   ├── Recording.swift
│   ├── Transcription.swift
│   ├── TimestampedWord.swift
│   └── TimestampedMedia.swift
├── SharedKeys/
│   └── SharedKeys.swift              # @Shared state keys
└── Helpers/
    ├── Helpers.swift                 # Formatting utilities
    └── BufferConverter.swift         # Audio buffer conversion
```

---

## Related Documentation

- [`README.md`](./README.md) - Project overview and setup
- [`../../docs/speech-recorder-app-implementation-plan.md`](../../docs/speech-recorder-app-implementation-plan.md) - Original implementation plan
- [`../../docs/tca-best-practices-comprehensive-guide.md`](../../docs/tca-best-practices-comprehensive-guide.md) - TCA patterns reference
- [`../../plans/speech-recorder-tca-audit.md`](../../plans/speech-recorder-tca-audit.md) - Architecture audit and improvement plan
- [`../../docs/swift-sharing-state-comprehensive-guide.md`](../../docs/swift-sharing-state-comprehensive-guide.md) - Swift Sharing patterns

---

*Last Updated: December 12, 2025*