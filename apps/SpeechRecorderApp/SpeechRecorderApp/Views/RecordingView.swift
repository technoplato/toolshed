/**
 HOW:
   Use with a StoreOf<RecordingFeature>:
   
   ```swift
   RecordingView(store: store.scope(state: \.recording, action: \.recording))
   ```
   
   [Inputs]
   - store: StoreOf<RecordingFeature>
   
   [Outputs]
   - SwiftUI View
   
   [Side Effects]
   - Sends actions to the store

 WHO:
   AI Agent, Developer
   (Context: SwiftUI view for recording feature)

 WHAT:
   SwiftUI view for the recording interface.
   Shows record/stop button, duration, live transcription,
   asset download status, and speech recognition errors.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/RecordingView.swift

 WHY:
   To provide a user interface for recording audio.
   Displays recording state, duration, and live transcription feedback.
 */

import ComposableArchitecture
import SwiftUI

struct RecordingView: View {
    @Bindable var store: StoreOf<RecordingFeature>
    @FocusState private var isTitleFocused: Bool
    
    var body: some View {
        VStack(spacing: 12) {
            /// Header with editable title and date/time
            recordingHeader
            
            /// Live transcription with inline media (takes up most of the screen)
            TranscriptionDisplayView(
                segments: store.finalizedSegments,
                words: store.transcription.words,
                media: store.capturedMedia,
                mediaThumbnails: store.mediaThumbnails,
                currentTime: store.duration,
                currentWordIndex: nil,
                volatileText: store.volatileTranscription.isEmpty ? nil : store.volatileTranscription,
                isAutoScrollEnabled: store.isAutoScrollEnabled,
                onWordTapped: nil,
                onMediaTapped: nil,
                onUserDidScroll: {
                    store.send(.userDidScroll)
                },
                onResumeAutoScrollTapped: {
                    store.send(.resumeAutoScrollTapped)
                },
                showEmptyState: true,
                emptyStateMessage: "Start speaking...",
                emptyStateSubtitle: "Your words will appear here as you speak."
            )
            /// Two-finger double-tap to enter fullscreen
            .onTwoFingerDoubleTap {
                store.send(.twoFingerDoubleTapped)
            }
            
            /// Asset download indicator
            if store.isDownloadingAssets {
                assetDownloadIndicator
            }
            
            /// Speech error message
            if let error = store.speechError {
                speechErrorView(error)
            }
            
            /// Time display and controls
            recordingFooter
        }
        .padding(.horizontal, 8)
        .padding(.top)
        .padding(.bottom, 8)
        .task { await store.send(.task).finish() }
        .alert($store.scope(state: \.alert, action: \.alert))
        .fullScreenCover(
            item: $store.scope(state: \.fullscreenTranscript, action: \.fullscreenTranscript)
        ) { fullscreenStore in
            FullscreenTranscriptView(store: fullscreenStore)
        }
    }
    
    // MARK: - Header
    
    private var recordingHeader: some View {
        VStack(alignment: .leading, spacing: 4) {
            /// Editable title
            TextField("Recording Title", text: $store.title.sending(\.titleChanged))
                .font(.headline)
                .focused($isTitleFocused)
                .textFieldStyle(.plain)
                .submitLabel(.done)
                .onSubmit {
                    isTitleFocused = false
                }
            
            /// Date and duration info
            if let startTime = store.recordingStartTime {
                HStack(spacing: 8) {
                    /// Start date/time
                    Text(formatHumanReadableDateShort(startTime))
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    Text("·")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    
                    /// Duration
                    Text("Duration: \(formatDurationHMS(store.duration))")
                        .font(.caption.monospacedDigit())
                        .foregroundColor(.secondary)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 8)
    }
    
    // MARK: - Subviews
    
    private var assetDownloadIndicator: some View {
        HStack(spacing: 8) {
            ProgressView()
                .progressViewStyle(CircularProgressViewStyle())
            
            Text("Downloading speech recognition assets...")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color.blue.opacity(0.1))
        .cornerRadius(8)
    }
    
    private func speechErrorView(_ error: String) -> some View {
        HStack(spacing: 8) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundColor(.orange)
            
            Text(error)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color.orange.opacity(0.1))
        .cornerRadius(8)
    }
    
    // MARK: - Footer
    
    private var recordingFooter: some View {
        VStack(spacing: 12) {
            /// Audio waveform visualization (only when recording)
            if store.isRecording {
                audioWaveform
            }
            
            /// Time display with recording indicator
            timeDisplay
            
            /// Recording controls
            recordingControls
        }
    }
    
    private var audioWaveform: some View {
        RollingWaveformView(
            currentLevel: store.currentAudioLevel,
            isRecording: store.isRecording,
            isPaused: store.isPaused,
            barColor: Color.red
        )
        .padding(EdgeInsets(top: 0, leading: 8, bottom: 0, trailing: 8))
    }
    
    private var timeDisplay: some View {
        HStack {
            /// Duration with milliseconds
            Text(formatDurationHMSms(store.duration))
                .font(.title2.monospacedDigit())
                .fontWeight(.medium)
            
            Spacer()
            
            /// Recording status indicator
            HStack(spacing: 8) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 10, height: 10)
                    .opacity(store.isRecording && !store.isPaused ? (Int(store.duration).isMultiple(of: 2) ? 1 : 0.3) : 1)
                    .animation(.easeInOut(duration: 0.5), value: store.duration)
                
                Text(statusText)
                    .font(.subheadline)
                    .foregroundColor(statusColor)
            }
        }
        .padding(.horizontal, 8)
    }
    
    private var statusText: String {
        switch store.mode {
        case .encoding:
            return "Processing..."
        case .paused:
            return "Paused"
        case .recording:
            return "Recording"
        case .idle:
            return "Ready"
        }
    }
    
    private var statusColor: Color {
        switch store.mode {
        case .encoding:
            return .secondary
        case .paused:
            return .orange
        case .recording:
            return .red
        case .idle:
            return .gray
        }
    }
    
    private var recordingControls: some View {
        HStack(spacing: 40) {
            /// Pause/Resume button (only visible when recording)
            if store.isRecording {
                Button {
                    if store.isPaused {
                        store.send(.resumeButtonTapped, animation: .default)
                    } else {
                        store.send(.pauseButtonTapped, animation: .default)
                    }
                } label: {
                    /// Show microphone when paused (to indicate "tap to resume recording")
                    /// Show pause when recording (to indicate "tap to pause")
                    Image(systemName: store.isPaused ? "mic.fill" : "pause.fill")
                        .font(.title2)
                        .foregroundColor(store.isPaused ? .red : .primary)
                        .frame(width: 44, height: 44)
                        .background(Color(.systemGray5))
                        .clipShape(Circle())
                }
                .disabled(store.mode == .encoding)
            } else {
                Color.clear
                    .frame(width: 44, height: 44)
            }
            
            /// Record/Stop button
            Button {
                if store.isRecording {
                    store.send(.stopButtonTapped, animation: .default)
                } else {
                    store.send(.recordButtonTapped, animation: .spring())
                }
            } label: {
                ZStack {
                    Circle()
                        .fill(Color(.label))
                        .frame(width: 64, height: 64)
                    
                    if store.isRecording {
                        /// Stop button (square)
                        RoundedRectangle(cornerRadius: 4)
                            .fill(Color.red)
                            .frame(width: 24, height: 24)
                    } else {
                        /// Record button (circle)
                        Circle()
                            .fill(Color.red)
                            .frame(width: 56, height: 56)
                    }
                }
            }
            .disabled(store.mode == .encoding)
            .opacity(store.mode == .encoding ? 0.5 : 1)
            
            /// Placeholder for symmetry
            Color.clear
                .frame(width: 44, height: 44)
        }
    }
}

// MARK: - Preview

#Preview("Idle") {
    RecordingView(
        store: Store(initialState: RecordingFeature.State()) {
            RecordingFeature()
        }
    )
}

#Preview("Recording") {
    /// Set up shared state for preview
    @Shared(.liveTranscription) var liveTranscription
    $liveTranscription.withLock { transcription in
        transcription.volatileText = "Hello, this is a test recording with live transcription. The words appear as you speak them."
    }
    
    var state = RecordingFeature.State()
    state.isRecording = true
    state.duration = 65
    
    return RecordingView(
        store: Store(initialState: state) {
            RecordingFeature()
        }
    )
}

#Preview("Downloading Assets") {
    var state = RecordingFeature.State()
    state.isRecording = true
    state.isDownloadingAssets = true
    state.duration = 5
    
    return RecordingView(
        store: Store(initialState: state) {
            RecordingFeature()
        }
    )
}

#Preview("Speech Error") {
    var state = RecordingFeature.State()
    state.isRecording = true
    state.duration = 10
    state.speechError = "Speech recognition not available for this locale"
    
    return RecordingView(
        store: Store(initialState: state) {
            RecordingFeature()
        }
    )
}

#Preview("Encoding") {
    var state = RecordingFeature.State()
    state.mode = .encoding
    state.duration = 120
    
    return RecordingView(
        store: Store(initialState: state) {
            RecordingFeature()
        }
    )
}