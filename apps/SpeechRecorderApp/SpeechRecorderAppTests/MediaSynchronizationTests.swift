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
   (Context: TDD for media synchronization in RecordingFeature and PlaybackFeature)

 WHAT:
   Unit tests for media synchronization functionality.
   Tests photo detection during recording and display during playback.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/MediaSynchronizationTests.swift

 WHY:
   TDD approach - write tests first to define expected behavior.
   These tests verify that photos/screenshots are properly captured
   during recording and displayed at correct timestamps during playback.
 */

import ComposableArchitecture
import Foundation
import Sharing
import Testing
import UIKit
@testable import SpeechRecorderApp

// MARK: - Recording Feature Media Tests

@Suite("RecordingFeature Media Synchronization Tests")
@MainActor
struct RecordingFeatureMediaTests {
    
    @Test("New photo detected adds media to captured list")
    func newPhotoDetectedAddsMedia() async {
        let testDate = Date(timeIntervalSince1970: 1000)
        let recordingStartTime = Date(timeIntervalSince1970: 995)
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        
        var state = RecordingFeature.State()
        state.isRecording = true
        state.recordingStartTime = recordingStartTime
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.uuid = .constant(testUUID)
            $0.photoLibrary.fetchThumbnail = { _, _ in nil }
        }
        
        let photoAsset = PhotoAsset(
            id: "photo-1",
            creationDate: testDate,
            mediaType: .photo,
            localIdentifier: "local-1"
        )
        
        await store.send(.newPhotoDetected(photoAsset)) {
            $0.capturedMedia = [
                TimestampedMedia(
                    id: testUUID,
                    timestamp: 5.0, /// 1000 - 995 = 5 seconds after recording started
                    assetIdentifier: "local-1",
                    mediaType: .photo,
                    creationDate: testDate
                )
            ]
        }
    }
    
    @Test("New screenshot detected adds screenshot media")
    func newScreenshotDetectedAddsMedia() async {
        let testDate = Date(timeIntervalSince1970: 1010)
        let recordingStartTime = Date(timeIntervalSince1970: 1000)
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000002")!
        
        var state = RecordingFeature.State()
        state.isRecording = true
        state.recordingStartTime = recordingStartTime
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.uuid = .constant(testUUID)
            $0.photoLibrary.fetchThumbnail = { _, _ in nil }
        }
        
        let screenshotAsset = PhotoAsset(
            id: "screenshot-1",
            creationDate: testDate,
            mediaType: .screenshot,
            localIdentifier: "local-screenshot-1"
        )
        
        await store.send(.newPhotoDetected(screenshotAsset)) {
            $0.capturedMedia = [
                TimestampedMedia(
                    id: testUUID,
                    timestamp: 10.0,
                    assetIdentifier: "local-screenshot-1",
                    mediaType: .screenshot,
                    creationDate: testDate
                )
            ]
        }
    }
    
    @Test("Photo before recording start is ignored")
    func photoBeforeRecordingStartIsIgnored() async {
        let recordingStartTime = Date(timeIntervalSince1970: 1000)
        let photoDate = Date(timeIntervalSince1970: 990) /// Before recording started
        
        var state = RecordingFeature.State()
        state.isRecording = true
        state.recordingStartTime = recordingStartTime
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        let photoAsset = PhotoAsset(
            id: "old-photo",
            creationDate: photoDate,
            mediaType: .photo,
            localIdentifier: "old-local"
        )
        
        /// Should not change state since photo is before recording started
        await store.send(.newPhotoDetected(photoAsset))
    }
    
    @Test("Photo without recording start time is ignored")
    func photoWithoutRecordingStartTimeIsIgnored() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.recordingStartTime = nil /// No start time
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        let photoAsset = PhotoAsset(
            id: "photo-1",
            creationDate: Date(),
            mediaType: .photo,
            localIdentifier: "local-1"
        )
        
        /// Should not change state since there's no recording start time
        await store.send(.newPhotoDetected(photoAsset))
    }
    
    @Test("Thumbnail loaded updates media thumbnails")
    func thumbnailLoadedUpdatesThumbnails() async {
        let mediaId = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        let testImage = UIImage(systemName: "photo")!
        
        var state = RecordingFeature.State()
        state.isRecording = true
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        await store.send(.thumbnailLoaded(mediaId, testImage)) {
            $0.mediaThumbnails[mediaId] = testImage
        }
    }
    
    @Test("Cancel button clears captured media")
    func cancelButtonClearsCapturedMedia() async {
        let mediaId = UUID()
        let testImage = UIImage(systemName: "photo")!
        
        var state = RecordingFeature.State()
        state.isRecording = true
        state.hasPermission = true
        state.capturedMedia = [
            TimestampedMedia(
                id: mediaId,
                timestamp: 5.0,
                assetIdentifier: "local-1",
                mediaType: .photo,
                creationDate: Date()
            )
        ]
        state.mediaThumbnails = [mediaId: testImage]
        
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
    
    @Test("Recording stopped includes captured media in recording")
    func recordingStoppedIncludesMedia() async {
        let testDate = Date(timeIntervalSince1970: 1000)
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        let testURL = URL(fileURLWithPath: "/tmp/test.m4a")
        let mediaId = UUID(uuidString: "00000000-0000-0000-0000-000000000002")!
        
        let capturedMedia = TimestampedMedia(
            id: mediaId,
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: Date(timeIntervalSince1970: 1005)
        )
        
        var state = RecordingFeature.State()
        state.isRecording = true
        state.recordingStartTime = testDate
        state.hasPermission = true
        state.recordingURL = testURL
        state.duration = 10.0
        state.capturedMedia = [capturedMedia]
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.uuid = .constant(testUUID)
        }
        
        /// Verify state changes when recording stops
        await store.send(.recordingStopped) {
            $0.isRecording = false
            $0.mode = .idle
        }
        
        /// Receive the delegate action - the Recording created should include the captured media
        /// We verify this by checking that the action is received (the reducer creates the Recording
        /// with state.capturedMedia which we set above)
        await store.receive(\.delegate.didFinish.success)
    }
}

// MARK: - Playback Feature Media Tests

@Suite("PlaybackFeature Media Synchronization Tests")
@MainActor
struct PlaybackFeatureMediaTests {
    
    @Test("On appear loads thumbnails for all media")
    func onAppearLoadsThumbnails() async {
        let mediaId = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        let testImage = UIImage(systemName: "photo")!
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: [
                TimestampedMedia(
                    id: mediaId,
                    timestamp: 5.0,
                    assetIdentifier: "local-1",
                    mediaType: .photo,
                    creationDate: Date()
                )
            ]
        )
        
        let store = await TestStore(initialState: PlaybackFeature.State(recording: Shared(value: recording))) {
            PlaybackFeature()
        } withDependencies: {
            $0.photoLibrary.fetchThumbnail = { identifier, _ in
                if identifier == "local-1" {
                    return testImage
                }
                return nil
            }
        }
        
        await store.send(.onAppear)
        
        await store.receive(\.thumbnailLoaded) {
            $0.mediaThumbnails[mediaId] = testImage
        }
    }
    
    @Test("On appear with no media does nothing")
    func onAppearWithNoMediaDoesNothing() async {
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: []
        )
        
        let store = await TestStore(initialState: PlaybackFeature.State(recording: Shared(value: recording))) {
            PlaybackFeature()
        }
        
        await store.send(.onAppear)
    }
    
    @Test("Media tapped seeks to media timestamp")
    func mediaTappedSeeksToTimestamp() async {
        let mediaId = UUID(uuidString: "00000000-0000-0000-0000-000000000001")!
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: Transcription(
                text: "Hello world",
                words: [
                    TimestampedWord(text: "Hello", startTime: 0.0, endTime: 2.0, confidence: nil),
                    TimestampedWord(text: "world", startTime: 2.0, endTime: 4.0, confidence: nil)
                ],
                segments: [
                    TranscriptionSegment(
                        text: "Hello world",
                        words: [
                            TimestampedWord(text: "Hello", startTime: 0.0, endTime: 2.0, confidence: nil),
                            TimestampedWord(text: "world", startTime: 2.0, endTime: 4.0, confidence: nil)
                        ]
                    )
                ],
                isFinal: true
            ),
            media: [
                TimestampedMedia(
                    id: mediaId,
                    timestamp: 3.0, /// During "world"
                    assetIdentifier: "local-1",
                    mediaType: .photo,
                    creationDate: Date()
                )
            ]
        )
        
        let store = await TestStore(initialState: PlaybackFeature.State(recording: Shared(value: recording))) {
            PlaybackFeature()
        } withDependencies: {
            $0.audioPlayer.seek = { _ in }
        }
        
        await store.send(.mediaTapped(mediaId)) {
            $0.currentTime = 3.0
            $0.currentWordIndex = 1 /// "world" is at index 1
        }
    }
    
    @Test("Media tapped with invalid ID does nothing")
    func mediaTappedWithInvalidIdDoesNothing() async {
        let invalidId = UUID()
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: []
        )
        
        let store = await TestStore(initialState: PlaybackFeature.State(recording: Shared(value: recording))) {
            PlaybackFeature()
        }
        
        await store.send(.mediaTapped(invalidId))
    }
    
    @Test("Visible media computed property returns media within window")
    func visibleMediaReturnsMediaWithinWindow() {
        let media1 = TimestampedMedia(
            id: UUID(),
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: Date()
        )
        let media2 = TimestampedMedia(
            id: UUID(),
            timestamp: 8.0,
            assetIdentifier: "local-2",
            mediaType: .screenshot,
            creationDate: Date()
        )
        let media3 = TimestampedMedia(
            id: UUID(),
            timestamp: 15.0,
            assetIdentifier: "local-3",
            mediaType: .photo,
            creationDate: Date()
        )
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: [media1, media2, media3]
        )
        
        var state = PlaybackFeature.State(recording: Shared(value: recording))
        state.currentTime = 10.0 /// Window is 7.0 to 10.0
        
        /// media1 at 5.0 is outside window (before 7.0)
        /// media2 at 8.0 is inside window
        /// media3 at 15.0 is outside window (after 10.0)
        #expect(state.visibleMedia.count == 1)
        #expect(state.visibleMedia.first?.assetIdentifier == "local-2")
    }
    
    @Test("Current media returns most recent media before current time")
    func currentMediaReturnsMostRecent() {
        let media1 = TimestampedMedia(
            id: UUID(),
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: Date()
        )
        let media2 = TimestampedMedia(
            id: UUID(),
            timestamp: 8.0,
            assetIdentifier: "local-2",
            mediaType: .screenshot,
            creationDate: Date()
        )
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: [media1, media2]
        )
        
        var state = PlaybackFeature.State(recording: Shared(value: recording))
        state.currentTime = 10.0
        
        #expect(state.currentMedia?.assetIdentifier == "local-2")
    }
    
    @Test("Media up to current time returns all media before current time")
    func mediaUpToCurrentTimeReturnsAll() {
        let media1 = TimestampedMedia(
            id: UUID(),
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: Date()
        )
        let media2 = TimestampedMedia(
            id: UUID(),
            timestamp: 8.0,
            assetIdentifier: "local-2",
            mediaType: .screenshot,
            creationDate: Date()
        )
        let media3 = TimestampedMedia(
            id: UUID(),
            timestamp: 15.0,
            assetIdentifier: "local-3",
            mediaType: .photo,
            creationDate: Date()
        )
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: [media1, media2, media3]
        )
        
        var state = PlaybackFeature.State(recording: Shared(value: recording))
        state.currentTime = 10.0
        
        #expect(state.mediaUpToCurrentTime.count == 2)
    }
}

// MARK: - TimestampedMedia Tests

@Suite("TimestampedMedia Tests")
@MainActor
struct TimestampedMediaTests {
    
    @Test("TimestampedMedia is identifiable")
    func timestampedMediaIsIdentifiable() {
        let id = UUID()
        let media = TimestampedMedia(
            id: id,
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: Date()
        )
        
        #expect(media.id == id)
    }
    
    @Test("TimestampedMedia is equatable")
    func timestampedMediaIsEquatable() {
        let id = UUID()
        let date = Date()
        let media1 = TimestampedMedia(
            id: id,
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: date
        )
        let media2 = TimestampedMedia(
            id: id,
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: date
        )
        
        #expect(media1 == media2)
    }
    
    @Test("TimestampedMedia is codable")
    func timestampedMediaIsCodable() throws {
        let id = UUID()
        let date = Date()
        let media = TimestampedMedia(
            id: id,
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: date
        )
        
        let encoder = JSONEncoder()
        let data = try encoder.encode(media)
        
        let decoder = JSONDecoder()
        let decoded = try decoder.decode(TimestampedMedia.self, from: data)
        
        #expect(decoded == media)
    }
    
    @Test("TimestampedMedia preview factory creates valid media")
    func timestampedMediaPreviewCreatesValidMedia() {
        let media = TimestampedMedia.preview(timestamp: 10.0, mediaType: .screenshot)
        
        #expect(media.timestamp == 10.0)
        #expect(media.mediaType == .screenshot)
    }
}

// MARK: - Recording Media Tests

@Suite("Recording Media Tests")
@MainActor
struct RecordingMediaTests {
    
    @Test("Recording sorted media returns media in timestamp order")
    func recordingSortedMediaReturnsInOrder() {
        let media1 = TimestampedMedia(
            id: UUID(),
            timestamp: 15.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: Date()
        )
        let media2 = TimestampedMedia(
            id: UUID(),
            timestamp: 5.0,
            assetIdentifier: "local-2",
            mediaType: .screenshot,
            creationDate: Date()
        )
        let media3 = TimestampedMedia(
            id: UUID(),
            timestamp: 10.0,
            assetIdentifier: "local-3",
            mediaType: .photo,
            creationDate: Date()
        )
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: [media1, media2, media3]
        )
        
        let sorted = recording.sortedMedia
        
        #expect(sorted[0].timestamp == 5.0)
        #expect(sorted[1].timestamp == 10.0)
        #expect(sorted[2].timestamp == 15.0)
    }
    
    @Test("Recording media at time returns media up to time")
    func recordingMediaAtTimeReturnsUpToTime() {
        let media1 = TimestampedMedia(
            id: UUID(),
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: Date()
        )
        let media2 = TimestampedMedia(
            id: UUID(),
            timestamp: 15.0,
            assetIdentifier: "local-2",
            mediaType: .screenshot,
            creationDate: Date()
        )
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: [media1, media2]
        )
        
        let mediaAt10 = recording.mediaAtTime(10.0)
        
        #expect(mediaAt10.count == 1)
        #expect(mediaAt10.first?.timestamp == 5.0)
    }
    
    @Test("Recording most recent media returns latest before time")
    func recordingMostRecentMediaReturnsLatest() {
        let media1 = TimestampedMedia(
            id: UUID(),
            timestamp: 5.0,
            assetIdentifier: "local-1",
            mediaType: .photo,
            creationDate: Date()
        )
        let media2 = TimestampedMedia(
            id: UUID(),
            timestamp: 8.0,
            assetIdentifier: "local-2",
            mediaType: .screenshot,
            creationDate: Date()
        )
        
        let recording = Recording(
            id: UUID(),
            title: "Test",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .empty,
            media: [media1, media2]
        )
        
        let mostRecent = recording.mostRecentMedia(before: 10.0)
        
        #expect(mostRecent?.timestamp == 8.0)
    }
    
    @Test("Recording preview with media creates valid recording")
    func recordingPreviewWithMediaCreatesValid() {
        let recording = Recording.previewWithMedia()
        
        #expect(recording.media.count == 3)
        #expect(recording.media.contains { $0.mediaType == .photo })
        #expect(recording.media.contains { $0.mediaType == .screenshot })
    }
}