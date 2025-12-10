/**
 HOW:
   Use in SwiftUI views with StoreOf<RecordingFeature>.
   
   ```swift
   struct RecordingView: View {
       @Bindable var store: StoreOf<RecordingFeature>
       
       var body: some View {
           // Use store.isRecording, store.duration, etc.
           Button("Record") { store.send(.recordButtonTapped) }
       }
   }
   ```
   
   [Inputs]
   - User actions: recordButtonTapped, stopButtonTapped, cancelButtonTapped
   - System events: permissionResponse, timerTicked, recordingStopped
   
   [Outputs]
   - State changes for UI updates
   - Delegate actions for parent feature
   
   [Side Effects]
   - Requests microphone permission
   - Starts/stops audio recording
   - Runs timer for duration updates

 WHO:
   AI Agent, Developer
   (Context: TCA reducer for recording functionality)

 WHAT:
   TCA reducer for managing audio recording state and actions.
   Handles permission requests, recording lifecycle, and timer updates.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingFeature.swift

 WHY:
   To provide a testable, composable recording feature.
   Follows TCA patterns for state management and side effects.
 */

import ComposableArchitecture
import Foundation

@Reducer
struct RecordingFeature {
    
    // MARK: - State
    
    @ObservableState
    struct State: Equatable, Sendable {
        /// Whether recording is in progress
        var isRecording = false
        
        /// When recording started
        var recordingStartTime: Date?
        
        /// Current recording duration in seconds
        var duration: TimeInterval = 0
        
        /// Whether microphone permission has been granted
        var hasPermission: Bool?
        
        /// Current mode of the recording feature
        var mode: Mode = .idle
        
        /// Alert state for permission errors
        @Presents var alert: AlertState<Action.Alert>?
        
        /// The URL where the recording will be saved
        var recordingURL: URL?
        
        /// Live transcription text (volatile, in-progress)
        var volatileTranscription: String = ""
        
        /// Finalized transcription
        var transcription: Transcription = .empty
        
        enum Mode: Equatable, Sendable {
            case idle
            case recording
            case encoding
        }
    }
    
    // MARK: - Action
    
    enum Action: Sendable {
        /// User tapped the record button
        case recordButtonTapped
        
        /// User tapped the stop button
        case stopButtonTapped
        
        /// User tapped the cancel button
        case cancelButtonTapped
        
        /// Permission response received
        case permissionResponse(Bool)
        
        /// Timer ticked (1 second interval)
        case timerTicked
        
        /// Final recording time received
        case finalRecordingTime(TimeInterval)
        
        /// Recording has stopped
        case recordingStopped
        
        /// Recording started successfully
        case recordingStarted
        
        /// Recording failed with error
        case recordingFailed(Error)
        
        /// Alert actions
        case alert(PresentationAction<Alert>)
        
        /// Delegate actions for parent feature
        case delegate(Delegate)
        
        enum Alert: Equatable, Sendable {}
        
        @CasePathable
        enum Delegate: Equatable, Sendable {
            case didFinish(Result<Recording, RecordingError>)
        }
    }
    
    // MARK: - Errors
    
    enum RecordingError: Error, Equatable, Sendable {
        case permissionDenied
        case recordingFailed
        case cancelled
    }
    
    // MARK: - Dependencies
    
    @Dependency(\.audioRecorder) var audioRecorder
    @Dependency(\.continuousClock) var clock
    @Dependency(\.date) var date
    @Dependency(\.uuid) var uuid
    
    // MARK: - Cancellation IDs
    
    private enum CancelID {
        case recording
        case timer
    }
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case .recordButtonTapped:
                state.isRecording = true
                state.recordingStartTime = date.now
                state.mode = .recording
                
                /// Generate recording URL
                let recordingURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent(uuid().uuidString)
                    .appendingPathExtension("m4a")
                state.recordingURL = recordingURL
                
                return .run { send in
                    let hasPermission = await audioRecorder.requestRecordPermission()
                    await send(.permissionResponse(hasPermission))
                }
                
            case let .permissionResponse(granted):
                state.hasPermission = granted
                
                if granted {
                    guard let recordingURL = state.recordingURL else {
                        return .none
                    }
                    
                    return .merge(
                        /// Start recording
                        .run { send in
                            do {
                                try await audioRecorder.startRecording(url: recordingURL)
                                await send(.recordingStarted)
                            } catch {
                                await send(.recordingFailed(error))
                            }
                        }
                        .cancellable(id: CancelID.recording),
                        
                        /// Start timer
                        .run { send in
                            for await _ in clock.timer(interval: .seconds(1)) {
                                await send(.timerTicked)
                            }
                        }
                        .cancellable(id: CancelID.timer)
                    )
                } else {
                    state.isRecording = false
                    state.recordingStartTime = nil
                    state.mode = .idle
                    state.alert = AlertState {
                        TextState("Permission Required")
                    } message: {
                        TextState("Microphone access is required to record audio.")
                    }
                    return .none
                }
                
            case .recordingStarted:
                return .none
                
            case .recordingFailed:
                state.isRecording = false
                state.mode = .idle
                state.alert = AlertState {
                    TextState("Recording Failed")
                } message: {
                    TextState("An error occurred while recording.")
                }
                return .cancel(id: CancelID.timer)
                
            case .stopButtonTapped:
                state.mode = .encoding
                
                return .run { send in
                    if let currentTime = await audioRecorder.currentTime() {
                        await send(.finalRecordingTime(currentTime))
                    }
                    await audioRecorder.stopRecording()
                    await send(.recordingStopped)
                }
                
            case let .finalRecordingTime(duration):
                state.duration = duration
                return .none
                
            case .recordingStopped:
                state.isRecording = false
                state.mode = .idle
                
                /// Create the recording
                if let recordingURL = state.recordingURL,
                   let startTime = state.recordingStartTime {
                    let recording = Recording(
                        id: uuid(),
                        title: "",
                        date: startTime,
                        duration: state.duration,
                        audioURL: recordingURL,
                        transcription: state.transcription
                    )
                    return .merge(
                        .cancel(id: CancelID.timer),
                        .send(.delegate(.didFinish(.success(recording))))
                    )
                }
                
                return .cancel(id: CancelID.timer)
                
            case .cancelButtonTapped:
                state.isRecording = false
                state.duration = 0
                state.mode = .idle
                state.volatileTranscription = ""
                state.transcription = .empty
                
                return .merge(
                    .cancel(id: CancelID.recording),
                    .cancel(id: CancelID.timer),
                    .run { _ in
                        await audioRecorder.stopRecording()
                    }
                )
                
            case .timerTicked:
                state.duration += 1
                return .none
                
            case .alert(.dismiss):
                state.alert = nil
                return .none
                
            case .alert:
                return .none
                
            case .delegate:
                return .none
            }
        }
        .ifLet(\.$alert, action: \.alert)
    }
}