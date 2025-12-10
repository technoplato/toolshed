/**
 HOW:
   Automatically used when running the app (not in tests/previews).
   Uses AVAudioPlayer for audio playback.
   
   [Inputs]
   - url: File URL of audio to play
   
   [Outputs]
   - Audio playback through device speakers
   
   [Side Effects]
   - Configures AVAudioSession for playback
   - Plays audio through speakers

 WHO:
   AI Agent, Developer
   (Context: Live implementation of AudioPlayerClient)

 WHAT:
   Live implementation of AudioPlayerClient using AVAudioPlayer.
   Plays recorded audio files with seek and time tracking.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/LiveAudioPlayerClient.swift

 WHY:
   To provide real audio playback functionality in production.
   Uses AVAudioPlayer for simple file-based playback.
 */

import AVFoundation
import Dependencies

// MARK: - Live Implementation

extension AudioPlayerClient: DependencyKey {
    static var liveValue: Self {
        let audioPlayer = AudioPlayer()
        return Self(
            play: { url in try await audioPlayer.play(url: url) },
            pause: { await audioPlayer.pause() },
            stop: { await audioPlayer.stop() },
            seek: { time in await audioPlayer.seek(to: time) },
            currentTime: { await audioPlayer.currentTime },
            duration: { await audioPlayer.duration }
        )
    }
}

// MARK: - AudioPlayer Actor

/// Actor that manages audio playback using AVAudioPlayer
private actor AudioPlayer {
    /// The audio player instance
    private var player: AVAudioPlayer?
    
    /// Delegate for playback events
    private var delegate: Delegate?
    
    /// Current playback time
    var currentTime: TimeInterval? {
        player?.currentTime
    }
    
    /// Total duration
    var duration: TimeInterval? {
        player?.duration
    }
    
    /// Play audio from the specified URL
    func play(url: URL) async throws {
        /// Stop any existing playback
        stop()
        
        /// Configure audio session
        let audioSession = AVAudioSession.sharedInstance()
        try audioSession.setCategory(.playback, mode: .spokenAudio)
        try audioSession.setActive(true)
        
        /// Create player
        player = try AVAudioPlayer(contentsOf: url)
        
        /// Set up delegate
        delegate = Delegate()
        player?.delegate = delegate
        
        /// Start playback
        player?.play()
        
        /// Wait for playback to finish
        await withCheckedContinuation { continuation in
            delegate?.onFinish = {
                continuation.resume()
            }
        }
    }
    
    /// Pause playback
    func pause() {
        player?.pause()
    }
    
    /// Stop playback
    func stop() {
        player?.stop()
        player = nil
        delegate = nil
        try? AVAudioSession.sharedInstance().setActive(false)
    }
    
    /// Seek to a specific time
    func seek(to time: TimeInterval) {
        player?.currentTime = time
    }
}

// MARK: - Delegate

private final class Delegate: NSObject, AVAudioPlayerDelegate, @unchecked Sendable {
    var onFinish: (() -> Void)?
    
    func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        onFinish?()
    }
}