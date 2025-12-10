/**
 HOW:
   Use to convert AVAudioPCMBuffer to AudioBuffer for SpeechClient.
   
   ```swift
   let audioBuffer = BufferConverter.convert(pcmBuffer)
   ```
   
   [Inputs]
   - AVAudioPCMBuffer from AVAudioEngine
   
   [Outputs]
   - AudioBuffer suitable for SpeechClient
   
   [Side Effects]
   - None (pure conversion)

 WHO:
   AI Agent, Developer
   (Context: Audio buffer conversion for speech recognition - Phase 2)

 WHAT:
   Utility for converting between audio buffer formats.
   Bridges AVAudioEngine output to SpeechAnalyzer input.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Helpers/BufferConverter.swift

 WHY:
   To provide a clean interface between audio recording and speech recognition.
   Encapsulates the complexity of audio format conversion.
 */

import AVFoundation
import Foundation

/// Utility for converting audio buffers between formats
enum BufferConverter {
    /// Convert AVAudioPCMBuffer to AudioBuffer for SpeechClient
    /// - Parameter pcmBuffer: The PCM buffer from AVAudioEngine
    /// - Returns: AudioBuffer suitable for SpeechClient, or nil if conversion fails
    static func convert(_ pcmBuffer: AVAudioPCMBuffer) -> AudioBuffer? {
        guard let floatChannelData = pcmBuffer.floatChannelData else {
            return nil
        }
        
        let frameLength = Int(pcmBuffer.frameLength)
        let channelCount = Int(pcmBuffer.format.channelCount)
        let sampleRate = pcmBuffer.format.sampleRate
        
        /// Convert float samples to Data
        var data = Data()
        for frame in 0..<frameLength {
            for channel in 0..<channelCount {
                let sample = floatChannelData[channel][frame]
                withUnsafeBytes(of: sample) { bytes in
                    data.append(contentsOf: bytes)
                }
            }
        }
        
        return AudioBuffer(
            data: data,
            sampleRate: sampleRate,
            channelCount: channelCount
        )
    }
    
    /// Convert AudioBuffer back to AVAudioPCMBuffer
    /// - Parameters:
    ///   - audioBuffer: The AudioBuffer to convert
    ///   - format: The target audio format
    /// - Returns: AVAudioPCMBuffer, or nil if conversion fails
    static func convert(_ audioBuffer: AudioBuffer, format: AVAudioFormat) -> AVAudioPCMBuffer? {
        let frameCount = audioBuffer.data.count / (MemoryLayout<Float>.size * audioBuffer.channelCount)
        
        guard let pcmBuffer = AVAudioPCMBuffer(pcmFormat: format, frameCapacity: AVAudioFrameCount(frameCount)) else {
            return nil
        }
        
        pcmBuffer.frameLength = AVAudioFrameCount(frameCount)
        
        guard let floatChannelData = pcmBuffer.floatChannelData else {
            return nil
        }
        
        audioBuffer.data.withUnsafeBytes { bytes in
            let floatPointer = bytes.bindMemory(to: Float.self)
            for frame in 0..<frameCount {
                for channel in 0..<audioBuffer.channelCount {
                    let index = frame * audioBuffer.channelCount + channel
                    floatChannelData[channel][frame] = floatPointer[index]
                }
            }
        }
        
        return pcmBuffer
    }
}