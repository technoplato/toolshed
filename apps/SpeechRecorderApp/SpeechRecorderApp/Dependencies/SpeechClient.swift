/**
 HOW:
   Use via @Dependency(\.speechClient) in TCA reducers.
   
   ```swift
   @Dependency(\.speechClient) var speechClient
   
   // Request authorization
   let status = await speechClient.requestAuthorization()
   
   // Start transcription
   for try await result in try await speechClient.startTranscription(locale) {
       // Handle transcription updates
   }
   ```
   
   [Inputs]
   - Locale for speech recognition
   - Audio buffers streamed via streamAudio
   
   [Outputs]
   - AsyncThrowingStream of TranscriptionResult
   
   [Side Effects]
   - Uses SpeechAnalyzer API (iOS 26.0+)
   - May download speech recognition assets

 WHO:
   AI Agent, Developer
   (Context: TDD for SpeechClient dependency - Phase 2)

 WHAT:
   Dependency client for speech recognition functionality.
   Wraps iOS 26.0+ SpeechAnalyzer API for real-time transcription.
   Follows TCA patterns from swift-composable-architecture/Examples/SpeechRecognition.

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

import AVFoundation
import ComposableArchitecture
import Foundation

// MARK: - Transcription Result

/// Result from speech transcription
struct TranscriptionResult: Equatable, Sendable {
    /// The transcribed text
    var text: String
    
    /// Word-level timing information
    var words: [TimestampedWord]
    
    /// Whether this is the final result for this segment
    var isFinal: Bool
}

// MARK: - Speech Client

/// Dependency client for speech recognition
@DependencyClient
struct SpeechClient: Sendable {
    /// Request speech recognition authorization
    var requestAuthorization: @Sendable () async -> AuthorizationStatus = { .notDetermined }
    
    /// Check if speech recognition is available for a locale
    var isAvailable: @Sendable (_ locale: Locale) async -> Bool = { _ in false }
    
    /// Check if assets are installed for a locale
    var isAssetInstalled: @Sendable (_ locale: Locale) async -> Bool = { _ in false }
    
    /// Ensure assets are installed for a locale (downloads if needed)
    var ensureAssets: @Sendable (_ locale: Locale) async throws -> Void
    
    /// Start transcription for a locale
    /// Returns a stream of transcription results
    var startTranscription: @Sendable (_ locale: Locale) async throws -> AsyncThrowingStream<TranscriptionResult, Error>
    
    /// Stream audio buffer to the transcriber
    var streamAudio: @Sendable (_ buffer: AVAudioPCMBuffer) async -> Void
    
    /// Finish transcription and get final results
    var finishTranscription: @Sendable () async throws -> Void
    
    // MARK: - Types
    
    enum AuthorizationStatus: Equatable, Sendable {
        case notDetermined
        case denied
        case restricted
        case authorized
    }
    
    enum Failure: Error, Equatable, Sendable {
        case notAuthorized
        case notAvailable
        case localeNotSupported
        case assetInstallationFailed
        case transcriptionFailed(String)
        case audioStreamingFailed
    }
}

// MARK: - Test Dependency Key

extension SpeechClient: TestDependencyKey {
    /// Preview implementation that returns mock transcriptions
    static var previewValue: Self {
        let isRecording = LockIsolated(false)
        
        return Self(
            requestAuthorization: { .authorized },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { _ in
                AsyncThrowingStream { continuation in
                    Task {
                        isRecording.setValue(true)
                        
                        /// Simulate transcription updates
                        var words: [TimestampedWord] = []
                        let sampleWords = ["Hello", "world", "this", "is", "a", "test"]
                        var currentTime: TimeInterval = 0
                        
                        for word in sampleWords {
                            guard isRecording.value else { break }
                            
                            try? await Task.sleep(for: .milliseconds(300))
                            
                            let startTime = currentTime
                            let endTime = currentTime + 0.3
                            currentTime = endTime + 0.1
                            
                            words.append(TimestampedWord(
                                text: word,
                                startTime: startTime,
                                endTime: endTime,
                                confidence: 0.95
                            ))
                            
                            continuation.yield(TranscriptionResult(
                                text: words.map(\.text).joined(separator: " "),
                                words: words,
                                isFinal: false
                            ))
                        }
                        
                        /// Final result
                        continuation.yield(TranscriptionResult(
                            text: words.map(\.text).joined(separator: " "),
                            words: words,
                            isFinal: true
                        ))
                        
                        continuation.finish()
                    }
                }
            },
            streamAudio: { _ in },
            finishTranscription: {
                isRecording.setValue(false)
            }
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