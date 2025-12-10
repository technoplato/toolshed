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
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/PlaybackFeatureTests.swift

 WHY:
   TDD approach - verify PlaybackFeature behavior.
 */

import ComposableArchitecture
import Foundation
import Testing
@testable import SpeechRecorderApp

@Suite("PlaybackFeature Tests")
struct PlaybackFeatureTests {
    
    @Test("Play button starts playback")
    func playButtonStartsPlayback() async {
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world",
                words: [
                    .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
                    .preview(text: "world", startTime: 0.6, endTime: 1.0)
                ],
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
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
        
        var state = PlaybackFeature.State(recording: recording)
        state.isPlaying = true
        
        let store = await TestStore(initialState: state) {
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
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world",
                words: [
                    .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
                    .preview(text: "world", startTime: 0.6, endTime: 1.0)
                ],
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
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
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world",
                words: [
                    .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
                    .preview(text: "world", startTime: 0.6, endTime: 1.0)
                ],
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
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
        
        var state = PlaybackFeature.State(recording: recording)
        state.isPlaying = true
        state.currentTime = 5.0
        state.currentWordIndex = 2
        
        let store = await TestStore(initialState: state) {
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
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world test",
                words: [
                    .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
                    .preview(text: "world", startTime: 0.5, endTime: 1.0),
                    .preview(text: "test", startTime: 1.0, endTime: 1.5)
                ],
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
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
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello",
                words: [
                    .preview(text: "Hello", startTime: 0.0, endTime: 0.5)
                ],
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
        ) {
            PlaybackFeature()
        }
        
        /// Tap on invalid index - should not change state
        await store.send(.wordTapped(5))
        /// No state change expected
    }
    
    @Test("Tap word with negative index does nothing")
    func tapWordNegativeIndexDoesNothing() async {
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello",
                words: [
                    .preview(text: "Hello", startTime: 0.0, endTime: 0.5)
                ],
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
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
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello world",
                words: [
                    .preview(text: "Hello", startTime: 0.0, endTime: 0.4),
                    /// Gap from 0.4 to 0.6
                    .preview(text: "world", startTime: 0.6, endTime: 1.0)
                ],
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
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
        let recording = Recording.preview(
            transcription: Transcription(
                text: "Hello",
                words: [
                    .preview(text: "Hello", startTime: 0.0, endTime: 0.5)
                ],
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
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
                isFinal: true
            )
        )
        
        let store = await TestStore(
            initialState: PlaybackFeature.State(recording: recording)
        ) {
            PlaybackFeature()
        }
        
        await store.send(.timeUpdated(0.5)) {
            $0.currentTime = 0.5
            $0.currentWordIndex = nil
        }
    }
}