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
    
    /// Pause the current recording
    var pauseRecording: @Sendable () async -> Void
    
    /// Resume a paused recording
    var resumeRecording: @Sendable () async throws -> Void
    
    /// Stop the current recording
    var stopRecording: @Sendable () async -> Void
    
    /// Whether recording is currently paused
    var isPaused: @Sendable () async -> Bool = { false }
    
    /// Stream of audio levels (0.0 to 1.0) for waveform visualization
    var audioLevelStream: @Sendable () -> AsyncStream<Float> = { AsyncStream { $0.finish() } }
}

// MARK: - Test Dependency Key

extension AudioRecorderClient: TestDependencyKey {
    /// Preview implementation that simulates recording
    static var previewValue: Self {
        let isRecording = LockIsolated(false)
        let isPaused = LockIsolated(false)
        let currentTime = LockIsolated(0.0)
        let levelContinuation = LockIsolated<AsyncStream<Float>.Continuation?>(nil)
        
        return Self(
            currentTime: { currentTime.value },
            requestRecordPermission: { true },
            startRecording: { _ in
                isRecording.setValue(true)
                isPaused.setValue(false)
                /// Return an empty stream for preview
                return AsyncStream { continuation in
                    Task {
                        while isRecording.value {
                            try? await Task.sleep(for: .seconds(1))
                            if !isPaused.value {
                                currentTime.withValue { $0 += 1 }
                            }
                        }
                        continuation.finish()
                    }
                }
            },
            pauseRecording: {
                isPaused.setValue(true)
            },
            resumeRecording: {
                isPaused.setValue(false)
            },
            stopRecording: {
                isRecording.setValue(false)
                isPaused.setValue(false)
                currentTime.setValue(0)
                levelContinuation.value?.finish()
            },
            isPaused: { isPaused.value },
            audioLevelStream: {
                AsyncStream { continuation in
                    levelContinuation.setValue(continuation)
                    /// Simulate audio levels for preview
                    Task {
                        while isRecording.value {
                            if !isPaused.value {
                                /// Generate random audio level for preview
                                let level = Float.random(in: 0.1...0.8)
                                continuation.yield(level)
                            }
                            try? await Task.sleep(for: .milliseconds(50))
                        }
                        continuation.finish()
                    }
                }
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

// MARK: - Convenience Initializers

extension AudioRecorderClient {
    /// A no-op implementation that does nothing - useful as a base for tests.
    /// All methods return empty/default values immediately.
    static let noop = Self(
        currentTime: { nil },
        requestRecordPermission: { false },
        startRecording: { _ in AsyncStream { $0.finish() } },
        pauseRecording: {},
        resumeRecording: {},
        stopRecording: {},
        isPaused: { false },
        audioLevelStream: { AsyncStream { $0.finish() } }
    )
    
    /// A preview implementation with simulated recording behavior for SwiftUI previews.
    /// - Parameters:
    ///   - permissionGranted: Whether permission is granted (default: true)
    ///   - simulatedDuration: How long the simulated recording runs (default: 60 seconds)
    /// - Returns: A configured AudioRecorderClient for previews
    static func preview(
        permissionGranted: Bool = true,
        simulatedDuration: TimeInterval = 60
    ) -> Self {
        let isRecording = LockIsolated(false)
        let isPausedState = LockIsolated(false)
        let currentTimeValue = LockIsolated(0.0)
        let levelContinuation = LockIsolated<AsyncStream<Float>.Continuation?>(nil)
        
        return Self(
            currentTime: { currentTimeValue.value },
            requestRecordPermission: { permissionGranted },
            startRecording: { [isRecording, isPausedState, currentTimeValue] _ in
                isRecording.setValue(true)
                isPausedState.setValue(false)
                currentTimeValue.setValue(0)
                
                return AsyncStream { continuation in
                    Task {
                        let elapsed = LockIsolated(0.0)
                        while isRecording.value && elapsed.value < simulatedDuration {
                            try? await Task.sleep(for: .milliseconds(100))
                            if !isPausedState.value {
                                elapsed.withValue { $0 += 0.1 }
                                currentTimeValue.setValue(elapsed.value)
                            }
                        }
                        continuation.finish()
                    }
                }
            },
            pauseRecording: { [isPausedState] in
                isPausedState.setValue(true)
            },
            resumeRecording: { [isPausedState] in
                isPausedState.setValue(false)
            },
            stopRecording: { [isRecording, isPausedState, currentTimeValue, levelContinuation] in
                isRecording.setValue(false)
                isPausedState.setValue(false)
                currentTimeValue.setValue(0)
                levelContinuation.value?.finish()
            },
            isPaused: { isPausedState.value },
            audioLevelStream: { [isRecording, isPausedState, levelContinuation] in
                AsyncStream { continuation in
                    levelContinuation.setValue(continuation)
                    Task {
                        while isRecording.value {
                            if !isPausedState.value {
                                /// Generate random audio level for preview visualization
                                let level = Float.random(in: 0.1...0.8)
                                continuation.yield(level)
                            }
                            try? await Task.sleep(for: .milliseconds(50))
                        }
                        continuation.finish()
                    }
                }
            }
        )
    }
    
    /// Convenience factory for testing permission states.
    /// Returns a noop client with the specified permission result.
    /// - Parameter granted: Whether permission should be granted
    /// - Returns: A configured AudioRecorderClient for testing permission flows
    static func withPermission(_ granted: Bool) -> Self {
        var client = noop
        client.requestRecordPermission = { granted }
        return client
    }
    
    /// Convenience factory for testing with a specific current time.
    /// - Parameter time: The time to return from currentTime
    /// - Returns: A configured AudioRecorderClient for testing time-based logic
    static func withCurrentTime(_ time: TimeInterval?) -> Self {
        var client = noop
        client.currentTime = { time }
        return client
    }
}