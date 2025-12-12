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
import Sharing
import SwiftUI

struct PlaybackView: View {
    @Bindable var store: StoreOf<PlaybackFeature>
    
    var body: some View {
        VStack(spacing: 20) {
            /// Transcription with segments, media, and word highlighting
            TranscriptionDisplayView(
                segments: store.recording.transcription.segments,
                words: store.recording.transcription.words,
                media: store.recording.media,
                mediaThumbnails: store.mediaThumbnails,
                currentTime: store.currentTime,
                currentWordIndex: store.currentWordIndex,
                volatileText: nil,
                onWordTapped: { index in
                    store.send(.wordTapped(index))
                },
                onMediaTapped: { id in
                    store.send(.mediaTapped(id))
                },
                onImageDoubleTapped: { id in
                    store.send(.imageDoubleTapped(id))
                },
                showEmptyState: false
            )
            /// Two-finger double-tap to enter fullscreen transcript
            .onTwoFingerDoubleTap {
                store.send(.twoFingerDoubleTapped)
            }
            
            /// Media timeline (if any media exists)
            if !store.recording.media.isEmpty {
                mediaTimeline
            }
            
            /// Progress bar
            progressBar
            
            /// Time display
            timeDisplay
            
            /// Playback controls
            playbackControls
        }
        .padding()
        .onAppear {
            store.send(.onAppear)
        }
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button("Done") {
                    store.send(.closeButtonTapped)
                }
            }
        }
        .fullScreenCover(
            item: $store.scope(state: \.fullscreenImage, action: \.fullscreenImage)
        ) { store in
            FullscreenImageView(store: store)
        }
        .fullScreenCover(
            item: $store.scope(state: \.fullscreenTranscript, action: \.fullscreenTranscript)
        ) { fullscreenStore in
            FullscreenTranscriptView(store: fullscreenStore)
        }
    }
    
    // MARK: - Media Timeline
    
    private var mediaTimeline: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Media")
                .font(.caption)
                .foregroundColor(.secondary)
            
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(store.recording.media) { media in
                        mediaThumbnailButton(media)
                    }
                }
            }
        }
    }
    
    private func mediaThumbnailButton(_ media: TimestampedMedia) -> some View {
        Button {
            store.send(.mediaTapped(media.id))
        } label: {
            VStack(spacing: 2) {
                if let thumbnail = store.mediaThumbnails[media.id] {
                    Image(uiImage: thumbnail)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: 50, height: 50)
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                        .overlay(
                            RoundedRectangle(cornerRadius: 6)
                                .stroke(
                                    isMediaActive(media) ? Color.blue : (media.mediaType == .screenshot ? Color.blue.opacity(0.5) : Color.green.opacity(0.5)),
                                    lineWidth: isMediaActive(media) ? 3 : 1
                                )
                        )
                } else {
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.gray.opacity(0.3))
                        .frame(width: 50, height: 50)
                        .overlay(
                            Image(systemName: media.mediaType == .screenshot ? "camera.viewfinder" : "photo")
                                .foregroundColor(.gray)
                        )
                }
                
                Text(formatTime(media.timestamp))
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .buttonStyle(.plain)
    }
    
    private func isMediaActive(_ media: TimestampedMedia) -> Bool {
        /// Media is active if current time is within 3 seconds after its timestamp
        store.currentTime >= media.timestamp && store.currentTime <= media.timestamp + 3.0
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

/**
 **Migration Note (2025-12-11):**
 Updated preview to use Shared(value:) for the recording parameter.
 This matches the new PlaybackFeature.State which uses @Shared var recording.
 
 **Source:** Recipe 7 from swift-sharing-state-comprehensive-guide.md
 **Motivation:** PlaybackFeature now receives derived shared state from parent.
 */
#Preview {
    let words: [TimestampedWord] = [
        .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
        .preview(text: "world,", startTime: 0.6, endTime: 1.0),
        .preview(text: "this", startTime: 1.1, endTime: 1.3),
        .preview(text: "is", startTime: 1.4, endTime: 1.5),
        .preview(text: "a", startTime: 1.6, endTime: 1.7),
        .preview(text: "test", startTime: 1.8, endTime: 2.1),
        .preview(text: "recording", startTime: 2.2, endTime: 2.8),
    ]
    
    let segments: [TranscriptionSegment] = [
        .preview(
            text: "Hello world, this is a test recording",
            words: words
        )
    ]
    
    let recording = Recording.preview(
        transcription: .preview(
            text: "Hello world, this is a test recording with multiple words to demonstrate the word highlighting feature.",
            words: words,
            segments: segments,
            isFinal: true
        )
    )
    
    NavigationStack {
        PlaybackView(
            store: Store(
                initialState: PlaybackFeature.State(
                    recording: Shared(value: recording),
                    currentWordIndex: 2
                )
            ) {
                PlaybackFeature()
            }
        )
        .navigationTitle("Test Recording")
    }
}