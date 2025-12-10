/**
 HOW:
   Used as a data model for photos/screenshots captured during recording.
   
   [Inputs]
   - id: Unique identifier
   - timestamp: When the media was captured relative to recording start
   - assetIdentifier: PHAsset local identifier for the photo
   - thumbnailData: Optional cached thumbnail for quick display
   
   [Outputs]
   - Codable struct for persistence with Recording
   
   [Side Effects]
   - None (pure data model)

 WHO:
   AI Agent, Developer
   (Context: Building speech recorder app with photo synchronization)

 WHAT:
   A photo or screenshot captured during recording with its timestamp.
   Used to display media inline during recording and playback.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Models/TimestampedMedia.swift

 WHY:
   To represent media captured during recording that can be displayed
   at the correct time during playback.
 */

import Foundation

/// Type of media captured
enum MediaType: String, Codable, Sendable {
    case photo
    case screenshot
}

/// A photo or screenshot captured during recording with its timestamp
struct TimestampedMedia: Codable, Identifiable, Equatable, Sendable {
    /// Unique identifier for the media
    let id: UUID
    
    /// When the media was captured relative to recording start (in seconds)
    let timestamp: TimeInterval
    
    /// PHAsset local identifier for accessing the photo from the library
    let assetIdentifier: String
    
    /// Type of media (photo or screenshot)
    let mediaType: MediaType
    
    /// Creation date of the media
    let creationDate: Date
    
    /// Optional cached thumbnail data for quick display
    var thumbnailData: Data?
    
    /// Create a new timestamped media
    init(
        id: UUID = UUID(),
        timestamp: TimeInterval,
        assetIdentifier: String,
        mediaType: MediaType,
        creationDate: Date = Date(),
        thumbnailData: Data? = nil
    ) {
        self.id = id
        self.timestamp = timestamp
        self.assetIdentifier = assetIdentifier
        self.mediaType = mediaType
        self.creationDate = creationDate
        self.thumbnailData = thumbnailData
    }
}

// MARK: - Preview Helpers

extension TimestampedMedia {
    /// Create a TimestampedMedia for testing or previews
    static func preview(
        id: UUID = UUID(),
        timestamp: TimeInterval = 5.0,
        assetIdentifier: String = "test-asset-id",
        mediaType: MediaType = .photo,
        creationDate: Date = Date()
    ) -> TimestampedMedia {
        TimestampedMedia(
            id: id,
            timestamp: timestamp,
            assetIdentifier: assetIdentifier,
            mediaType: mediaType,
            creationDate: creationDate
        )
    }
}