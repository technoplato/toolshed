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
   Shows record/stop button, duration, and live transcription.

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
            
            /// Live transcription preview
            if !store.volatileTranscription.isEmpty {
                transcriptionPreview
            }
            
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
            
            Text(store.isRecording ? "Recording" : "Ready")
                .font(.headline)
                .foregroundColor(store.isRecording ? .red : .secondary)
        }
    }
    
    private var durationDisplay: some View {
        Text(formattedDuration)
            .font(.system(size: 48, weight: .light, design: .monospaced))
            .foregroundColor(.primary)
    }
    
    private var transcriptionPreview: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Live Transcription")
                .font(.caption)
                .foregroundColor(.secondary)
            
            Text(store.volatileTranscription)
                .font(.body)
                .foregroundColor(.purple.opacity(0.8))
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding()
                .background(Color.purple.opacity(0.1))
                .cornerRadius(8)
        }
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
    state.volatileTranscription = "Hello, this is a test recording..."
    
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