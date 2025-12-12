/**
 HOW:
   Use in SwiftUI views with StoreOf<RecordingsListFeature>.
   
   ```swift
   RecordingsListView(store: store.scope(state: \.recordingsList, action: \.recordingsList))
   ```
   
   [Inputs]
   - User actions: recordButtonTapped, selectRecording, deleteRecording
   - Child feature actions: playback
   
   [Outputs]
   - List of recordings
   - Presented playback sheet
   
   [Side Effects]
   - Persists recordings to disk via @Shared

 WHO:
   AI Agent, Developer
   (Context: TCA reducer for recordings list)

 WHAT:
   TCA reducer for managing the list of recordings.
   Handles adding, deleting, and selecting recordings.
   Uses @Shared for persistence with Swift Sharing.
   
   Note: Recording is now handled at AppFeature level to support
   the collapsible modal pattern (recording persists when minimized).
   
   **Migration Note (2025-12-11):**
   Updated to use IdentifiedArrayOf<Recording> for O(1) lookup by ID.
   Default value is now embedded in the SharedKey definition.
   
   Reference: SyncUpsList.swift:17-21
   https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpsList.swift
   
   See: docs/swift-sharing-state-comprehensive-guide.md#appendix-a-speechrecorderapp-migration-guide

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-12
   [Change Log:
     - 2025-12-11: Migrated to IdentifiedArrayOf<Recording> for O(1) lookup
                   Removed default value (now embedded in SharedKey)
     - 2025-12-12: Added @Shared(.activeRecording) and @Shared(.liveTranscription)
                   for displaying active recording in list (Phase 2.3)
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingsListFeature.swift

 WHY:
   To provide a testable, composable recordings list feature.
   Uses Swift Sharing for automatic persistence to disk.
   
   Using IdentifiedArrayOf:
   1. O(1) lookup by ID instead of O(n) with plain arrays
   2. Matches the production SyncUps app pattern
   3. Enables derived shared state for child features
 */

import ComposableArchitecture
import Foundation

@Reducer
struct RecordingsListFeature {
    
    // MARK: - State
    
    @ObservableState
    struct State: Equatable {
        /**
         The list of recordings, persisted to disk.
         
         **Pattern Source:** SyncUpsList.swift:20
         
         Uses IdentifiedArrayOf for O(1) lookup by ID.
         No default value needed - embedded in SharedKey definition.
         */
        @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording>
        
        /**
         Access to the active recording being created.
         
         **Phase 2.3 Addition (2025-12-12):**
         This allows RecordingsListView to display the active recording
         at the top of the list with a LIVE indicator while recording is in progress.
         
         The state is owned by AppFeature and shared here for read access.
         */
        @Shared(.activeRecording) var activeRecording: Recording?
        
        /**
         Access to live transcription for preview.
         
         **Phase 2.3 Addition (2025-12-12):**
         This allows RecordingsListView to show the most recent transcription
         segment as a preview in the active recording row.
         
         The state is owned by AppFeature and shared here for read access.
         */
        @Shared(.liveTranscription) var liveTranscription: LiveTranscriptionState
        
        /// Currently presented playback sheet
        @Presents var playback: PlaybackFeature.State?
        
        /// Alert for when user tries to play active recording
        @Presents var alert: AlertState<Action.Alert>?
    }
    
    // MARK: - Action
    
    enum Action: Sendable {
        /// User tapped the record button (forwarded to AppFeature)
        case recordButtonTapped
        
        /**
         User selected a recording for playback.
         
         **Pattern Source:** SyncUpsList.swift - uses ID for selection
         
         Changed from `selectRecording(Recording)` to `selectRecording(Recording.ID)`
         to enable derived shared state lookup.
         */
        case selectRecording(Recording.ID)
        
        /// User deleted recordings at indices
        case deleteRecordings(IndexSet)
        
        /// Playback feature actions
        case playback(PresentationAction<PlaybackFeature.Action>)
        
        /// Alert actions
        case alert(PresentationAction<Alert>)
        
        enum Alert: Equatable, Sendable {}
    }
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case .recordButtonTapped:
                /// This action is intercepted by AppFeature to start recording at app level
                return .none
                
            case let .selectRecording(recordingID):
                /**
                 Derive shared state for the selected recording.
                 
                 **Pattern Source:** SyncUpsList.swift:83-86
                 
                 Uses Shared($recordings[id:]) to get a derived Shared<Recording>
                 that propagates mutations back to the parent's recordings list.
                 */
                guard let sharedRecording = Shared(state.$recordings[id: recordingID]) else {
                    return .none
                }
                state.playback = PlaybackFeature.State(recording: sharedRecording)
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
                
            case .playback(.presented(.delegate(.didClose))):
                state.playback = nil
                return .none
                
            case .playback:
                return .none
                
            case .alert(.dismiss):
                state.alert = nil
                return .none
                
            case .alert:
                return .none
            }
        }
        .ifLet(\.$playback, action: \.playback) {
            PlaybackFeature()
        }
        .ifLet(\.$alert, action: \.alert)
    }
}