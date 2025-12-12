/**
 HOW:
   Use with a StoreOf<RecordingsListFeature>:
   
   ```swift
   RecordingsListView(store: store.scope(state: \.recordingsList, action: \.recordingsList))
   ```
   
   [Inputs]
   - store: StoreOf<RecordingsListFeature>
   
   [Outputs]
   - SwiftUI View
   
   [Side Effects]
   - Sends actions to the store

 WHO:
   AI Agent, Developer
   (Context: SwiftUI view for recordings list)

 WHAT:
   SwiftUI view for displaying the list of recordings.
   Shows recordings with title, date, and duration.
   Provides record button and navigation to playback.
   
   **Migration Note (2025-12-11):**
   Updated to pass recording.id instead of full recording object.
   This enables derived shared state in the reducer.
   
   Reference: SyncUpsListView.swift
   See: docs/swift-sharing-state-comprehensive-guide.md#appendix-a-speechrecorderapp-migration-guide

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-12
   [Change Log:
     - 2025-12-11: Updated selectRecording to pass ID for derived shared state
     - 2025-12-12: Added active recording section at top of list with LIVE indicator (Phase 2.3)
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/RecordingsListView.swift

 WHY:
   To provide a user interface for browsing recordings.
   Main navigation hub for the app.
 */

import ComposableArchitecture
import SwiftUI

struct RecordingsListView: View {
    @Bindable var store: StoreOf<RecordingsListFeature>
    
    var body: some View {
        VStack {
            /// Recordings list (includes active recording section if recording in progress)
            if store.recordings.isEmpty && store.activeRecording == nil {
                emptyState
            } else {
                recordingsList
            }
            
            /// Record button
            recordButton
        }
        .navigationTitle("Recordings")
        .fullScreenCover(item: $store.scope(state: \.playback, action: \.playback)) { playbackStore in
            NavigationStack {
                PlaybackView(store: playbackStore)
                    .navigationTitle(playbackStore.recording.displayTitle)
                    .navigationBarTitleDisplayMode(.inline)
            }
        }
        .alert($store.scope(state: \.alert, action: \.alert))
    }
    
    // MARK: - Subviews
    
    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()
            
            Image(systemName: "waveform")
                .font(.system(size: 60))
                .foregroundColor(.secondary)
            
            Text("No Recordings")
                .font(.title2)
                .foregroundColor(.secondary)
            
            Text("Tap the record button to create your first recording.")
                .font(.body)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
            
            Spacer()
        }
    }
    
    private var recordingsList: some View {
        List {
            /**
             Active recording section (if recording in progress).
             
             **Phase 2.3 Addition (2025-12-12):**
             Shows the active recording at the top of the list with a LIVE indicator
             and live transcription preview. This provides visual feedback to users
             about the ongoing recording.
             */
            if let activeRecording = store.activeRecording {
                Section {
                    ActiveRecordingRow(
                        recording: activeRecording,
                        transcription: store.liveTranscription
                    )
                } header: {
                    HStack {
                        Text("Recording Now")
                        LiveBadge()
                    }
                }
            }
            
            /// Saved recordings section
            Section(store.activeRecording != nil ? "Saved Recordings" : "") {
                ForEach(store.recordings) { recording in
                    RecordingRow(recording: recording)
                        .contentShape(Rectangle())
                        .onTapGesture {
                            /**
                             Pass recording.id for derived shared state lookup.
                             
                             **Pattern Source:** SyncUpsListView.swift
                             
                             The reducer uses this ID to derive a Shared<Recording>
                             that propagates mutations back to the recordings list.
                             */
                            store.send(.selectRecording(recording.id))
                        }
                }
                .onDelete { indexSet in
                    store.send(.deleteRecordings(indexSet))
                }
            }
        }
    }
    
    private var recordButton: some View {
        Button {
            store.send(.recordButtonTapped, animation: .spring())
        } label: {
            ZStack {
                Circle()
                    .fill(Color(.label))
                    .frame(width: 74, height: 74)
                
                Circle()
                    .fill(Color.red)
                    .frame(width: 66, height: 66)
            }
        }
        .padding()
        .background(Color(.systemBackground))
    }
}

// MARK: - Active Recording Row

/**
 A row view for displaying the active recording in progress.
 
 **Phase 2.3 Addition (2025-12-12):**
 Shows the active recording with:
 - Pulsing red dot to indicate active recording
 - Recording title (or "Recording..." placeholder)
 - Duration counter
 - Live transcription preview (last segment)
 
 This view is displayed at the top of the recordings list while recording is in progress.
 */
struct ActiveRecordingRow: View {
    let recording: Recording
    let transcription: LiveTranscriptionState
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                /// Recording indicator (pulsing red dot)
                PulsingRecordingDot()
                
                Text(recording.displayTitle)
                    .font(.headline)
                
                Spacer()
                
                /// Duration
                Text(formattedDuration)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            
            /// Live transcription preview
            if let lastSegment = transcription.segments.last {
                Text(lastSegment.text)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            } else if let volatile = transcription.volatileText, !volatile.isEmpty {
                Text(volatile)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }
        }
        .padding(.vertical, 4)
    }
    
    private var formattedDuration: String {
        let minutes = Int(recording.duration) / 60
        let seconds = Int(recording.duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

// MARK: - Pulsing Recording Dot

/**
 A pulsing red dot that indicates active recording.
 
 Uses a repeating animation to create a visual "heartbeat" effect
 that draws attention to the active recording state.
 */
struct PulsingRecordingDot: View {
    @State private var isAnimating = false
    
    var body: some View {
        Circle()
            .fill(Color.red)
            .frame(width: 8, height: 8)
            .scaleEffect(isAnimating ? 1.3 : 1.0)
            .opacity(isAnimating ? 0.7 : 1.0)
            .onAppear {
                withAnimation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true)) {
                    isAnimating = true
                }
            }
    }
}

// MARK: - Recording Row

struct RecordingRow: View {
    let recording: Recording
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            /// Title row with media indicator
            HStack {
                Text(recording.displayTitle)
                    .font(.headline)
                    .lineLimit(2)
                
                Spacer()
                
                /// Media indicator icon if has media
                if !recording.media.isEmpty {
                    HStack(spacing: 2) {
                        Image(systemName: "photo.fill")
                            .font(.caption)
                            .foregroundColor(.secondary)
                        Text("\(recording.media.count)")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }
            }
            
            /// Date and duration row
            HStack {
                Text(formattedDate)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(formattedDuration)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            /// Media thumbnails row (if has media)
            if !recording.media.isEmpty {
                mediaThumbnailsRow
            }
            
            /// Transcription preview
            if !recording.transcription.text.isEmpty {
                Text(recording.transcription.text)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
        }
        .padding(.vertical, 4)
    }
    
    // MARK: - Media Thumbnails
    
    @ViewBuilder
    private var mediaThumbnailsRow: some View {
        let maxThumbnails = 4
        let displayMedia = Array(recording.media.prefix(maxThumbnails))
        let remainingCount = recording.media.count - maxThumbnails
        
        HStack(spacing: 6) {
            ForEach(displayMedia) { media in
                if let thumbnailData = media.thumbnailData,
                   let uiImage = UIImage(data: thumbnailData) {
                    Image(uiImage: uiImage)
                        .resizable()
                        .aspectRatio(contentMode: .fill)
                        .frame(width: 44, height: 44)
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                } else {
                    /// Placeholder for missing thumbnail
                    RoundedRectangle(cornerRadius: 6)
                        .fill(Color.gray.opacity(0.3))
                        .frame(width: 44, height: 44)
                        .overlay {
                            Image(systemName: "photo")
                                .foregroundColor(.gray)
                        }
                }
            }
            
            /// "+N" indicator for remaining media
            if remainingCount > 0 {
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color.gray.opacity(0.2))
                    .frame(width: 44, height: 44)
                    .overlay {
                        Text("+\(remainingCount)")
                            .font(.caption)
                            .fontWeight(.medium)
                            .foregroundColor(.secondary)
                    }
            }
            
            Spacer()
        }
    }
    
    // MARK: - Formatting
    
    private var formattedDate: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: recording.date)
    }
    
    private var formattedDuration: String {
        let minutes = Int(recording.duration) / 60
        let seconds = Int(recording.duration) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

// MARK: - Preview

#Preview("Empty") {
    NavigationStack {
        RecordingsListView(
            store: Store(initialState: RecordingsListFeature.State()) {
                RecordingsListFeature()
            }
        )
    }
}

#Preview("With Recordings") {
    var state = RecordingsListFeature.State()
    
    return NavigationStack {
        RecordingsListView(
            store: Store(initialState: state) {
                RecordingsListFeature()
            } withDependencies: {
                $0.defaultFileStorage = .inMemory
            }
        )
    }
}