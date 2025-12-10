/**
 HOW:
   Use via @Dependency(\.audioRecorder) in TCA reducers.
   
   ```swift
   @Dependency(\.audioRecorder) var audioRecorder
   
   // Request permission
   let hasPermission = await audioRecorder.requestRecordPermission()
   
   // Start recording
   try await audioRecorder.startRecording(url: recordingURL)
   
   // Get current time
   let time = await audioRecorder.currentTime()
   
   // Stop recording
   await audioRecorder.stopRecording()
   ```
   
   [Inputs]
   - url: File URL for recording destination
   
   [Outputs]
   - Permission status, current recording time
   
   [Side Effects]
   - Requests microphone permission
   - Writes audio to file system

 WHO:
   AI Agent, Developer
   (Context: TDD for AudioRecorderClient dependency)

 WHAT:
   Dependency client for audio recording functionality.
   Wraps AVAudioEngine for recording audio to disk.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/AudioRecorderClient.swift

 WHY:
   To provide a testable interface for audio recording.
   Following TCA patterns, this allows mocking in tests while
   providing real implementation in production.
 */

import AVFoundation
import ComposableArchitecture
import Foundation

/// Dependency client for audio recording
@DependencyClient
struct AudioRecorderClient: Sendable {
    /// Get the current recording time, or nil if not recording
    var currentTime: @Sendable () async -> TimeInterval? = { nil }
    
    /// Request permission to record audio
    var requestRecordPermission: @Sendable () async -> Bool = { false }
    
    /// Start recording audio to the specified URL
    /// Returns a stream of audio buffers for transcription
    var startRecording: @Sendable (_ url: URL) async throws -> AsyncStream<AVAudioPCMBuffer>
    
    /// Stop the current recording
    var stopRecording: @Sendable () async -> Void
}

// MARK: - Test Dependency Key

extension AudioRecorderClient: TestDependencyKey {
    /// Preview implementation that simulates recording
    static var previewValue: Self {
        let isRecording = LockIsolated(false)
        let currentTime = LockIsolated(0.0)
        
        return Self(
            currentTime: { currentTime.value },
            requestRecordPermission: { true },
            startRecording: { _ in
                isRecording.setValue(true)
                /// Return an empty stream for preview
                return AsyncStream { continuation in
                    Task {
                        while isRecording.value {
                            try? await Task.sleep(for: .seconds(1))
                            currentTime.withValue { $0 += 1 }
                        }
                        continuation.finish()
                    }
                }
            },
            stopRecording: {
                isRecording.setValue(false)
                currentTime.setValue(0)
            }
        )
    }
    
    /// Test implementation with unimplemented closures
    static let testValue = Self()
}

// MARK: - Dependency Values Extension

extension DependencyValues {
    /// Access the audio recorder client
    var audioRecorder: AudioRecorderClient {
        get { self[AudioRecorderClient.self] }
        set { self[AudioRecorderClient.self] = newValue }
    }
}