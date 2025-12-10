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

/// The transcription with word-level timing
struct Transcription: Codable, Equatable, Sendable {
    /// The full transcription text
    var text: String
    
    /// Individual words with their timing information
    var words: [TimestampedWord]
    
    /// Whether this transcription is finalized or still in progress (volatile)
    var isFinal: Bool
    
    /// Create an empty transcription
    static var empty: Transcription {
        Transcription(text: "", words: [], isFinal: false)
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
        isFinal: Bool = true
    ) -> Transcription {
        let defaultWords = [
            TimestampedWord.preview(text: "Hello", startTime: 0.0, endTime: 0.5),
            TimestampedWord.preview(text: "world", startTime: 0.6, endTime: 1.0)
        ]
        return Transcription(
            text: text,
            words: words ?? defaultWords,
            isFinal: isFinal
        )
    }
}