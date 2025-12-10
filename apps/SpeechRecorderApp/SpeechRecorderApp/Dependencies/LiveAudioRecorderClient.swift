/**
 HOW:
   Automatically used when running the app (not in tests/previews).
   Uses AVAudioRecorder to record audio to disk.
   
   [Inputs]
   - url: File URL for recording destination
   
   [Outputs]
   - Audio file written to disk
   
   [Side Effects]
   - Requests microphone permission via AVAudioApplication
   - Configures AVAudioSession for recording
   - Writes audio to file

 WHO:
   AI Agent, Developer
   (Context: Live implementation of AudioRecorderClient)

 WHAT:
   Live implementation of AudioRecorderClient using AVAudioRecorder.
   Based on TCA VoiceMemos example pattern.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/LiveAudioRecorderClient.swift

 WHY:
   To provide real audio recording functionality in production.
   Uses AVAudioRecorder for simplicity and compatibility with Swift 6 concurrency.
 */

import AVFoundation
import Dependencies

// MARK: - Live Implementation

extension AudioRecorderClient: DependencyKey {
    static var liveValue: Self {
        let audioRecorder = AudioRecorder()
        return Self(
            currentTime: { await audioRecorder.currentTime },
            requestRecordPermission: { await AudioRecorder.requestPermission() },
            startRecording: { url in try await audioRecorder.start(url: url) },
            stopRecording: { await audioRecorder.stop() }
        )
    }
}

// MARK: - AudioRecorder Actor

private actor AudioRecorder {
    var delegate: Delegate?
    var recorder: AVAudioRecorder?
    
    var currentTime: TimeInterval? {
        guard let recorder, recorder.isRecording else { return nil }
        return recorder.currentTime
    }
    
    static func requestPermission() async -> Bool {
        await AVAudioApplication.requestRecordPermission()
    }
    
    func stop() {
        recorder?.stop()
        try? AVAudioSession.sharedInstance().setActive(false)
    }
    
    func start(url: URL) async throws {
        stop()
        
        let stream = AsyncThrowingStream<Bool, any Error> { continuation in
            do {
                self.delegate = Delegate(
                    didFinishRecording: { flag in
                        continuation.yield(flag)
                        continuation.finish()
                        try? AVAudioSession.sharedInstance().setActive(false)
                    },
                    encodeErrorDidOccur: { error in
                        continuation.finish(throwing: error)
                        try? AVAudioSession.sharedInstance().setActive(false)
                    }
                )
                
                let recorder = try AVAudioRecorder(
                    url: url,
                    settings: [
                        AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
                        AVSampleRateKey: 44100,
                        AVNumberOfChannelsKey: 1,
                        AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue,
                    ]
                )
                self.recorder = recorder
                recorder.delegate = self.delegate
                
                continuation.onTermination = { [recorder = UncheckedSendable(recorder)] _ in
                    recorder.wrappedValue.stop()
                }
                
                try AVAudioSession.sharedInstance().setCategory(
                    .playAndRecord, mode: .default, options: .defaultToSpeaker
                )
                try AVAudioSession.sharedInstance().setActive(true)
                self.recorder?.record()
            } catch {
                continuation.finish(throwing: error)
            }
        }
        
        for try await _ in stream {
            return
        }
        throw CancellationError()
    }
}

// MARK: - Delegate

private final class Delegate: NSObject, AVAudioRecorderDelegate, Sendable {
    let didFinishRecording: @Sendable (Bool) -> Void
    let encodeErrorDidOccur: @Sendable ((any Error)?) -> Void
    
    init(
        didFinishRecording: @escaping @Sendable (Bool) -> Void,
        encodeErrorDidOccur: @escaping @Sendable ((any Error)?) -> Void
    ) {
        self.didFinishRecording = didFinishRecording
        self.encodeErrorDidOccur = encodeErrorDidOccur
    }
    
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        didFinishRecording(flag)
    }
    
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: (any Error)?) {
        encodeErrorDidOccur(error)
    }
}

// MARK: - Errors

enum AudioRecorderError: Error, Equatable {
    case engineNotAvailable
    case permissionDenied
    case recordingFailed
}