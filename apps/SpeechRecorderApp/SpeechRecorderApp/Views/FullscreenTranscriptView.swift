/**
 HOW:
   Use in SwiftUI views with StoreOf<FullscreenTranscriptFeature>:
   
   ```swift
   FullscreenTranscriptView(store: store.scope(
       state: \.fullscreenTranscript,
       action: \.fullscreenTranscript
   ))
   ```
   
   [Inputs]
   - store: StoreOf<FullscreenTranscriptFeature>
   
   [Outputs]
   - SwiftUI View
   
   [Side Effects]
   - None (pure view component)

 WHO:
   AI Agent, Developer
   (Context: SwiftUI view for fullscreen transcript display)

 WHAT:
   A fullscreen SwiftUI view for displaying transcripts with:
   - Pinch-to-zoom for text size adjustment
   - Two-finger double-tap to exit
   - Auto-scroll with resume button
   - Black background for distraction-free reading

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/FullscreenTranscriptView.swift

 WHY:
   To provide a distraction-free reading experience for transcripts.
   Inspired by Otter.ai's fullscreen mode but without settings UI.
 */

import ComposableArchitecture
import SwiftUI

struct FullscreenTranscriptView: View {
    @Bindable var store: StoreOf<FullscreenTranscriptFeature>
    
    /// Track the base text size when pinch gesture starts
    @State private var pinchStartTextSize: Double = 24.0
    
    var body: some View {
        ZStack {
            /// Black background for distraction-free reading
            Color.black
                .ignoresSafeArea()
            
            /// Main content with pinch gesture
            ScrollViewReader { proxy in
                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        /// Display segments with timestamps
                        ForEach(store.segments) { segment in
                            segmentView(segment)
                        }
                        
                        /// If no segments, fall back to simple word view
                        if store.segments.isEmpty && !store.words.isEmpty {
                            wordsView
                        }
                        
                        /// Show volatile transcription (current in-progress segment)
                        if let volatile = store.volatileText, !volatile.isEmpty {
                            volatileTextView(volatile)
                                .id("volatile")
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal, 24)
                    .padding(.vertical, 40)
                }
                .scrollDismissesKeyboard(.interactively)
                .onScrollPhaseChange { oldPhase, newPhase in
                    /// Detect when user starts interacting with scroll
                    if newPhase == .interacting || newPhase == .decelerating {
                        store.send(.userDidScroll)
                    }
                }
                .onChange(of: store.volatileText) { _, _ in
                    if store.isAutoScrollEnabled {
                        withAnimation {
                            proxy.scrollTo("volatile", anchor: .bottom)
                        }
                    }
                }
                .onChange(of: store.currentWordIndex) { _, newIndex in
                    if store.isAutoScrollEnabled, let index = newIndex {
                        withAnimation {
                            proxy.scrollTo("word-\(index)", anchor: .center)
                        }
                    }
                }
                .onChange(of: store.isAutoScrollEnabled) { _, newValue in
                    if newValue {
                        withAnimation {
                            proxy.scrollTo("volatile", anchor: .bottom)
                        }
                    }
                }
            }
            /// Apply pinch gesture on top of scroll view
            .contentShape(Rectangle())
            .gesture(
                MagnificationGesture()
                    .onChanged { scale in
                        /// Calculate new size based on the starting size and current scale
                        let newSize = pinchStartTextSize * scale
                        store.send(.pinchGestureChanged(scale: newSize / store.textSize))
                    }
                    .onEnded { _ in
                        /// Save current size as the new starting point
                        pinchStartTextSize = store.textSize
                    }
            )
            
            /// Floating "Resume auto-scroll" button
            if !store.isAutoScrollEnabled {
                VStack {
                    Spacer()
                    resumeAutoScrollButton
                        .padding(.bottom, 40)
                }
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(.easeInOut(duration: 0.2), value: store.isAutoScrollEnabled)
        /// Two-finger double-tap to exit
        .onTwoFingerDoubleTap {
            store.send(.twoFingerDoubleTapped)
        }
        .onAppear {
            pinchStartTextSize = store.textSize
        }
    }
    
    // MARK: - Resume Auto-scroll Button
    
    private var resumeAutoScrollButton: some View {
        Button {
            store.send(.resumeAutoScrollTapped)
        } label: {
            HStack(spacing: 6) {
                Image(systemName: "arrow.down.circle.fill")
                    .font(.body)
                Text("Resume auto-scroll")
                    .font(.subheadline.weight(.medium))
            }
            .foregroundColor(.black)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color.white)
            .clipShape(Capsule())
            .shadow(color: .white.opacity(0.3), radius: 4, x: 0, y: 2)
        }
    }
    
    // MARK: - Segment View
    
    private func segmentView(_ segment: TranscriptionSegment) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            /// Timestamp header in light gray
            Text(formatTime(segment.startTime))
                .font(.system(size: store.textSize * 0.5).monospacedDigit())
                .foregroundColor(.gray)
            
            /// Words with highlighting
            FlowLayout(spacing: 4) {
                ForEach(Array(segment.words.enumerated()), id: \.element.id) { _, word in
                    let globalIndex = findGlobalWordIndex(word)
                    let isCurrentWord = store.currentWordIndex == globalIndex
                    
                    Text(word.text)
                        .font(.system(size: store.textSize))
                        .foregroundColor(.white)
                        .padding(.horizontal, 4)
                        .padding(.vertical, 2)
                        .background(isCurrentWord ? Color.yellow : Color.clear)
                        .cornerRadius(4)
                        .id("word-\(globalIndex ?? -1)")
                }
            }
        }
    }
    
    // MARK: - Words View (fallback when no segments)
    
    private var wordsView: some View {
        FlowLayout(spacing: 4) {
            ForEach(Array(store.words.enumerated()), id: \.element.id) { index, word in
                let isCurrentWord = store.currentWordIndex == index
                
                Text(word.text)
                    .font(.system(size: store.textSize))
                    .foregroundColor(.white)
                    .padding(.horizontal, 4)
                    .padding(.vertical, 2)
                    .background(isCurrentWord ? Color.yellow : Color.clear)
                    .cornerRadius(4)
                    .id("word-\(index)")
            }
        }
    }
    
    // MARK: - Volatile Text View
    
    private func volatileTextView(_ text: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            /// Timestamp header
            Text(formatTime(store.segments.last?.endTime ?? 0))
                .font(.system(size: store.textSize * 0.5).monospacedDigit())
                .foregroundColor(.gray)
            
            Text(text.trimmingCharacters(in: .whitespaces))
                .font(.system(size: store.textSize))
                .foregroundColor(.purple.opacity(0.8))
        }
    }
    
    // MARK: - Helpers
    
    private func findGlobalWordIndex(_ word: TimestampedWord) -> Int? {
        store.words.firstIndex { $0.id == word.id }
    }
    
    /// Format time using the shared HH:MM:SS format for consistency
    private func formatTime(_ time: TimeInterval) -> String {
        formatDurationHMS(time)
    }
}

// MARK: - Preview

#Preview("Fullscreen Transcript") {
    /// Set up shared state for preview
    @Shared(.liveTranscription) var liveTranscription
    
    let words: [TimestampedWord] = [
        .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
        .preview(text: "world,", startTime: 0.6, endTime: 1.0),
        .preview(text: "this", startTime: 1.1, endTime: 1.3),
        .preview(text: "is", startTime: 1.4, endTime: 1.5),
        .preview(text: "a", startTime: 1.6, endTime: 1.7),
        .preview(text: "test", startTime: 1.8, endTime: 2.1),
    ]
    
    let segments: [TranscriptionSegment] = [
        .preview(
            text: "Hello world, this is a test",
            words: words
        )
    ]
    
    /// Update shared state with preview data using withLock
    $liveTranscription.withLock { transcription in
        transcription.segments = segments
        transcription.words = words
        transcription.currentTime = 1.2
        transcription.currentWordIndex = 2
    }
    
    return FullscreenTranscriptView(
        store: Store(
            initialState: FullscreenTranscriptFeature.State()
        ) {
            FullscreenTranscriptFeature()
        }
    )
}