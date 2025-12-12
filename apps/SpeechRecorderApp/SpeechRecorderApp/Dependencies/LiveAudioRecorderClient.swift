/**
 HOW:
   Automatically used when running the app (not in tests/previews).
   Uses AVAudioEngine to record audio to disk AND stream buffers for transcription.
   
   [Inputs]
   - url: File URL for recording destination
   
   [Outputs]
   - Audio file written to disk
   - AsyncStream of AVAudioPCMBuffer for transcription
   
   [Side Effects]
   - Requests microphone permission via AVAudioApplication
   - Configures AVAudioSession for recording
   - Writes audio to file
   - Streams audio buffers

 WHO:
   AI Agent, Developer
   (Context: Live implementation of AudioRecorderClient)

 WHAT:
   Live implementation of AudioRecorderClient using AVAudioEngine.
   Based on Apple's SwiftTranscriptionSampleApp Recorder.swift pattern.
   Records audio to disk while simultaneously streaming buffers for transcription.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/LiveAudioRecorderClient.swift

 WHY:
   To provide real audio recording functionality in production.
   Uses AVAudioEngine to enable both file recording and buffer streaming
   for live transcription.
 */

@preconcurrency import AVFoundation
import Dependencies
import os.log

private let logger = Logger(subsystem: "com.example.SpeechRecorderApp", category: "AudioRecorder")

// MARK: - Live Implementation

extension AudioRecorderClient: DependencyKey {
    static var liveValue: Self {
        /// Use a class-based recorder (like Apple's sample) to avoid actor isolation issues
        let recorder = Recorder()
        
        return Self(
            currentTime: { recorder.currentTime },
            requestRecordPermission: { await Recorder.requestPermission() },
            startRecording: { url in
                try recorder.start(url: url)
            },
            pauseRecording: {
                recorder.pause()
            },
            resumeRecording: {
                try recorder.resume()
            },
            stopRecording: {
                recorder.stop()
            },
            isPaused: { recorder.isPaused },
            audioLevelStream: { recorder.audioLevelStream }
        )
    }
}

// MARK: - Recorder Class

/**
 Class that manages audio recording using AVAudioEngine.
 
 This implementation follows Apple's SwiftTranscriptionSampleApp pattern:
 1. Uses AVAudioEngine with an input tap to capture audio buffers
 2. Writes buffers to disk via AVAudioFile
 3. Yields buffers to an AsyncStream for transcription
 
 Using a class (not actor) to match Apple's sample and avoid Sendable issues.
 All methods are synchronous except for permission request.
 */
private final class Recorder: @unchecked Sendable {
    private var audioEngine: AVAudioEngine?
    private var audioFile: AVAudioFile?
    private var outputContinuation: AsyncStream<AVAudioPCMBuffer>.Continuation?
    private var levelContinuation: AsyncStream<Float>.Continuation?
    private var recordingStartTime: Date?
    private var pausedTime: Date?
    private var totalPausedDuration: TimeInterval = 0
    private(set) var isPaused: Bool = false
    
    /// Stream of audio levels for waveform visualization
    var audioLevelStream: AsyncStream<Float> {
        AsyncStream { [weak self] continuation in
            self?.levelContinuation = continuation
        }
    }
    
    var currentTime: TimeInterval? {
        guard let startTime = recordingStartTime else {
            return nil
        }
        
        if isPaused, let pauseStart = pausedTime {
            /// When paused, return time up to when we paused
            return pauseStart.timeIntervalSince(startTime) - totalPausedDuration
        }
        
        guard audioEngine?.isRunning == true else {
            return nil
        }
        
        return Date().timeIntervalSince(startTime) - totalPausedDuration
    }
    
    static func requestPermission() async -> Bool {
        await AVAudioApplication.requestRecordPermission()
    }
    
    func pause() {
        guard let audioEngine, audioEngine.isRunning, !isPaused else {
            logger.warning("⚠️ Cannot pause: engine not running or already paused")
            return
        }
        
        logger.info("⏸️ Pausing audio recording...")
        
        /// Record when we paused
        pausedTime = Date()
        isPaused = true
        
        /// Pause the audio engine (keeps the tap installed)
        audioEngine.pause()
        
        logger.info("✅ Audio recording paused")
    }
    
    func resume() throws {
        guard let audioEngine, isPaused else {
            logger.warning("⚠️ Cannot resume: not paused")
            return
        }
        
        logger.info("▶️ Resuming audio recording...")
        
        /// Calculate how long we were paused
        if let pauseStart = pausedTime {
            totalPausedDuration += Date().timeIntervalSince(pauseStart)
        }
        pausedTime = nil
        isPaused = false
        
        /// Resume the audio engine
        try audioEngine.start()
        
        logger.info("✅ Audio recording resumed")
    }
    
    func stop() {
        logger.info("🛑 Stopping audio recording...")
        
        /// Stop the audio engine
        audioEngine?.stop()
        
        /// Remove the tap
        audioEngine?.inputNode.removeTap(onBus: 0)
        
        /// Finish the streams
        outputContinuation?.finish()
        outputContinuation = nil
        levelContinuation?.finish()
        levelContinuation = nil
        
        /// Clean up
        audioFile = nil
        audioEngine = nil
        recordingStartTime = nil
        pausedTime = nil
        totalPausedDuration = 0
        isPaused = false
        
        /// Deactivate audio session
        try? AVAudioSession.sharedInstance().setActive(false)
        
        logger.info("✅ Audio recording stopped")
    }
    
    /// Start recording - this is synchronous to avoid async/lock issues
    func start(url: URL) throws -> AsyncStream<AVAudioPCMBuffer> {
        logger.info("🎙️ Starting audio recording to: \(url.lastPathComponent)")
        
        /// Stop any existing recording
        stop()
        
        /// Set up audio session
        #if os(iOS)
        try setupAudioSession()
        #endif
        
        /// Create audio engine
        audioEngine = AVAudioEngine()
        guard let audioEngine else {
            throw AudioRecorderError.engineNotAvailable
        }
        
        /// Get input format
        let inputNode = audioEngine.inputNode
        let inputFormat = inputNode.outputFormat(forBus: 0)
        logger.info("📊 Input format: \(inputFormat.sampleRate) Hz, \(inputFormat.channelCount) channels")
        
        /// Create audio file for writing
        let fileSettings: [String: Any] = [
            AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
            AVSampleRateKey: inputFormat.sampleRate,
            AVNumberOfChannelsKey: inputFormat.channelCount,
            AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
        ]
        
        audioFile = try AVAudioFile(forWriting: url, settings: fileSettings)
        logger.info("✅ Audio file created for writing")
        
        /// Remove any existing tap
        inputNode.removeTap(onBus: 0)
        
        /// Create the async stream for buffer output
        let stream = AsyncStream<AVAudioPCMBuffer>(bufferingPolicy: .unbounded) { [weak self] continuation in
            self?.outputContinuation = continuation
        }
        
        /// Install tap on input node to capture audio buffers
        /// Following Apple's pattern from Recorder.swift
        inputNode.installTap(
            onBus: 0,
            bufferSize: 4096,
            format: inputFormat
        ) { [weak self] buffer, time in
            guard let self else { return }
            
            /// Write buffer to disk
            if let audioFile = self.audioFile {
                do {
                    try audioFile.write(from: buffer)
                } catch {
                    logger.error("❌ Failed to write buffer to disk: \(error.localizedDescription)")
                }
            }
            
            /// Yield buffer to stream for transcription
            self.outputContinuation?.yield(buffer)
            
            /// Calculate and yield audio level for waveform visualization
            if let channelData = buffer.floatChannelData?[0] {
                let frameLength = Int(buffer.frameLength)
                var sum: Float = 0
                for i in 0..<frameLength {
                    let sample = channelData[i]
                    sum += sample * sample
                }
                let rms = sqrt(sum / Float(frameLength))
                /// Convert to 0-1 range with some scaling for better visualization
                let level = min(1.0, rms * 5.0)
                self.levelContinuation?.yield(level)
            }
        }
        
        /// Prepare and start the engine
        audioEngine.prepare()
        try audioEngine.start()
        recordingStartTime = Date()
        logger.info("✅ Audio engine started successfully")
        
        return stream
    }
    
    #if os(iOS)
    private func setupAudioSession() throws {
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playAndRecord, mode: .spokenAudio)
        try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        logger.info("✅ Audio session configured")
    }
    #endif
}

// MARK: - Errors

enum AudioRecorderError: Error, Equatable {
    case engineNotAvailable
    case permissionDenied
    case recordingFailed
}