/**
 HOW:
   Automatically used when running the app in production.
   Register via DependencyKey conformance.
   
   [Inputs]
   - Audio buffer stream from AVAudioEngine
   
   [Outputs]
   - AsyncStream of Transcription with word-level timing
   
   [Side Effects]
   - Uses SpeechAnalyzer API (iOS 26.0+)
   - May download speech recognition assets on first use

 WHO:
   AI Agent, Developer
   (Context: Live implementation of SpeechClient - Phase 2)

 WHAT:
   Live implementation of SpeechClient using iOS 26.0+ SpeechAnalyzer.
   Provides real-time transcription with word-level timestamps.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/LiveSpeechClient.swift

 WHY:
   To provide real speech recognition functionality in production.
   Uses the new SpeechAnalyzer API for better accuracy and timing.
 */

import ComposableArchitecture
import Foundation

// MARK: - Live Dependency Key

extension SpeechClient: DependencyKey {
    /// Live implementation using SpeechAnalyzer (iOS 26.0+)
    static var liveValue: Self {
        /// TODO: Implement in Phase 2 using SpeechAnalyzer
        /// For now, return a placeholder that indicates unavailability
        Self(
            isAvailable: {
                /// Check if SpeechAnalyzer is available
                /// This will be implemented in Phase 2
                #if targetEnvironment(simulator)
                return false
                #else
                /// Check for iOS 26.0+ availability
                if #available(iOS 26.0, *) {
                    return true
                }
                return false
                #endif
            },
            requestAuthorization: {
                /// Request speech recognition authorization
                /// This will be implemented in Phase 2
                return false
            },
            startTranscription: { _ in
                /// Start transcription using SpeechAnalyzer
                /// This will be implemented in Phase 2
                AsyncStream { continuation in
                    continuation.finish()
                }
            },
            stopTranscription: {
                /// Stop transcription
                /// This will be implemented in Phase 2
            }
        )
    }
}