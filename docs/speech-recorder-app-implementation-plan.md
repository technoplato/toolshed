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
4. [Phase 1: Project Setup & Basic Recording](#phase-1-project-setup--basic-recording)
5. [Phase 2: SpeechAnalyzer Integration](#phase-2-speechanalyzer-integration)
6. [Phase 3: Word-Level Timestamps](#phase-3-word-level-timestamps)
7. [Phase 4: Persistence with Swift Sharing](#phase-4-persistence-with-swift-sharing)
8. [Phase 5: Synchronized Playback](#phase-5-synchronized-playback)
9. [Reference Materials](#reference-materials)

---

## Project Overview

### Goals

1. **Record audio** with real-time transcription
2. **Display live transcription** with volatile (in-progress) and finalized text
3. **Store word-level timestamps** for each transcribed word
4. **Persist recordings** to disk with their transcriptions
5. **Synchronized playback** - highlight words as audio plays

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
│  │  @Shared(.fileStorage) var recordings: [Recording]       ││
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

## Phase 1: Project Setup & Basic Recording

### Goals

- Set up Xcode project with TCA dependencies
- Implement basic audio recording (no transcription yet)
- Create AudioRecorder dependency

### Tasks

#### 1.1 Create Xcode Project

```bash
# Create new iOS app project in Xcode
# Add Swift Package dependencies:
# - https://github.com/pointfreeco/swift-composable-architecture
# - https://github.com/pointfreeco/swift-sharing
# - https://github.com/pointfreeco/swift-dependencies
```

#### 1.2 Define AudioRecorder Dependency

**Test First:**

```swift
@Test
func testAudioRecorder_startsRecording() async throws {
    let recordingURL = URL(fileURLWithPath: "/tmp/test.m4a")
    var didStartRecording = false

    let store = TestStore(initialState: RecordingFeature.State()) {
        RecordingFeature()
    } withDependencies: {
        $0.audioRecorder.requestPermission = { true }
        $0.audioRecorder.startRecording = { url in
            didStartRecording = true
            XCTAssertEqual(url, recordingURL)
        }
        $0.temporaryDirectory = { URL(fileURLWithPath: "/tmp") }
        $0.uuid = .constant(UUID(uuidString: "00000000-0000-0000-0000-000000000000")!)
    }

    await store.send(.recordButtonTapped) {
        $0.isRecording = true
    }

    XCTAssertTrue(didStartRecording)
}
```

**Implementation:**

```swift
// AudioRecorderClient.swift
@DependencyClient
struct AudioRecorderClient {
    var requestPermission: @Sendable () async -> Bool = { false }
    var startRecording: @Sendable (URL) async throws -> Void
    var stopRecording: @Sendable () async -> Void
    var currentTime: @Sendable () async -> TimeInterval? = { nil }
}

extension AudioRecorderClient: DependencyKey {
    static var liveValue: Self {
        let recorder = AudioRecorder()
        return Self(
            requestPermission: { await recorder.requestPermission() },
            startRecording: { url in try await recorder.startRecording(url: url) },
            stopRecording: { await recorder.stopRecording() },
            currentTime: { await recorder.currentTime }
        )
    }
}

extension DependencyValues {
    var audioRecorder: AudioRecorderClient {
        get { self[AudioRecorderClient.self] }
        set { self[AudioRecorderClient.self] = newValue }
    }
}
```

#### 1.3 Implement Live AudioRecorder

Reference: [`VoiceMemos/RecordingMemo.swift`](../references/swift-composable-architecture/Examples/VoiceMemos/VoiceMemos/RecordingMemo.swift)

```swift
private actor AudioRecorder {
    var audioEngine: AVAudioEngine?
    var audioFile: AVAudioFile?

    func requestPermission() async -> Bool {
        await withCheckedContinuation { continuation in
            AVAudioApplication.requestRecordPermission { granted in
                continuation.resume(returning: granted)
            }
        }
    }

    func startRecording(url: URL) async throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playAndRecord, mode: .spokenAudio)
        try audioSession.setActive(true)

        audioEngine = AVAudioEngine()
        guard let audioEngine else { throw RecordingError.engineNotAvailable }

        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)

        audioFile = try AVAudioFile(forWriting: url, settings: format.settings)

        inputNode.installTap(onBus: 0, bufferSize: 4096, format: format) { [weak self] buffer, _ in
            try? self?.audioFile?.write(from: buffer)
        }

        audioEngine.prepare()
        try audioEngine.start()
    }

    func stopRecording() {
        audioEngine?.stop()
        audioEngine?.inputNode.removeTap(onBus: 0)
        audioEngine = nil
        audioFile = nil
    }
}
```

---

## Phase 2: SpeechAnalyzer Integration

### Goals

- Create SpeechClient dependency wrapping SpeechAnalyzer
- Integrate live transcription with recording
- Handle asset installation for locale-specific models

### Key Concepts from Apple's SpeechAnalyzer API

From the [SpeechAnalyzer documentation](../docs/apple/speech/019b0605-a9aa-738b-912a-db8b12168304/developer.apple.com_documentation_speech_speechanalyzer.md):

1. **Modules**: `SpeechTranscriber` performs speech-to-text
2. **Input**: `AnalyzerInput` wraps `AVAudioPCMBuffer`
3. **Results**: `AsyncSequence` of `SpeechTranscriber.Result`
4. **Assets**: `AssetInventory` manages locale-specific model downloads

### Tasks

#### 2.1 Define SpeechClient Dependency

**Test First:**

```swift
@Test
func testSpeechClient_transcribesAudio() async {
    let transcriptionStream = AsyncThrowingStream<TranscriptionUpdate, Error>.makeStream()

    let store = TestStore(initialState: RecordingFeature.State()) {
        RecordingFeature()
    } withDependencies: {
        $0.speechClient.requestAuthorization = { .authorized }
        $0.speechClient.startTranscription = { _ in transcriptionStream.stream }
        $0.speechClient.finishTranscription = { transcriptionStream.continuation.finish() }
    }

    await store.send(.recordButtonTapped) {
        $0.isRecording = true
    }

    // Simulate transcription result
    transcriptionStream.continuation.yield(.init(
        text: "Hello",
        words: [.init(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: 0.95)],
        isFinal: false
    ))

    await store.receive(\.transcriptionResult.success) {
        $0.transcription.text = "Hello"
        $0.transcription.words = [.init(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: 0.95)]
    }
}
```

**Implementation:**

```swift
// SpeechClient.swift
struct TranscriptionUpdate: Equatable, Sendable {
    var text: String
    var words: [TimestampedWord]
    var isFinal: Bool
}

@DependencyClient
struct SpeechClient {
    var requestAuthorization: @Sendable () async -> SFSpeechRecognizerAuthorizationStatus = { .notDetermined }
    var checkAvailability: @Sendable () async -> Bool = { false }
    var ensureAssets: @Sendable (Locale) async throws -> Void
    var startTranscription: @Sendable (Locale) async throws -> AsyncThrowingStream<TranscriptionUpdate, Error>
    var streamAudio: @Sendable (AVAudioPCMBuffer) async throws -> Void
    var finishTranscription: @Sendable () async throws -> Void

    enum Failure: Error, Equatable {
        case notAuthorized
        case notAvailable
        case assetInstallationFailed
        case transcriptionFailed
    }
}

extension SpeechClient: TestDependencyKey {
    static var previewValue: Self {
        Self(
            requestAuthorization: { .authorized },
            checkAvailability: { true },
            ensureAssets: { _ in },
            startTranscription: { _ in
                AsyncThrowingStream { continuation in
                    // Simulate streaming transcription
                    Task {
                        try await Task.sleep(for: .milliseconds(500))
                        continuation.yield(.init(text: "Hello", words: [], isFinal: false))
                        try await Task.sleep(for: .milliseconds(500))
                        continuation.yield(.init(text: "Hello world", words: [], isFinal: true))
                        continuation.finish()
                    }
                }
            },
            streamAudio: { _ in },
            finishTranscription: { }
        )
    }

    static var testValue: Self {
        Self()
    }
}

extension DependencyValues {
    var speechClient: SpeechClient {
        get { self[SpeechClient.self] }
        set { self[SpeechClient.self] = newValue }
    }
}
```

#### 2.2 Implement Live SpeechClient

Reference: [Apple's Transcription.swift](../references/apple-speech-to-text-sample/SwiftTranscriptionSampleApp/Recording%20and%20Transcription/Transcription.swift)

```swift
extension SpeechClient: DependencyKey {
    static var liveValue: Self {
        let speech = Speech()
        return Self(
            requestAuthorization: {
                await withCheckedContinuation { continuation in
                    SFSpeechRecognizer.requestAuthorization { status in
                        continuation.resume(returning: status)
                    }
                }
            },
            checkAvailability: {
                await SpeechTranscriber.isAvailable
            },
            ensureAssets: { locale in
                await speech.ensureAssets(for: locale)
            },
            startTranscription: { locale in
                try await speech.startTranscription(locale: locale)
            },
            streamAudio: { buffer in
                await speech.streamAudio(buffer)
            },
            finishTranscription: {
                try await speech.finishTranscription()
            }
        )
    }
}

private actor Speech {
    private var transcriber: SpeechTranscriber?
    private var analyzer: SpeechAnalyzer?
    private var inputBuilder: AsyncStream<AnalyzerInput>.Continuation?
    private var analyzerFormat: AVAudioFormat?
    private var converter: BufferConverter?

    func ensureAssets(for locale: Locale) async throws {
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            throw SpeechClient.Failure.notAvailable
        }

        let transcriber = SpeechTranscriber(
            locale: supportedLocale,
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )

        if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
            try await request.downloadAndInstall()
        }
    }

    func startTranscription(locale: Locale) async throws -> AsyncThrowingStream<TranscriptionUpdate, Error> {
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            throw SpeechClient.Failure.notAvailable
        }

        transcriber = SpeechTranscriber(
            locale: supportedLocale,
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )

        guard let transcriber else {
            throw SpeechClient.Failure.transcriptionFailed
        }

        analyzer = SpeechAnalyzer(modules: [transcriber])
        analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber])
        converter = BufferConverter()

        let (inputSequence, inputBuilder) = AsyncStream<AnalyzerInput>.makeStream()
        self.inputBuilder = inputBuilder

        // Start analysis in background
        Task {
            try await analyzer?.start(inputSequence: inputSequence)
        }

        // Return stream of transcription results
        return AsyncThrowingStream { continuation in
            Task {
                do {
                    for try await result in transcriber.results {
                        let update = TranscriptionUpdate(
                            text: String(result.text.characters),
                            words: extractWords(from: result),
                            isFinal: result.isFinal
                        )
                        continuation.yield(update)
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

    func streamAudio(_ buffer: AVAudioPCMBuffer) {
        guard let analyzerFormat, let converter, let inputBuilder else { return }

        do {
            let converted = try converter.convertBuffer(buffer, to: analyzerFormat)
            let input = AnalyzerInput(buffer: converted)
            inputBuilder.yield(input)
        } catch {
            print("Buffer conversion failed: \(error)")
        }
    }

    func finishTranscription() async throws {
        inputBuilder?.finish()
        try await analyzer?.finalizeAndFinishThroughEndOfInput()
        transcriber = nil
        analyzer = nil
    }

    private func extractWords(from result: SpeechTranscriber.Result) -> [TimestampedWord] {
        // Extract word-level timing from AttributedString
        var words: [TimestampedWord] = []
        let text = result.text

        for run in text.runs {
            if let timeRange = run.audioTimeRange {
                let word = String(text[run.range].characters)
                words.append(TimestampedWord(
                    text: word,
                    startTime: timeRange.start.seconds,
                    endTime: timeRange.end.seconds,
                    confidence: nil
                ))
            }
        }

        return words
    }
}
```

---

## Phase 3: Word-Level Timestamps

### Goals

- Extract word-level timing from SpeechTranscriber.Result
- Store timestamps with each word
- Enable synchronized playback preparation

### Key Insight: AttributedString with audioTimeRange

The `SpeechTranscriber.Result.text` is an `AttributedString` that can contain `audioTimeRange` attributes when configured with `.audioTimeRange` in `attributeOptions`.

```swift
// From SpeechTranscriber initialization
let transcriber = SpeechTranscriber(
    locale: locale,
    transcriptionOptions: [],
    reportingOptions: [.volatileResults],
    attributeOptions: [.audioTimeRange]  // <-- This enables word-level timing
)
```

### Tasks

#### 3.1 Test Word Extraction

```swift
@Test
func testWordExtraction_extractsTimestamps() async {
    var receivedWords: [TimestampedWord] = []

    let store = TestStore(initialState: RecordingFeature.State()) {
        RecordingFeature()
    } withDependencies: {
        $0.speechClient.startTranscription = { _ in
            AsyncThrowingStream { continuation in
                continuation.yield(.init(
                    text: "Hello world",
                    words: [
                        .init(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: 0.95),
                        .init(text: "world", startTime: 0.6, endTime: 1.0, confidence: 0.92)
                    ],
                    isFinal: true
                ))
                continuation.finish()
            }
        }
    }

    await store.send(.recordButtonTapped)

    await store.receive(\.transcriptionResult.success) {
        $0.transcription.words.count == 2
        $0.transcription.words[0].startTime == 0.0
        $0.transcription.words[1].startTime == 0.6
    }
}
```

#### 3.2 Implement Word Extraction

```swift
private func extractWords(from result: SpeechTranscriber.Result) -> [TimestampedWord] {
    var words: [TimestampedWord] = []
    let text = result.text

    // Iterate through runs in the AttributedString
    for run in text.runs {
        // Check if this run has timing information
        if let timeRange = run.audioTimeRange {
            let wordText = String(text[run.range].characters).trimmingCharacters(in: .whitespaces)

            // Skip empty strings
            guard !wordText.isEmpty else { continue }

            words.append(TimestampedWord(
                text: wordText,
                startTime: timeRange.start.seconds,
                endTime: timeRange.end.seconds,
                confidence: nil  // Confidence not available in new API
            ))
        }
    }

    return words
}
```

---

## Phase 4: Persistence with Swift Sharing

### Goals

- Persist recordings list using @Shared
- Save audio files to documents directory
- Store transcriptions as JSON

### Key Concepts from Swift Sharing

From [FileStorageKey.swift](../references/swift-sharing/Sources/Sharing/SharedKeys/FileStorageKey.swift):

```swift
// Basic usage
@Shared(.fileStorage(.documentsDirectory.appending(component: "recordings.json")))
var recordings: [Recording] = []
```

### Tasks

#### 4.1 Define Shared State

```swift
// SharedKeys.swift
extension SharedReaderKey where Self == FileStorageKey<[Recording]> {
    static var recordings: Self {
        .fileStorage(.documentsDirectory.appending(component: "recordings.json"))
    }
}
```

#### 4.2 Test Persistence

```swift
@Test
func testRecordingPersistence_savesToDisk() async {
    let fileSystem = LockIsolated<[URL: Data]>([:])

    let store = TestStore(initialState: RecordingsListFeature.State()) {
        RecordingsListFeature()
    } withDependencies: {
        $0.defaultFileStorage = .inMemory(fileSystem: fileSystem)
    }

    let recording = Recording(
        id: UUID(),
        title: "Test Recording",
        date: Date(),
        duration: 10.0,
        audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
        transcription: .init(text: "Hello world", words: [], isFinal: true)
    )

    await store.send(.addRecording(recording)) {
        $0.recordings.append(recording)
    }

    // Verify file was written
    XCTAssertFalse(fileSystem.value.isEmpty)
}
```

#### 4.3 Implement RecordingsListFeature

```swift
@Reducer
struct RecordingsListFeature {
    @ObservableState
    struct State: Equatable {
        @Shared(.recordings) var recordings: [Recording] = []
        @Presents var recording: RecordingFeature.State?
        @Presents var playback: PlaybackFeature.State?
    }

    enum Action: Sendable {
        case addRecording(Recording)
        case deleteRecording(IndexSet)
        case recordButtonTapped
        case recording(PresentationAction<RecordingFeature.Action>)
        case playback(PresentationAction<PlaybackFeature.Action>)
        case selectRecording(Recording)
    }

    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case let .addRecording(recording):
                state.$recordings.withLock { $0.append(recording) }
                return .none

            case let .deleteRecording(indexSet):
                state.$recordings.withLock { $0.remove(atOffsets: indexSet) }
                return .none

            case .recordButtonTapped:
                state.recording = RecordingFeature.State()
                return .none

            case .recording(.presented(.delegate(.didFinish(.success(let recording))))):
                state.recording = nil
                state.$recordings.withLock { $0.insert(recording, at: 0) }
                return .none

            case .recording(.presented(.delegate(.didFinish(.failure)))):
                state.recording = nil
                return .none

            case let .selectRecording(recording):
                state.playback = PlaybackFeature.State(recording: recording)
                return .none

            case .recording, .playback:
                return .none
            }
        }
        .ifLet(\.$recording, action: \.recording) {
            RecordingFeature()
        }
        .ifLet(\.$playback, action: \.playback) {
            PlaybackFeature()
        }
    }
}
```

---

## Phase 5: Synchronized Playback

### Goals

- Play audio with word highlighting
- Sync current playback position with transcription
- Highlight current word based on timestamps

### Tasks

#### 5.1 Define PlaybackFeature

```swift
@Reducer
struct PlaybackFeature {
    @ObservableState
    struct State: Equatable {
        var recording: Recording
        var isPlaying = false
        var currentTime: TimeInterval = 0
        var currentWordIndex: Int?

        var currentWord: TimestampedWord? {
            guard let index = currentWordIndex else { return nil }
            return recording.transcription.words[safe: index]
        }
    }

    enum Action: Sendable {
        case playButtonTapped
        case pauseButtonTapped
        case seekTo(TimeInterval)
        case timeUpdated(TimeInterval)
        case playbackFinished
    }

    @Dependency(\.audioPlayer) var audioPlayer
    @Dependency(\.continuousClock) var clock

    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case .playButtonTapped:
                state.isPlaying = true
                return .run { [url = state.recording.audioURL] send in
                    try await audioPlayer.play(url)

                    // Update time periodically
                    for await _ in clock.timer(interval: .milliseconds(50)) {
                        if let time = await audioPlayer.currentTime() {
                            await send(.timeUpdated(time))
                        }
                    }
                }

            case .pauseButtonTapped:
                state.isPlaying = false
                return .run { _ in
                    await audioPlayer.pause()
                }

            case let .seekTo(time):
                state.currentTime = time
                return .run { _ in
                    await audioPlayer.seek(to: time)
                }

            case let .timeUpdated(time):
                state.currentTime = time
                state.currentWordIndex = findWordIndex(at: time, in: state.recording.transcription.words)
                return .none

            case .playbackFinished:
                state.isPlaying = false
                state.currentTime = 0
                state.currentWordIndex = nil
                return .none
            }
        }
    }

    private func findWordIndex(at time: TimeInterval, in words: [TimestampedWord]) -> Int? {
        words.firstIndex { word in
            time >= word.startTime && time < word.endTime
        }
    }
}
```

#### 5.2 Test Synchronized Playback

```swift
@Test
func testPlayback_highlightsCurrentWord() async {
    let recording = Recording(
        id: UUID(),
        title: "Test",
        date: Date(),
        duration: 2.0,
        audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
        transcription: .init(
            text: "Hello world",
            words: [
                .init(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: nil),
                .init(text: "world", startTime: 0.6, endTime: 1.0, confidence: nil)
            ],
            isFinal: true
        )
    )

    let clock = TestClock()

    let store = TestStore(initialState: PlaybackFeature.State(recording: recording)) {
        PlaybackFeature()
    } withDependencies: {
        $0.audioPlayer.play = { _ in }
        $0.audioPlayer.currentTime = { 0.3 }
        $0.continuousClock = clock
    }

    await store.send(.playButtonTapped) {
        $0.isPlaying = true
    }

    await clock.advance(by: .milliseconds(50))

    await store.receive(\.timeUpdated) {
        $0.currentTime = 0.3
        $0.currentWordIndex = 0  // "Hello" is at index 0
    }
}
```

#### 5.3 Implement PlaybackView

```swift
struct PlaybackView: View {
    @Bindable var store: StoreOf<PlaybackFeature>

    var body: some View {
        VStack(spacing: 20) {
            // Transcription with word highlighting
            TranscriptionTextView(
                words: store.recording.transcription.words,
                currentWordIndex: store.currentWordIndex
            )

            // Playback controls
            HStack {
                Button {
                    if store.isPlaying {
                        store.send(.pauseButtonTapped)
                    } else {
                        store.send(.playButtonTapped)
                    }
                } label: {
                    Image(systemName: store.isPlaying ? "pause.fill" : "play.fill")
                        .font(.largeTitle)
                }

                // Progress slider
                Slider(
                    value: Binding(
                        get: { store.currentTime },
                        set: { store.send(.seekTo($0)) }
                    ),
                    in: 0...store.recording.duration
                )
            }
            .padding()
        }
    }
}

struct TranscriptionTextView: View {
    let words: [TimestampedWord]
    let currentWordIndex: Int?

    var body: some View {
        Text(attributedText)
            .font(.body)
            .padding()
    }

    private var attributedText: AttributedString {
        var result = AttributedString()

        for (index, word) in words.enumerated() {
            var wordString = AttributedString(word.text + " ")

            if index == currentWordIndex {
                wordString.backgroundColor = .yellow
                wordString.font = .body.bold()
            }

            result.append(wordString)
        }

        return result
    }
}
```

---

## Reference Materials

### TCA Examples in Repository

| Example            | Path                                                                                                                                              | Key Patterns                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Voice Memos        | [`references/swift-composable-architecture/Examples/VoiceMemos/`](../references/swift-composable-architecture/Examples/VoiceMemos/)               | Audio recording, @Dependency, delegate pattern |
| Speech Recognition | [`references/swift-composable-architecture/Examples/SpeechRecognition/`](../references/swift-composable-architecture/Examples/SpeechRecognition/) | SpeechClient, AsyncThrowingStream, TestStore   |

### Apple Sample Code

| Sample         | Path                                                                                    | Key Patterns                                     |
| -------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------ |
| Speech-to-Text | [`references/apple-speech-to-text-sample/`](../references/apple-speech-to-text-sample/) | SpeechAnalyzer, SpeechTranscriber, AnalyzerInput |

### Documentation

| Topic              | Path                                                                                                                                                                    |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SpeechAnalyzer     | [`docs/apple/speech/.../speechanalyzer.md`](../docs/apple/speech/019b0605-a9aa-738b-912a-db8b12168304/developer.apple.com_documentation_speech_speechanalyzer.md)       |
| SpeechTranscriber  | [`docs/apple/speech/.../speechtranscriber.md`](../docs/apple/speech/019b0605-a9aa-738b-912a-db8b12168304/developer.apple.com_documentation_speech_speechtranscriber.md) |
| Swift Sharing      | [`references/swift-sharing/`](../references/swift-sharing/)                                                                                                             |
| Swift Dependencies | [`references/swift-dependencies/`](../references/swift-dependencies/)                                                                                                   |

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

---

## Development Checklist

### Phase 1: Basic Recording

- [ ] Create Xcode project with TCA dependencies
- [ ] Define AudioRecorderClient dependency
- [ ] Write tests for recording start/stop
- [ ] Implement live AudioRecorder
- [ ] Create basic RecordingView

### Phase 2: Speech Integration

- [ ] Define SpeechClient dependency
- [ ] Write tests for transcription flow
- [ ] Implement live SpeechClient with SpeechAnalyzer
- [ ] Handle asset installation
- [ ] Display live transcription

### Phase 3: Word Timestamps

- [ ] Write tests for word extraction
- [ ] Implement word extraction from AttributedString
- [ ] Store TimestampedWord array
- [ ] Verify timing accuracy

### Phase 4: Persistence

- [ ] Define @Shared recordings key
- [ ] Write tests for persistence
- [ ] Implement RecordingsListFeature
- [ ] Save audio files to documents
- [ ] Create recordings list UI

### Phase 5: Synchronized Playback

- [ ] Define AudioPlayerClient dependency
- [ ] Write tests for playback sync
- [ ] Implement PlaybackFeature
- [ ] Create word highlighting view
- [ ] Add seek functionality

---

## Notes for Agents

1. **Always write tests first** - Use TestStore to define expected behavior before implementation
2. **Mock all dependencies** - Never use live implementations in tests
3. **Use exhaustive testing** - Call `store.finish()` to ensure all effects complete
4. **Reference existing patterns** - The TCA examples show battle-tested patterns
5. **Verify with code** - Run tests frequently to validate assumptions
6. **Check git status** - Ensure clean state before and after changes
