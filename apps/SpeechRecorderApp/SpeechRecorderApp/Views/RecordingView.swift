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
    
    var body: some View {
        VStack(spacing: 24) {
            /// Recording status
            recordingStatus
            
            /// Duration display
            durationDisplay
            
            /// Asset download indicator
            if store.isDownloadingAssets {
                assetDownloadIndicator
            }
            
            /// Speech error message
            if let error = store.speechError {
                speechErrorView(error)
            }
            
            /// Live transcription with inline media
            if !store.fullTranscriptionText.isEmpty || !store.capturedMedia.isEmpty {
                transcriptionWithMediaPreview
            }
            
            Spacer()
            
            /// Record/Stop button
            recordButton
            
            /// Cancel button (when recording)
            if store.isRecording {
                cancelButton
            }
        }
        .padding()
        .alert($store.scope(state: \.alert, action: \.alert))
    }
    
    // MARK: - Subviews
    
    private var recordingStatus: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(store.isRecording ? Color.red : Color.gray)
                .frame(width: 12, height: 12)
                .opacity(store.isRecording ? (Int(store.duration).isMultiple(of: 2) ? 1 : 0.3) : 1)
                .animation(.easeInOut(duration: 0.5), value: store.duration)
            
            Text(statusText)
                .font(.headline)
                .foregroundColor(store.isRecording ? .red : .secondary)
        }
    }
    
    private var statusText: String {
        if store.mode == .encoding {
            return "Processing..."
        } else if store.isRecording {
            return "Recording"
        } else {
            return "Ready"
        }
    }
    
    private var durationDisplay: some View {
        Text(formattedDuration)
            .font(.system(size: 48, weight: .light, design: .monospaced))
            .foregroundColor(.primary)
    }
    
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
    
    private var transcriptionWithMediaPreview: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Live Transcription")
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                /// Show word count and media count
                HStack(spacing: 8) {
                    if !store.capturedMedia.isEmpty {
                        Label("\(store.capturedMedia.count)", systemImage: "photo")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                    }
                    Text("\(store.transcription.words.count) words")
                        .font(.caption2)
                        .foregroundColor(.secondary)
                }
            }
            
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 12) {
                        /// Show segments with timestamps and inline media
                        ForEach(store.finalizedSegments) { segment in
                            segmentView(segment)
                        }
                        
                        /// Show volatile transcription (current in-progress segment)
                        if !store.volatileTranscription.isEmpty {
                            HStack(alignment: .top, spacing: 8) {
                                /// Show the start time of the current segment (after last finalized segment)
                                Text(formatTimestamp(store.finalizedSegments.last?.endTime ?? 0))
                                    .font(.caption2.monospacedDigit())
                                    .foregroundColor(.secondary)
                                    .frame(width: 40, alignment: .leading)
                                
                                Text(store.volatileTranscription.trimmingCharacters(in: .whitespaces))
                                    .font(.body)
                                    .foregroundColor(.purple.opacity(0.8))
                            }
                            .id("volatile")
                        }
                        
                        /// Show any media captured after the last segment
                        let lastSegmentEndTime = store.finalizedSegments.last?.endTime ?? 0
                        let trailingMedia = store.capturedMedia.filter { $0.timestamp > lastSegmentEndTime }
                        if !trailingMedia.isEmpty {
                            mediaRow(trailingMedia)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .onChange(of: store.volatileTranscription) { _, _ in
                    withAnimation {
                        proxy.scrollTo("volatile", anchor: .bottom)
                    }
                }
            }
            .frame(maxHeight: 200)
            .padding()
            .background(Color.purple.opacity(0.1))
            .cornerRadius(8)
        }
    }
    
    private func segmentView(_ segment: TranscriptionSegment) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            /// Show any media captured during this segment
            let segmentMedia = store.capturedMedia.filter { media in
                media.timestamp >= segment.startTime && media.timestamp <= segment.endTime
            }
            if !segmentMedia.isEmpty {
                mediaRow(segmentMedia)
            }
            
            /// Segment with timestamp
            HStack(alignment: .top, spacing: 8) {
                Text(formatTimestamp(segment.startTime))
                    .font(.caption2.monospacedDigit())
                    .foregroundColor(.secondary)
                    .frame(width: 40, alignment: .leading)
                
                Text(segment.text)
                    .font(.body)
                    .foregroundColor(.primary)
            }
        }
    }
    
    private func mediaRow(_ media: [TimestampedMedia]) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(media) { item in
                    mediaThumbnail(item)
                }
            }
        }
        .padding(.leading, 48) /// Align with text after timestamp
    }
    
    private func mediaThumbnail(_ media: TimestampedMedia) -> some View {
        VStack(spacing: 2) {
            if let thumbnail = store.mediaThumbnails[media.id] {
                Image(uiImage: thumbnail)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 60, height: 60)
                    .clipShape(RoundedRectangle(cornerRadius: 6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(media.mediaType == .screenshot ? Color.blue : Color.green, lineWidth: 2)
                    )
            } else {
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.gray.opacity(0.3))
                    .frame(width: 60, height: 60)
                    .overlay(
                        Image(systemName: media.mediaType == .screenshot ? "camera.viewfinder" : "photo")
                            .foregroundColor(.gray)
                    )
            }
            
            Text(formatTimestamp(media.timestamp))
                .font(.caption2)
                .foregroundColor(.secondary)
        }
    }
    
    private func formatTimestamp(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private var recordButton: some View {
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
                    .frame(width: 74, height: 74)
                
                if store.isRecording {
                    /// Stop button (square)
                    RoundedRectangle(cornerRadius: 4)
                        .fill(Color.red)
                        .frame(width: 28, height: 28)
                } else {
                    /// Record button (circle)
                    Circle()
                        .fill(Color.red)
                        .frame(width: 66, height: 66)
                }
            }
        }
        .disabled(store.mode == .encoding)
        .opacity(store.mode == .encoding ? 0.5 : 1)
    }
    
    private var cancelButton: some View {
        Button("Cancel") {
            store.send(.cancelButtonTapped)
        }
        .foregroundColor(.secondary)
    }
    
    // MARK: - Helpers
    
    private var formattedDuration: String {
        let minutes = Int(store.duration) / 60
        let seconds = Int(store.duration) % 60
        return String(format: "%02d:%02d", minutes, seconds)
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
    var state = RecordingFeature.State()
    state.isRecording = true
    state.duration = 65
    state.volatileTranscription = "Hello, this is a test recording with live transcription. The words appear as you speak them."
    
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