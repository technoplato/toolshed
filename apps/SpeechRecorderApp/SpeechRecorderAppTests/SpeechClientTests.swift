/**
 HOW:
   Run tests with: `xcodebuild test -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 17'`
   
   [Inputs]
   - None (unit tests)
   
   [Outputs]
   - Test results
   
   [Side Effects]
   - None (uses mocked dependencies)

 WHO:
   AI Agent, Developer
   (Context: TDD for SpeechClient dependency - Phase 2)

 WHAT:
   Unit tests for the SpeechClient dependency.
   Tests authorization, availability, and transcription flow.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/SpeechClientTests.swift

 WHY:
   TDD approach - tests the SpeechClient interface.
   Uses mock implementations to test the dependency contract.
 */

import ComposableArchitecture
import Foundation
import Testing
@testable import SpeechRecorderApp

@Suite("SpeechClient Tests")
struct SpeechClientTests {
    
    // MARK: - Authorization Tests
    
    @Test("Request authorization returns authorized status")
    func requestAuthorizationAuthorized() async {
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        let status = await client.requestAuthorization()
        #expect(status == .authorized)
    }
    
    @Test("Request authorization returns denied status")
    func requestAuthorizationDenied() async {
        let client = SpeechClient(
            requestAuthorization: { .denied },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        let status = await client.requestAuthorization()
        #expect(status == .denied)
    }
    
    @Test("Request authorization returns restricted status")
    func requestAuthorizationRestricted() async {
        let client = SpeechClient(
            requestAuthorization: { .restricted },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        let status = await client.requestAuthorization()
        #expect(status == .restricted)
    }
    
    // MARK: - Availability Tests
    
    @Test("isAvailable returns true for supported locale")
    func isAvailableForSupportedLocale() async {
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { locale in locale.identifier == "en_US" },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        let available = await client.isAvailable(Locale(identifier: "en_US"))
        #expect(available == true)
    }
    
    @Test("isAvailable returns false for unsupported locale")
    func isAvailableForUnsupportedLocale() async {
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { locale in locale.identifier == "en_US" },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        let available = await client.isAvailable(Locale(identifier: "xx_XX"))
        #expect(available == false)
    }
    
    // MARK: - Asset Installation Tests
    
    @Test("isAssetInstalled returns true when assets are installed")
    func isAssetInstalledTrue() async {
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        let installed = await client.isAssetInstalled(Locale(identifier: "en_US"))
        #expect(installed == true)
    }
    
    @Test("isAssetInstalled returns false when assets are not installed")
    func isAssetInstalledFalse() async {
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in false },
            ensureAssets: { _ in },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        let installed = await client.isAssetInstalled(Locale(identifier: "en_US"))
        #expect(installed == false)
    }
    
    @Test("ensureAssets completes successfully")
    func ensureAssetsSuccess() async throws {
        let ensureAssetsCalled = LockIsolated(false)
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in ensureAssetsCalled.setValue(true) },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        try await client.ensureAssets(Locale(identifier: "en_US"))
        #expect(ensureAssetsCalled.value == true)
    }
    
    @Test("ensureAssets throws for unsupported locale")
    func ensureAssetsThrows() async {
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in false },
            ensureAssets: { _ in throw SpeechClient.Failure.localeNotSupported },
            startTranscription: { _ in AsyncThrowingStream { _ in } },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        do {
            try await client.ensureAssets(Locale(identifier: "xx_XX"))
            Issue.record("Expected error to be thrown")
        } catch {
            #expect(error is SpeechClient.Failure)
        }
    }
    
    // MARK: - Transcription Tests
    
    @Test("startTranscription returns stream of results")
    func startTranscriptionReturnsStream() async throws {
        let expectedResults = [
            TranscriptionResult(
                text: "Hello",
                words: [TimestampedWord(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: nil)],
                isFinal: false
            ),
            TranscriptionResult(
                text: "Hello world",
                words: [
                    TimestampedWord(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: nil),
                    TimestampedWord(text: "world", startTime: 0.5, endTime: 1.0, confidence: nil)
                ],
                isFinal: true
            )
        ]
        
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { _ in true },
            isAssetInstalled: { _ in true },
            ensureAssets: { _ in },
            startTranscription: { _ in
                AsyncThrowingStream { continuation in
                    for result in expectedResults {
                        continuation.yield(result)
                    }
                    continuation.finish()
                }
            },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        let stream = try await client.startTranscription(Locale(identifier: "en_US"))
        var receivedResults: [TranscriptionResult] = []
        
        for try await result in stream {
            receivedResults.append(result)
        }
        
        #expect(receivedResults.count == 2)
        #expect(receivedResults[0].text == "Hello")
        #expect(receivedResults[0].isFinal == false)
        #expect(receivedResults[1].text == "Hello world")
        #expect(receivedResults[1].isFinal == true)
        #expect(receivedResults[1].words.count == 2)
    }
    
    @Test("startTranscription throws for unsupported locale")
    func startTranscriptionThrowsForUnsupportedLocale() async {
        let client = SpeechClient(
            requestAuthorization: { .authorized },
            isAvailable: { _ in false },
            isAssetInstalled: { _ in false },
            ensureAssets: { _ in },
            startTranscription: { _ in throw SpeechClient.Failure.localeNotSupported },
            streamAudio: { _ in },
            finishTranscription: { }
        )
        
        do {
            _ = try await client.startTranscription(Locale(identifier: "xx_XX"))
            Issue.record("Expected error to be thrown")
        } catch {
            #expect(error is SpeechClient.Failure)
        }
    }
    
    // MARK: - TranscriptionResult Tests
    
    @Test("TranscriptionResult stores text and words correctly")
    func transcriptionResultStoresData() {
        let words = [
            TimestampedWord(text: "Hello", startTime: 0.0, endTime: 0.5, confidence: 0.95),
            TimestampedWord(text: "world", startTime: 0.5, endTime: 1.0, confidence: 0.90)
        ]
        
        let result = TranscriptionResult(
            text: "Hello world",
            words: words,
            isFinal: true
        )
        
        #expect(result.text == "Hello world")
        #expect(result.words.count == 2)
        #expect(result.isFinal == true)
        #expect(result.words[0].text == "Hello")
        #expect(result.words[1].text == "world")
    }
    
    @Test("TranscriptionResult with empty words")
    func transcriptionResultEmptyWords() {
        let result = TranscriptionResult(
            text: "",
            words: [],
            isFinal: false
        )
        
        #expect(result.text == "")
        #expect(result.words.isEmpty)
        #expect(result.isFinal == false)
    }
    
    // MARK: - TimestampedWord Tests
    
    @Test("TimestampedWord stores timing correctly")
    func timestampedWordStoresTiming() {
        let word = TimestampedWord(
            text: "Hello",
            startTime: 1.5,
            endTime: 2.0,
            confidence: 0.95
        )
        
        #expect(word.text == "Hello")
        #expect(word.startTime == 1.5)
        #expect(word.endTime == 2.0)
        #expect(word.confidence == 0.95)
    }
    
    @Test("TimestampedWord duration calculation")
    func timestampedWordDuration() {
        let word = TimestampedWord(
            text: "Hello",
            startTime: 1.0,
            endTime: 2.5,
            confidence: nil
        )
        
        let duration = word.endTime - word.startTime
        #expect(duration == 1.5)
    }
    
    @Test("TimestampedWord with nil confidence")
    func timestampedWordNilConfidence() {
        let word = TimestampedWord(
            text: "Hello",
            startTime: 0.0,
            endTime: 0.5,
            confidence: nil
        )
        
        #expect(word.confidence == nil)
    }
    
    // MARK: - Failure Tests
    
    @Test("SpeechClient.Failure cases are distinct")
    func failureCasesDistinct() {
        let localeNotSupported = SpeechClient.Failure.localeNotSupported
        let notAuthorized = SpeechClient.Failure.notAuthorized
        let transcriptionFailed = SpeechClient.Failure.transcriptionFailed("Test error")
        
        #expect(localeNotSupported != notAuthorized)
        #expect(localeNotSupported != transcriptionFailed)
        #expect(notAuthorized != transcriptionFailed)
    }
    
    @Test("SpeechClient.Failure transcriptionFailed stores message")
    func failureTranscriptionFailedMessage() {
        let failure = SpeechClient.Failure.transcriptionFailed("Custom error message")
        
        if case .transcriptionFailed(let message) = failure {
            #expect(message == "Custom error message")
        } else {
            Issue.record("Expected transcriptionFailed case")
        }
    }
}