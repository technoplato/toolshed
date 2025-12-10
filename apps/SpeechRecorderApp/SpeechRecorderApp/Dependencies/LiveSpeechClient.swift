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
    
    /// Check if SpeechTranscriber is available on this device and locale is supported
    /// Following Apple's official documentation pattern
    /// NOTE: SpeechTranscriber is NOT available on iOS Simulator - only on real devices
    func isAvailable(for locale: Locale) async -> Bool {
        logger.info("🔍 Checking availability for locale: \(locale.identifier)")
        
        /// First check device capability
        /// IMPORTANT: SpeechTranscriber.isAvailable returns false on iOS Simulator
        /// The new SpeechAnalyzer API (iOS 26.0+) only works on real devices
        let deviceAvailable = await SpeechTranscriber.isAvailable
        logger.info("📱 Device supports SpeechTranscriber: \(deviceAvailable)")
        
        #if targetEnvironment(simulator)
        if !deviceAvailable {
            logger.warning("⚠️ SpeechTranscriber is NOT available on iOS Simulator. Please test on a real device.")
            return false
        }
        #else
        if !deviceAvailable {
            logger.error("❌ SpeechTranscriber not available on this device")
            return false
        }
        #endif
        
        /// Check if locale is supported using supportedLocale(equivalentTo:)
        /// This is the official Apple documentation pattern
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            logger.warning("❌ No supported locale found equivalent to: \(locale.identifier)")
            return false
        }
        
        logger.info("✅ Found supported locale: \(supportedLocale.identifier(.bcp47)) for input: \(locale.identifier)")
        return true
    }
    
    /// Check if assets are installed for a locale
    /// Following Apple's official documentation pattern
    func isAssetInstalled(for locale: Locale) async -> Bool {
        logger.info("🔍 Checking if asset is installed for locale: \(locale.identifier)")
        
        /// First get the supported locale equivalent
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            logger.warning("❌ No supported locale found equivalent to: \(locale.identifier)")
            return false
        }
        
        let installedLocales = await SpeechTranscriber.installedLocales
        logger.info("📋 Installed locales: \(installedLocales.map { $0.identifier(.bcp47) }.joined(separator: ", "))")
        
        /// Check if the supported locale is installed
        let supportedLocaleId = supportedLocale.identifier(.bcp47)
        let isInstalled = installedLocales.map { $0.identifier(.bcp47) }.contains(supportedLocaleId)
        logger.info("🔍 Asset for \(supportedLocaleId) is installed: \(isInstalled)")
        
        return isInstalled
    }
    
    // MARK: - Asset Management
    
    /// Ensures assets are installed for the given locale.
    /// This follows the OFFICIAL Apple documentation pattern:
    /// 1. Get supported locale using supportedLocale(equivalentTo:)
    /// 2. Create transcriber with that locale
    /// 3. Download assets if needed via AssetInventory
    func ensureAssets(for locale: Locale) async throws {
        logger.info("🚀 ensureAssets called for locale: \(locale.identifier)")
        
        /// Step 1: Get supported locale (OFFICIAL Apple documentation pattern)
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            logger.error("❌ No supported locale found equivalent to: \(locale.identifier)")
            throw SpeechClient.Failure.localeNotSupported
        }
        logger.info("✅ Found supported locale: \(supportedLocale.identifier(.bcp47))")
        
        /// Step 2: Create transcriber with the supported locale (OFFICIAL pattern)
        logger.info("📝 Creating transcriber with supported locale...")
        let tempTranscriber = SpeechTranscriber(
            locale: supportedLocale,  /// Use the SUPPORTED locale from supportedLocale(equivalentTo:)
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )
        logger.info("✅ Transcriber created for locale: \(supportedLocale.identifier(.bcp47))")
        
        /// Step 3: Download assets if needed (OFFICIAL pattern)
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
    /// Following the OFFICIAL Apple documentation pattern from SpeechAnalyzer docs
    func startTranscription(locale: Locale) async throws -> AsyncThrowingStream<TranscriptionResult, Error> {
        logger.info("🎙️ startTranscription called for locale: \(locale.identifier)")
        
        /// Step 1: Check device capability
        /// IMPORTANT: SpeechTranscriber.isAvailable returns false on iOS Simulator
        /// The new SpeechAnalyzer API (iOS 26.0+) only works on real devices
        let deviceAvailable = await SpeechTranscriber.isAvailable
        logger.info("📱 Device supports SpeechTranscriber: \(deviceAvailable)")
        
        guard deviceAvailable else {
            #if targetEnvironment(simulator)
            logger.error("❌ SpeechTranscriber is NOT available on iOS Simulator. Please test on a real device.")
            throw SpeechClient.Failure.transcriptionFailed("SpeechTranscriber is not available on iOS Simulator. Please test on a real device.")
            #else
            logger.error("❌ SpeechTranscriber not available on this device")
            throw SpeechClient.Failure.notAvailable
            #endif
        }
        
        /// Step 2: Get supported locale (OFFICIAL Apple documentation pattern)
        /// From docs: "guard let locale = SpeechTranscriber.supportedLocale(equivalentTo: Locale.current)"
        guard let supportedLocale = await SpeechTranscriber.supportedLocale(equivalentTo: locale) else {
            logger.error("❌ No supported locale found equivalent to: \(locale.identifier)")
            throw SpeechClient.Failure.localeNotSupported
        }
        logger.info("✅ Found supported locale: \(supportedLocale.identifier(.bcp47)) for input: \(locale.identifier)")
        
        /// Step 3: Create the transcriber with the SUPPORTED locale (OFFICIAL pattern)
        /// From docs: "let transcriber = SpeechTranscriber(locale: locale, preset: .offlineTranscription)"
        logger.info("📝 Creating transcriber with supported locale: \(supportedLocale.identifier(.bcp47))")
        transcriber = SpeechTranscriber(
            locale: supportedLocale,  /// Use the SUPPORTED locale from supportedLocale(equivalentTo:)
            transcriptionOptions: [],
            reportingOptions: [.volatileResults],
            attributeOptions: [.audioTimeRange]
        )
        
        guard let transcriber else {
            logger.error("❌ Failed to create transcriber")
            throw SpeechClient.Failure.transcriptionFailed("Failed to create transcriber")
        }
        logger.info("✅ Transcriber created successfully")
        
        /// Step 4: Download assets if needed (OFFICIAL pattern)
        /// From docs: "if let installationRequest = try await AssetInventory.assetInstallationRequest(supporting: [transcriber])"
        logger.info("📥 Checking if asset download is needed...")
        do {
            if let request = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
                logger.info("📥 Asset download required, starting download...")
                logger.info("📊 Download progress: \(request.progress.fractionCompleted * 100)%")
                try await request.downloadAndInstall()
                logger.info("✅ Asset downloaded and installed successfully")
            } else {
                logger.info("ℹ️ No asset installation request returned - asset already available")
            }
        } catch {
            logger.error("❌ Asset download failed: \(error.localizedDescription)")
            logger.error("❌ Full error: \(String(describing: error))")
            throw SpeechClient.Failure.assetInstallationFailed
        }
        
        /// Step 5: Get the best audio format for the transcriber
        logger.info("🎵 Getting best audio format...")
        analyzerFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber])
        if let format = analyzerFormat {
            logger.info("✅ Audio format: \(format.sampleRate) Hz, \(format.channelCount) channels")
        } else {
            logger.warning("⚠️ No audio format returned")
        }
        
        /// Step 6: Create the analyzer
        logger.info("🔧 Creating SpeechAnalyzer...")
        analyzer = SpeechAnalyzer(modules: [transcriber])
        logger.info("✅ SpeechAnalyzer created")
        
        /// Step 7: Create buffer converter
        logger.info("🔄 Creating buffer converter...")
        converter = BufferConverter()
        logger.info("✅ Buffer converter created")
        
        /// Step 8: Create the input stream
        logger.info("📡 Creating input stream...")
        let (inputSequence, inputBuilder) = AsyncStream<AnalyzerInput>.makeStream()
        self.inputBuilder = inputBuilder
        logger.info("✅ Input stream created")
        
        /// Step 9: Start the analyzer in the background
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
        
        /// Step 10: Return stream of transcription results
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