# Speech Recorder App Implementation Plan

## TDD-Focused Development with The Composable Architecture

**HOW:**
This document guides the development of a speech recording app using TCA's test-driven development approach.

**Prerequisites:**

- Xcode 26.0+ (for iOS 26.0+ SpeechAnalyzer API)
- macOS 26.0+ for development
- Approved Swift macros in Xcode (swift-case-paths, swift-dependencies, swift-perception)

**WHO:**
AI Agents, Developers
(Context: Building a speech recording app with live transcription and synchronized playback)

**WHAT:**
A comprehensive implementation plan for building a speech recording app that:

- Records audio with live transcription using Apple's new SpeechAnalyzer API (iOS 26.0+)
- Provides word-level timestamps for synchronized playback
- Persists recordings and transcriptions using Swift Sharing
- Follows TCA patterns for testability and composability

**WHEN:**
Created: 2025-12-10
Last Modified: 2025-12-10

**WHERE:**
docs/speech-recorder-app-implementation-plan.md

**WHY:**
To provide a structured, test-driven approach for building a production-quality speech recording app
that leverages the latest Apple Speech APIs and Point-Free's TCA ecosystem.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [TDD Workflow with TCA](#tdd-workflow-with-tca)
4. [Phase 1: Project Setup & Basic Recording](#phase-1-project-setup--basic-recording) ✅
5. [Phase 2: SpeechAnalyzer Integration](#phase-2-speechanalyzer-integration) ✅
6. [Phase 3: Word-Level Timestamps](#phase-3-word-level-timestamps) ✅
7. [Phase 4: Persistence with Swift Sharing](#phase-4-persistence-with-swift-sharing) ✅
8. [Phase 5: Synchronized Playback](#phase-5-synchronized-playback) ✅
9. [Phase 6: State Sharing Improvements](#phase-6-state-sharing-improvements) 🆕
10. [Phase 7: Test Coverage Enhancement](#phase-7-test-coverage-enhancement) 🆕
11. [Phase 8: Code Quality & Cleanup](#phase-8-code-quality--cleanup) 🆕
12. [Reference Materials](#reference-materials)

---

## Project Overview

### Goals

1. **Record audio** with real-time transcription ✅
2. **Display live transcription** with volatile (in-progress) and finalized text ✅
3. **Store word-level timestamps** for each transcribed word ✅
4. **Persist recordings** to disk with their transcriptions ✅
5. **Synchronized playback** - highlight words as audio plays ✅

### Technology Stack

| Component            | Technology                                     |
| -------------------- | ---------------------------------------------- |
| Architecture         | The Composable Architecture (TCA)              |
| Speech Recognition   | SpeechAnalyzer + SpeechTranscriber (iOS 26.0+) |
| Audio Recording      | AVAudioEngine                                  |
| Persistence          | Swift Sharing (@Shared with .fileStorage)      |
| Dependency Injection | Swift Dependencies (@Dependency)               |
| Testing              | TCA TestStore + Swift Testing                  |

---

## Architecture Overview

### Feature Composition

```
┌─────────────────────────────────────────────────────────────┐
│                      AppFeature                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  RecordingsListFeature                   ││
│  │  @Shared(.recordings) var recordings: [Recording]        ││
│  └─────────────────────────────────────────────────────────┘│
│                              │                               │
│              ┌───────────────┴───────────────┐              │
│              ▼                               ▼              │
│  ┌─────────────────────┐         ┌─────────────────────┐   │
│  │  RecordingFeature   │         │   PlaybackFeature   │   │
│  │  - AudioRecorder    │         │   - AudioPlayer     │   │
│  │  - SpeechClient     │         │   - WordHighlighter │   │
│  └─────────────────────┘         └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Data Models

```swift
/// A single recording with its transcription
struct Recording: Codable, Identifiable, Equatable, Sendable {
    let id: UUID
    var title: String
    var date: Date
    var duration: TimeInterval
    var audioURL: URL
    var transcription: Transcription
}

/// The transcription with word-level timing
struct Transcription: Codable, Equatable, Sendable {
    var text: String
    var words: [TimestampedWord]
    var isFinal: Bool
}

/// A word with its timing information
struct TimestampedWord: Codable, Equatable, Sendable {
    let text: String
    let startTime: TimeInterval
    let endTime: TimeInterval
    let confidence: Float?
}
```

---

## TDD Workflow with TCA

### The TestStore Pattern

TCA's `TestStore` is the cornerstone of our TDD approach. It allows us to:

1. **Send actions** and assert state changes
2. **Receive effects** and verify async behavior
3. **Override dependencies** for deterministic testing
4. **Exhaust all effects** to ensure no unexpected behavior

### Test-First Development Cycle

```
┌─────────────────────────────────────────────────────────────┐
│  1. Write a failing test                                     │
│     - Define expected state changes                          │
│     - Mock dependencies                                      │
│     - Use TestStore to send actions                          │
├─────────────────────────────────────────────────────────────┤
│  2. Implement the minimum code to pass                       │
│     - Add State properties                                   │
│     - Add Action cases                                       │
│     - Implement Reducer body                                 │
├─────────────────────────────────────────────────────────────┤
│  3. Refactor                                                 │
│     - Extract dependencies                                   │
│     - Improve naming                                         │
│     - Add documentation                                      │
├─────────────────────────────────────────────────────────────┤
│  4. Repeat                                                   │
└─────────────────────────────────────────────────────────────┘
```

### Example: TDD for Recording Feature

**Step 1: Write the failing test**

```swift
@Test
func testRecordButtonTapped_startsRecording() async {
    let store = TestStore(initialState: RecordingFeature.State()) {
        RecordingFeature()
    } withDependencies: {
        $0.audioRecorder.requestPermission = { true }
        $0.audioRecorder.startRecording = { _ in }
        $0.speechClient.requestAuthorization = { .authorized }
        $0.speechClient.startTranscription = { _ in .finished() }
        $0.date.now = Date(timeIntervalSince1970: 0)
        $0.uuid = .incrementing
    }

    await store.send(.recordButtonTapped) {
        $0.isRecording = true
        $0.recordingStartTime = Date(timeIntervalSince1970: 0)
    }

    await store.receive(\.permissionResponse)
    await store.receive(\.recordingStarted)
}
```

**Step 2: Implement the feature**

```swift
@Reducer
struct RecordingFeature {
    @ObservableState
    struct State: Equatable {
        var isRecording = false
        var recordingStartTime: Date?
        var transcription = Transcription(text: "", words: [], isFinal: false)
    }

    enum Action: Sendable {
        case recordButtonTapped
        case permissionResponse(Bool)
        case recordingStarted
        case transcriptionResult(Result<TranscriptionUpdate, Error>)
    }

    @Dependency(\.audioRecorder) var audioRecorder
    @Dependency(\.speechClient) var speechClient
    @Dependency(\.date) var date
    @Dependency(\.uuid) var uuid

    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case .recordButtonTapped:
                state.isRecording = true
                state.recordingStartTime = date.now
                return .run { send in
                    let hasPermission = await audioRecorder.requestPermission()
                    await send(.permissionResponse(hasPermission))
                }
            // ... more cases
            }
        }
    }
}
```

---

## Phase 1: Project Setup & Basic Recording ✅

### Goals

- Set up Xcode project with TCA dependencies ✅
- Implement basic audio recording (no transcription yet) ✅
- Create AudioRecorder dependency ✅

### Completed Tasks

- [x] Create Xcode project with TCA dependencies
- [x] Define AudioRecorderClient dependency
- [x] Write tests for recording start/stop
- [x] Implement live AudioRecorder
- [x] Create basic RecordingView

---

## Phase 2: SpeechAnalyzer Integration ✅

### Goals

- Create SpeechClient dependency wrapping SpeechAnalyzer ✅
- Integrate live transcription with recording ✅
- Handle asset installation for locale-specific models ✅

### Completed Tasks

- [x] Define SpeechClient dependency
- [x] Write tests for transcription flow
- [x] Implement live SpeechClient with SpeechAnalyzer
- [x] Handle asset installation
- [x] Display live transcription

---

## Phase 3: Word-Level Timestamps ✅

### Goals

- Extract word-level timing from SpeechTranscriber.Result ✅
- Store timestamps with each word ✅
- Enable synchronized playback preparation ✅

### Completed Tasks

- [x] Write tests for word extraction
- [x] Implement word extraction from AttributedString
- [x] Store TimestampedWord array
- [x] Verify timing accuracy

---

## Phase 4: Persistence with Swift Sharing ✅

### Goals

- Persist recordings list using @Shared ✅
- Save audio files to documents directory ✅
- Store transcriptions as JSON ✅

### Completed Tasks

- [x] Define @Shared recordings key
- [x] Write tests for persistence
- [x] Implement RecordingsListFeature
- [x] Save audio files to documents
- [x] Create recordings list UI

---

## Phase 5: Synchronized Playback ✅

### Goals

- Play audio with word highlighting ✅
- Sync current playback position with transcription ✅
- Highlight current word based on timestamps ✅

### Completed Tasks

- [x] Define AudioPlayerClient dependency
- [x] Write tests for playback sync
- [x] Implement PlaybackFeature
- [x] Create word highlighting view
- [x] Add seek functionality

---

## Phase 6: State Sharing Improvements 🆕

### Goals

Based on the [Swift Sharing State Comprehensive Guide](./swift-sharing-state-comprehensive-guide.md) and the SyncUps reference implementation, improve the state sharing patterns in the app.

### 6.1 Add Default Value to SharedKey

**Current Implementation** ([`SharedKeys.swift:43-47`](../apps/SpeechRecorderApp/SpeechRecorderApp/SharedKeys/SharedKeys.swift:43)):

```swift
extension SharedReaderKey where Self == FileStorageKey<[Recording]> {
    static var recordings: Self {
        .fileStorage(.documentsDirectory.appending(component: "recordings.json"))
    }
}
```

**Improved Implementation** (following SyncUps pattern from [`SyncUpsList.swift:183-186`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpsList.swift:183)):

```swift
extension SharedKey where Self == FileStorageKey<[Recording]>.Default {
    static var recordings: Self {
        Self[.fileStorage(.documentsDirectory.appending(component: "recordings.json")), default: []]
    }
}
```

**Benefits:**

- No need to specify default value at each usage site
- Consistent with SyncUps pattern
- Type-safe default value

**Files to Change:**

- [`SharedKeys.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/SharedKeys/SharedKeys.swift) - Update key definition
- [`RecordingsListFeature.swift:56`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingsListFeature.swift:56) - Remove default value from declaration

### 6.2 Use IdentifiedArrayOf for Recordings

**Current Implementation:**

```swift
@Shared(.recordings) var recordings: [Recording] = []
```

**Improved Implementation:**

```swift
@Shared(.recordings) var recordings: IdentifiedArrayOf<Recording>
```

**Benefits:**

- O(1) lookup by ID instead of O(n)
- Better integration with TCA's `ForEach` and navigation
- Enables derived shared state for individual recordings

**Files to Change:**

- [`SharedKeys.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/SharedKeys/SharedKeys.swift) - Update type
- [`RecordingsListFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingsListFeature.swift) - Update usage
- [`AppFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/AppFeature.swift) - Update usage
- [`Recording.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Models/Recording.swift) - Ensure Identifiable conformance (already done)

### 6.3 Derive Shared State for PlaybackFeature

**Current Implementation** ([`RecordingsListFeature.swift:96`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingsListFeature.swift:96)):

```swift
case let .selectRecording(recording):
    state.playback = PlaybackFeature.State(recording: recording)
    return .none
```

**Improved Implementation** (following SyncUps pattern from [`SyncUpsList.swift:83-86`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpsList.swift:83)):

```swift
// In RecordingsListView
ForEach(Array(store.$recordings)) { $recording in
    NavigationLink(state: AppFeature.Path.State.playback(
        PlaybackFeature.State(recording: $recording)
    )) {
        RecordingRow(recording: recording)
    }
}
```

**Benefits:**

- Changes to recording during playback propagate back to list
- Enables editing recording metadata during playback
- Follows SyncUps pattern for parent-child shared state

**Files to Change:**

- [`PlaybackFeature.swift:55-56`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/PlaybackFeature.swift:55) - Change `var recording: Recording` to `@Shared var recording: Recording`
- [`RecordingsListFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingsListFeature.swift) - Pass derived shared state
- [`PlaybackView.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Views/PlaybackView.swift) - Update to use shared binding

### 6.4 Add Type-Safe Key for User Settings

**New Implementation:**

```swift
// SharedKeys.swift
extension SharedKey where Self == AppStorageKey<Bool>.Default {
    static var isHapticsEnabled: Self {
        Self[.appStorage("isHapticsEnabled"), default: true]
    }

    static var isAutoScrollEnabled: Self {
        Self[.appStorage("isAutoScrollEnabled"), default: true]
    }
}

extension SharedKey where Self == AppStorageKey<Double>.Default {
    static var playbackSpeed: Self {
        Self[.appStorage("playbackSpeed"), default: 1.0]
    }
}
```

**Benefits:**

- Centralized settings management
- Type-safe access throughout app
- Automatic persistence to UserDefaults

**Files to Change:**

- [`SharedKeys.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/SharedKeys/SharedKeys.swift) - Add new keys
- [`PlaybackFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/PlaybackFeature.swift) - Use settings
- [`RecordingFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingFeature.swift) - Use settings

### 6.5 Implement Delete with Shared State Access

**Current Implementation** ([`RecordingsListFeature.swift:99-107`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingsListFeature.swift:99)):

```swift
case let .deleteRecordings(indexSet):
    state.$recordings.withLock { recordings in
        for index in indexSet {
            let recording = recordings[index]
            try? FileManager.default.removeItem(at: recording.audioURL)
        }
        recordings.remove(atOffsets: indexSet)
    }
    return .none
```

**Improved Implementation** (following SyncUps pattern from [`SyncUpDetail.swift:66-68`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpDetail.swift:66)):

```swift
// In PlaybackFeature for deleting current recording
case .deleteButtonTapped:
    state.destination = .alert(.deleteRecording)
    return .none

case .destination(.presented(.alert(.confirmDeletion))):
    @Shared(.recordings) var recordings
    $recordings.withLock { _ = $0.remove(id: state.recording.id) }
    // Also delete audio file
    try? FileManager.default.removeItem(at: state.recording.audioURL)
    return .run { _ in await dismiss() }
```

**Benefits:**

- Child feature can access parent's shared state directly
- Cleaner separation of concerns
- Follows SyncUps pattern for deletion

**Files to Change:**

- [`PlaybackFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/PlaybackFeature.swift) - Add delete functionality
- [`PlaybackView.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Views/PlaybackView.swift) - Add delete button

---

## Phase 7: Test Coverage Enhancement 🆕

### Goals

Improve test coverage following patterns from SyncUps tests.

### 7.1 Add Shared State Mutation Tests

**Reference:** [`SyncUpsListTests.swift:34-37`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpsListTests.swift:34)

**New Test Pattern:**

```swift
@Test
func addRecording() async {
    let store = await TestStore(initialState: RecordingsListFeature.State()) {
        RecordingsListFeature()
    } withDependencies: {
        $0.uuid = .incrementing
        $0.defaultFileStorage = .inMemory
    }

    let recording = Recording(
        id: UUID(0),
        title: "Test",
        date: Date(),
        duration: 10.0,
        audioURL: URL(fileURLWithPath: "/tmp/test.m4a")
    )

    // Simulate recording finished
    await store.send(.recordingFinished(.success(recording))) {
        $0.$recordings.withLock { $0 = [recording] }
    }
}
```

**Files to Change:**

- [`RecordingsListFeatureTests.swift`](../apps/SpeechRecorderApp/SpeechRecorderAppTests/RecordingsListFeatureTests.swift) - Add shared state tests

### 7.2 Add Delete with Shared State Access Test

**Reference:** [`SyncUpDetailTests.swift:117-135`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpDetailTests.swift:117)

**New Test Pattern:**

```swift
@Test
func deleteRecording() async throws {
    let recording = Recording.preview()
    @Shared(.recordings) var recordings = [recording]
    defer { #expect(recordings == []) }

    let sharedRecording = try #require(Shared($recordings[id: recording.id]))

    let store = await TestStore(
        initialState: PlaybackFeature.State(recording: sharedRecording)
    ) {
        PlaybackFeature()
    }

    await store.send(.deleteButtonTapped) {
        $0.destination = .alert(.deleteRecording)
    }

    await store.send(\.destination.alert.confirmDeletion) {
        $0.destination = nil
    }

    #expect(store.isDismissed)
}
```

**Files to Change:**

- [`PlaybackFeatureTests.swift`](../apps/SpeechRecorderApp/SpeechRecorderAppTests/PlaybackFeatureTests.swift) - Add delete test

### 7.3 Add Edit Recording Test

**Reference:** [`SyncUpDetailTests.swift:93-115`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpDetailTests.swift:93)

**New Test Pattern:**

```swift
@Test
func editRecordingTitle() async {
    var recording = Recording.preview()

    let store = await TestStore(
        initialState: PlaybackFeature.State(recording: Shared(value: recording))
    ) {
        PlaybackFeature()
    }

    await store.send(.editButtonTapped) {
        $0.destination = .edit(RecordingEditFeature.State(recording: recording))
    }

    recording.title = "Updated Title"
    await store.send(\.destination.edit.binding.recording, recording) {
        $0.destination?.modify(\.edit) { $0.recording.title = "Updated Title" }
    }

    await store.send(.doneEditingButtonTapped) {
        $0.destination = nil
        $0.$recording.withLock { $0.title = "Updated Title" }
    }
}
```

**Files to Change:**

- [`PlaybackFeatureTests.swift`](../apps/SpeechRecorderApp/SpeechRecorderAppTests/PlaybackFeatureTests.swift) - Add edit test
- Create new `RecordingEditFeature.swift` for editing

### 7.4 Add @MainActor to All Test Structs

**Reference:** [`SyncUpsListTests.swift:8-9`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpsListTests.swift:8)

**Current Implementation:**

```swift
@Suite("RecordingsListFeature Tests")
struct RecordingsListFeatureTests {
    // ...
}
```

**Improved Implementation:**

```swift
@MainActor
struct RecordingsListFeatureTests {
    init() { uncheckedUseMainSerialExecutor = true }
    // ...
}
```

**Benefits:**

- Ensures tests run on main actor
- Prevents race conditions in tests
- Follows SyncUps pattern

**Files to Change:**

- [`RecordingsListFeatureTests.swift`](../apps/SpeechRecorderApp/SpeechRecorderAppTests/RecordingsListFeatureTests.swift)
- [`PlaybackFeatureTests.swift`](../apps/SpeechRecorderApp/SpeechRecorderAppTests/PlaybackFeatureTests.swift)
- [`RecordingFeatureTests.swift`](../apps/SpeechRecorderApp/SpeechRecorderAppTests/RecordingFeatureTests.swift)
- [`AppFeatureTests.swift`](../apps/SpeechRecorderApp/SpeechRecorderAppTests/AppFeatureTests.swift)

### 7.5 Add Delegate Action Tests

**Reference:** [`SyncUpDetailTests.swift:77-78`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpDetailTests.swift:77)

**New Test Pattern:**

```swift
@Test
func recordingFinishedSendsDelegate() async {
    let recording = Recording.preview()

    let store = await TestStore(
        initialState: RecordingFeature.State()
    ) {
        RecordingFeature()
    } withDependencies: {
        // ... dependencies
    }

    // ... trigger recording finish

    await store.receive(\.delegate.didFinish.success) { _ in
        // Verify delegate action received
    }
}
```

**Files to Change:**

- [`RecordingFeatureTests.swift`](../apps/SpeechRecorderApp/SpeechRecorderAppTests/RecordingFeatureTests.swift) - Add delegate tests

---

## Phase 8: Code Quality & Cleanup 🆕

### Goals

Improve code quality, documentation, and maintainability.

### 8.1 Add Destination Enum for Navigation

**Reference:** [`SyncUpDetail.swift:5-17`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpDetail.swift:5)

**Current Implementation:**

```swift
@ObservableState
struct State: Equatable {
    @Presents var alert: AlertState<Action.Alert>?
    @Presents var fullscreenTranscript: FullscreenTranscriptFeature.State?
    @Presents var fullscreenImage: FullscreenImageFeature.State?
}
```

**Improved Implementation:**

```swift
@Reducer
enum Destination {
    case alert(AlertState<Alert>)
    case fullscreenTranscript(FullscreenTranscriptFeature)
    case fullscreenImage(FullscreenImageFeature)
    case edit(RecordingEditFeature)

    @CasePathable
    enum Alert {
        case confirmDeletion
        case discardChanges
    }
}

@ObservableState
struct State: Equatable {
    @Presents var destination: Destination.State?
}
```

**Benefits:**

- Single presentation state
- Cleaner action handling
- Better navigation management

**Files to Change:**

- [`PlaybackFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/PlaybackFeature.swift) - Add Destination enum
- [`RecordingFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingFeature.swift) - Add Destination enum

### 8.2 Extract Alert States to Extensions

**Reference:** [`SyncUpDetail.swift:213-264`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpDetail.swift:213)

**New Implementation:**

```swift
extension AlertState where Action == PlaybackFeature.Destination.Alert {
    static let deleteRecording = Self {
        TextState("Delete Recording?")
    } actions: {
        ButtonState(role: .destructive, action: .confirmDeletion) {
            TextState("Delete")
        }
        ButtonState(role: .cancel) {
            TextState("Cancel")
        }
    } message: {
        TextState("This will permanently delete the recording and its transcription.")
    }
}
```

**Benefits:**

- Reusable alert definitions
- Cleaner reducer code
- Easier to test

**Files to Change:**

- Create new `Alerts.swift` file
- [`PlaybackFeature.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Features/PlaybackFeature.swift) - Use alert extensions

### 8.3 Add Preview Helpers with @Shared

**Reference:** [`SyncUpsList.swift:158-170`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpsList.swift:158)

**New Implementation:**

```swift
#Preview("Recordings List") {
    @Shared(.recordings) var recordings = [
        .preview(title: "Meeting Notes"),
        .preview(title: "Voice Memo"),
        .preview(title: "Interview")
    ]

    NavigationStack {
        RecordingsListView(
            store: Store(initialState: RecordingsListFeature.State()) {
                RecordingsListFeature()
            }
        )
    }
}
```

**Benefits:**

- Previews with realistic data
- Easy to test different states
- Follows SyncUps pattern

**Files to Change:**

- [`RecordingsListView.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Views/RecordingsListView.swift) - Add previews
- [`PlaybackView.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/Views/PlaybackView.swift) - Add previews

### 8.4 Add UI Testing Setup

**Reference:** [Swift Sharing Guide - UI Testing Setup](./swift-sharing-state-comprehensive-guide.md#ui-testing-setup)

**New Implementation:**

```swift
// SpeechRecorderApp.swift
@main
struct SpeechRecorderApp: App {
    init() {
        if ProcessInfo.processInfo.environment["UI_TESTING"] != nil {
            prepareDependencies {
                $0.defaultAppStorage = .inMemory
                $0.defaultFileStorage = .inMemory
            }
        }
    }

    var body: some Scene {
        WindowGroup {
            if !isTesting {
                ContentView()
            }
        }
    }
}
```

**Benefits:**

- Isolated UI tests
- No file system pollution
- Deterministic test runs

**Files to Change:**

- [`SpeechRecorderApp.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/SpeechRecorderApp.swift) - Add UI testing setup

### 8.5 Document All Shared Keys

**Current Implementation:**

```swift
extension SharedReaderKey where Self == FileStorageKey<[Recording]> {
    /// Shared key for the list of recordings
    static var recordings: Self {
        .fileStorage(.documentsDirectory.appending(component: "recordings.json"))
    }
}
```

**Improved Implementation:**

````swift
/// Shared key for the list of recordings.
///
/// This key persists recordings to the documents directory as JSON.
/// Each recording includes its audio URL, transcription, and metadata.
///
/// Usage:
/// ```swift
/// @Shared(.recordings) var recordings
/// ```
///
/// In tests, use `.inMemory` file storage:
/// ```swift
/// withDependencies {
///     $0.defaultFileStorage = .inMemory
/// }
/// ```
extension SharedKey where Self == FileStorageKey<IdentifiedArrayOf<Recording>>.Default {
    static var recordings: Self {
        Self[.fileStorage(.documentsDirectory.appending(component: "recordings.json")), default: []]
    }
}
````

**Files to Change:**

- [`SharedKeys.swift`](../apps/SpeechRecorderApp/SpeechRecorderApp/SharedKeys/SharedKeys.swift) - Add comprehensive documentation

---

## Development Checklist

### Phase 1: Basic Recording ✅

- [x] Create Xcode project with TCA dependencies
- [x] Define AudioRecorderClient dependency
- [x] Write tests for recording start/stop
- [x] Implement live AudioRecorder
- [x] Create basic RecordingView

### Phase 2: Speech Integration ✅

- [x] Define SpeechClient dependency
- [x] Write tests for transcription flow
- [x] Implement live SpeechClient with SpeechAnalyzer
- [x] Handle asset installation
- [x] Display live transcription

### Phase 3: Word Timestamps ✅

- [x] Write tests for word extraction
- [x] Implement word extraction from AttributedString
- [x] Store TimestampedWord array
- [x] Verify timing accuracy

### Phase 4: Persistence ✅

- [x] Define @Shared recordings key
- [x] Write tests for persistence
- [x] Implement RecordingsListFeature
- [x] Save audio files to documents
- [x] Create recordings list UI

### Phase 5: Synchronized Playback ✅

- [x] Define AudioPlayerClient dependency
- [x] Write tests for playback sync
- [x] Implement PlaybackFeature
- [x] Create word highlighting view
- [x] Add seek functionality

### Phase 6: State Sharing Improvements 🆕

- [ ] Add default value to SharedKey (6.1)
- [ ] Use IdentifiedArrayOf for recordings (6.2)
- [ ] Derive shared state for PlaybackFeature (6.3)
- [ ] Add type-safe keys for user settings (6.4)
- [ ] Implement delete with shared state access (6.5)

### Phase 7: Test Coverage Enhancement 🆕

- [ ] Add shared state mutation tests (7.1)
- [ ] Add delete with shared state access test (7.2)
- [ ] Add edit recording test (7.3)
- [ ] Add @MainActor to all test structs (7.4)
- [ ] Add delegate action tests (7.5)

### Phase 8: Code Quality & Cleanup 🆕

- [ ] Add Destination enum for navigation (8.1)
- [ ] Extract alert states to extensions (8.2)
- [ ] Add preview helpers with @Shared (8.3)
- [ ] Add UI testing setup (8.4)
- [ ] Document all shared keys (8.5)

---

## Reference Materials

### TCA Examples in Repository

| Example            | Path                                                                                                                                              | Key Patterns                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Voice Memos        | [`references/swift-composable-architecture/Examples/VoiceMemos/`](../references/swift-composable-architecture/Examples/VoiceMemos/)               | Audio recording, @Dependency, delegate pattern |
| Speech Recognition | [`references/swift-composable-architecture/Examples/SpeechRecognition/`](../references/swift-composable-architecture/Examples/SpeechRecognition/) | SpeechClient, AsyncThrowingStream, TestStore   |
| SyncUps            | [`references/swift-composable-architecture/Examples/SyncUps/`](../references/swift-composable-architecture/Examples/SyncUps/)                     | @Shared, navigation, testing patterns          |

### Apple Sample Code

| Sample         | Path                                                                                    | Key Patterns                                     |
| -------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------ |
| Speech-to-Text | [`references/apple-speech-to-text-sample/`](../references/apple-speech-to-text-sample/) | SpeechAnalyzer, SpeechTranscriber, AnalyzerInput |

### Documentation

| Topic               | Path                                                                                                                                                                    |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SpeechAnalyzer      | [`docs/apple/speech/.../speechanalyzer.md`](../docs/apple/speech/019b0605-a9aa-738b-912a-db8b12168304/developer.apple.com_documentation_speech_speechanalyzer.md)       |
| SpeechTranscriber   | [`docs/apple/speech/.../speechtranscriber.md`](../docs/apple/speech/019b0605-a9aa-738b-912a-db8b12168304/developer.apple.com_documentation_speech_speechtranscriber.md) |
| Swift Sharing       | [`references/swift-sharing/`](../references/swift-sharing/)                                                                                                             |
| Swift Dependencies  | [`references/swift-dependencies/`](../references/swift-dependencies/)                                                                                                   |
| State Sharing Guide | [`docs/swift-sharing-state-comprehensive-guide.md`](./swift-sharing-state-comprehensive-guide.md)                                                                       |

### Key Files to Study

1. **TCA SpeechClient Pattern**
   - [`Client.swift`](../references/swift-composable-architecture/Examples/SpeechRecognition/SpeechRecognition/SpeechClient/Client.swift) - Dependency definition
   - [`Live.swift`](../references/swift-composable-architecture/Examples/SpeechRecognition/SpeechRecognition/SpeechClient/Live.swift) - Live implementation
   - [`SpeechRecognitionTests.swift`](../references/swift-composable-architecture/Examples/SpeechRecognition/SpeechRecognitionTests/SpeechRecognitionTests.swift) - Test patterns

2. **Audio Recording Pattern**
   - [`RecordingMemo.swift`](../references/swift-composable-architecture/Examples/VoiceMemos/VoiceMemos/RecordingMemo.swift) - Recording reducer
   - [`VoiceMemos.swift`](../references/swift-composable-architecture/Examples/VoiceMemos/VoiceMemos/VoiceMemos.swift) - Parent feature

3. **New SpeechAnalyzer API**
   - [`Transcription.swift`](../references/apple-speech-to-text-sample/SwiftTranscriptionSampleApp/Recording%20and%20Transcription/Transcription.swift) - SpokenWordTranscriber
   - [`Recorder.swift`](../references/apple-speech-to-text-sample/SwiftTranscriptionSampleApp/Recording%20and%20Transcription/Recorder.swift) - Audio streaming

4. **Persistence Pattern**
   - [`FileStorageKey.swift`](../references/swift-sharing/Sources/Sharing/SharedKeys/FileStorageKey.swift) - @Shared file storage

5. **SyncUps Patterns (State Sharing)**
   - [`SyncUpsList.swift`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpsList.swift) - SharedKey with default, ForEach with derived state
   - [`SyncUpDetail.swift`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpDetail.swift) - Child with @Shared, delete via parent key
   - [`SyncUpsListTests.swift`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpsListTests.swift) - Testing shared state mutations
   - [`SyncUpDetailTests.swift`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpDetailTests.swift) - Testing delete with shared state

---

## Notes for Agents

1. **Always write tests first** - Use TestStore to define expected behavior before implementation
2. **Mock all dependencies** - Never use live implementations in tests
3. **Use exhaustive testing** - Call `store.finish()` to ensure all effects complete
4. **Reference existing patterns** - The TCA examples show battle-tested patterns
5. **Verify with code** - Run tests frequently to validate assumptions
6. **Check git status** - Ensure clean state before and after changes
7. **Follow SyncUps patterns** - The SyncUps example is the gold standard for @Shared usage
8. **Use `$0.$sharedValue.withLock`** - For asserting shared state mutations in tests
9. **Add @MainActor to test structs** - With `uncheckedUseMainSerialExecutor = true` in init
10. **Derive shared state for children** - Pass only what child features need
