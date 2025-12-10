/**
 HOW:
   This file provides the live implementation of SpeechClient.
   It uses iOS 26.0+ SpeechAnalyzer API for real-time transcription.
   
   [Inputs]
   - Locale for speech recognition
   - Audio buffers from AVAudioEngine
   
   [Outputs]
   - AsyncThrowingStream of TranscriptionResult
   
   [Side Effects]
   - Downloads speech recognition assets if needed
   - Uses microphone for audio input

 WHO:
   AI Agent, Developer
   (Context: Live implementation of SpeechClient for Phase 2)

 WHAT:
   Live implementation of SpeechClient using SpeechAnalyzer.
   Handles asset installation, audio streaming, and word extraction.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/LiveSpeechClient.swift

 WHY:
   To provide real speech recognition functionality in production.
   Follows patterns from Apple's speech-to-text sample code.
 */

@preconcurrency import AVFoundation
import ComposableArchitecture
import Foundation
import Speech

// MARK: - Live Speech Client

extension SpeechClient: DependencyKey {
    static var liveValue: Self {
        let speech = Speech()
        
        return Self(
            requestAuthorization: {
                await withCheckedContinuation { continuation in
                    SFSpeechRecognizer.requestAuthorization { status in
                        let authStatus: AuthorizationStatus
                        switch status {
                        case .notDetermined:
                            authStatus = .notDetermined
                        case .denied:
                            authStatus = .denied
                        case .restricted:
                            authStatus = .restricted
                        case .authorized:
                            authStatus = .authorized
                        @unknown default:
                            authStatus = .notDetermined
                        }
                        continuation.resume(returning: authStatus)
                    }
                }
            },
            isAvailable: { locale in
                await speech.isAvailable(for: locale)
            },
            isAssetInstalled: { locale in
                await speech.isAssetInstalled(for: locale)
            },
            ensureAssets: { locale in
                try await speech.ensureAssets(for: locale)
            },
            startTranscription: { locale in
                try await speech.startTranscription(locale: locale)
            },
            streamAudio: { buffer in
                /// Use nonisolated(unsafe) to bypass Sendable check for AVAudioPCMBuffer
                /// This is safe because we're immediately consuming the buffer in the actor
                nonisolated(unsafe) let unsafeBuffer = buffer
                await speech.streamAudio(unsafeBuffer)
            },
            finishTranscription: {
                try await speech.finishTranscription()
            }
        )
    }
}

// MARK: - Speech Actor

/// Actor that manages speech recognition state
private actor Speech {
    private var transcriber: SpeechTranscriber?
    private var analyzer: SpeechAnalyzer?
    private var inputBuilder: AsyncStream<AnalyzerInput>.Continuation?
    private var analyzerFormat: AVAudioFormat?
    private var converter: BufferConverter?
    private var recognizerTask: Task<Void, Error>?
    
    // MARK: - Availability
    
    func isAvailable(for locale: Locale) async -> Bool {
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            return false
        }
        let supportedLocales = await SpeechTranscriber.supportedLocales
        return supportedLocales.contains { $0.identifier(.bcp47) == supportedLocale.identifier(.bcp47) }
    }
    
    func isAssetInstalled(for locale: Locale) async -> Bool {
        let installedLocales = await SpeechTranscriber.installedLocales
        return installedLocales.contains { $0.identifier(.bcp47) == locale.identifier(.bcp47) }
    }
    
    // MARK: - Asset Management
    
    func ensureAssets(for locale: Locale) async throws {
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            throw SpeechClient.Failure.localeNotSupported
        }
        
        /// Create a temporary transcriber to check asset requirements
        let tempTranscriber = SpeechTranscriber(
            locale: supportedLocale,
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )
        
        /// Check if we need to download assets
        if let request = try await AssetInventory.assetInstallationRequest(supporting: [tempTranscriber]) {
            try await request.downloadAndInstall()
        }
    }
    
    // MARK: - Transcription
    
    func startTranscription(locale: Locale) async throws -> AsyncThrowingStream<TranscriptionResult, Error> {
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            throw SpeechClient.Failure.localeNotSupported
        }
        
        /// Create the transcriber with word-level timing
        transcriber = SpeechTranscriber(
            locale: supportedLocale,
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )
        
        guard let transcriber else {
            throw SpeechClient.Failure.transcriptionFailed("Failed to create transcriber")
        }
        
        /// Create the analyzer
        analyzer = SpeechAnalyzer(modules: [transcriber])
        
        /// Get the best audio format for the transcriber
        analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber])
        
        /// Create buffer converter
        converter = BufferConverter()
        
        /// Create the input stream
        let (inputSequence, inputBuilder) = AsyncStream<AnalyzerInput>.makeStream()
        self.inputBuilder = inputBuilder
        
        /// Start the analyzer in the background
        let analyzerRef = analyzer
        Task {
            do {
                try await analyzerRef?.start(inputSequence: inputSequence)
            } catch {
                print("Analyzer failed to start: \(error)")
            }
        }
        
        /// Return stream of transcription results
        return AsyncThrowingStream { continuation in
            self.recognizerTask = Task {
                do {
                    for try await result in transcriber.results {
                        let transcriptionResult = TranscriptionResult(
                            text: String(result.text.characters),
                            words: self.extractWords(from: result),
                            isFinal: result.isFinal
                        )
                        continuation.yield(transcriptionResult)
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }
    
    func streamAudio(_ buffer: AVAudioPCMBuffer) {
        guard let analyzerFormat, let converter, let inputBuilder else { return }
        
        do {
            let converted = try converter.convertBuffer(buffer, to: analyzerFormat)
            let input = AnalyzerInput(buffer: converted)
            inputBuilder.yield(input)
        } catch {
            print("Buffer conversion failed: \(error)")
        }
    }
    
    func finishTranscription() async throws {
        inputBuilder?.finish()
        try await analyzer?.finalizeAndFinishThroughEndOfInput()
        recognizerTask?.cancel()
        
        /// Clean up
        transcriber = nil
        analyzer = nil
        inputBuilder = nil
        analyzerFormat = nil
        converter = nil
        recognizerTask = nil
    }
    
    // MARK: - Word Extraction
    
    /// Extract word-level timing from the transcription result
    private func extractWords(from result: SpeechTranscriber.Result) -> [TimestampedWord] {
        var words: [TimestampedWord] = []
        let text = result.text
        
        /// Iterate through runs in the AttributedString
        for run in text.runs {
            /// Check if this run has timing information
            if let timeRange = run.audioTimeRange {
                let wordText = String(text[run.range].characters).trimmingCharacters(in: .whitespaces)
                
                /// Skip empty strings
                guard !wordText.isEmpty else { continue }
                
                words.append(TimestampedWord(
                    text: wordText,
                    startTime: timeRange.start.seconds,
                    endTime: timeRange.end.seconds,
                    confidence: nil  /// Confidence not available in new API
                ))
            }
        }
        
        return words
    }
}

// MARK: - CMTime Extension

extension CMTime {
    /// Convert CMTime to seconds
    var seconds: TimeInterval {
        CMTimeGetSeconds(self)
    }
}