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
   - Photo events: photoLibraryAuthorizationResponse, newPhotoDetected
   
   [Outputs]
   - State changes for UI updates
   - Delegate actions for parent feature
   
   [Side Effects]
   - Requests microphone permission
   - Requests photo library permission
   - Starts/stops audio recording
   - Runs timer for duration updates
   - Performs live speech transcription
   - Observes photo library for new photos/screenshots

 WHO:
   AI Agent, Developer
   (Context: TCA reducer for recording functionality)

 WHAT:
   TCA reducer for managing audio recording state and actions.
   Handles permission requests, recording lifecycle, timer updates,
   live speech transcription with word-level timestamps, and
   photo/screenshot synchronization.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/RecordingFeature.swift

 WHY:
   To provide a testable, composable recording feature.
   Follows TCA patterns for state management and side effects.
 */

import AVFoundation
import ComposableArchitecture
import Foundation
import UIKit

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
        
        /// Photo library authorization status
        var photoLibraryAuthorizationStatus: PhotoLibraryClient.AuthorizationStatus = .notDetermined
        
        /// Current mode of the recording feature
        var mode: Mode = .idle
        
        /// Alert state for permission errors
        @Presents var alert: AlertState<Action.Alert>?
        
        /// The URL where the recording will be saved
        var recordingURL: URL?
        
        /// Live transcription text (volatile, in-progress for current segment)
        var volatileTranscription: String = ""
        
        /// Accumulated finalized text from all completed segments
        var finalizedText: String = ""
        
        /// Accumulated finalized words from all completed segments
        var finalizedWords: [TimestampedWord] = []
        
        /// Accumulated finalized segments
        var finalizedSegments: [TranscriptionSegment] = []
        
        /// Finalized transcription (combines all segments)
        var transcription: Transcription = .empty
        
        /// Full transcription text (finalized + volatile)
        var fullTranscriptionText: String {
            let trimmedFinalized = finalizedText.trimmingCharacters(in: .whitespaces)
            let trimmedVolatile = volatileTranscription.trimmingCharacters(in: .whitespaces)
            
            if trimmedFinalized.isEmpty {
                return trimmedVolatile
            } else if trimmedVolatile.isEmpty {
                return trimmedFinalized
            } else {
                return trimmedFinalized + " " + trimmedVolatile
            }
        }
        
        /// Whether speech assets are being downloaded
        var isDownloadingAssets = false
        
        /// Error message for speech recognition issues
        var speechError: String?
        
        /// Photos and screenshots captured during recording
        var capturedMedia: [TimestampedMedia] = []
        
        /// Thumbnails for captured media (keyed by media ID)
        var mediaThumbnails: [UUID: UIImage] = [:]
        
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
        
        /// Photo library authorization response received
        case photoLibraryAuthorizationResponse(PhotoLibraryClient.AuthorizationStatus)
        
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
        
        /// New photo or screenshot detected during recording
        case newPhotoDetected(PhotoAsset)
        
        /// Thumbnail loaded for a media item
        case thumbnailLoaded(UUID, UIImage)
        
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
    @Dependency(\.photoLibrary) var photoLibrary
    @Dependency(\.continuousClock) var clock
    @Dependency(\.date) var date
    @Dependency(\.uuid) var uuid
    
    // MARK: - Cancellation IDs
    
    private enum CancelID {
        case recording
        case timer
        case transcription
        case photoObservation
        case audioStreaming
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
                state.finalizedText = ""
                state.finalizedWords = []
                state.finalizedSegments = []
                state.transcription = .empty
                state.speechError = nil
                state.capturedMedia = []
                state.mediaThumbnails = [:]
                
                /// Generate recording URL
                let recordingURL = FileManager.default.temporaryDirectory
                    .appendingPathComponent(uuid().uuidString)
                    .appendingPathExtension("m4a")
                state.recordingURL = recordingURL
                
                return .run { send in
                    /// Request microphone, speech, and photo library permissions
                    async let micPermission = audioRecorder.requestRecordPermission()
                    async let speechAuth = speechClient.requestAuthorization()
                    async let photoAuth = photoLibrary.requestAuthorization()
                    
                    let hasMicPermission = await micPermission
                    let speechStatus = await speechAuth
                    let photoStatus = await photoAuth
                    
                    await send(.speechAuthorizationResponse(speechStatus))
                    await send(.photoLibraryAuthorizationResponse(photoStatus))
                    await send(.permissionResponse(hasMicPermission))
                }
                
            case let .speechAuthorizationResponse(status):
                state.speechAuthorizationStatus = status
                return .none
                
            case let .photoLibraryAuthorizationResponse(status):
                state.photoLibraryAuthorizationStatus = status
                return .none
                
            case let .permissionResponse(granted):
                state.hasPermission = granted
                
                if granted {
                    guard let recordingURL = state.recordingURL else {
                        return .none
                    }
                    
                    let speechAuthorized = state.speechAuthorizationStatus == .authorized
                    let photoAuthorized = state.photoLibraryAuthorizationStatus == .authorized ||
                                          state.photoLibraryAuthorizationStatus == .limited
                    
                    return .merge(
                        /// Start recording and stream audio buffers to speech client
                        .run { send in
                            do {
                                /// Start recording - returns a stream of audio buffers
                                let bufferStream = try await audioRecorder.startRecording(url: recordingURL)
                                await send(.recordingStarted)
                                
                                /// Stream each buffer to the speech client for transcription
                                for await buffer in bufferStream {
                                    await speechClient.streamAudio(buffer)
                                }
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
                        speechAuthorized ? startTranscription() : .none,
                        
                        /// Start photo observation if authorized
                        photoAuthorized ? startPhotoObservation() : .none
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
                    .cancel(id: CancelID.transcription),
                    .cancel(id: CancelID.photoObservation),
                    .run { _ in
                        await photoLibrary.stopObserving()
                    }
                )
                
            case let .transcriptionResult(result):
                if result.isFinal {
                    /// Append finalized segment to accumulated text
                    let segmentText = result.text.trimmingCharacters(in: .whitespaces)
                    if !segmentText.isEmpty {
                        if state.finalizedText.isEmpty {
                            state.finalizedText = segmentText
                        } else {
                            state.finalizedText += " " + segmentText
                        }
                        
                        /// Create a segment for this finalized result
                        let segment = TranscriptionSegment(
                            text: segmentText,
                            words: result.words
                        )
                        state.finalizedSegments.append(segment)
                    }
                    
                    /// Append finalized words to accumulated words
                    state.finalizedWords.append(contentsOf: result.words)
                    
                    /// Clear volatile since this segment is now finalized
                    state.volatileTranscription = ""
                    
                    /// Update the transcription with all accumulated data
                    state.transcription = Transcription(
                        text: state.finalizedText,
                        words: state.finalizedWords,
                        segments: state.finalizedSegments,
                        isFinal: true
                    )
                } else {
                    /// Update volatile transcription for current in-progress segment
                    state.volatileTranscription = result.text
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
                    .run { _ in
                        await photoLibrary.stopObserving()
                    },
                    .cancel(id: CancelID.transcription),
                    .cancel(id: CancelID.photoObservation)
                )
                
            case let .finalRecordingTime(duration):
                state.duration = duration
                return .none
                
            case .recordingStopped:
                state.isRecording = false
                state.mode = .idle
                
                /// Create the recording with captured media
                if let recordingURL = state.recordingURL,
                   let startTime = state.recordingStartTime {
                    let recording = Recording(
                        id: uuid(),
                        title: "",
                        date: startTime,
                        duration: state.duration,
                        audioURL: recordingURL,
                        transcription: state.transcription,
                        media: state.capturedMedia
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
                state.finalizedText = ""
                state.finalizedWords = []
                state.finalizedSegments = []
                state.transcription = .empty
                state.capturedMedia = []
                state.mediaThumbnails = [:]
                
                return .merge(
                    .cancel(id: CancelID.recording),
                    .cancel(id: CancelID.timer),
                    .cancel(id: CancelID.transcription),
                    .cancel(id: CancelID.photoObservation),
                    .run { _ in
                        await audioRecorder.stopRecording()
                        try? await speechClient.finishTranscription()
                        await photoLibrary.stopObserving()
                    }
                )
                
            case .timerTicked:
                state.duration += 1
                return .none
                
            case let .newPhotoDetected(photoAsset):
                /// Calculate the timestamp relative to recording start
                guard let startTime = state.recordingStartTime else {
                    return .none
                }
                
                let timestamp = photoAsset.creationDate.timeIntervalSince(startTime)
                
                /// Only include photos taken after recording started
                guard timestamp >= 0 else {
                    return .none
                }
                
                let mediaId = uuid()
                let media = TimestampedMedia(
                    id: mediaId,
                    timestamp: timestamp,
                    assetIdentifier: photoAsset.localIdentifier,
                    mediaType: photoAsset.mediaType == .screenshot ? .screenshot : .photo,
                    creationDate: photoAsset.creationDate
                )
                
                state.capturedMedia.append(media)
                
                /// Fetch thumbnail for display
                return .run { send in
                    if let thumbnail = await photoLibrary.fetchThumbnail(
                        photoAsset.localIdentifier,
                        CGSize(width: 100, height: 100)
                    ) {
                        await send(.thumbnailLoaded(mediaId, thumbnail))
                    }
                }
                
            case let .thumbnailLoaded(mediaId, image):
                state.mediaThumbnails[mediaId] = image
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
                /// Use the current locale or default to en_US
                let locale = Locale(identifier: "en_US")
                
                /// Start transcription - the LiveSpeechClient will handle:
                /// 1. Creating the transcriber (which subscribes to the asset)
                /// 2. Checking if assets are installed
                /// 3. Downloading assets if needed
                /// 4. Starting the transcription stream
                ///
                /// Note: We don't check isAssetInstalled separately because
                /// you cannot check asset status without first having a transcriber
                /// that subscribes to that asset. The "not subscribed" error occurs
                /// when trying to check status before creating a transcriber.
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
    
    private func startPhotoObservation() -> Effect<Action> {
        .run { send in
            let stream = await photoLibrary.observeNewPhotos()
            
            for await photoAsset in stream {
                await send(.newPhotoDetected(photoAsset))
            }
        }
        .cancellable(id: CancelID.photoObservation)
    }
}