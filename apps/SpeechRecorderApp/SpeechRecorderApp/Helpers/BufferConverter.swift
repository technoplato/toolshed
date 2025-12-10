/**
 HOW:
   Use to convert audio buffers between formats for SpeechAnalyzer.
   
   ```swift
   let converter = BufferConverter()
   let convertedBuffer = try converter.convertBuffer(inputBuffer, to: targetFormat)
   ```
   
   [Inputs]
   - Source AVAudioPCMBuffer
   - Target AVAudioFormat
   
   [Outputs]
   - Converted AVAudioPCMBuffer
   
   [Side Effects]
   - None (pure conversion)

 WHO:
   AI Agent, Developer
   (Context: Audio buffer conversion for SpeechAnalyzer)

 WHAT:
   Converts audio buffers between different formats.
   Required because the microphone format may differ from
   what SpeechAnalyzer expects.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Helpers/BufferConverter.swift

 WHY:
   SpeechAnalyzer requires audio in a specific format.
   The microphone may provide audio in a different format,
   so we need to convert between them.
 */

@preconcurrency import AVFoundation
import Foundation

/// Converts audio buffers between formats
/// Note: This class is not thread-safe. Use from a single actor/thread.
final class BufferConverter {
    private var converter: AVAudioConverter?
    private var sourceFormat: AVAudioFormat?
    private var targetFormat: AVAudioFormat?
    
    /// Convert a buffer to the target format
    /// - Parameters:
    ///   - buffer: The source audio buffer
    ///   - targetFormat: The desired output format
    /// - Returns: A new buffer in the target format
    func convertBuffer(_ buffer: AVAudioPCMBuffer, to targetFormat: AVAudioFormat) throws -> AVAudioPCMBuffer {
        let sourceFormat = buffer.format
        
        /// If formats match, return the original buffer
        if sourceFormat == targetFormat {
            return buffer
        }
        
        /// Create or update converter if needed
        if self.converter == nil || self.sourceFormat != sourceFormat || self.targetFormat != targetFormat {
            guard let newConverter = AVAudioConverter(from: sourceFormat, to: targetFormat) else {
                throw BufferConverterError.converterCreationFailed
            }
            self.converter = newConverter
            self.sourceFormat = sourceFormat
            self.targetFormat = targetFormat
        }
        
        guard let converter else {
            throw BufferConverterError.converterNotAvailable
        }
        
        /// Calculate output frame capacity
        let ratio = targetFormat.sampleRate / sourceFormat.sampleRate
        let outputFrameCapacity = AVAudioFrameCount(Double(buffer.frameLength) * ratio)
        
        guard let outputBuffer = AVAudioPCMBuffer(
            pcmFormat: targetFormat,
            frameCapacity: outputFrameCapacity
        ) else {
            throw BufferConverterError.outputBufferCreationFailed
        }
        
        /// Perform conversion - capture buffer in a nonisolated way
        /// since AVAudioConverterInputBlock is not Sendable
        var error: NSError?
        nonisolated(unsafe) let inputBuffer = buffer
        let inputBlock: AVAudioConverterInputBlock = { _, outStatus in
            outStatus.pointee = .haveData
            return inputBuffer
        }
        
        let status = converter.convert(to: outputBuffer, error: &error, withInputFrom: inputBlock)
        
        if let error {
            throw BufferConverterError.conversionFailed(error.localizedDescription)
        }
        
        guard status != .error else {
            throw BufferConverterError.conversionFailed("Conversion returned error status")
        }
        
        return outputBuffer
    }
    
    /// Reset the converter
    func reset() {
        converter?.reset()
    }
}

// MARK: - Errors

enum BufferConverterError: Error, Equatable {
    case converterCreationFailed
    case converterNotAvailable
    case outputBufferCreationFailed
    case conversionFailed(String)
}