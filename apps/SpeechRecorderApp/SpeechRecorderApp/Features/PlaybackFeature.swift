/**
 HOW:
   Use in SwiftUI views with StoreOf<PlaybackFeature>.
   
   ```swift
   PlaybackView(store: store.scope(state: \.playback, action: \.playback))
   ```
   
   [Inputs]
   - User actions: playButtonTapped, pauseButtonTapped, seekTo, mediaTapped
   - System events: timeUpdated, playbackFinished
   
   [Outputs]
   - Playback state for UI updates
   - Current word index for highlighting
   - Visible media at current time
   
   [Side Effects]
   - Plays audio via AudioPlayerClient
   - Fetches media thumbnails via PhotoLibraryClient

 WHO:
   AI Agent, Developer
   (Context: TCA reducer for playback functionality)

 WHAT:
   TCA reducer for managing audio playback with word highlighting
   and synchronized media display.
   Syncs current playback time with transcription words and shows
   photos/screenshots at their capture timestamps.
   
   **Migration Note (2025-12-11):**
   Updated to use @Shared var recording for derived shared state.
   This allows mutations to propagate back to the parent's recordings list.
   
   Reference: SyncUpDetail.swift:22
   https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpDetail.swift
   
   See: docs/swift-sharing-state-comprehensive-guide.md#appendix-a-speechrecorderapp-migration-guide

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-11
   [Change Log:
     - 2025-12-11: Migrated to @Shared var recording for derived shared state
                   Enables mutations to propagate to parent's recordings list
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/PlaybackFeature.swift

 WHY:
   To provide synchronized playback with word highlighting and media display.
   Uses the word timestamps to highlight the current word as audio plays,
   and shows photos/screenshots at the times they were captured.
   
   Using @Shared var recording:
   1. Receives derived shared state from parent (RecordingsListFeature)
   2. Any mutations propagate back to parent automatically
   3. Matches the production SyncUps app pattern (SyncUpDetail)
 */

import ComposableArchitecture
import Foundation
import Sharing
import UIKit

@Reducer
struct PlaybackFeature {
    
    // MARK: - State
    
    @ObservableState
    struct State: Equatable, Sendable {
        /**
         The recording being played.
         
         **Pattern Source:** SyncUpDetail.swift:22
         
         Uses @Shared for derived shared state from parent.
         Mutations propagate back to parent's recordings list automatically.
         */
        @Shared var recording: Recording
        
        /// Whether audio is currently playing
        var isPlaying = false
        
        /// Current playback time in seconds
        var currentTime: TimeInterval = 0
        
        /// Index of the currently highlighted word
        var currentWordIndex: Int?
        
        /// Fullscreen image presentation state
        @Presents var fullscreenImage: FullscreenImageFeature.State?
        
        /// Fullscreen transcript presentation state
        @Presents var fullscreenTranscript: FullscreenTranscriptFeature.State?
        
        /// The current word being spoken
        var currentWord: TimestampedWord? {
            guard let index = currentWordIndex else { return nil }
            guard index < recording.transcription.words.count else { return nil }
            return recording.transcription.words[index]
        }
        
        /// Thumbnails for media items (keyed by media ID)
        var mediaThumbnails: [UUID: UIImage] = [:]
        
        /// Media items visible at the current time (within a window)
        var visibleMedia: [TimestampedMedia] {
            /// Show media that was captured within the last 3 seconds of current time
            let windowStart = max(0, currentTime - 3.0)
            return recording.media.filter { media in
                media.timestamp >= windowStart && media.timestamp <= currentTime
            }.sorted { $0.timestamp < $1.timestamp }
        }
        
        /// The most recently captured media at current time
        var currentMedia: TimestampedMedia? {
            recording.mostRecentMedia(before: currentTime)
        }
        
        /// All media up to current time (for timeline display)
        var mediaUpToCurrentTime: [TimestampedMedia] {
            recording.mediaAtTime(currentTime)
        }
    }
    
    // MARK: - Action
    
    enum Action: Sendable {
        /// User tapped the play button
        case playButtonTapped
        
        /// User tapped the pause button
        case pauseButtonTapped
        
        /// User seeked to a specific time (scrubbing)
        case seekTo(TimeInterval)
        
        /// User tapped on a word to seek to its start time
        case wordTapped(Int)
        
        /// User tapped on a media item to seek to its timestamp
        case mediaTapped(UUID)
        
        /// Playback time was updated
        case timeUpdated(TimeInterval)
        
        /// Playback finished
        case playbackFinished
        
        /// Close the playback view
        case closeButtonTapped
        
        /// View appeared - load thumbnails
        case onAppear
        
        /// Thumbnail loaded for a media item
        case thumbnailLoaded(UUID, UIImage)
        
        /// User double-tapped an image to view fullscreen
        case imageDoubleTapped(UUID)
        
        /// User double-tapped with two fingers to enter fullscreen transcript
        case twoFingerDoubleTapped
        
        /// Fullscreen image presentation actions
        case fullscreenImage(PresentationAction<FullscreenImageFeature.Action>)
        
        /// Fullscreen transcript presentation actions
        case fullscreenTranscript(PresentationAction<FullscreenTranscriptFeature.Action>)
        
        /// Delegate actions for parent feature
        case delegate(Delegate)
        
        enum Delegate: Equatable, Sendable {
            case didClose
        }
    }
    
    // MARK: - Dependencies
    
    @Dependency(\.audioPlayer) var audioPlayer
    @Dependency(\.photoLibrary) var photoLibrary
    @Dependency(\.continuousClock) var clock
    
    // MARK: - Cancellation IDs
    
    private enum CancelID {
        case playback
        case timer
        case thumbnailLoading
    }
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case .onAppear:
                /// Load thumbnails for all media in the recording
                let mediaItems = state.recording.media
                guard !mediaItems.isEmpty else { return .none }
                
                return .run { send in
                    for media in mediaItems {
                        if let thumbnail = await photoLibrary.fetchThumbnail(
                            media.assetIdentifier,
                            CGSize(width: 100, height: 100)
                        ) {
                            await send(.thumbnailLoaded(media.id, thumbnail))
                        }
                    }
                }
                .cancellable(id: CancelID.thumbnailLoading)
                
            case let .thumbnailLoaded(mediaId, image):
                state.mediaThumbnails[mediaId] = image
                return .none
                
            case .playButtonTapped:
                state.isPlaying = true
                
                return .merge(
                    /// Start playback
                    .run { [url = state.recording.audioURL] send in
                        do {
                            try await audioPlayer.play(url)
                            await send(.playbackFinished)
                        } catch {
                            await send(.playbackFinished)
                        }
                    }
                    .cancellable(id: CancelID.playback),
                    
                    /// Start timer for time updates
                    .run { send in
                        for await _ in clock.timer(interval: .milliseconds(50)) {
                            if let time = await audioPlayer.currentTime() {
                                await send(.timeUpdated(time))
                            }
                        }
                    }
                    .cancellable(id: CancelID.timer)
                )
                
            case .pauseButtonTapped:
                state.isPlaying = false
                
                return .merge(
                    .cancel(id: CancelID.timer),
                    .run { _ in
                        await audioPlayer.pause()
                    }
                )
                
            case let .seekTo(time):
                state.currentTime = time
                state.currentWordIndex = findWordIndex(at: time, in: state.recording.transcription.words)
                
                return .run { _ in
                    await audioPlayer.seek(time)
                }
                
            case let .wordTapped(index):
                guard index >= 0 && index < state.recording.transcription.words.count else {
                    return .none
                }
                let word = state.recording.transcription.words[index]
                state.currentTime = word.startTime
                state.currentWordIndex = index
                
                return .run { [startTime = word.startTime] _ in
                    await audioPlayer.seek(startTime)
                }
                
            case let .mediaTapped(mediaId):
                guard let media = state.recording.media.first(where: { $0.id == mediaId }) else {
                    return .none
                }
                state.currentTime = media.timestamp
                state.currentWordIndex = findWordIndex(at: media.timestamp, in: state.recording.transcription.words)
                
                return .run { [timestamp = media.timestamp] _ in
                    await audioPlayer.seek(timestamp)
                }
                
            case let .timeUpdated(time):
                state.currentTime = time
                state.currentWordIndex = findWordIndex(at: time, in: state.recording.transcription.words)
                return .none
                
            case .playbackFinished:
                state.isPlaying = false
                state.currentTime = 0
                state.currentWordIndex = nil
                
                return .cancel(id: CancelID.timer)
                
            case .closeButtonTapped:
                return .merge(
                    .cancel(id: CancelID.playback),
                    .cancel(id: CancelID.timer),
                    .cancel(id: CancelID.thumbnailLoading),
                    .run { _ in
                        await audioPlayer.stop()
                    },
                    .send(.delegate(.didClose))
                )
                
            case let .imageDoubleTapped(mediaId):
                guard let media = state.recording.media.first(where: { $0.id == mediaId }) else {
                    return .none
                }
                state.fullscreenImage = FullscreenImageFeature.State(
                    assetIdentifier: media.assetIdentifier,
                    mediaId: media.id
                )
                return .none
                
            case .twoFingerDoubleTapped:
                /// Enter fullscreen transcript mode
                /// Populate the shared state with recording data for playback viewing
                @Shared(.liveTranscription) var liveTranscription
                $liveTranscription.withLock { transcription in
                    transcription.segments = state.recording.transcription.segments
                    transcription.words = state.recording.transcription.words
                    transcription.volatileText = nil
                    transcription.currentTime = state.currentTime
                    transcription.currentWordIndex = state.currentWordIndex
                }
                state.fullscreenTranscript = FullscreenTranscriptFeature.State()
                return .none
                
            case .fullscreenImage(.presented(.delegate(.didClose))):
                state.fullscreenImage = nil
                return .none
                
            case .fullscreenImage:
                return .none
                
            case .fullscreenTranscript(.presented(.delegate(.didClose))):
                state.fullscreenTranscript = nil
                return .none
                
            case .fullscreenTranscript:
                return .none
                
            case .delegate:
                return .none
            }
        }
        .ifLet(\.$fullscreenImage, action: \.fullscreenImage) {
            FullscreenImageFeature()
        }
        .ifLet(\.$fullscreenTranscript, action: \.fullscreenTranscript) {
            FullscreenTranscriptFeature()
        }
    }
    
    // MARK: - Helpers
    
    /// Find the index of the word at the given time
    private func findWordIndex(at time: TimeInterval, in words: [TimestampedWord]) -> Int? {
        words.firstIndex { word in
            time >= word.startTime && time < word.endTime
        }
    }
}