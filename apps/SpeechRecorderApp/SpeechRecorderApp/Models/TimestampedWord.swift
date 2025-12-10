/**
 HOW:
   Used as a data model for word-level timing information in transcriptions.
   
   [Inputs]
   - text: The word text
   - startTime: When the word starts in the audio (seconds)
   - endTime: When the word ends in the audio (seconds)
   - confidence: Optional confidence score from speech recognition
   
   [Outputs]
   - Codable struct for persistence
   
   [Side Effects]
   - None (pure data model)

 WHO:
   AI Agent, Developer
   (Context: Building speech recorder app with word-level timestamps)

 WHAT:
   A word with its timing information extracted from speech recognition.
   Used for synchronized playback where words are highlighted as audio plays.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Models/TimestampedWord.swift

 WHY:
   To enable synchronized playback with word highlighting.
   The SpeechAnalyzer API provides audioTimeRange attributes on AttributedString
   runs, which we extract into this structured format.
 */

import Foundation

/// A word with its timing information from speech recognition
struct TimestampedWord: Codable, Equatable, Sendable, Identifiable {
    /// Unique identifier for SwiftUI list rendering
    var id: UUID = UUID()
    
    /// The word text
    let text: String
    
    /// Start time in seconds from the beginning of the recording
    let startTime: TimeInterval
    
    /// End time in seconds from the beginning of the recording
    let endTime: TimeInterval
    
    /// Optional confidence score (0.0 to 1.0) from speech recognition
    /// Note: The new SpeechAnalyzer API may not provide confidence scores
    let confidence: Float?
    
    /// Duration of the word in seconds
    var duration: TimeInterval {
        endTime - startTime
    }
    
    /// Check if a given time falls within this word's time range
    func contains(time: TimeInterval) -> Bool {
        time >= startTime && time < endTime
    }
}

extension TimestampedWord {
    /// Create a TimestampedWord for testing or previews
    static func preview(
        text: String,
        startTime: TimeInterval,
        endTime: TimeInterval,
        confidence: Float? = nil
    ) -> TimestampedWord {
        TimestampedWord(
            text: text,
            startTime: startTime,
            endTime: endTime,
            confidence: confidence
        )
    }
}