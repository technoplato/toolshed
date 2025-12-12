/**
 HOW:
   Used as the root reducer for the application.
   
   ```swift
   let store = Store(initialState: AppFeature.State()) {
       AppFeature()
   }
   ```
   
   [Inputs]
   - Child feature actions
   - Recording feature actions (at app level for persistence when minimized)
   
   [Outputs]
   - Composed state from child features
   - Active recording state (persists when minimized)
   
   [Side Effects]
   - Delegates to child features

 WHO:
   AI Agent, Developer
   (Context: Root app feature for SpeechRecorderApp)

 WHAT:
   The root TCA reducer that composes all child features.
   Holds recording state at app level so it persists when the modal is minimized.
   This enables the "collapsible recording modal" pattern like Otter.ai.
   
   **Migration Note (2025-12-11):**
   Updated to handle selectRecording(Recording.ID) instead of selectRecording(Recording).
   This supports the derived shared state pattern.
   
   **Migration Note (2025-12-12):**
   FIXED: Removed the Destination enum pattern which was causing duplicate state.
   Now uses a single activeRecording: RecordingFeature.State? with isRecordingExpanded: Bool.
   This ensures only ONE RecordingFeature reducer runs, and effects continue when minimized.
   
   The previous architecture had TWO RecordingFeature instances:
   - One via .ifLet(\.$destination, action: \.destination)
   - One via .ifLet(\.activeRecording, action: \.activeRecording)
   
   This caused timer/transcription to stop when minimizing because effects were
   tied to the destination scope which was dismissed.
   
   See: docs/swift-sharing-state-comprehensive-guide.md#appendix-a-speechrecorderapp-migration-guide

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-12
   [Change Log:
     - 2025-12-11: Updated selectRecording handling for Recording.ID
     - 2025-12-12: Fixed minimized recording bug by removing Destination enum
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/AppFeature.swift

 WHY:
   To provide a single root reducer for the application.
   Recording state is held here (not in RecordingsListFeature) so it persists
   when the user minimizes the recording modal to browse the app.
   
   Using a simple isRecordingExpanded boolean instead of Destination enum:
   - Single source of truth for recording state (activeRecording)
   - Effects continue running when modal is minimized
   - Simpler architecture with less state synchronization
 */

import ComposableArchitecture
import Foundation

@Reducer
struct AppFeature {
    
    // MARK: - State
    
    @ObservableState
    struct State: Equatable {
        /// The recordings list feature state
        var recordingsList = RecordingsListFeature.State()
        
        /// Active recording state (nil when not recording)
        /// Held at app level so it persists when modal is minimized
        /// This is the SINGLE source of truth for recording state
        var activeRecording: RecordingFeature.State?
        
        /// Whether the recording modal is expanded (fullscreen)
        /// When false and activeRecording is non-nil, shows the floating indicator
        var isRecordingExpanded: Bool = false
        
        /// Live transcription state - owned at app level for sharing with child features
        /// RecordingFeature and FullscreenTranscriptFeature receive derived references
        @Shared(.liveTranscription) var liveTranscription: LiveTranscriptionState
        
        /// Shared active recording for RecordingsListFeature to display
        /// This is a Recording (not RecordingFeature.State) for the list view
        @Shared(.activeRecording) var sharedActiveRecording: Recording?
        
        /// Whether there's an active recording in progress
        var hasActiveRecording: Bool {
            activeRecording?.isRecording == true
        }
        
        /// The URL of the active recording (for preventing playback)
        var activeRecordingURL: URL? {
            activeRecording?.recordingURL
        }
    }
    
    // MARK: - Action
    
    enum Action: Sendable, BindableAction {
        /// Recordings list feature actions
        case recordingsList(RecordingsListFeature.Action)
        
        /// Active recording feature actions
        /// This is the ONLY place RecordingFeature actions are handled
        case activeRecording(RecordingFeature.Action)
        
        /// Binding action for isRecordingExpanded
        case binding(BindingAction<State>)
        
        /// User tapped the floating recording indicator to expand
        case floatingIndicatorTapped
        
        /// User swiped down to minimize the recording modal
        case minimizeRecording
        
        /// User tapped record button (starts new recording)
        case startRecording
        
        /// Recording finished - save and clear
        case recordingFinished(Result<Recording, RecordingFeature.RecordingError>)
    }
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        /// Binding reducer for isRecordingExpanded
        BindingReducer()
        
        /// Pre-process actions BEFORE child reducers run
        /// This allows us to intercept and block certain actions
        Reduce { state, action in
            switch action {
            case let .recordingsList(.selectRecording(recordingID)):
                /**
                 Check if user is trying to play the active recording.
                 
                 **Migration Note (2025-12-11):**
                 Updated to use Recording.ID for lookup, then compare URLs.
                 The active recording doesn't have an ID until it's saved,
                 so we compare URLs instead.
                 */
                if let activeURL = state.activeRecordingURL,
                   let recording = state.recordingsList.recordings[id: recordingID],
                   recording.audioURL == activeURL {
                    /// Show alert - cannot play recording that's currently being recorded
                    state.recordingsList.alert = AlertState {
                        TextState("Recording in Progress")
                    } actions: {
                        ButtonState(role: .cancel) {
                            TextState("OK")
                        }
                    } message: {
                        TextState("You cannot play a recording while it's still being recorded. Stop the recording first to play it back.")
                    }
                    /// Return .none to prevent the action from reaching RecordingsListFeature
                    /// But we need a way to signal that we handled it...
                }
                /// Let the action pass through to RecordingsListFeature
                return .none
                
            default:
                return .none
            }
        }
        
        /// Child reducer for recordings list
        /// Note: We need to conditionally skip this for blocked selectRecording actions
        Scope(state: \.recordingsList, action: \.recordingsList) {
            RecordingsListFeature()
        }
        
        /// Main reducer for app-level actions
        Reduce { state, action in
            switch action {
            case .binding:
                /// Handle binding changes (e.g., isRecordingExpanded toggled by sheet dismiss)
                return .none
                
            case .startRecording:
                /// Reset live transcription state before starting new recording
                state.$liveTranscription.withLock { transcription in
                    transcription = LiveTranscriptionState()
                }
                
                /// Create new recording state with shared liveTranscription from AppFeature
                /// This is the SINGLE source of truth - no copying to destination
                let recordingState = RecordingFeature.State(
                    liveTranscription: state.$liveTranscription
                )
                state.activeRecording = recordingState
                state.isRecordingExpanded = true
                
                /// Create initial shared Recording for RecordingsListFeature to display
                updateSharedActiveRecording(state: &state)
                
                /// Auto-start recording
                return .send(.activeRecording(.recordButtonTapped))
                
            case .floatingIndicatorTapped:
                /// Expand the minimized recording modal
                state.isRecordingExpanded = true
                return .none
                
            case .activeRecording(.timerTicked):
                /// Sync timer updates to shared state for RecordingsListFeature
                updateSharedActiveRecording(state: &state)
                return .none
                
            case .activeRecording(.transcriptionResult):
                /// Sync transcription updates to shared state for RecordingsListFeature
                updateSharedActiveRecording(state: &state)
                return .none
                
            case .minimizeRecording:
                /// Minimize the recording modal (recording continues in background)
                /// No state sync needed - activeRecording IS the single source of truth
                state.isRecordingExpanded = false
                return .none
                
            case .activeRecording(.delegate(.didFinish(let result))):
                /// Recording finished - save to list and clear
                state.activeRecording = nil
                state.isRecordingExpanded = false
                /// Clear shared active recording
                state.$sharedActiveRecording.withLock { $0 = nil }
                return .send(.recordingFinished(result))
                
            case .activeRecording(.cancelButtonTapped):
                /// User cancelled - clear active recording
                state.activeRecording = nil
                state.isRecordingExpanded = false
                /// Clear shared active recording
                state.$sharedActiveRecording.withLock { $0 = nil }
                return .none
                
            case .activeRecording:
                /// All other recording actions are handled by the child reducer
                /// Effects continue running regardless of isRecordingExpanded
                return .none
                
            case .recordingFinished(.success(let recording)):
                /// Add recording to the list
                state.recordingsList.$recordings.withLock { recordings in
                    recordings.insert(recording, at: 0)
                }
                return .none
                
            case .recordingFinished(.failure):
                /// Recording failed - already cleared
                return .none
                
            case .recordingsList(.recordButtonTapped):
                /// Intercept record button tap from list and start recording at app level
                return .send(.startRecording)
                
            case let .recordingsList(.selectRecording(recordingID)):
                /**
                 Handle selectRecording after child reducer processes it.
                 
                 **Migration Note (2025-12-11):**
                 Updated to use Recording.ID instead of Recording object.
                 */
                if state.recordingsList.alert != nil {
                    /// Already handled by pre-processor, clear the playback that was set
                    state.recordingsList.playback = nil
                }
                return .none
                
            case .recordingsList:
                return .none
            }
        }
        /// Only ONE RecordingFeature reducer - tied to activeRecording
        /// Effects continue running when isRecordingExpanded changes
        .ifLet(\.activeRecording, action: \.activeRecording) {
            RecordingFeature()
        }
    }
    
    // MARK: - Private Helpers
    
    /**
     Updates the shared active recording from the current RecordingFeature.State.
     
     This converts RecordingFeature.State to Recording so RecordingsListFeature
     can display the active recording in the list with a LIVE indicator.
     */
    private func updateSharedActiveRecording(state: inout State) {
        guard let activeRecording = state.activeRecording,
              let recordingURL = activeRecording.recordingURL,
              let startTime = activeRecording.recordingStartTime else {
            return
        }
        
        let recording = Recording(
            id: UUID(),
            title: activeRecording.title,
            date: startTime,
            duration: activeRecording.duration,
            audioURL: recordingURL,
            transcription: activeRecording.transcription,
            media: activeRecording.capturedMedia
        )
        
        state.$sharedActiveRecording.withLock { $0 = recording }
    }
}

// MARK: - Custom Printers

extension _ReducerPrinter where State == RecordingsListFeature.State, Action == RecordingsListFeature.Action {
    /// A custom printer that filters out noisy timer tick actions
    static var filteredActions: Self {
        Self { receivedAction, oldState, newState in
            /// Filter out playback time updates as well (50ms interval is very noisy)
            if case .playback(.presented(.timeUpdated)) = receivedAction {
                return
            }
            
            /// Use the default printer for all other actions
            _ReducerPrinter.customDump.printChange(receivedAction: receivedAction, oldState: oldState, newState: newState)
        }
    }
}

extension _ReducerPrinter where State == RecordingFeature.State, Action == RecordingFeature.Action {
    /**
     A custom printer that filters out noisy transcription-related state changes.
     
     The RecordingFeature has several properties that change frequently during recording:
     - `finalizedWords`: Array of timestamped words (grows with each transcription result)
     - `finalizedSegments`: Array of transcription segments
     - `transcription`: The full transcription object
     - `volatileTranscription`: In-progress transcription text
     - `currentAudioLevel`: Audio level for waveform (updates very frequently)
     - `timerTicked`: Fires every second
     
     This printer shows the action but uses a custom diff that excludes these noisy fields.
     */
    static var recordingFiltered: Self {
        Self { receivedAction, oldState, newState in
            /// Filter out very noisy actions entirely
            switch receivedAction {
            case .timerTicked:
                /// Skip timer ticks entirely - too noisy
                return
                
            case .audioLevelReceived:
                /// Skip audio level updates entirely - too noisy
                return
                
            case .transcriptionResult:
                /// Print action on one line, state changes on the next
                let wordCount = newState.finalizedWords.count
                let segmentCount = newState.finalizedSegments.count
                let volatilePreview = newState.volatileTranscription.prefix(50)
                print("RecordingFeature: transcriptionResult")
                print("  → words: \(wordCount), segments: \(segmentCount), volatile: \"\(volatilePreview)...\"")
                return
                
            default:
                break
            }
            
            /// For other actions, create a filtered state for diffing
            /// that excludes the noisy transcription fields
            var filteredOldState = oldState
            var filteredNewState = newState
            
            /// Zero out the noisy fields so they don't appear in the diff
            /// Note: finalizedWords, finalizedSegments, volatileTranscription are now computed
            /// properties from liveTranscription, so we reset the shared state instead
            filteredOldState.$liveTranscription.withLock { $0 = LiveTranscriptionState() }
            filteredNewState.$liveTranscription.withLock { $0 = LiveTranscriptionState() }
            filteredOldState.transcription = .empty
            filteredNewState.transcription = .empty
            filteredOldState.currentAudioLevel = 0
            filteredNewState.currentAudioLevel = 0
            filteredOldState.duration = 0
            filteredNewState.duration = 0
            
            /// Use the default printer with filtered state
            _ReducerPrinter.customDump.printChange(
                receivedAction: receivedAction,
                oldState: filteredOldState,
                newState: filteredNewState
            )
        }
    }
}

extension _ReducerPrinter where State == AppFeature.State, Action == AppFeature.Action {
    /**
     A custom printer for AppFeature that filters out noisy activeRecording state changes.
     
     This filters:
     - Timer ticks (duration changes)
     - Audio level updates
     - Transcription results (shows summary instead)
     - All the noisy transcription-related fields in state diffs
     */
    static var appFiltered: Self {
        Self { receivedAction, oldState, newState in
            /// Filter out very noisy actions entirely
            switch receivedAction {
            case .activeRecording(.timerTicked):
                /// Skip timer ticks entirely - too noisy
                return
                
            case .activeRecording(.audioLevelReceived):
                /// Skip audio level updates entirely - too noisy
                return
                
            case .activeRecording(.transcriptionResult):
                /// Print action on one line, state changes on the next
                if let recording = newState.activeRecording {
                    let wordCount = recording.finalizedWords.count
                    let segmentCount = recording.finalizedSegments.count
                    let volatilePreview = recording.volatileTranscription.prefix(50)
                    print("AppFeature: transcriptionResult")
                    print("  → words: \(wordCount), segments: \(segmentCount), volatile: \"\(volatilePreview)...\"")
                }
                return
                
            case .binding:
                /// Skip binding actions - usually just isRecordingExpanded changes
                return
                
            default:
                break
            }
            
            /// For other actions, create a filtered state for diffing
            var filteredOldState = oldState
            var filteredNewState = newState
            
            /// Filter the activeRecording state if present
            /// Note: finalizedWords, finalizedSegments, volatileTranscription are now computed
            /// properties from liveTranscription, so we reset the shared state instead
            if var oldRecording = filteredOldState.activeRecording {
                oldRecording.$liveTranscription.withLock { $0 = LiveTranscriptionState() }
                oldRecording.transcription = .empty
                oldRecording.currentAudioLevel = 0
                oldRecording.duration = 0
                filteredOldState.activeRecording = oldRecording
            }
            
            if var newRecording = filteredNewState.activeRecording {
                newRecording.$liveTranscription.withLock { $0 = LiveTranscriptionState() }
                newRecording.transcription = .empty
                newRecording.currentAudioLevel = 0
                newRecording.duration = 0
                filteredNewState.activeRecording = newRecording
            }
            
            /// Use the default printer with filtered state
            _ReducerPrinter.customDump.printChange(
                receivedAction: receivedAction,
                oldState: filteredOldState,
                newState: filteredNewState
            )
        }
    }
}
