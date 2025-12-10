/**
 HOW:
   Use via @Dependency(\.speechClient) in TCA reducers.
   
   ```swift
   @Dependency(\.speechClient) var speechClient
   
   // Check if speech recognition is available
   let available = await speechClient.isAvailable()
   
   // Start transcription
   for try await transcription in speechClient.startTranscription(audioStream) {
       // Handle transcription updates
   }
   ```
   
   [Inputs]
   - Audio buffer stream for transcription
   
   [Outputs]
   - AsyncStream of Transcription updates
   
   [Side Effects]
   - Uses SpeechAnalyzer API (iOS 26.0+)
   - May download speech recognition assets

 WHO:
   AI Agent, Developer
   (Context: TDD for SpeechClient dependency - Phase 2)

 WHAT:
   Dependency client for speech recognition functionality.
   Wraps iOS 26.0+ SpeechAnalyzer API for real-time transcription.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/SpeechClient.swift

 WHY:
   To provide a testable interface for speech recognition.
   Following TCA patterns, this allows mocking in tests while
   providing real implementation in production.
 */

import ComposableArchitecture
import Foundation

/// Dependency client for speech recognition
@DependencyClient
struct SpeechClient: Sendable {
    /// Check if speech recognition is available
    var isAvailable: @Sendable () async -> Bool = { false }
    
    /// Request speech recognition permission
    var requestAuthorization: @Sendable () async -> Bool = { false }
    
    /// Start transcription from audio buffers
    /// Returns an AsyncStream of Transcription updates
    var startTranscription: @Sendable (
        _ audioStream: AsyncStream<AudioBuffer>
    ) async throws -> AsyncStream<Transcription>
    
    /// Stop the current transcription
    var stopTranscription: @Sendable () async -> Void
}

/// Represents an audio buffer for speech recognition
struct AudioBuffer: Sendable {
    let data: Data
    let sampleRate: Double
    let channelCount: Int
}

// MARK: - Test Dependency Key

extension SpeechClient: TestDependencyKey {
    /// Preview implementation that returns mock transcriptions
    static var previewValue: Self {
        Self(
            isAvailable: { true },
            requestAuthorization: { true },
            startTranscription: { _ in
                AsyncStream { continuation in
                    Task {
                        /// Simulate transcription updates
                        try? await Task.sleep(for: .seconds(1))
                        continuation.yield(Transcription(
                            text: "Hello",
                            words: [
                                TimestampedWord(text: "Hello", startTime: 0, endTime: 0.5, confidence: nil)
                            ],
                            isFinal: false
                        ))
                        try? await Task.sleep(for: .seconds(1))
                        continuation.yield(Transcription(
                            text: "Hello world",
                            words: [
                                TimestampedWord(text: "Hello", startTime: 0, endTime: 0.5, confidence: nil),
                                TimestampedWord(text: "world", startTime: 0.5, endTime: 1.0, confidence: nil)
                            ],
                            isFinal: true
                        ))
                        continuation.finish()
                    }
                }
            },
            stopTranscription: {}
        )
    }
    
    /// Test implementation with unimplemented closures
    static let testValue = Self()
}

// MARK: - Dependency Values Extension

extension DependencyValues {
    /// Access the speech client
    var speechClient: SpeechClient {
        get { self[SpeechClient.self] }
        set { self[SpeechClient.self] = newValue }
    }
}