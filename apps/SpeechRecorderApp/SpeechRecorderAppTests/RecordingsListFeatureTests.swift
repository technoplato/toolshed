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
   (Context: TDD for RecordingsListFeature reducer)

 WHAT:
   Unit tests for the RecordingsListFeature reducer.
   Tests adding, deleting, and selecting recordings.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-11
   [Change Log:
     - 2025-12-11: Updated to use IdentifiedArrayOf and Recording.ID patterns
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/RecordingsListFeatureTests.swift

 WHY:
   TDD approach - verify RecordingsListFeature behavior.
   
   **Migration Note (2025-12-11):**
   Updated tests to use the new patterns from swift-sharing-state-comprehensive-guide.md:
   - Use Recording.ID instead of Recording for selectRecording action
   - Set up shared state using @Shared in tests
   - Use IdentifiedArrayOf for O(1) lookups
 */

import ComposableArchitecture
import Foundation
import Sharing
import Testing
@testable import SpeechRecorderApp

/**
 **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
 **Motivation:** Tests need to set up shared state before testing features that use @Shared.
 The pattern uses @Shared to override initial values in tests.
 */
@Suite("RecordingsListFeature Tests")
@MainActor
struct RecordingsListFeatureTests {
    
    /**
     **Source:** SyncUps example - SyncUpsListTests.swift
     **Motivation:** Use uncheckedUseMainSerialExecutor for deterministic async testing
     */
    init() { uncheckedUseMainSerialExecutor = true }
    
    @Test("Record button tapped sends action (handled by AppFeature)")
    func recordButtonTappedSendsAction() async {
        /// Note: Recording is now managed at AppFeature level for collapsible modal support.
        /// This test verifies the action is sent; AppFeature intercepts it to start recording.
        let store = TestStore(initialState: RecordingsListFeature.State()) {
            RecordingsListFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /// The action is sent but no state change occurs in RecordingsListFeature
        /// because AppFeature intercepts .recordButtonTapped and handles it
        await store.send(.recordButtonTapped)
    }
    
    /**
     **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
     **Motivation:** Test selecting a recording by ID and deriving shared state.
     The pattern uses @Shared to set up test data, then verifies the derived
     Shared<Recording> is passed to PlaybackFeature.
     */
    @Test("Select recording presents playback sheet with derived shared state")
    func selectRecordingPresentsPlayback() async throws {
        let recording = Recording.preview()
        
        /**
         Override shared state for this test.
         **Source:** Recipe 7 - "Testing with Pre-populated Shared State"
         */
        @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording> = [recording]
        
        let store = TestStore(initialState: RecordingsListFeature.State()) {
            RecordingsListFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /**
         **Migration Note:** Now using Recording.ID instead of Recording.
         The reducer derives Shared<Recording> from the IdentifiedArrayOf.
         */
        await store.send(.selectRecording(recording.id)) {
            /**
             **Source:** SyncUps SyncUpDetail pattern
             **Motivation:** PlaybackFeature now receives @Shared var recording
             instead of var recording, enabling mutations to propagate back.
             
             Note: We can't directly compare Shared<Recording> in state assertions,
             so we verify the recording value matches.
             */
            $0.playback = PlaybackFeature.State(
                recording: Shared(value: recordings[id: recording.id]!)
            )
        }
    }
    
    /**
     **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
     **Motivation:** Test deleting recordings using withLock pattern.
     */
    @Test("Delete recordings removes from list")
    func deleteRecordingsRemovesFromList() async {
        let recording1 = Recording.preview(id: UUID())
        let recording2 = Recording.preview(id: UUID())
        
        /**
         Set up shared state with two recordings.
         **Source:** Recipe 7 - "Testing with Pre-populated Shared State"
         */
        @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording> = [recording1, recording2]
        defer { #expect(recordings.count == 1) }
        
        let store = TestStore(initialState: RecordingsListFeature.State()) {
            RecordingsListFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /**
         **Source:** SyncUpsList.onDelete pattern
         **Motivation:** Verify deletion uses withLock for thread-safe mutation.
         */
        await store.send(.deleteRecordings(IndexSet(integer: 0))) {
            /**
             Assert shared state mutation using withLock pattern.
             **Source:** Recipe 7 - "Testing Shared State Mutations"
             */
            $0.$recordings.withLock { $0.remove(atOffsets: IndexSet(integer: 0)) }
        }
    }
    
    /**
     **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
     **Motivation:** Test that selecting a non-existent recording ID does nothing.
     */
    @Test("Select non-existent recording does nothing")
    func selectNonExistentRecordingDoesNothing() async {
        @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording> = []
        
        let store = TestStore(initialState: RecordingsListFeature.State()) {
            RecordingsListFeature()
        } withDependencies: {
            $0.defaultFileStorage = .inMemory
        }
        
        /// Selecting a non-existent ID should not change state
        await store.send(.selectRecording(UUID()))
        /// No state change expected - playback remains nil
    }
}