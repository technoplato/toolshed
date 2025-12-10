/**
 HOW:
   Used as a data model for transcription data with word-level timing.
   
   [Inputs]
   - text: Full transcription text
   - words: Array of TimestampedWord with timing info
   - isFinal: Whether transcription is complete
   
   [Outputs]
   - Codable struct for persistence
   
   [Side Effects]
   - None (pure data model)

 WHO:
   AI Agent, Developer
   (Context: Building speech recorder app with word-level timestamps)

 WHAT:
   The transcription with word-level timing information.
   Contains both the full text and individual words with their timestamps.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Models/Transcription.swift

 WHY:
   To store transcription results from SpeechAnalyzer with timing data.
   The isFinal flag distinguishes between volatile (in-progress) and
   finalized transcription results.
 */

import Foundation

/// A segment of transcription with its timing information
struct TranscriptionSegment: Codable, Equatable, Sendable, Identifiable {
    /// Unique identifier
    var id: UUID = UUID()
    
    /// The text of this segment
    var text: String
    
    /// Words in this segment with their timing
    var words: [TimestampedWord]
    
    /// Start time of this segment (from first word)
    var startTime: TimeInterval {
        words.first?.startTime ?? 0
    }
    
    /// End time of this segment (from last word)
    var endTime: TimeInterval {
        words.last?.endTime ?? 0
    }
    
    /// Duration of this segment
    var duration: TimeInterval {
        endTime - startTime
    }
}

/// The transcription with word-level timing
struct Transcription: Codable, Equatable, Sendable {
    /// The full transcription text
    var text: String
    
    /// Individual words with their timing information
    var words: [TimestampedWord]
    
    /// Segments of transcription (separated by pauses)
    var segments: [TranscriptionSegment]
    
    /// Whether this transcription is finalized or still in progress (volatile)
    var isFinal: Bool
    
    /// Create an empty transcription
    static var empty: Transcription {
        Transcription(text: "", words: [], segments: [], isFinal: false)
    }
    
    /// Total duration based on the last word's end time
    var duration: TimeInterval {
        words.last?.endTime ?? 0
    }
    
    /// Find the word at a given time
    func word(at time: TimeInterval) -> TimestampedWord? {
        words.first { $0.contains(time: time) }
    }
    
    /// Find the index of the word at a given time
    func wordIndex(at time: TimeInterval) -> Int? {
        words.firstIndex { $0.contains(time: time) }
    }
}

extension Transcription {
    /// Create a Transcription for testing or previews
    static func preview(
        text: String = "Hello world",
        words: [TimestampedWord]? = nil,
        segments: [TranscriptionSegment]? = nil,
        isFinal: Bool = true
    ) -> Transcription {
        let defaultWords = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5),
            TimestampedWord.preview(text: "world", startTime: 0.6, endTime: 1.0)
        ]
        let actualWords = words ?? defaultWords
        let defaultSegments = [
            TranscriptionSegment(text: text, words: actualWords)
        ]
        return Transcription(
            text: text,
            words: actualWords,
            segments: segments ?? defaultSegments,
            isFinal: isFinal
        )
    }
}

extension TranscriptionSegment {
    /// Create a TranscriptionSegment for testing or previews
    static func preview(
        text: String,
        words: [TimestampedWord]
    ) -> TranscriptionSegment {
        TranscriptionSegment(text: text, words: words)
    }
}