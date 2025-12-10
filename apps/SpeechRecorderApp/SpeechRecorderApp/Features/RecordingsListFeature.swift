/**
 HOW:
   Use in SwiftUI views with StoreOf<RecordingsListFeature>.
   
   ```swift
   RecordingsListView(store: store.scope(state: \.recordingsList, action: \.recordingsList))
   ```
   
   [Inputs]
   - User actions: recordButtonTapped, selectRecording, deleteRecording
   - Child feature actions: recording, playback
   
   [Outputs]
   - List of recordings
   - Presented recording/playback sheets
   
   [Side Effects]
   - Persists recordings to disk via @Shared

 WHO:
   AI Agent, Developer
   (Context: TCA reducer for recordings list)

 WHAT:
   TCA reducer for managing the list of recordings.
   Handles adding, deleting, and selecting recordings.
   Uses @Shared for persistence with Swift Sharing.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingsListFeature.swift

 WHY:
   To provide a testable, composable recordings list feature.
   Uses Swift Sharing for automatic persistence to disk.
 */

import ComposableArchitecture
import Foundation
import Sharing

@Reducer
struct RecordingsListFeature {
    
    // MARK: - State
    
    @ObservableState
    struct State: Equatable {
        /// The list of recordings, persisted to disk
        @Shared(.recordings) var recordings: [Recording] = []
        
        /// Currently presented recording sheet
        @Presents var recording: RecordingFeature.State?
        
        /// Currently presented playback sheet
        @Presents var playback: PlaybackFeature.State?
    }
    
    // MARK: - Action
    
    enum Action: Sendable {
        /// User tapped the record button
        case recordButtonTapped
        
        /// User selected a recording for playback
        case selectRecording(Recording)
        
        /// User deleted recordings at indices
        case deleteRecordings(IndexSet)
        
        /// Recording feature actions
        case recording(PresentationAction<RecordingFeature.Action>)
        
        /// Playback feature actions
        case playback(PresentationAction<PlaybackFeature.Action>)
    }
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case .recordButtonTapped:
                state.recording = RecordingFeature.State()
                return .none
                
            case let .selectRecording(recording):
                state.playback = PlaybackFeature.State(recording: recording)
                return .none
                
            case let .deleteRecordings(indexSet):
                state.$recordings.withLock { recordings in
                    /// Delete audio files
                    for index in indexSet {
                        let recording = recordings[index]
                        try? FileManager.default.removeItem(at: recording.audioURL)
                    }
                    recordings.remove(atOffsets: indexSet)
                }
                return .none
                
            case .recording(.presented(.delegate(.didFinish(.success(let recording))))):
                state.recording = nil
                state.$recordings.withLock { recordings in
                    recordings.insert(recording, at: 0)
                }
                return .none
                
            case .recording(.presented(.delegate(.didFinish(.failure)))):
                state.recording = nil
                return .none
                
            case .recording:
                return .none
                
            case .playback:
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