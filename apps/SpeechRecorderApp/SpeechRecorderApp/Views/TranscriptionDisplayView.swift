/**
 HOW:
   Use in SwiftUI views for displaying transcription with segments and media:
   
   ```swift
   TranscriptionDisplayView(
       segments: transcription.segments,
       words: transcription.words,
       media: recording.media,
       mediaThumbnails: thumbnails,
       currentTime: currentTime,
       currentWordIndex: currentWordIndex,
       volatileText: nil,
       onWordTapped: { index in store.send(.wordTapped(index)) },
       onMediaTapped: { id in store.send(.mediaTapped(id)) }
   )
   ```
   
   [Inputs]
   - segments: Array of TranscriptionSegment
   - words: Array of TimestampedWord (for global index lookup)
   - media: Array of TimestampedMedia
   - mediaThumbnails: Dictionary of media ID to UIImage
   - currentTime: Current playback/recording time
   - currentWordIndex: Currently highlighted word index (optional)
   - volatileText: In-progress transcription text (optional, for recording)
   - onWordTapped: Callback when a word is tapped (optional)
   - onMediaTapped: Callback when media is tapped (optional)
   
   [Outputs]
   - SwiftUI View
   
   [Side Effects]
   - None (pure view component)

 WHO:
   AI Agent, Developer
   (Context: Shared UI component for transcription display)

 WHAT:
   A reusable SwiftUI view for displaying transcription with:
   - Segments with timestamps
   - Word highlighting
   - Inline media thumbnails
   - Flow layout for words
   Used by both PlaybackView and RecordingView.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/TranscriptionDisplayView.swift

 WHY:
   To share UI code between recording and playback views.
   Both views display transcription with similar layouts.
 */

import SwiftUI

// MARK: - Transcription Display View

struct TranscriptionDisplayView: View {
    /// The transcription segments to display
    let segments: [TranscriptionSegment]
    
    /// All words for global index lookup
    let words: [TimestampedWord]
    
    /// Media items to display inline
    let media: [TimestampedMedia]
    
    /// Thumbnails for media items
    let mediaThumbnails: [UUID: UIImage]
    
    /// Current playback/recording time
    let currentTime: TimeInterval
    
    /// Currently highlighted word index
    let currentWordIndex: Int?
    
    /// In-progress transcription text (for recording mode)
    let volatileText: String?
    
    /// Whether auto-scroll is enabled
    var isAutoScrollEnabled: Bool = true
    
    /// Callback when a word is tapped
    var onWordTapped: ((Int) -> Void)?
    
    /// Callback when media is tapped
    var onMediaTapped: ((UUID) -> Void)?
    
    /// Callback when media is double-tapped (for fullscreen view)
    var onImageDoubleTapped: ((UUID) -> Void)?
    
    /// Callback when user scrolls manually
    var onUserDidScroll: (() -> Void)?
    
    /// Callback when user taps resume auto-scroll
    var onResumeAutoScrollTapped: (() -> Void)?
    
    /// Whether to show empty state
    var showEmptyState: Bool = true
    
    /// Empty state message
    var emptyStateMessage: String = "Start speaking..."
    
    /// Empty state subtitle
    var emptyStateSubtitle: String = "Your words will appear here as you speak."
    
    var body: some View {
        ZStack(alignment: .bottom) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 16) {
                        if segments.isEmpty && words.isEmpty && (volatileText?.isEmpty ?? true) && media.isEmpty && showEmptyState {
                            /// Empty state
                            emptyStateView
                        } else {
                            /// Show segments with timestamps and inline media
                            ForEach(segments) { segment in
                                segmentView(segment)
                            }
                            
                            /// If no segments, fall back to simple word view
                            if segments.isEmpty && !words.isEmpty {
                                TranscriptionTextView(
                                    words: words,
                                    currentWordIndex: currentWordIndex
                                )
                            }
                            
                            /// Show volatile transcription (current in-progress segment)
                            if let volatile = volatileText, !volatile.isEmpty {
                                volatileTextView(volatile)
                                    .id("volatile")
                            }
                            
                            /// Show any media captured after the last segment
                            let lastSegmentEndTime = segments.last?.endTime ?? 0
                            let trailingMedia = media.filter { $0.timestamp > lastSegmentEndTime }
                            if !trailingMedia.isEmpty {
                                mediaRow(trailingMedia)
                            }
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()
                }
                /// Use introspection to detect user scroll via UIScrollView delegate
                .scrollDismissesKeyboard(.interactively)
                .onScrollPhaseChange { oldPhase, newPhase in
                    /// Detect when user starts interacting with scroll
                    if newPhase == .interacting || newPhase == .decelerating {
                        onUserDidScroll?()
                    }
                }
                .onChange(of: volatileText) { _, _ in
                    if isAutoScrollEnabled {
                        withAnimation {
                            proxy.scrollTo("volatile", anchor: .bottom)
                        }
                    }
                }
                .onChange(of: currentWordIndex) { _, newIndex in
                    if isAutoScrollEnabled, let index = newIndex {
                        withAnimation {
                            proxy.scrollTo("word-\(index)", anchor: .center)
                        }
                    }
                }
                .onChange(of: isAutoScrollEnabled) { _, newValue in
                    /// When auto-scroll is re-enabled, scroll to the latest content
                    if newValue {
                        withAnimation {
                            proxy.scrollTo("volatile", anchor: .bottom)
                        }
                    }
                }
            }
            
            /// Floating "Resume auto-scroll" button
            if !isAutoScrollEnabled {
                resumeAutoScrollButton
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(.easeInOut(duration: 0.2), value: isAutoScrollEnabled)
    }
    
    // MARK: - Resume Auto-scroll Button
    
    private var resumeAutoScrollButton: some View {
        Button {
            onResumeAutoScrollTapped?()
        } label: {
            HStack(spacing: 6) {
                Image(systemName: "arrow.down.circle.fill")
                    .font(.body)
                Text("Resume auto-scroll")
                    .font(.subheadline.weight(.medium))
            }
            .foregroundColor(.white)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color.blue)
            .clipShape(Capsule())
            .shadow(color: .black.opacity(0.2), radius: 4, x: 0, y: 2)
        }
        .padding(.bottom, 16)
    }
    
    // MARK: - Empty State
    
    private var emptyStateView: some View {
        VStack(spacing: 16) {
            Spacer()
            
            Image(systemName: "waveform")
                .font(.system(size: 60))
                .foregroundColor(.secondary.opacity(0.5))
            
            Text(emptyStateMessage)
                .font(.title3)
                .foregroundColor(.secondary)
            
            Text(emptyStateSubtitle)
                .font(.body)
                .foregroundColor(.secondary.opacity(0.7))
                .multilineTextAlignment(.center)
            
            Spacer()
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }
    
    // MARK: - Segment View
    
    private func segmentView(_ segment: TranscriptionSegment) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            /// Show media captured during this segment
            let segmentMedia = media.filter { item in
                item.timestamp >= segment.startTime && item.timestamp <= segment.endTime
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
                ForEach(Array(segment.words.enumerated()), id: \.element.id) { _, word in
                    let globalIndex = findGlobalWordIndex(word)
                    let isCurrentWord = currentWordIndex == globalIndex
                    
                    Text(word.text)
                        .font(.body)
                        .padding(.horizontal, 4)
                        .padding(.vertical, 2)
                        .background(isCurrentWord ? Color.yellow : Color.clear)
                        .cornerRadius(4)
                        .id("word-\(globalIndex ?? -1)")
                        .onTapGesture {
                            if let idx = globalIndex, let callback = onWordTapped {
                                callback(idx)
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
    
    private func volatileTextView(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 8) {
            /// Show the start time of the current segment (after last finalized segment)
            Text(formatTime(segments.last?.endTime ?? 0))
                .font(.caption2.monospacedDigit())
                .foregroundColor(.secondary)
                .frame(width: 40, alignment: .leading)
            
            Text(text.trimmingCharacters(in: .whitespaces))
                .font(.body)
                .foregroundColor(.purple.opacity(0.8))
        }
    }
    
    private func isSegmentActive(_ segment: TranscriptionSegment) -> Bool {
        currentTime >= segment.startTime && currentTime <= segment.endTime
    }
    
    private func findGlobalWordIndex(_ word: TimestampedWord) -> Int? {
        words.firstIndex { $0.id == word.id }
    }
    
    // MARK: - Media Views
    
    private func mediaRow(_ items: [TimestampedMedia]) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(items) { item in
                    mediaThumbnailView(item)
                }
            }
        }
    }
    
    private func mediaThumbnailView(_ item: TimestampedMedia) -> some View {
        VStack(spacing: 2) {
            if let thumbnail = mediaThumbnails[item.id] {
                Image(uiImage: thumbnail)
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .frame(width: 50, height: 50)
                    .clipShape(RoundedRectangle(cornerRadius: 6))
                    .overlay(
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(
                                isMediaActive(item) ? Color.blue : (item.mediaType == .screenshot ? Color.blue.opacity(0.5) : Color.green.opacity(0.5)),
                                lineWidth: isMediaActive(item) ? 3 : 1
                            )
                    )
            } else {
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.gray.opacity(0.3))
                    .frame(width: 50, height: 50)
                    .overlay(
                        Image(systemName: item.mediaType == .screenshot ? "camera.viewfinder" : "photo")
                            .foregroundColor(.gray)
                    )
            }
            
            Text(formatTime(item.timestamp))
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .onTapGesture {
            onMediaTapped?(item.id)
        }
        .onTapGesture(count: 2) {
            onImageDoubleTapped?(item.id)
        }
    }
    
    private func isMediaActive(_ item: TimestampedMedia) -> Bool {
        /// Media is active if current time is within 3 seconds after its timestamp
        currentTime >= item.timestamp && currentTime <= item.timestamp + 3.0
    }
    
    // MARK: - Helpers
    
    /// Format time using the shared HH:MM:SS format for consistency
    private func formatTime(_ time: TimeInterval) -> String {
        formatDurationHMS(time)
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

// MARK: - Scroll Offset Preference Key

/// Preference key for tracking scroll offset
struct ScrollOffsetPreferenceKey: PreferenceKey {
    static let defaultValue: CGPoint = .zero
    
    static func reduce(value: inout CGPoint, nextValue: () -> CGPoint) {
        value = nextValue()
    }
}

// MARK: - Preview

#Preview("With Segments") {
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
    
    return TranscriptionDisplayView(
        segments: segments,
        words: words,
        media: [],
        mediaThumbnails: [:],
        currentTime: 1.2,
        currentWordIndex: 2,
        volatileText: nil
    )
}

#Preview("Empty State") {
    TranscriptionDisplayView(
        segments: [],
        words: [],
        media: [],
        mediaThumbnails: [:],
        currentTime: 0,
        currentWordIndex: nil,
        volatileText: nil
    )
}

#Preview("With Volatile Text") {
    let words: [TimestampedWord] = [
        .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
    ]
    
    let segments: [TranscriptionSegment] = [
        .preview(text: "Hello", words: words)
    ]
    
    return TranscriptionDisplayView(
        segments: segments,
        words: words,
        media: [],
        mediaThumbnails: [:],
        currentTime: 2.0,
        currentWordIndex: nil,
        volatileText: "This is being spoken right now..."
    )
}