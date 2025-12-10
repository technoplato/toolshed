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

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

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
            /// Recordings list
            if store.recordings.isEmpty {
                emptyState
            } else {
                recordingsList
            }
            
            /// Record button
            recordButton
        }
        .navigationTitle("Recordings")
        .fullScreenCover(item: $store.scope(state: \.recording, action: \.recording)) { recordingStore in
            NavigationStack {
                RecordingView(store: recordingStore)
                    .navigationTitle("New Recording")
                    .navigationBarTitleDisplayMode(.inline)
                    .toolbar {
                        ToolbarItem(placement: .cancellationAction) {
                            Button("Cancel") {
                                recordingStore.send(.cancelButtonTapped)
                            }
                        }
                    }
            }
            .onAppear {
                /// Auto-start recording when the view appears
                if !recordingStore.isRecording {
                    recordingStore.send(.recordButtonTapped)
                }
            }
        }
        .fullScreenCover(item: $store.scope(state: \.playback, action: \.playback)) { playbackStore in
            NavigationStack {
                PlaybackView(store: playbackStore)
                    .navigationTitle(playbackStore.recording.displayTitle)
                    .navigationBarTitleDisplayMode(.inline)
            }
        }
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
            ForEach(store.recordings) { recording in
                RecordingRow(recording: recording)
                    .contentShape(Rectangle())
                    .onTapGesture {
                        store.send(.selectRecording(recording))
                    }
            }
            .onDelete { indexSet in
                store.send(.deleteRecordings(indexSet))
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

// MARK: - Recording Row

struct RecordingRow: View {
    let recording: Recording
    
    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(recording.displayTitle)
                .font(.headline)
            
            HStack {
                Text(formattedDate)
                    .font(.caption)
                    .foregroundColor(.secondary)
                
                Spacer()
                
                Text(formattedDuration)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
            
            if !recording.transcription.text.isEmpty {
                Text(recording.transcription.text)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .lineLimit(2)
            }
        }
        .padding(.vertical, 4)
    }
    
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