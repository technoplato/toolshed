/**
 HOW:
   Use with a StoreOf<PlaybackFeature>:
   
   ```swift
   PlaybackView(store: store.scope(state: \.playback, action: \.playback))
   ```
   
   [Inputs]
   - store: StoreOf<PlaybackFeature>
   
   [Outputs]
   - SwiftUI View
   
   [Side Effects]
   - Sends actions to the store

 WHO:
   AI Agent, Developer
   (Context: SwiftUI view for playback feature)

 WHAT:
   SwiftUI view for playing back recordings with word highlighting.
   Shows transcription with current word highlighted.
   Provides play/pause, seek, and progress controls.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/PlaybackView.swift

 WHY:
   To provide synchronized playback with word highlighting.
   The main value proposition of the app.
 */

import ComposableArchitecture
import SwiftUI

struct PlaybackView: View {
    @Bindable var store: StoreOf<PlaybackFeature>
    
    var body: some View {
        VStack(spacing: 20) {
            /// Transcription with word highlighting
            ScrollView {
                TranscriptionTextView(
                    words: store.recording.transcription.words,
                    currentWordIndex: store.currentWordIndex
                )
                .padding()
            }
            
            Spacer()
            
            /// Progress bar
            progressBar
            
            /// Time display
            timeDisplay
            
            /// Playback controls
            playbackControls
        }
        .padding()
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Done") {
                    store.send(.closeButtonTapped)
                }
            }
        }
    }
    
    // MARK: - Subviews
    
    private var progressBar: some View {
        Slider(
            value: Binding(
                get: { store.currentTime },
                set: { store.send(.seekTo($0)) }
            ),
            in: 0...max(store.recording.duration, 0.01)
        )
        .tint(.blue)
    }
    
    private var timeDisplay: some View {
        HStack {
            Text(formatTime(store.currentTime))
                .font(.caption.monospacedDigit())
                .foregroundColor(.secondary)
            
            Spacer()
            
            Text(formatTime(store.recording.duration))
                .font(.caption.monospacedDigit())
                .foregroundColor(.secondary)
        }
    }
    
    private var playbackControls: some View {
        HStack(spacing: 40) {
            /// Rewind 10 seconds
            Button {
                store.send(.seekTo(max(0, store.currentTime - 10)))
            } label: {
                Image(systemName: "gobackward.10")
                    .font(.title)
            }
            
            /// Play/Pause
            Button {
                if store.isPlaying {
                    store.send(.pauseButtonTapped)
                } else {
                    store.send(.playButtonTapped)
                }
            } label: {
                Image(systemName: store.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                    .font(.system(size: 64))
            }
            
            /// Forward 10 seconds
            Button {
                store.send(.seekTo(min(store.recording.duration, store.currentTime + 10)))
            } label: {
                Image(systemName: "goforward.10")
                    .font(.title)
            }
        }
        .padding(.bottom)
    }
    
    // MARK: - Helpers
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

// MARK: - Preview

#Preview {
    NavigationStack {
        PlaybackView(
            store: Store(
                initialState: PlaybackFeature.State(
                    recording: .preview(
                        transcription: Transcription(
                            text: "Hello world, this is a test recording with multiple words to demonstrate the word highlighting feature.",
                            words: [
                                .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
                                .preview(text: "world,", startTime: 0.6, endTime: 1.0),
                                .preview(text: "this", startTime: 1.1, endTime: 1.3),
                                .preview(text: "is", startTime: 1.4, endTime: 1.5),
                                .preview(text: "a", startTime: 1.6, endTime: 1.7),
                                .preview(text: "test", startTime: 1.8, endTime: 2.1),
                                .preview(text: "recording", startTime: 2.2, endTime: 2.8),
                            ],
                            isFinal: true
                        )
                    ),
                    currentWordIndex: 2
                )
            ) {
                PlaybackFeature()
            }
        )
        .navigationTitle("Test Recording")
    }
}