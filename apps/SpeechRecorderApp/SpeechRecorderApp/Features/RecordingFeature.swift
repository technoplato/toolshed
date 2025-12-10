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
   - Performs live speech transcription

 WHO:
   AI Agent, Developer
   (Context: TCA reducer for recording functionality)

 WHAT:
   TCA reducer for managing audio recording state and actions.
   Handles permission requests, recording lifecycle, timer updates,
   and live speech transcription with word-level timestamps.

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
        
        /// Whether speech recognition is authorized
        var speechAuthorizationStatus: SpeechClient.AuthorizationStatus = .notDetermined
        
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
        
        /// Whether speech assets are being downloaded
        var isDownloadingAssets = false
        
        /// Error message for speech recognition issues
        var speechError: String?
        
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
        
        /// Speech authorization response received
        case speechAuthorizationResponse(SpeechClient.AuthorizationStatus)
        
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
        
        /// Transcription result received
        case transcriptionResult(TranscriptionResult)
        
        /// Transcription stream finished
        case transcriptionFinished
        
        /// Transcription failed with error
        case transcriptionFailed(Error)
        
        /// Speech assets download started
        case assetsDownloadStarted
        
        /// Speech assets download completed
        case assetsDownloadCompleted
        
        /// Speech assets download failed
        case assetsDownloadFailed(Error)
        
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
        case speechNotAuthorized
    }
    
    // MARK: - Dependencies
    
    @Dependency(\.audioRecorder) var audioRecorder
    @Dependency(\.speechClient) var speechClient
    @Dependency(\.continuousClock) var clock
    @Dependency(\.date) var date
    @Dependency(\.uuid) var uuid
    
    // MARK: - Cancellation IDs
    
    private enum CancelID {
        case recording
        case timer
        case transcription
    }
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case .recordButtonTapped:
                state.isRecording = true
                state.recordingStartTime = date.now
                state.mode = .recording
                state.volatileTranscription = ""
                state.transcription = .empty
                state.speechError = nil
                
                /// Generate recording URL
                let recordingURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent(uuid().uuidString)
                    .appendingPathExtension("m4a")
                state.recordingURL = recordingURL
                
                return .run { send in
                    /// Request both microphone and speech permissions
                    async let micPermission = audioRecorder.requestRecordPermission()
                    async let speechAuth = speechClient.requestAuthorization()
                    
                    let hasMicPermission = await micPermission
                    let speechStatus = await speechAuth
                    
                    await send(.speechAuthorizationResponse(speechStatus))
                    await send(.permissionResponse(hasMicPermission))
                }
                
            case let .speechAuthorizationResponse(status):
                state.speechAuthorizationStatus = status
                return .none
                
            case let .permissionResponse(granted):
                state.hasPermission = granted
                
                if granted {
                    guard let recordingURL = state.recordingURL else {
                        return .none
                    }
                    
                    let speechAuthorized = state.speechAuthorizationStatus == .authorized
                    
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
                        .cancellable(id: CancelID.timer),
                        
                        /// Start transcription if authorized
                        speechAuthorized ? startTranscription() : .none
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
                return .merge(
                    .cancel(id: CancelID.timer),
                    .cancel(id: CancelID.transcription)
                )
                
            case let .transcriptionResult(result):
                state.volatileTranscription = result.text
                
                /// If this is a final result, update the transcription
                if result.isFinal {
                    state.transcription = Transcription(
                        text: result.text,
                        words: result.words,
                        isFinal: true
                    )
                }
                return .none
                
            case .transcriptionFinished:
                /// Transcription stream ended normally
                return .none
                
            case let .transcriptionFailed(error):
                state.speechError = error.localizedDescription
                /// Continue recording even if transcription fails
                return .none
                
            case .assetsDownloadStarted:
                state.isDownloadingAssets = true
                return .none
                
            case .assetsDownloadCompleted:
                state.isDownloadingAssets = false
                /// Restart transcription after assets are downloaded
                return startTranscription()
                
            case let .assetsDownloadFailed(error):
                state.isDownloadingAssets = false
                state.speechError = "Failed to download speech assets: \(error.localizedDescription)"
                return .none
                
            case .stopButtonTapped:
                state.mode = .encoding
                
                return .merge(
                    .run { send in
                        if let currentTime = await audioRecorder.currentTime() {
                            await send(.finalRecordingTime(currentTime))
                        }
                        await audioRecorder.stopRecording()
                        await send(.recordingStopped)
                    },
                    .run { _ in
                        try? await speechClient.finishTranscription()
                    },
                    .cancel(id: CancelID.transcription)
                )
                
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
                    .cancel(id: CancelID.transcription),
                    .run { _ in
                        await audioRecorder.stopRecording()
                        try? await speechClient.finishTranscription()
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
    
    // MARK: - Private Helpers
    
    private func startTranscription() -> Effect<Action> {
        .run { send in
            do {
                /// Ensure assets are installed
                let locale = Locale(identifier: "en_US")
                let isInstalled = await speechClient.isAssetInstalled(locale)
                
                if !isInstalled {
                    await send(.assetsDownloadStarted)
                    try await speechClient.ensureAssets(locale)
                    await send(.assetsDownloadCompleted)
                    return
                }
                
                /// Start transcription
                let stream = try await speechClient.startTranscription(locale)
                
                for try await result in stream {
                    await send(.transcriptionResult(result))
                }
                
                await send(.transcriptionFinished)
            } catch {
                await send(.transcriptionFailed(error))
            }
        }
        .cancellable(id: CancelID.transcription)
    }
}