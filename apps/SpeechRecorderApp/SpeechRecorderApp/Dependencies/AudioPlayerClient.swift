/**
 HOW:
   Use via @Dependency(\.audioPlayer) in TCA reducers.
   
   ```swift
   @Dependency(\.audioPlayer) var audioPlayer
   
   // Play audio
   try await audioPlayer.play(url)
   
   // Get current time
   let time = await audioPlayer.currentTime()
   
   // Pause/Stop
   await audioPlayer.pause()
   await audioPlayer.stop()
   
   // Seek
   await audioPlayer.seek(to: time)
   ```
   
   [Inputs]
   - url: File URL of audio to play
   - time: TimeInterval for seeking
   
   [Outputs]
   - Current playback time
   
   [Side Effects]
   - Plays audio through device speakers

 WHO:
   AI Agent, Developer
   (Context: TDD for AudioPlayerClient dependency)

 WHAT:
   Dependency client for audio playback functionality.
   Wraps AVAudioPlayer for playing recorded audio.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/AudioPlayerClient.swift

 WHY:
   To provide a testable interface for audio playback.
   Following TCA patterns for dependency injection.
 */

import ComposableArchitecture
import Foundation

/// Dependency client for audio playback
@DependencyClient
struct AudioPlayerClient: Sendable {
    /// Play audio from the specified URL
    var play: @Sendable (_ url: URL) async throws -> Void
    
    /// Pause playback
    var pause: @Sendable () async -> Void
    
    /// Stop playback
    var stop: @Sendable () async -> Void
    
    /// Seek to a specific time
    var seek: @Sendable (_ time: TimeInterval) async -> Void
    
    /// Get the current playback time
    var currentTime: @Sendable () async -> TimeInterval? = { nil }
    
    /// Get the total duration
    var duration: @Sendable () async -> TimeInterval? = { nil }
}

// MARK: - Test Dependency Key

extension AudioPlayerClient: TestDependencyKey {
    /// Preview implementation that simulates playback
    static var previewValue: Self {
        let isPlaying = LockIsolated(false)
        let currentTime = LockIsolated(0.0)
        let duration = LockIsolated(10.0)
        
        return Self(
            play: { _ in
                isPlaying.setValue(true)
                while isPlaying.value && currentTime.value < duration.value {
                    try await Task.sleep(for: .milliseconds(50))
                    currentTime.withValue { $0 += 0.05 }
                }
                isPlaying.setValue(false)
            },
            pause: {
                isPlaying.setValue(false)
            },
            stop: {
                isPlaying.setValue(false)
                currentTime.setValue(0)
            },
            seek: { time in
                currentTime.setValue(time)
            },
            currentTime: { currentTime.value },
            duration: { duration.value }
        )
    }
    
    /// Test implementation with unimplemented closures
    static let testValue = Self()
}

// MARK: - Dependency Values Extension

extension DependencyValues {
    /// Access the audio player client
    var audioPlayer: AudioPlayerClient {
        get { self[AudioPlayerClient.self] }
        set { self[AudioPlayerClient.self] = newValue }
    }
}

// MARK: - Convenience Initializers

extension AudioPlayerClient {
    /// A no-op implementation that does nothing - useful as a base for tests.
    /// All methods return empty/default values immediately.
    static let noop = Self(
        play: { _ in },
        pause: {},
        stop: {},
        seek: { _ in },
        currentTime: { nil },
        duration: { nil }
    )
    
    /// A preview implementation with simulated playback behavior for SwiftUI previews.
    /// - Parameters:
    ///   - duration: The simulated duration of the audio (default: 10 seconds)
    ///   - playbackSpeed: Speed multiplier for simulated playback (default: 1.0)
    /// - Returns: A configured AudioPlayerClient for previews
    static func preview(
        duration: TimeInterval = 10.0,
        playbackSpeed: Double = 1.0
    ) -> Self {
        let isPlaying = LockIsolated(false)
        let currentTimeValue = LockIsolated(0.0)
        let durationValue = LockIsolated(duration)
        
        return Self(
            play: { [isPlaying, currentTimeValue, durationValue] _ in
                isPlaying.setValue(true)
                while isPlaying.value && currentTimeValue.value < durationValue.value {
                    try await Task.sleep(for: .milliseconds(50))
                    currentTimeValue.withValue { $0 += 0.05 * playbackSpeed }
                }
                isPlaying.setValue(false)
            },
            pause: { [isPlaying] in
                isPlaying.setValue(false)
            },
            stop: { [isPlaying, currentTimeValue] in
                isPlaying.setValue(false)
                currentTimeValue.setValue(0)
            },
            seek: { [currentTimeValue, durationValue] time in
                currentTimeValue.setValue(min(max(0, time), durationValue.value))
            },
            currentTime: { currentTimeValue.value },
            duration: { durationValue.value }
        )
    }
    
    /// Convenience factory for testing with a specific duration.
    /// - Parameter duration: The duration to return
    /// - Returns: A configured AudioPlayerClient for testing duration-based logic
    static func withDuration(_ duration: TimeInterval) -> Self {
        var client = noop
        client.duration = { duration }
        return client
    }
    
    /// Convenience factory for testing with a specific current time.
    /// - Parameter time: The current time to return
    /// - Returns: A configured AudioPlayerClient for testing time-based logic
    static func withCurrentTime(_ time: TimeInterval) -> Self {
        var client = noop
        client.currentTime = { time }
        return client
    }
    
    /// Convenience factory for testing playback state.
    /// - Parameters:
    ///   - currentTime: The current playback time
    ///   - duration: The total duration
    /// - Returns: A configured AudioPlayerClient for testing playback state
    static func withPlaybackState(
        currentTime: TimeInterval,
        duration: TimeInterval
    ) -> Self {
        var client = noop
        client.currentTime = { currentTime }
        client.duration = { duration }
        return client
    }
}