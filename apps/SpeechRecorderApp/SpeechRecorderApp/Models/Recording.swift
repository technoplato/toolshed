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
   - media: Array of photos/screenshots captured during recording
   
   [Outputs]
   - Codable struct for persistence with @Shared(.fileStorage)
   
   [Side Effects]
   - None (pure data model)

 WHO:
   AI Agent, Developer
   (Context: Building speech recorder app with word-level timestamps)

 WHAT:
   A single recording with its transcription and synchronized media.
   This is the main entity persisted to disk using Swift Sharing.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Models/Recording.swift

 WHY:
   To represent a complete recording that can be persisted and played back.
   Contains all data needed for synchronized playback with word highlighting
   and inline photo/screenshot display.
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
    
    /// Photos and screenshots captured during recording
    var media: [TimestampedMedia]
    
    /// Create a new recording with default values
    init(
        id: UUID = UUID(),
        title: String = "",
        date: Date = Date(),
        duration: TimeInterval = 0,
        audioURL: URL,
        transcription: Transcription = .empty,
        media: [TimestampedMedia] = []
    ) {
        self.id = id
        self.title = title
        self.date = date
        self.duration = duration
        self.audioURL = audioURL
        self.transcription = transcription
        self.media = media
    }
    
    /// Get media items sorted by timestamp
    var sortedMedia: [TimestampedMedia] {
        media.sorted { $0.timestamp < $1.timestamp }
    }
    
    /// Find media at or before the given time
    func mediaAtTime(_ time: TimeInterval) -> [TimestampedMedia] {
        media.filter { $0.timestamp <= time }
    }
    
    /// Find the most recent media before the given time
    func mostRecentMedia(before time: TimeInterval) -> TimestampedMedia? {
        media
            .filter { $0.timestamp <= time }
            .max { $0.timestamp < $1.timestamp }
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
        transcription: Transcription = .preview(),
        media: [TimestampedMedia] = []
    ) -> Recording {
        Recording(
            id: id,
            title: title,
            date: date,
            duration: duration,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: transcription,
            media: media
        )
    }
    
    /// Create a Recording with sample media for previews
    static func previewWithMedia() -> Recording {
        Recording(
            id: UUID(),
            title: "Recording with Photos",
            date: Date(),
            duration: 30.0,
            audioURL: URL(fileURLWithPath: "/tmp/test.m4a"),
            transcription: .preview(),
            media: [
                .preview(timestamp: 5.0, mediaType: .photo),
                .preview(timestamp: 12.0, mediaType: .screenshot),
                .preview(timestamp: 25.0, mediaType: .photo)
            ]
        )
    }
}