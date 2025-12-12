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
   (Context: TDD for PlaybackFeature reducer)

 WHAT:
   Unit tests for the PlaybackFeature reducer.
   Tests playback controls and word highlighting sync.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-11
   [Change Log:
     - 2025-12-11: Updated to use Shared<Recording> pattern for derived state
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/PlaybackFeatureTests.swift

 WHY:
   TDD approach - verify PlaybackFeature behavior.
   
   **Migration Note (2025-12-11):**
   Updated tests to use Shared<Recording> instead of Recording.
   This matches the SyncUpDetail pattern where child features receive
   derived shared state from their parent.
   
   **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
   **Motivation:** PlaybackFeature now uses @Shared var recording to enable
   mutations to propagate back to the parent's IdentifiedArrayOf<Recording>.
 */

import ComposableArchitecture
import Foundation
import Sharing
import Testing
@testable import SpeechRecorderApp

/**
 **Source:** SyncUps example - SyncUpDetailTests.swift
 **Motivation:** Use @MainActor and uncheckedUseMainSerialExecutor for deterministic testing
 */
@Suite("PlaybackFeature Tests")
@MainActor
struct PlaybackFeatureTests {
    
    init() { uncheckedUseMainSerialExecutor = true }
    
    /**
     Helper to create a PlaybackFeature.State with Shared<Recording>.
     
     **Source:** Recipe 7 - "Testing Shared State in TCA"
     **Motivation:** Use Shared(value:) for inline test values when the recording
     doesn't need to be part of a persisted collection.
     */
    private func makeState(recording: Recording) -> PlaybackFeature.State {
        PlaybackFeature.State(recording: Shared(value: recording))
    }
    
    @Test("Play button starts playback")
    func playButtonStartsPlayback() async {
        let words = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5),
            TimestampedWord.preview(text: "world", startTime: 0.6, endTime: 1.0)
        ]
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world",
                words: words,
                segments: [TranscriptionSegment(text: "Hello world", words: words)],
                isFinal: true
            )
        )
        
        /**
         **Source:** Recipe 7 - "Use Shared(value:) for inline test values"
         **Motivation:** When testing a child feature in isolation, we don't need
         the recording to be part of a persisted collection.
         */
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        } withDependencies: {
            $0.audioPlayer.play = { _ in }
            $0.audioPlayer.currentTime = { 0.3 }
            $0.continuousClock = ImmediateClock()
        }
        
        /// Mark as non-exhaustive since we're just testing the immediate state change
        /// The playback and timer effects will run in the background
        store.exhaustivity = .off
        
        await store.send(.playButtonTapped) {
            $0.isPlaying = true
        }
    }
    
    @Test("Pause button stops playback")
    func pauseButtonStopsPlayback() async {
        let recording = Recording.preview()
        
        var state = makeState(recording: recording)
        state.isPlaying = true
        
        let store = TestStore(initialState: state) {
            PlaybackFeature()
        } withDependencies: {
            $0.audioPlayer.pause = { }
        }
        
        await store.send(.pauseButtonTapped) {
            $0.isPlaying = false
        }
    }
    
    @Test("Time update highlights correct word")
    func timeUpdateHighlightsWord() async {
        let words = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5),
            TimestampedWord.preview(text: "world", startTime: 0.6, endTime: 1.0)
        ]
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world",
                words: words,
                segments: [TranscriptionSegment(text: "Hello world", words: words)],
                isFinal: true
            )
        )
        
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        }
        
        /// Time 0.3 should highlight "Hello" (index 0)
        await store.send(.timeUpdated(0.3)) {
            $0.currentTime = 0.3
            $0.currentWordIndex = 0
        }
        
        /// Time 0.7 should highlight "world" (index 1)
        await store.send(.timeUpdated(0.7)) {
            $0.currentTime = 0.7
            $0.currentWordIndex = 1
        }
    }
    
    @Test("Seek updates time and word index")
    func seekUpdatesTimeAndWordIndex() async {
        let words = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5),
            TimestampedWord.preview(text: "world", startTime: 0.6, endTime: 1.0)
        ]
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world",
                words: words,
                segments: [TranscriptionSegment(text: "Hello world", words: words)],
                isFinal: true
            )
        )
        
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        } withDependencies: {
            $0.audioPlayer.seek = { _ in }
        }
        
        await store.send(.seekTo(0.7)) {
            $0.currentTime = 0.7
            $0.currentWordIndex = 1
        }
    }
    
    @Test("Playback finished resets state")
    func playbackFinishedResetsState() async {
        let recording = Recording.preview()
        
        var state = makeState(recording: recording)
        state.isPlaying = true
        state.currentTime = 5.0
        state.currentWordIndex = 2
        
        let store = TestStore(initialState: state) {
            PlaybackFeature()
        }
        
        await store.send(.playbackFinished) {
            $0.isPlaying = false
            $0.currentTime = 0
            $0.currentWordIndex = nil
        }
    }
    
    // MARK: - Word Tapped Tests
    
    @Test("Tap word seeks to word start time")
    func tapWordSeeksToWordStart() async {
        let words = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5),
            TimestampedWord.preview(text: "world", startTime: 0.5, endTime: 1.0),
            TimestampedWord.preview(text: "test", startTime: 1.0, endTime: 1.5)
        ]
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world test",
                words: words,
                segments: [TranscriptionSegment(text: "Hello world test", words: words)],
                isFinal: true
            )
        )
        
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        } withDependencies: {
            $0.audioPlayer.seek = { _ in }
        }
        
        /// Tap on "world" (index 1) - should seek to 0.5
        await store.send(.wordTapped(1)) {
            $0.currentTime = 0.5
            $0.currentWordIndex = 1
        }
        
        /// Tap on "test" (index 2) - should seek to 1.0
        await store.send(.wordTapped(2)) {
            $0.currentTime = 1.0
            $0.currentWordIndex = 2
        }
    }
    
    @Test("Tap word with invalid index does nothing")
    func tapWordInvalidIndexDoesNothing() async {
        let words = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5)
        ]
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello",
                words: words,
                segments: [TranscriptionSegment(text: "Hello", words: words)],
                isFinal: true
            )
        )
        
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        }
        
        /// Tap on invalid index - should not change state
        await store.send(.wordTapped(5))
        /// No state change expected
    }
    
    @Test("Tap word with negative index does nothing")
    func tapWordNegativeIndexDoesNothing() async {
        let words = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5)
        ]
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello",
                words: words,
                segments: [TranscriptionSegment(text: "Hello", words: words)],
                isFinal: true
            )
        )
        
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        }
        
        /// Tap on negative index - should not change state
        await store.send(.wordTapped(-1))
        /// No state change expected
    }
    
    // MARK: - Edge Case Tests
    
    @Test("Time between words returns nil index")
    func timeBetweenWordsReturnsNil() async {
        let words = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.4),
            /// Gap from 0.4 to 0.6
            TimestampedWord.preview(text: "world", startTime: 0.6, endTime: 1.0)
        ]
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world",
                words: words,
                segments: [TranscriptionSegment(text: "Hello world", words: words)],
                isFinal: true
            )
        )
        
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        }
        
        /// Time 0.5 is in the gap between words
        await store.send(.timeUpdated(0.5)) {
            $0.currentTime = 0.5
            $0.currentWordIndex = nil
        }
    }
    
    @Test("Time after all words returns nil index")
    func timeAfterAllWordsReturnsNil() async {
        let words = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5)
        ]
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello",
                words: words,
                segments: [TranscriptionSegment(text: "Hello", words: words)],
                isFinal: true
            )
        )
        
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        }
        
        /// Time 1.0 is after all words
        await store.send(.timeUpdated(1.0)) {
            $0.currentTime = 1.0
            $0.currentWordIndex = nil
        }
    }
    
    @Test("Empty transcription always returns nil index")
    func emptyTranscriptionReturnsNil() async {
        let recording = Recording.preview(
            transcription: Transcription(
                text: "",
                words: [],
                segments: [],
                isFinal: true
            )
        )
        
        let store = TestStore(
            initialState: makeState(recording: recording)
        ) {
            PlaybackFeature()
        }
        
        await store.send(.timeUpdated(0.5)) {
            $0.currentTime = 0.5
            $0.currentWordIndex = nil
        }
    }
}