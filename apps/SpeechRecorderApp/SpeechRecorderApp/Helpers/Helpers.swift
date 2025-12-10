/**
 HOW:
   Import and use helper functions throughout the app.
   
   [Inputs]
   - Various
   
   [Outputs]
   - Utility functions
   
   [Side Effects]
   - None

 WHO:
   AI Agent, Developer
   (Context: Utility helpers for SpeechRecorderApp)

 WHAT:
   Collection of utility functions and extensions.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Helpers/Helpers.swift

 WHY:
   To provide reusable utility functions across the app.
 */

import Foundation

// MARK: - Date Formatting

extension DateFormatter {
    /// Formatter for recording dates
    static let recordingDate: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter
    }()
}

// MARK: - Duration Formatting

/// Format a duration in seconds to MM:SS format
func formatDuration(_ duration: TimeInterval) -> String {
    let minutes = Int(duration) / 60
    let seconds = Int(duration) % 60
    return String(format: "%02d:%02d", minutes, seconds)
}

/// Format a duration in seconds to M:SS format (no leading zero on minutes)
func formatDurationShort(_ duration: TimeInterval) -> String {
    let minutes = Int(duration) / 60
    let seconds = Int(duration) % 60
    return String(format: "%d:%02d", minutes, seconds)
}

// MARK: - Array Safe Subscript

extension Array {
    /// Safe subscript that returns nil for out-of-bounds indices
    subscript(safe index: Index) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}

// MARK: - URL Helpers

extension URL {
    /// Check if a file exists at this URL
    var fileExists: Bool {
        FileManager.default.fileExists(atPath: path)
    }
    
    /// Get the file size in bytes
    var fileSize: Int64? {
        guard let attributes = try? FileManager.default.attributesOfItem(atPath: path) else {
            return nil
        }
        return attributes[.size] as? Int64
    }
}