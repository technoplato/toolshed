/**
 HOW:
   Run tests with: `xcodebuild test -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 17'`
   Or run specific test: `xcodebuild test -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 17' -only-testing:SpeechRecorderAppTests/MinimizedRecordingBugTests`
   
   [Inputs]
   - None (unit tests)
   
   [Outputs]
   - Test results
   
   [Side Effects]
   - None (uses mocked dependencies)

 WHO:
   AI Agent, Developer
   (Context: Bug reproduction tests for minimized recording issues)

 WHAT:
   Failing tests that reproduce bugs found after TCA refactoring:
   
   1. Timer/transcription delay bug: When minimizing the recording view,
      the timer gets stuck and transcription updates are delayed when
      reopening the recording screen.
      
   2. Live recording view not showing: The active recording row doesn't
      appear in the recordings list because RecordingsListFeature uses
      @Shared(.activeRecording) which is a Recording? type, but AppFeature
      uses activeRecording: RecordingFeature.State? which is a different type.

 WHEN:
   Created: 2025-12-12
   Last Modified: 2025-12-12

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/MinimizedRecordingBugTests.swift

 WHY:
   TDD approach - write failing tests first to reproduce the bugs,
   then fix the code to make the tests pass.
   
   These tests verify:
   1. Timer continues to tick when recording is minimized
   2. Transcription updates are received when recording is minimized
   3. Active recording is visible in RecordingsListFeature.State
 */

import ComposableArchitecture
import Foundation
import Sharing
import Testing
@testable import SpeechRecorderApp

@Suite("Minimized Recording Bug Tests")
@MainActor
struct MinimizedRecordingBugTests {
    
    init() { uncheckedUseMainSerialExecutor = true }
    
    // MARK: - Bug 1: Timer/Transcription Delay When Minimized
    
    /**
     Test that timer continues to tick when recording is minimized.
     
     **Bug Description:**
     When the user starts a recording and then collapses/minimizes the recording view,
     the timer gets stuck. When they reopen the recording screen, there's a delay
     before new transcribed text appears.
     
     **Expected Behavior:**
     Timer should continue ticking via activeRecording actions even when destination is nil.
     
     **Root Cause Hypothesis:**
     The timer effect is tied to the destination presentation, so when destination
     becomes nil (minimized), the timer effect may be cancelled.
     */
    @Test("Timer continues ticking when recording is minimized")
    func timerContinuesWhenMinimized() async {
        let testClock = TestClock()
        
        var state = AppFeature.State()
        state.activeRecording = RecordingFeature.State()
        state.activeRecording?.isRecording = true
        state.activeRecording?.hasPermission = true
        state.activeRecording?.duration = 5
        
        /// Start with recording expanded
        state.isRecordingExpanded = true
        
        let store = TestStore(initialState: state) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
            $0.continuousClock = testClock
        }
        
        /// Minimize the recording
        await store.send(.minimizeRecording) {
            /// isRecordingExpanded becomes false
            $0.isRecordingExpanded = false
        }
        
        /// Verify activeRecording still exists
        #expect(store.state.activeRecording != nil)
        #expect(store.state.hasActiveRecording == true)
        
        /// Send timer tick while minimized - this should still work
        await store.send(.activeRecording(.timerTicked)) {
            $0.activeRecording?.duration = 6
        }
        
        /// Send another timer tick
        await store.send(.activeRecording(.timerTicked)) {
            $0.activeRecording?.duration = 7
        }
        
        /// Verify duration increased
        #expect(store.state.activeRecording?.duration == 7)
    }
    
    /**
     Test that transcription updates are received when recording is minimized.
     
     **Bug Description:**
     When the recording view is minimized, transcription updates stop being
     reflected in the state. When reopening, there's a delay before new text appears.
     
     **Expected Behavior:**
     Transcription results should update activeRecording state even when minimized.
     */
    @Test("Transcription updates when recording is minimized")
    func transcriptionUpdatesWhenMinimized() async {
        var state = AppFeature.State()
        state.activeRecording = RecordingFeature.State()
        state.activeRecording?.isRecording = true
        state.activeRecording?.hasPermission = true
        
        /// Start with recording expanded
        state.isRecordingExpanded = true
        
        let store = TestStore(initialState: state) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /// Minimize the recording
        await store.send(.minimizeRecording) {
            $0.isRecordingExpanded = false
        }
        
        /// Send transcription result while minimized
        let result = TranscriptionResult(
            text: "Hello world",
            words: [
                TimestampedWord(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: nil),
                TimestampedWord(text: "world", startTime: 0.5, endTime: 1.0, confidence: nil)
            ],
            isFinal: false
        )
        
        /// This should update the activeRecording's volatile transcription
        await store.send(.activeRecording(.transcriptionResult(result)))
        
        /// Verify transcription was updated
        #expect(store.state.activeRecording?.volatileTranscription == "Hello world")
    }
    
    // MARK: - Bug 2: Live Recording View Not Showing
    
    /**
     Test that RecordingsListFeature can see the active recording.
     
     **Bug Description:**
     The active recording row doesn't appear in the recordings list.
     
     **Root Cause:**
     RecordingsListFeature uses `@Shared(.activeRecording) var activeRecording: Recording?`
     but AppFeature uses `var activeRecording: RecordingFeature.State?`
     These are completely different types and not connected!
     
     **Expected Behavior:**
     When AppFeature has an active recording, RecordingsListFeature should be able
     to access it (or a derived Recording from it) to display in the list.
     */
    @Test("RecordingsListFeature can see active recording from AppFeature")
    func recordingsListCanSeeActiveRecording() async {
        var state = AppFeature.State()
        
        /// Start a recording
        state.activeRecording = RecordingFeature.State()
        state.activeRecording?.isRecording = true
        state.activeRecording?.title = "Test Recording"
        state.activeRecording?.duration = 10
        state.activeRecording?.recordingURL = URL(fileURLWithPath: "/tmp/test.m4a")
        
        let store = TestStore(initialState: state) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /**
         BUG: This test will FAIL because:
         - AppFeature.State.activeRecording is RecordingFeature.State?
         - RecordingsListFeature.State.activeRecording is @Shared(.activeRecording) Recording?
         - These are completely different and not connected!
         
         The @Shared(.activeRecording) in RecordingsListFeature reads from InMemoryKey
         but nothing ever writes to it.
         */
        
        /// Check if recordingsList can see the active recording
        /// This should be non-nil but currently it's nil because the types don't match
        #expect(store.state.recordingsList.activeRecording != nil,
                "RecordingsListFeature should be able to see the active recording")
        
        /// If it can see it, verify the properties match
        if let activeRecording = store.state.recordingsList.activeRecording {
            #expect(activeRecording.title == "Test Recording")
            #expect(activeRecording.duration == 10)
        }
    }
    
    /**
     Test that @Shared(.activeRecording) is updated when AppFeature starts recording.
     
     **Expected Behavior:**
     When AppFeature.startRecording is called, it should also update the
     @Shared(.activeRecording) so RecordingsListFeature can display it.
     */
    @Test("Starting recording updates shared activeRecording state")
    func startingRecordingUpdatesSharedState() async {
        let testDate = Date(timeIntervalSince1970: 0)
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000000")!
        
        let store = TestStore(initialState: AppFeature.State()) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
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
        
        store.exhaustivity = .off
        
        /// Start recording
        await store.send(.startRecording)
        
        /// Wait for effects to process
        await store.skipReceivedActions()
        
        /**
         BUG: This test will FAIL because:
         - AppFeature.startRecording creates activeRecording: RecordingFeature.State
         - But it never updates @Shared(.activeRecording): Recording?
         - RecordingsListFeature reads from @Shared(.activeRecording) which is nil
         */
        
        /// The shared activeRecording should be set
        #expect(store.state.recordingsList.activeRecording != nil,
                "@Shared(.activeRecording) should be updated when recording starts")
    }
    
    /**
     Test that live transcription is visible in RecordingsListFeature.
     
     **Expected Behavior:**
     When transcription updates come in, RecordingsListFeature should be able
     to see them via @Shared(.liveTranscription).
     */
    @Test("Live transcription is visible in RecordingsListFeature")
    func liveTranscriptionVisibleInRecordingsList() async {
        var state = AppFeature.State()
        state.activeRecording = RecordingFeature.State()
        state.activeRecording?.isRecording = true
        state.activeRecording?.hasPermission = true
        
        let store = TestStore(initialState: state) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /// Send a transcription result
        let result = TranscriptionResult(
            text: "Hello world",
            words: [
                TimestampedWord(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: nil),
                TimestampedWord(text: "world", startTime: 0.5, endTime: 1.0, confidence: nil)
            ],
            isFinal: false
        )
        
        store.exhaustivity = .off
        
        await store.send(.activeRecording(.transcriptionResult(result)))
        
        /// RecordingsListFeature should be able to see the live transcription
        /// via @Shared(.liveTranscription)
        #expect(store.state.recordingsList.liveTranscription.volatileText == "Hello world",
                "RecordingsListFeature should see live transcription updates")
    }
}