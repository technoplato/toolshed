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
            /// Transcription with segments, media, and word highlighting
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        ForEach(store.recording.transcription.segments) { segment in
                            segmentView(segment, proxy: proxy)
                        }
                        
                        /// If no segments, fall back to simple word view
                        if store.recording.transcription.segments.isEmpty && !store.recording.transcription.words.isEmpty {
                            TranscriptionTextView(
                                words: store.recording.transcription.words,
                                currentWordIndex: store.currentWordIndex
                            )
                        }
                    }
                    .padding()
                }
                .onChange(of: store.currentWordIndex) { _, newIndex in
                    if let index = newIndex {
                        withAnimation {
                            proxy.scrollTo("word-\(index)", anchor: .center)
                        }
                    }
                }
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
    }
    
    // MARK: - Segment View
    
    private func segmentView(_ segment: TranscriptionSegment, proxy: ScrollViewProxy) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            /// Show media captured during this segment
            let segmentMedia = store.recording.media.filter { media in
                media.timestamp >= segment.startTime && media.timestamp <= segment.endTime
            }
            if !segmentMedia.isEmpty {
                mediaRow(segmentMedia)
            }
            
            /// Segment header with timestamp
            HStack {
                Text(formatTime(segment.startTime))
                    .font(.caption.monospacedDigit())
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .background(Color.secondary.opacity(0.1))
                    .cornerRadius(4)
                
                Spacer()
            }
            
            /// Words with highlighting
            FlowLayout(spacing: 4) {
                ForEach(Array(segment.words.enumerated()), id: \.element.id) { index, word in
                    let globalIndex = findGlobalWordIndex(word)
                    let isCurrentWord = store.currentWordIndex == globalIndex
                    
                    Text(word.text)
                        .font(.body)
                        .padding(.horizontal, 4)
                        .padding(.vertical, 2)
                        .background(isCurrentWord ? Color.yellow : Color.clear)
                        .cornerRadius(4)
                        .id("word-\(globalIndex ?? -1)")
                        .onTapGesture {
                            if let idx = globalIndex {
                                store.send(.wordTapped(idx))
                            }
                        }
                }
            }
        }
        .padding()
        .background(
            isSegmentActive(segment) ? Color.blue.opacity(0.05) : Color.clear
        )
        .cornerRadius(8)
    }
    
    private func isSegmentActive(_ segment: TranscriptionSegment) -> Bool {
        store.currentTime >= segment.startTime && store.currentTime <= segment.endTime
    }
    
    private func findGlobalWordIndex(_ word: TimestampedWord) -> Int? {
        store.recording.transcription.words.firstIndex { $0.id == word.id }
    }
    
    // MARK: - Media Views
    
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
    
    private func mediaRow(_ media: [TimestampedMedia]) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(media) { item in
                    mediaThumbnailButton(item)
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

// MARK: - Flow Layout for Words

/// A simple flow layout that wraps content to the next line
struct FlowLayout: Layout {
    var spacing: CGFloat = 4
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = layout(proposal: proposal, subviews: subviews)
        return result.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = layout(proposal: proposal, subviews: subviews)
        
        for (index, subview) in subviews.enumerated() {
            subview.place(at: CGPoint(x: bounds.minX + result.positions[index].x,
                                       y: bounds.minY + result.positions[index].y),
                          proposal: .unspecified)
        }
    }
    
    private func layout(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, positions: [CGPoint]) {
        let maxWidth = proposal.width ?? .infinity
        var positions: [CGPoint] = []
        var currentX: CGFloat = 0
        var currentY: CGFloat = 0
        var lineHeight: CGFloat = 0
        var maxX: CGFloat = 0
        
        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            
            if currentX + size.width > maxWidth && currentX > 0 {
                currentX = 0
                currentY += lineHeight + spacing
                lineHeight = 0
            }
            
            positions.append(CGPoint(x: currentX, y: currentY))
            
            currentX += size.width + spacing
            lineHeight = max(lineHeight, size.height)
            maxX = max(maxX, currentX)
        }
        
        return (CGSize(width: maxX, height: currentY + lineHeight), positions)
    }
}

// MARK: - Preview

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
    
    return NavigationStack {
        PlaybackView(
            store: Store(
                initialState: PlaybackFeature.State(
                    recording: .preview(
                        transcription: .preview(
                            text: "Hello world, this is a test recording with multiple words to demonstrate the word highlighting feature.",
                            words: words,
                            segments: segments,
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