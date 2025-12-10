/**
 HOW:
   Used as a data model for a complete recording with its transcription.
   
   [Inputs]
   - id: Unique identifier
   - title: User-editable title
   - date: When the recording was created
   - duration: Length of the recording in seconds
   - audioURL: File URL where audio is stored
   - transcription: The transcription with word-level timing
   
   [Outputs]
   - Codable struct for persistence with @Shared(.fileStorage)
   
   [Side Effects]
   - None (pure data model)

 WHO:
   AI Agent, Developer
   (Context: Building speech recorder app with word-level timestamps)

 WHAT:
   A single recording with its transcription.
   This is the main entity persisted to disk using Swift Sharing.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Models/Recording.swift

 WHY:
   To represent a complete recording that can be persisted and played back.
   Contains all data needed for synchronized playback with word highlighting.
 */

import Foundation

/// A single recording with its transcription
struct Recording: Codable, Identifiable, Equatable, Sendable {
    /// Unique identifier for the recording
    let id: UUID
    
    /// User-editable title for the recording
    var title: String
    
    /// When the recording was created
    var date: Date
    
    /// Duration of the recording in seconds
    var duration: TimeInterval
    
    /// File URL where the audio is stored
    var audioURL: URL
    
    /// The transcription with word-level timing
    var transcription: Transcription
    
    /// Create a new recording with default values
    init(
        id: UUID = UUID(),
        title: String = "",
        date: Date = Date(),
        duration: TimeInterval = 0,
        audioURL: URL,
        transcription: Transcription = .empty
    ) {
        self.id = id
        self.title = title
        self.date = date
        self.duration = duration
        self.audioURL = audioURL
        self.transcription = transcription
    }
    
    /// Generate a default title based on the date
    var defaultTitle: String {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return "Recording \(formatter.string(from: date))"
    }
    
    /// Display title (uses default if title is empty)
    var displayTitle: String {
        title.isEmpty ? defaultTitle : title
    }
}

extension Recording {
    /// Create a Recording for testing or previews
    static func preview(
        id: UUID = UUID(),
        title: String = "Test Recording",
        date: Date = Date(),
        duration: TimeInterval = 10.0,
        transcription: Transcription = .preview()
    ) -> Recording {
        Recording(
            id: id,
            title: title,
            date: date,
            duration: duration,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: transcription
        )
    }
}