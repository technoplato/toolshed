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
    
    /// Check if SpeechTranscriber is available on this device
    /// This is a device capability check, not a locale check
    func isAvailable(for locale: Locale) async -> Bool {
        logger.info("🔍 Checking availability for locale: \(locale.identifier)")
        
        /// First check device capability
        let deviceAvailable = await SpeechTranscriber.isAvailable
        logger.info("📱 Device supports SpeechTranscriber: \(deviceAvailable)")
        
        if !deviceAvailable {
            logger.error("❌ SpeechTranscriber not available on this device")
            return false
        }
        
        /// Check if locale is supported (following Apple's sample pattern)
        let supportedLocales = await SpeechTranscriber.supportedLocales
        logger.info("📋 Supported locales: \(supportedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        /// Use the locale's BCP47 identifier for comparison (Apple's pattern)
        let localeId = locale.identifier(.bcp47)
        let isSupported = supportedLocales.map { $0.identifier(.bcp47) }.contains(localeId)
        logger.info("🔍 Locale \(localeId) is supported: \(isSupported)")
        
        return isSupported
    }
    
    /// Check if assets are installed for a locale
    /// Following Apple's sample pattern from Transcription.swift
    func isAssetInstalled(for locale: Locale) async -> Bool {
        logger.info("🔍 Checking if asset is installed for locale: \(locale.identifier)")
        
        let installedLocales = await SpeechTranscriber.installedLocales
        logger.info("📋 Installed locales: \(installedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        /// Use the locale's BCP47 identifier for comparison (Apple's pattern)
        let localeId = locale.identifier(.bcp47)
        let isInstalled = installedLocales.map { $0.identifier(.bcp47) }.contains(localeId)
        logger.info("🔍 Asset for \(localeId) is installed: \(isInstalled)")
        
        return isInstalled
    }
    
    // MARK: - Asset Management
    
    /// Ensures assets are installed for the given locale.
    /// This follows the pattern from Apple's sample code (Transcription.swift):
    /// 1. Check if locale is supported
    /// 2. Check if already installed
    /// 3. Create a transcriber and download if needed
    func ensureAssets(for locale: Locale) async throws {
        logger.info("🚀 ensureAssets called for locale: \(locale.identifier)")
        
        /// Step 1: Check if locale is supported (Apple's pattern)
        let supportedLocales = await SpeechTranscriber.supportedLocales
        let localeId = locale.identifier(.bcp47)
        let isSupported = supportedLocales.map { $0.identifier(.bcp47) }.contains(localeId)
        
        logger.info("📋 Supported locales: \(supportedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        logger.info("🔍 Locale \(localeId) is supported: \(isSupported)")
        
        guard isSupported else {
            logger.error("❌ Locale not supported: \(localeId)")
            throw SpeechClient.Failure.localeNotSupported
        }
        
        /// Step 2: Check if already installed (Apple's pattern)
        let installedLocales = await SpeechTranscriber.installedLocales
        let isInstalled = installedLocales.map { $0.identifier(.bcp47) }.contains(localeId)
        
        logger.info("📋 Installed locales: \(installedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        logger.info("🔍 Asset for \(localeId) is installed: \(isInstalled)")
        
        if isInstalled {
            logger.info("✅ Asset already installed, no download needed")
            return
        }
        
        /// Step 3: Create transcriber and download (Apple's pattern)
        /// Note: Apple's sample uses Locale.current directly, not supportedLocale(equivalentTo:)
        logger.info("📝 Creating transcriber for download...")
        let tempTranscriber = SpeechTranscriber(
            locale: locale,  /// Use the original locale, not a mapped one
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )
        logger.info("✅ Transcriber created for locale: \(locale.identifier)")
        
        /// Download if needed
        logger.info("📥 Checking if asset download is needed...")
        do {
            if let request = try await AssetInventory.assetInstallationRequest(supporting: [tempTranscriber]) {
                logger.info("📥 Asset download required, starting download...")
                logger.info("📊 Download progress: \(request.progress.fractionCompleted * 100)%")
                try await request.downloadAndInstall()
                logger.info("✅ Asset download and installation complete!")
            } else {
                logger.info("ℹ️ No asset installation request returned - asset may already be available")
            }
        } catch {
            logger.error("❌ Asset download failed: \(error.localizedDescription)")
            logger.error("❌ Full error: \(String(describing: error))")
            throw SpeechClient.Failure.assetInstallationFailed
        }
    }
    
    // MARK: - Transcription
    
    /// Start transcription for a locale
    /// Following Apple's sample pattern from Transcription.swift
    func startTranscription(locale: Locale) async throws -> AsyncThrowingStream<TranscriptionResult, Error> {
        logger.info("🎙️ startTranscription called for locale: \(locale.identifier)")
        
        /// Step 1: Check device capability
        let deviceAvailable = await SpeechTranscriber.isAvailable
        logger.info("📱 Device supports SpeechTranscriber: \(deviceAvailable)")
        
        guard deviceAvailable else {
            logger.error("❌ SpeechTranscriber not available on this device")
            throw SpeechClient.Failure.notAvailable
        }
        
        /// Step 2: Create the transcriber with word-level timing
        /// Note: Apple's sample uses Locale.current directly
        logger.info("📝 Creating transcriber with word-level timing for locale: \(locale.identifier)")
        transcriber = SpeechTranscriber(
            locale: locale,  /// Use the original locale directly (Apple's pattern)
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )
        
        guard let transcriber else {
            logger.error("❌ Failed to create transcriber")
            throw SpeechClient.Failure.transcriptionFailed("Failed to create transcriber")
        }
        logger.info("✅ Transcriber created successfully")
        
        /// Step 3: Create the analyzer
        logger.info("🔧 Creating SpeechAnalyzer...")
        analyzer = SpeechAnalyzer(modules: [transcriber])
        logger.info("✅ SpeechAnalyzer created")
        
        /// Step 4: Ensure model is available (Apple's ensureModel pattern)
        logger.info("🔍 Ensuring model is available...")
        try await ensureModel(transcriber: transcriber, locale: locale)
        
        /// Step 5: Get the best audio format for the transcriber
        logger.info("🎵 Getting best audio format...")
        analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber])
        if let format = analyzerFormat {
            logger.info("✅ Audio format: \(format.sampleRate) Hz, \(format.channelCount) channels")
        } else {
            logger.warning("⚠️ No audio format returned")
        }
        
        /// Step 6: Create buffer converter
        logger.info("🔄 Creating buffer converter...")
        converter = BufferConverter()
        logger.info("✅ Buffer converter created")
        
        /// Step 7: Create the input stream
        logger.info("📡 Creating input stream...")
        let (inputSequence, inputBuilder) = AsyncStream<AnalyzerInput>.makeStream()
        self.inputBuilder = inputBuilder
        logger.info("✅ Input stream created")
        
        /// Step 8: Start the analyzer in the background
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
        
        /// Step 9: Return stream of transcription results
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
    
    /// Ensure model is available for transcription
    /// This follows Apple's ensureModel pattern from Transcription.swift
    private func ensureModel(transcriber: SpeechTranscriber, locale: Locale) async throws {
        logger.info("🔍 ensureModel called for locale: \(locale.identifier)")
        
        /// Check if locale is supported
        let supportedLocales = await SpeechTranscriber.supportedLocales
        let localeId = locale.identifier(.bcp47)
        let isSupported = supportedLocales.map { $0.identifier(.bcp47) }.contains(localeId)
        
        logger.info("📋 Supported locales: \(supportedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        guard isSupported else {
            logger.error("❌ Locale not supported: \(localeId)")
            throw SpeechClient.Failure.localeNotSupported
        }
        logger.info("✅ Locale \(localeId) is supported")
        
        /// Check if already installed
        let installedLocales = await SpeechTranscriber.installedLocales
        let isInstalled = installedLocales.map { $0.identifier(.bcp47) }.contains(localeId)
        
        logger.info("📋 Installed locales: \(installedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        if isInstalled {
            logger.info("✅ Asset for \(localeId) is already installed")
            return
        }
        
        logger.info("📥 Asset not installed, downloading...")
        
        /// Download if needed (Apple's downloadIfNeeded pattern)
        do {
            if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
                logger.info("📥 Starting asset download...")
                logger.info("📊 Download progress: \(request.progress.fractionCompleted * 100)%")
                try await request.downloadAndInstall()
                logger.info("✅ Asset downloaded and installed successfully")
            } else {
                logger.info("ℹ️ No installation request returned - asset may already be available")
            }
        } catch {
            logger.error("❌ Asset download failed: \(error.localizedDescription)")
            logger.error("❌ Full error: \(String(describing: error))")
            throw SpeechClient.Failure.assetInstallationFailed
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