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
import os.log
import Speech

// MARK: - Logging

private let logger = Logger(subsystem: "com.example.SpeechRecorderApp", category: "SpeechClient")

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
        logger.info("🔍 Checking availability for locale: \(locale.identifier)")
        
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            logger.warning("❌ No supported locale found equivalent to: \(locale.identifier)")
            return false
        }
        
        logger.info("✅ Found supported locale: \(supportedLocale.identifier(.bcp47))")
        
        let supportedLocales = await SpeechTranscriber.supportedLocales
        logger.info("📋 All supported locales: \(supportedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        let isSupported = supportedLocales.contains { $0.identifier(.bcp47) == supportedLocale.identifier(.bcp47) }
        logger.info("🔍 Locale \(supportedLocale.identifier(.bcp47)) is supported: \(isSupported)")
        
        return isSupported
    }
    
    func isAssetInstalled(for locale: Locale) async -> Bool {
        logger.info("🔍 Checking if asset is installed for locale: \(locale.identifier)")
        
        /// First check if locale is supported
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            logger.warning("❌ Locale not supported, cannot check asset installation: \(locale.identifier)")
            return false
        }
        
        logger.info("✅ Supported locale for asset check: \(supportedLocale.identifier(.bcp47))")
        
        let installedLocales = await SpeechTranscriber.installedLocales
        logger.info("📋 Installed locales: \(installedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        /// Check using the supported locale identifier
        let isInstalled = installedLocales.contains { $0.identifier(.bcp47) == supportedLocale.identifier(.bcp47) }
        logger.info("🔍 Asset for \(supportedLocale.identifier(.bcp47)) is installed: \(isInstalled)")
        
        return isInstalled
    }
    
    // MARK: - Asset Management
    
    /// Ensures assets are installed for the given locale.
    /// This follows the pattern from Apple's sample code:
    /// 1. Create a transcriber (which subscribes to the asset)
    /// 2. Check if download is needed via AssetInventory
    /// 3. Download and install if needed
    func ensureAssets(for locale: Locale) async throws {
        logger.info("🚀 ensureAssets called for locale: \(locale.identifier)")
        
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            logger.error("❌ Locale not supported: \(locale.identifier)")
            throw SpeechClient.Failure.localeNotSupported
        }
        
        logger.info("✅ Supported locale found: \(supportedLocale.identifier(.bcp47))")
        
        /// Create a transcriber - this subscribes to the transcription asset
        /// The transcriber must exist when checking asset status
        logger.info("📝 Creating temporary transcriber to subscribe to asset...")
        let tempTranscriber = SpeechTranscriber(
            locale: supportedLocale,
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )
        logger.info("✅ Temporary transcriber created")
        
        /// Check if assets are already installed for this locale
        let installedLocales = await SpeechTranscriber.installedLocales
        logger.info("📋 Currently installed locales: \(installedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        let isInstalled = installedLocales.contains { $0.identifier(.bcp47) == supportedLocale.identifier(.bcp47) }
        logger.info("🔍 Asset already installed: \(isInstalled)")
        
        if isInstalled {
            logger.info("✅ Asset already installed, no download needed")
            return
        }
        
        /// Check if we need to download assets
        /// This requires the transcriber to be subscribed to the asset
        logger.info("📥 Checking if asset download is needed...")
        do {
            if let request = try await AssetInventory.assetInstallationRequest(supporting: [tempTranscriber]) {
                logger.info("📥 Asset download required, starting download...")
                logger.info("📊 Download progress will be tracked...")
                try await request.downloadAndInstall()
                logger.info("✅ Asset download and installation complete!")
            } else {
                logger.info("ℹ️ No asset installation request returned - asset may already be available")
            }
        } catch {
            logger.error("❌ Asset download failed: \(error.localizedDescription)")
            logger.error("❌ Full error: \(String(describing: error))")
            throw error
        }
    }
    
    // MARK: - Transcription
    
    func startTranscription(locale: Locale) async throws -> AsyncThrowingStream<TranscriptionResult, Error> {
        logger.info("🎙️ startTranscription called for locale: \(locale.identifier)")
        
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            logger.error("❌ Locale not supported for transcription: \(locale.identifier)")
            throw SpeechClient.Failure.localeNotSupported
        }
        
        logger.info("✅ Using supported locale: \(supportedLocale.identifier(.bcp47))")
        
        /// Create the transcriber with word-level timing
        logger.info("📝 Creating transcriber with word-level timing...")
        transcriber = SpeechTranscriber(
            locale: supportedLocale,
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )
        
        guard let transcriber else {
            logger.error("❌ Failed to create transcriber")
            throw SpeechClient.Failure.transcriptionFailed("Failed to create transcriber")
        }
        logger.info("✅ Transcriber created successfully")
        
        /// Ensure assets are installed before starting
        /// This is critical - we must check/download assets with the transcriber that will be used
        logger.info("🔍 Checking if assets are installed...")
        let installedLocales = await SpeechTranscriber.installedLocales
        logger.info("📋 Installed locales: \(installedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        let isInstalled = installedLocales.contains { $0.identifier(.bcp47) == supportedLocale.identifier(.bcp47) }
        logger.info("🔍 Asset installed: \(isInstalled)")
        
        if !isInstalled {
            logger.info("📥 Asset not installed, attempting download...")
            do {
                if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
                    logger.info("📥 Starting asset download...")
                    try await request.downloadAndInstall()
                    logger.info("✅ Asset downloaded and installed successfully")
                } else {
                    logger.warning("⚠️ No installation request returned but asset not in installed list")
                }
            } catch {
                logger.error("❌ Asset download failed: \(error.localizedDescription)")
                logger.error("❌ Full error: \(String(describing: error))")
                throw SpeechClient.Failure.assetInstallationFailed
            }
        }
        
        /// Create the analyzer
        logger.info("🔧 Creating SpeechAnalyzer...")
        analyzer = SpeechAnalyzer(modules: [transcriber])
        logger.info("✅ SpeechAnalyzer created")
        
        /// Get the best audio format for the transcriber
        logger.info("🎵 Getting best audio format...")
        analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber])
        if let format = analyzerFormat {
            logger.info("✅ Audio format: \(format.sampleRate) Hz, \(format.channelCount) channels")
        } else {
            logger.warning("⚠️ No audio format returned")
        }
        
        /// Create buffer converter
        logger.info("🔄 Creating buffer converter...")
        converter = BufferConverter()
        logger.info("✅ Buffer converter created")
        
        /// Create the input stream
        logger.info("📡 Creating input stream...")
        let (inputSequence, inputBuilder) = AsyncStream<AnalyzerInput>.makeStream()
        self.inputBuilder = inputBuilder
        logger.info("✅ Input stream created")
        
        /// Start the analyzer in the background
        logger.info("▶️ Starting analyzer...")
        let analyzerRef = analyzer
        Task {
            do {
                try await analyzerRef?.start(inputSequence: inputSequence)
                logger.info("✅ Analyzer started successfully")
            } catch {
                logger.error("❌ Analyzer failed to start: \(error.localizedDescription)")
                logger.error("❌ Full error: \(String(describing: error))")
            }
        }
        
        /// Return stream of transcription results
        logger.info("🎤 Returning transcription result stream...")
        return AsyncThrowingStream { continuation in
            self.recognizerTask = Task {
                do {
                    logger.info("👂 Listening for transcription results...")
                    for try await result in transcriber.results {
                        let transcriptionResult = TranscriptionResult(
                            text: String(result.text.characters),
                            words: self.extractWords(from: result),
                            isFinal: result.isFinal
                        )
                        logger.info("📝 Received result: '\(transcriptionResult.text)' (final: \(transcriptionResult.isFinal))")
                        continuation.yield(transcriptionResult)
                    }
                    logger.info("✅ Transcription stream completed normally")
                    continuation.finish()
                } catch {
                    logger.error("❌ Transcription error: \(error.localizedDescription)")
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