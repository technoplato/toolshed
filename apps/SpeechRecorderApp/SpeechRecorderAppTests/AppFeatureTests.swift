/**
 HOW:
   Run tests with: `xcodebuild test -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 16'`
   
   [Inputs]
   - None (unit tests)
   
   [Outputs]
   - Test results
   
   [Side Effects]
   - None (uses mocked dependencies)

 WHO:
   AI Agent, Developer
   (Context: TDD for AppFeature reducer)

 WHAT:
   Unit tests for the AppFeature reducer.
   Tests app-level coordination including:
   - Recording lifecycle (start, minimize, expand)
   - Preventing playback of active recording
   - Floating indicator behavior

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-11
   [Change Log:
     - 2025-12-11: Updated to use Recording.ID and IdentifiedArrayOf patterns
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/AppFeatureTests.swift

 WHY:
   TDD approach - verify AppFeature behavior for collapsible recording modal
   and preventing playback of active recordings.
   
   **Migration Note (2025-12-11):**
   Updated tests to use the new patterns from swift-sharing-state-comprehensive-guide.md:
   - Use Recording.ID instead of Recording for selectRecording action
   - Set up shared state using @Shared in tests
   - Use IdentifiedArrayOf for O(1) lookups
   
   **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
   **Motivation:** Tests need to set up shared state before testing features that use @Shared.
 */

import ComposableArchitecture
import Foundation
import Sharing
import Testing
@testable import SpeechRecorderApp

/**
 **Source:** SyncUps example - AppFeatureTests pattern
 **Motivation:** Use @MainActor and uncheckedUseMainSerialExecutor for deterministic testing
 */
@Suite("AppFeature Tests")
@MainActor
struct AppFeatureTests {
    
    init() { uncheckedUseMainSerialExecutor = true }
    
    @Test("Minimize recording hides modal but keeps recording active")
    func minimizeRecordingHidesModal() async {
        /// Create recording state
        var recordingState = RecordingFeature.State()
        recordingState.isRecording = true
        
        /// Set up state with expanded recording using isRecordingExpanded
        var state = AppFeature.State()
        state.activeRecording = recordingState
        state.isRecordingExpanded = true
        
        let store = TestStore(initialState: state) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        await store.send(.minimizeRecording) {
            /// isRecordingExpanded becomes false (modal hidden)
            $0.isRecordingExpanded = false
            /// activeRecording should still exist
        }
        
        #expect(store.state.activeRecording != nil)
        #expect(store.state.hasActiveRecording == true)
        #expect(store.state.isRecordingExpanded == false)
    }
    
    @Test("Floating indicator tap expands recording modal")
    func floatingIndicatorTapExpandsModal() async {
        /// Create recording state
        var recordingState = RecordingFeature.State()
        recordingState.isRecording = true
        
        /// Set up state with minimized recording (isRecordingExpanded is false)
        var state = AppFeature.State()
        state.activeRecording = recordingState
        state.isRecordingExpanded = false
        
        let store = TestStore(initialState: state) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        await store.send(.floatingIndicatorTapped) {
            /// isRecordingExpanded becomes true
            $0.isRecordingExpanded = true
        }
        
        #expect(store.state.isRecordingExpanded == true)
    }
    
    /**
     **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
     **Motivation:** Test that selecting the active recording shows an alert.
     Now uses Recording.ID and sets up shared state with @Shared.
     */
    @Test("Selecting active recording shows alert instead of playback")
    func selectingActiveRecordingShowsAlert() async {
        /// Create a recording URL that matches the active recording
        let recordingURL = URL(fileURLWithPath: "/tmp/active-recording.m4a")
        
        /// Create a recording with that URL
        let recording = Recording(
            id: UUID(),
            title: "Active Recording",
            date: Date(),
            duration: 10.0,
            audioURL: recordingURL
        )
        
        /**
         Set up shared state with the recording.
         **Source:** Recipe 7 - "Testing with Pre-populated Shared State"
         */
        @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording> = [recording]
        
        /// Create recording state with the URL
        var recordingState = RecordingFeature.State()
        recordingState.isRecording = true
        recordingState.recordingURL = recordingURL
        
        /// Set up state with an active recording at the same URL (minimized)
        var state = AppFeature.State()
        state.activeRecording = recordingState
        state.isRecordingExpanded = false
        
        let store = TestStore(initialState: state) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /**
         Try to select the active recording for playback.
         **Migration Note:** Now using Recording.ID instead of Recording.
         */
        await store.send(.recordingsList(.selectRecording(recording.id))) {
            /// Should show alert instead of presenting playback
            $0.recordingsList.alert = AlertState {
                TextState("Recording in Progress")
            } actions: {
                ButtonState(role: .cancel) {
                    TextState("OK")
                }
            } message: {
                TextState("You cannot play a recording while it's still being recorded. Stop the recording first to play it back.")
            }
        }
        
        /// Playback should NOT be presented
        #expect(store.state.recordingsList.playback == nil)
    }
    
    /**
     **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
     **Motivation:** Test that selecting a different recording allows playback.
     */
    @Test("Selecting different recording allows playback during active recording")
    func selectingDifferentRecordingAllowsPlayback() async {
        /// Create different URLs for active recording and selected recording
        let activeRecordingURL = URL(fileURLWithPath: "/tmp/active-recording.m4a")
        let otherRecordingURL = URL(fileURLWithPath: "/tmp/other-recording.m4a")
        
        /// Create a recording with a different URL
        let otherRecording = Recording(
            id: UUID(),
            title: "Other Recording",
            date: Date(),
            duration: 10.0,
            audioURL: otherRecordingURL
        )
        
        /**
         Set up shared state with the recording.
         **Source:** Recipe 7 - "Testing with Pre-populated Shared State"
         */
        @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording> = [otherRecording]
        
        /// Create recording state with the active URL
        var recordingState = RecordingFeature.State()
        recordingState.isRecording = true
        recordingState.recordingURL = activeRecordingURL
        
        /// Set up state with an active recording (minimized)
        var state = AppFeature.State()
        state.activeRecording = recordingState
        state.isRecordingExpanded = false
        
        let store = TestStore(initialState: state) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /**
         Select a different recording for playback.
         **Migration Note:** Now using Recording.ID instead of Recording.
         */
        await store.send(.recordingsList(.selectRecording(otherRecording.id))) {
            /// Should present playback (no alert)
            /// PlaybackFeature.State now takes Shared<Recording>
            $0.recordingsList.playback = PlaybackFeature.State(
                recording: Shared(value: recordings[id: otherRecording.id]!)
            )
        }
        
        /// Alert should NOT be shown
        #expect(store.state.recordingsList.alert == nil)
    }
    
    /**
     **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
     **Motivation:** Test that selecting a recording when no active recording allows playback.
     */
    @Test("Selecting recording when no active recording allows playback")
    func selectingRecordingWithNoActiveRecordingAllowsPlayback() async {
        let recording = Recording.preview()
        
        /**
         Set up shared state with the recording.
         **Source:** Recipe 7 - "Testing with Pre-populated Shared State"
         */
        @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording> = [recording]
        
        let store = TestStore(initialState: AppFeature.State()) {
            AppFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /**
         Select a recording when there's no active recording.
         **Migration Note:** Now using Recording.ID instead of Recording.
         */
        await store.send(.recordingsList(.selectRecording(recording.id))) {
            /// Should present playback normally
            /// PlaybackFeature.State now takes Shared<Recording>
            $0.recordingsList.playback = PlaybackFeature.State(
                recording: Shared(value: recordings[id: recording.id]!)
            )
        }
    }
    
}