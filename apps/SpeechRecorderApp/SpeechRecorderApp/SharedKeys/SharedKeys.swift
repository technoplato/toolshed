/**
 HOW:
   Import this file to access shared persistence keys.
   
   ```swift
   @Shared(.recordings) var recordings
   @Shared(.fullscreenTextSize) var textSize
   @Shared(.liveTranscription) var transcription
   ```
   
 WHO:
   AI Agent, Developer
   (Context: Shared state keys for TCA features)

 WHAT:
   Defines type-safe SharedKey extensions for persisted and in-memory state.
   Follows Point-Free's swift-sharing patterns.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-11

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/SharedKeys/SharedKeys.swift

 WHY:
   To provide type-safe, reusable keys for @Shared state.
   Enables automatic state synchronization between parent and child features.
 */

/**
 HOW:
   Use with @Shared property wrapper:
   
   ```swift
   @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording>
   ```
   
   No default value needed at usage site - it's embedded in the key definition.
   
   [Inputs]
   - None
   
   [Outputs]
   - Shared key for file storage with embedded default
   
   [Side Effects]
   - Reads/writes to documents directory

 WHO:
   AI Agent, Developer
   (Context: Swift Sharing keys for persistence)

 WHAT:
   Defines shared keys for persisting app data using Swift Sharing.
   Uses .fileStorage for JSON persistence to the documents directory.
   
   **Migration Note (2025-12-11):**
   Updated to use SharedKey with .Default pattern and IdentifiedArrayOf
   following the SyncUps reference implementation.
   
   Reference: SyncUpsList.swift:183-186
   https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpsList.swift
   
   See: docs/swift-sharing-state-comprehensive-guide.md#appendix-a-speechrecorderapp-migration-guide

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-11
   [Change Log:
     - 2025-12-11: Migrated to SharedKey.Default pattern with IdentifiedArrayOf
                   for O(1) lookup and embedded default value
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/SharedKeys/SharedKeys.swift

 WHY:
   To provide type-safe, reusable persistence keys.
   Follows Swift Sharing patterns for file-based persistence.
   
   Using SharedKey.Default pattern:
   1. Embeds default value in key definition (no default at usage sites)
   2. Uses IdentifiedArrayOf for O(1) lookup by ID
   3. Matches the production SyncUps app pattern
 */

import ComposableArchitecture
import Foundation

// MARK: - Recordings Key

/**
 Shared key for the list of recordings with embedded default.
 
 **Pattern Source:** SyncUpsList.swift:183-186
 
 Uses `SharedKey` (not `SharedReaderKey`) for read-write access.
 Uses `.Default` to embed the default value in the key definition.
 Uses `IdentifiedArrayOf<Recording>` for O(1) lookup by ID.
 
 Usage:
 ```swift
 @Shared(.recordings) var recordings: IdentifiedArrayOf<Recording>
 // No default needed - embedded in key definition
 ```
 */
extension SharedKey where Self == FileStorageKey<IdentifiedArrayOf<Recording>>.Default {
    static var recordings: Self {
        Self[.fileStorage(.documentsDirectory.appending(component: "recordings.json")), default: []]
    }
}

// MARK: - Fullscreen Text Size Key

extension SharedKey where Self == AppStorageKey<Double>.Default {
    /// Shared key for the fullscreen transcript text size
    /// Default is 24pt, range is 16-48pt
    static var fullscreenTextSize: Self {
        Self[.appStorage("fullscreenTextSize"), default: 24.0]
    }
}

// MARK: - Live Transcription State

/**
 Live transcription state shared between AppFeature, RecordingFeature, and FullscreenTranscriptFeature.
 
 Uses in-memory storage since this is ephemeral session state that doesn't need persistence.
 
 **Ownership Pattern (2025-12-12):**
 - AppFeature owns this state with `@Shared(.liveTranscription)`
 - RecordingFeature receives it via `@Shared var liveTranscription` (no key - from parent)
 - FullscreenTranscriptFeature receives a derived reference and sees updates automatically
 
 This follows TCA best practice: shared state should be owned at the highest level
 that needs access, with child features receiving derived references.
 
 **Pattern Source:** Recipe 4 in swift-sharing-state-comprehensive-guide.md
 */
struct LiveTranscriptionState: Equatable, Sendable {
    /// Finalized transcription segments
    var segments: [TranscriptionSegment] = []
    
    /// All finalized words with timestamps
    var words: [TimestampedWord] = []
    
    /// In-progress volatile text (current segment being transcribed)
    var volatileText: String?
    
    /// Current recording/playback time
    var currentTime: TimeInterval = 0
    
    /// Currently highlighted word index (for playback)
    var currentWordIndex: Int?
    
    /// Full text combining all segments
    var fullText: String {
        let segmentText = segments.map(\.text).joined(separator: " ")
        if let volatile = volatileText, !volatile.isEmpty {
            return segmentText.isEmpty ? volatile : segmentText + " " + volatile
        }
        return segmentText
    }
}

extension SharedKey where Self == InMemoryKey<LiveTranscriptionState>.Default {
    /// Shared key for live transcription state during recording
    /// Uses in-memory storage since this is ephemeral session state
    static var liveTranscription: Self {
        Self[.inMemory("liveTranscription"), default: LiveTranscriptionState()]
    }
}

// MARK: - Active Recording Key

/**
 The currently active recording (in-memory, not persisted).
 
 **Ownership Pattern (2025-12-12):**
 - AppFeature owns this state with `@Shared(.activeRecording)`
 - This is ephemeral session state that doesn't need persistence
 - Used to track the recording in progress before it's saved to the recordings list
 
 **Pattern Source:** Recipe 4 in swift-sharing-state-comprehensive-guide.md
 */
extension SharedKey where Self == InMemoryKey<Recording?>.Default {
    /// The currently active recording (in-memory, not persisted)
    static var activeRecording: Self {
        Self[.inMemory("activeRecording"), default: nil]
    }
}

// MARK: - URL Extensions

extension URL {
    /// The documents directory for the app
    static var documentsDirectory: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
    
    /// The recordings directory within documents
    static var recordingsDirectory: URL {
        documentsDirectory.appending(component: "Recordings")
    }
}