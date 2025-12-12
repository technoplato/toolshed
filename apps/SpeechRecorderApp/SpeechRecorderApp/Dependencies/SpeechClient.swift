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

// MARK: - Convenience Initializers

extension SpeechClient {
    /// A no-op implementation that does nothing - useful as a base for tests.
    /// All methods return empty/default values immediately.
    static let noop = Self(
        requestAuthorization: { .notDetermined },
        isAvailable: { _ in false },
        isAssetInstalled: { _ in false },
        ensureAssets: { _ in },
        startTranscription: { _ in AsyncThrowingStream { $0.finish() } },
        streamAudio: { _ in },
        finishTranscription: {}
    )
    
    /// A preview implementation with simulated transcription for SwiftUI previews.
    /// - Parameters:
    ///   - transcriptionText: The text to simulate transcribing (default: sample text)
    ///   - wordDelay: Delay between words in milliseconds (default: 300)
    /// - Returns: A configured SpeechClient for previews
    static func preview(
        transcriptionText: String = "Hello world this is a test transcription",
        wordDelay: Int = 300
    ) -> Self {
        let isTranscribing = LockIsolated(false)
        
        return Self(
            requestAuthorization: { .authorized },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { [isTranscribing] _ in
                AsyncThrowingStream { continuation in
                    Task {
                        isTranscribing.setValue(true)
                        
                        let wordList = transcriptionText.split(separator: " ").map(String.init)
                        var accumulatedWords: [TimestampedWord] = []
                        var currentTime: TimeInterval = 0
                        
                        for word in wordList {
                            guard isTranscribing.value else { break }
                            
                            try? await Task.sleep(for: .milliseconds(wordDelay))
                            
                            let startTime = currentTime
                            let endTime = currentTime + Double(wordDelay) / 1000.0
                            currentTime = endTime + 0.1
                            
                            accumulatedWords.append(TimestampedWord(
                                text: word,
                                startTime: startTime,
                                endTime: endTime,
                                confidence: Float.random(in: 0.85...0.99)
                            ))
                            
                            continuation.yield(TranscriptionResult(
                                text: accumulatedWords.map(\.text).joined(separator: " "),
                                words: accumulatedWords,
                                isFinal: false
                            ))
                        }
                        
                        /// Final result
                        if !accumulatedWords.isEmpty {
                            continuation.yield(TranscriptionResult(
                                text: accumulatedWords.map(\.text).joined(separator: " "),
                                words: accumulatedWords,
                                isFinal: true
                            ))
                        }
                        
                        continuation.finish()
                    }
                }
            },
            streamAudio: { _ in },
            finishTranscription: { [isTranscribing] in
                isTranscribing.setValue(false)
            }
        )
    }
    
    /// Convenience factory for testing authorization states.
    /// - Parameter status: The authorization status to return
    /// - Returns: A configured SpeechClient for testing authorization flows
    static func withAuthorizationStatus(_ status: AuthorizationStatus) -> Self {
        var client = noop
        client.requestAuthorization = { status }
        return client
    }
    
    /// Convenience factory for testing availability.
    /// - Parameter available: Whether speech recognition is available
    /// - Returns: A configured SpeechClient for testing availability checks
    static func withAvailability(_ available: Bool) -> Self {
        var client = noop
        client.isAvailable = { _ in available }
        client.isAssetInstalled = { _ in available }
        return client
    }
    
    /// Convenience factory for testing with a specific transcription result.
    /// - Parameter result: The transcription result to return immediately
    /// - Returns: A configured SpeechClient for testing transcription handling
    static func withTranscriptionResult(_ result: TranscriptionResult) -> Self {
        var client = noop
        client.requestAuthorization = { .authorized }
        client.isAvailable = { _ in true }
        client.isAssetInstalled = { _ in true }
        client.startTranscription = { _ in
            AsyncThrowingStream { continuation in
                continuation.yield(result)
                continuation.finish()
            }
        }
        return client
    }
    
    /// Convenience factory for testing transcription errors.
    /// - Parameter error: The error to throw during transcription
    /// - Returns: A configured SpeechClient for testing error handling
    static func withTranscriptionError(_ error: Failure) -> Self {
        var client = noop
        client.requestAuthorization = { .authorized }
        client.isAvailable = { _ in true }
        client.isAssetInstalled = { _ in true }
        client.startTranscription = { _ in
            AsyncThrowingStream { continuation in
                continuation.finish(throwing: error)
            }
        }
        return client
    }
}