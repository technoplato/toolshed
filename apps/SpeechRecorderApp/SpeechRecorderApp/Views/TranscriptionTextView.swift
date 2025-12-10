/**
 HOW:
   Use in SwiftUI views:
   
   ```swift
   TranscriptionTextView(
       words: transcription.words,
       currentWordIndex: currentWordIndex
   )
   ```
   
   [Inputs]
   - words: Array of TimestampedWord
   - currentWordIndex: Optional index of currently highlighted word
   
   [Outputs]
   - SwiftUI View with highlighted text
   
   [Side Effects]
   - None

 WHO:
   AI Agent, Developer
   (Context: SwiftUI view for transcription display)

 WHAT:
   SwiftUI view for displaying transcription with word highlighting.
   Highlights the current word based on playback position.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/TranscriptionTextView.swift

 WHY:
   To provide visual feedback during synchronized playback.
   Highlights words as they are spoken in the audio.
 */

import SwiftUI

struct TranscriptionTextView: View {
    /// The words to display
    let words: [TimestampedWord]
    
    /// The index of the currently highlighted word
    let currentWordIndex: Int?
    
    var body: some View {
        Text(attributedText)
            .font(.body)
            .lineSpacing(8)
            .frame(maxWidth: .infinity, alignment: .leading)
    }
    
    /// Build the attributed string with highlighting
    private var attributedText: AttributedString {
        var result = AttributedString()
        
        for (index, word) in words.enumerated() {
            var wordString = AttributedString(word.text)
            
            /// Apply highlighting to current word
            if index == currentWordIndex {
                wordString.backgroundColor = .yellow
                wordString.font = .body.bold()
            }
            
            result.append(wordString)
            
            /// Add space after word (except for last word)
            if index < words.count - 1 {
                result.append(AttributedString(" "))
            }
        }
        
        return result
    }
}

// MARK: - Preview

#Preview("No Highlight") {
    TranscriptionTextView(
        words: [
            .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
            .preview(text: "world,", startTime: 0.6, endTime: 1.0),
            .preview(text: "this", startTime: 1.1, endTime: 1.3),
            .preview(text: "is", startTime: 1.4, endTime: 1.5),
            .preview(text: "a", startTime: 1.6, endTime: 1.7),
            .preview(text: "test", startTime: 1.8, endTime: 2.1),
            .preview(text: "recording.", startTime: 2.2, endTime: 2.8),
        ],
        currentWordIndex: nil
    )
    .padding()
}

#Preview("With Highlight") {
    TranscriptionTextView(
        words: [
            .preview(text: "Hello", startTime: 0.0, endTime: 0.5),
            .preview(text: "world,", startTime: 0.6, endTime: 1.0),
            .preview(text: "this", startTime: 1.1, endTime: 1.3),
            .preview(text: "is", startTime: 1.4, endTime: 1.5),
            .preview(text: "a", startTime: 1.6, endTime: 1.7),
            .preview(text: "test", startTime: 1.8, endTime: 2.1),
            .preview(text: "recording.", startTime: 2.2, endTime: 2.8),
        ],
        currentWordIndex: 3
    )
    .padding()
}