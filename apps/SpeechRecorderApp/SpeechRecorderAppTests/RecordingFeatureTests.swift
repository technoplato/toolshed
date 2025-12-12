/**
 HOW:
   Run tests with: `xcodebuild test -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 17'`
   Or use SweetPad: `sweetpad.build.test`
   
   [Inputs]
   - None (unit tests)
   
   [Outputs]
   - Test results
   
   [Side Effects]
   - None (uses mocked dependencies)

 WHO:
   AI Agent, Developer
   (Context: TDD for RecordingFeature reducer)

 WHAT:
   Unit tests for the RecordingFeature reducer.
   Tests recording flow, permission handling, and state transitions.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/RecordingFeatureTests.swift

 WHY:
   TDD approach - write tests first to define expected behavior.
   These tests verify the RecordingFeature reducer handles all
   recording states and actions correctly.
 */

import ComposableArchitecture
import Foundation
import Testing
@testable import SpeechRecorderApp

@Suite("RecordingFeature Tests")
@MainActor
struct RecordingFeatureTests {
    
    @Test("Record button tapped starts recording when permission granted")
    func recordButtonTappedStartsRecording() async {
        let testDate = Date(timeIntervalSince1970: 0)
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000000")!
        
        let store = await TestStore(initialState: RecordingFeature.State()) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.requestRecordPermission = { true }
            $0.audioRecorder.startRecording = { _ in AsyncStream { _ in } }
            $0.audioRecorder.currentTime = { nil }
            $0.audioRecorder.audioLevelStream = { AsyncStream { $0.finish() } }
            $0.speechClient.requestAuthorization = { .authorized }
            $0.speechClient.isAssetInstalled = { _ in true }
            $0.speechClient.startTranscription = { _ in AsyncThrowingStream { _ in } }
            $0.speechClient.finishTranscription = { }
            $0.photoLibrary.requestAuthorization = { .authorized }
            $0.photoLibrary.observeNewPhotos = { AsyncStream { _ in } }
            $0.photoLibrary.stopObserving = { }
            $0.date.now = testDate
            $0.uuid = .constant(testUUID)
            $0.continuousClock = ImmediateClock()
        }
        
        /// Mark as non-exhaustive since we're just testing the immediate state change
        /// The recording and timer effects will run in the background
        store.exhaustivity = .off
        
        await store.send(.recordButtonTapped) {
            $0.isRecording = true
            $0.recordingStartTime = testDate
            $0.mode = .recording
            /// volatileTranscription is now a computed property from liveTranscription
            /// The liveTranscription is reset via $liveTranscription.withLock in the reducer
            $0.transcription = .empty
            $0.speechError = nil
            $0.capturedMedia = []
            $0.mediaThumbnails = [:]
            $0.recordingURL = URL(fileURLWithPath: NSTemporaryDirectory())
                .appendingPathComponent(testUUID.uuidString)
                .appendingPathExtension("m4a")
            $0.title = formatHumanReadableDate(testDate)
        }
        
        await store.receive(\.speechAuthorizationResponse) {
            $0.speechAuthorizationStatus = SpeechClient.AuthorizationStatus.authorized
        }
        
        await store.receive(\.photoLibraryAuthorizationResponse) {
            $0.photoLibraryAuthorizationStatus = PhotoLibraryClient.AuthorizationStatus.authorized
        }
        
        await store.receive(\.permissionResponse) {
            $0.hasPermission = true
        }
    }
    
    @Test("Record button tapped shows alert when permission denied")
    func recordButtonTappedShowsAlertWhenDenied() async {
        let testDate = Date(timeIntervalSince1970: 0)
        
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000000")!
        
        let store = await TestStore(initialState: RecordingFeature.State()) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.requestRecordPermission = { false }
            $0.speechClient.requestAuthorization = { .denied }
            $0.photoLibrary.requestAuthorization = { .denied }
            $0.date.now = testDate
            $0.uuid = .constant(testUUID)
            $0.continuousClock = ImmediateClock()
        }
        
        await store.send(.recordButtonTapped) {
            $0.isRecording = true
            $0.recordingStartTime = testDate
            $0.mode = .recording
            /// volatileTranscription is now a computed property from liveTranscription
            /// The liveTranscription is reset via $liveTranscription.withLock in the reducer
            $0.transcription = .empty
            $0.speechError = nil
            $0.capturedMedia = []
            $0.mediaThumbnails = [:]
            $0.recordingURL = URL(fileURLWithPath: NSTemporaryDirectory())
                .appendingPathComponent(testUUID.uuidString)
                .appendingPathExtension("m4a")
            $0.title = formatHumanReadableDate(testDate)
        }
        
        await store.receive(\.speechAuthorizationResponse) {
            $0.speechAuthorizationStatus = SpeechClient.AuthorizationStatus.denied
        }
        
        await store.receive(\.photoLibraryAuthorizationResponse) {
            $0.photoLibraryAuthorizationStatus = PhotoLibraryClient.AuthorizationStatus.denied
        }
        
        await store.receive(\.permissionResponse) {
            $0.isRecording = false
            $0.recordingStartTime = nil
            $0.mode = .idle
            $0.hasPermission = false
            $0.title = ""
            $0.alert = AlertState {
                TextState("Permission Required")
            } message: {
                TextState("Microphone access is required to record audio.")
            }
        }
    }
    
    @Test("Stop button tapped stops recording")
    func stopButtonTappedStopsRecording() async {
        let testDate = Date(timeIntervalSince1970: 0)
        let testDuration: TimeInterval = 5.0
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000000")!
        let testURL = URL(fileURLWithPath: "/tmp/test.m4a")
        
        var state = RecordingFeature.State()
        state.isRecording = true
        state.recordingStartTime = testDate
        state.hasPermission = true
        state.recordingURL = testURL
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.stopRecording = { }
            $0.audioRecorder.currentTime = { testDuration }
            $0.speechClient.finishTranscription = { }
            $0.photoLibrary.stopObserving = { }
            $0.uuid = .constant(testUUID)
        }
        
        await store.send(.stopButtonTapped) {
            $0.mode = .encoding
        }
        
        await store.receive(\.finalRecordingTime) {
            $0.duration = testDuration
        }
        
        await store.receive(\.recordingStopped) {
            $0.isRecording = false
            $0.mode = .idle
        }
        
        await store.receive(\.delegate)
    }
    
    @Test("Timer updates duration while recording")
    func timerUpdatesDuration() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        await store.send(.timerTicked) {
            $0.duration += 1
        }
        
        await store.send(.timerTicked) {
            $0.duration += 1
        }
    }
    
    @Test("Cancel button resets state")
    func cancelButtonResetsState() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.duration = 5.0
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.stopRecording = { }
            $0.speechClient.finishTranscription = { }
            $0.photoLibrary.stopObserving = { }
        }
        
        /// Use non-exhaustive testing since shared state changes are complex
        store.exhaustivity = .off
        
        await store.send(.cancelButtonTapped) {
            $0.isRecording = false
            $0.duration = 0
            $0.mode = .idle
            /// volatileTranscription is now a computed property - it will be "" after reset
            $0.transcription = .empty
            $0.capturedMedia = []
            $0.mediaThumbnails = [:]
        }
    }
    
    @Test("Alert dismissed clears alert state")
    func alertDismissedClearsState() async {
        var state = RecordingFeature.State()
        state.alert = AlertState {
            TextState("Test Alert")
        }
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        await store.send(.alert(.dismiss)) {
            $0.alert = nil
        }
    }
    
    @Test("Transcription result updates volatile transcription")
    func transcriptionResultUpdatesVolatileTranscription() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        /// Use non-exhaustive testing since shared state changes are complex
        store.exhaustivity = .off
        
        let result = TranscriptionResult(
            text: "Hello world",
            words: [
                TimestampedWord(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: nil),
                TimestampedWord(text: "world", startTime: 0.5, endTime: 1.0, confidence: nil)
            ],
            isFinal: false
        )
        
        await store.send(.transcriptionResult(result))
        
        /// Verify the shared state was updated by checking the store's state
        #expect(store.state.volatileTranscription == "Hello world")
    }
    
    @Test("Final transcription result updates transcription")
    func finalTranscriptionResultUpdatesTranscription() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        /// Use non-exhaustive testing since TranscriptionSegment has auto-generated UUIDs
        store.exhaustivity = .off
        
        let words = [
            TimestampedWord(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: nil),
            TimestampedWord(text: "world", startTime: 0.5, endTime: 1.0, confidence: nil)
        ]
        
        let result = TranscriptionResult(
            text: "Hello world",
            words: words,
            isFinal: true
        )
        
        await store.send(.transcriptionResult(result))
        
        /// Verify the final state after the action
        #expect(store.state.volatileTranscription == "")
        #expect(store.state.finalizedText == "Hello world")
        #expect(store.state.finalizedWords == words)
        #expect(store.state.finalizedSegments.count == 1)
        #expect(store.state.finalizedSegments.first?.text == "Hello world")
        #expect(store.state.finalizedSegments.first?.words == words)
        #expect(store.state.transcription.text == "Hello world")
        #expect(store.state.transcription.words == words)
        #expect(store.state.transcription.segments.count == 1)
        #expect(store.state.transcription.isFinal == true)
    }
    
    @Test("Transcription failure sets error message")
    func transcriptionFailureSetsError() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        let error = SpeechClient.Failure.localeNotSupported
        
        await store.send(.transcriptionFailed(error)) {
            $0.speechError = error.localizedDescription
        }
    }
    
    @Test("Assets download started sets downloading flag")
    func assetsDownloadStartedSetsFlag() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        await store.send(.assetsDownloadStarted) {
            $0.isDownloadingAssets = true
        }
    }
    
    @Test("Assets download completed clears downloading flag")
    func assetsDownloadCompletedClearsFlag() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.isDownloadingAssets = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.speechClient.isAssetInstalled = { _ in true }
            $0.speechClient.startTranscription = { _ in AsyncThrowingStream { _ in } }
        }
        
        store.exhaustivity = .off
        
        await store.send(.assetsDownloadCompleted) {
            $0.isDownloadingAssets = false
        }
    }
    
    @Test("Pause button pauses recording")
    func pauseButtonPausesRecording() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.mode = .recording
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.pauseRecording = { }
        }
        
        await store.send(.pauseButtonTapped) {
            $0.isPaused = true
            $0.mode = .paused
        }
    }
    
    @Test("Resume button resumes recording")
    func resumeButtonResumesRecording() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.isPaused = true
        state.mode = .paused
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.resumeRecording = { }
        }
        
        await store.send(.resumeButtonTapped) {
            $0.isPaused = false
            $0.mode = .recording
        }
    }
    
    @Test("Timer does not increment duration when paused")
    func timerDoesNotIncrementWhenPaused() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.isPaused = true
        state.duration = 10
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        /// Duration should not change when paused
        await store.send(.timerTicked)
        
        /// Verify duration is still 10
        #expect(store.state.duration == 10)
    }
    
    @Test("Pause button does nothing when not recording")
    func pauseButtonDoesNothingWhenNotRecording() async {
        let state = RecordingFeature.State()
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        /// Should not change state when not recording
        await store.send(.pauseButtonTapped)
    }
    
    @Test("Resume button does nothing when not paused")
    func resumeButtonDoesNothingWhenNotPaused() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.isPaused = false
        state.mode = .recording
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        /// Should not change state when not paused
        await store.send(.resumeButtonTapped)
    }
    
    // MARK: - Auto-scroll Tests
    
    @Test("User scroll disables auto-scroll")
    func userScrollDisablesAutoScroll() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.isAutoScrollEnabled = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        await store.send(.userDidScroll) {
            $0.isAutoScrollEnabled = false
        }
    }
    
    @Test("Resume auto-scroll button re-enables auto-scroll")
    func resumeAutoScrollButtonReEnablesAutoScroll() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.isAutoScrollEnabled = false
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        await store.send(.resumeAutoScrollTapped) {
            $0.isAutoScrollEnabled = true
        }
    }
    
    @Test("Auto-scroll is enabled by default")
    func autoScrollIsEnabledByDefault() async {
        let state = RecordingFeature.State()
        
        #expect(state.isAutoScrollEnabled == true)
    }
    
    @Test("User scroll does nothing when auto-scroll already disabled")
    func userScrollDoesNothingWhenAlreadyDisabled() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.isAutoScrollEnabled = false
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        /// Should not change state when already disabled
        await store.send(.userDidScroll)
    }
    
    @Test("Resume auto-scroll does nothing when already enabled")
    func resumeAutoScrollDoesNothingWhenAlreadyEnabled() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.isAutoScrollEnabled = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        /// Should not change state when already enabled
        await store.send(.resumeAutoScrollTapped)
    }
}