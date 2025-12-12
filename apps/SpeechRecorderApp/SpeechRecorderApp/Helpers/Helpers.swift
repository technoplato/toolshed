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
import SwiftUI
import UIKit

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

/// Format a date to human-readable format like "December 10th, 2024 at 12:25 PM EST"
func formatHumanReadableDate(_ date: Date) -> String {
    let calendar = Calendar.current
    let day = calendar.component(.day, from: date)
    
    /// Get ordinal suffix for day
    let ordinalSuffix: String
    switch day {
    case 1, 21, 31: ordinalSuffix = "st"
    case 2, 22: ordinalSuffix = "nd"
    case 3, 23: ordinalSuffix = "rd"
    default: ordinalSuffix = "th"
    }
    
    /// Format: "December 10th, 2024 at 12:25 PM EST"
    let monthFormatter = DateFormatter()
    monthFormatter.dateFormat = "MMMM"
    let month = monthFormatter.string(from: date)
    
    let yearFormatter = DateFormatter()
    yearFormatter.dateFormat = "yyyy"
    let year = yearFormatter.string(from: date)
    
    let timeFormatter = DateFormatter()
    timeFormatter.dateFormat = "h:mm a"
    let time = timeFormatter.string(from: date)
    
    let timezoneFormatter = DateFormatter()
    timezoneFormatter.dateFormat = "zzz"
    let timezone = timezoneFormatter.string(from: date)
    
    return "\(month) \(day)\(ordinalSuffix), \(year) at \(time) \(timezone)"
}

/// Format a date to short human-readable format like "December 10th, 2024"
func formatHumanReadableDateShort(_ date: Date) -> String {
    let calendar = Calendar.current
    let day = calendar.component(.day, from: date)
    
    /// Get ordinal suffix for day
    let ordinalSuffix: String
    switch day {
    case 1, 21, 31: ordinalSuffix = "st"
    case 2, 22: ordinalSuffix = "nd"
    case 3, 23: ordinalSuffix = "rd"
    default: ordinalSuffix = "th"
    }
    
    let monthFormatter = DateFormatter()
    monthFormatter.dateFormat = "MMMM"
    let month = monthFormatter.string(from: date)
    
    let yearFormatter = DateFormatter()
    yearFormatter.dateFormat = "yyyy"
    let year = yearFormatter.string(from: date)
    
    return "\(month) \(day)\(ordinalSuffix), \(year)"
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

/// Format a duration in seconds to HH:MM:SS format
func formatDurationHMS(_ duration: TimeInterval) -> String {
    let hours = Int(duration) / 3600
    let minutes = (Int(duration) % 3600) / 60
    let seconds = Int(duration) % 60
    
    if hours > 0 {
        return String(format: "%d:%02d:%02d", hours, minutes, seconds)
    } else {
        return String(format: "%d:%02d", minutes, seconds)
    }
}

/// Format a duration in seconds to HH:MM:SS.mmm format (with milliseconds)
func formatDurationHMSms(_ duration: TimeInterval) -> String {
    let hours = Int(duration) / 3600
    let minutes = (Int(duration) % 3600) / 60
    let seconds = Int(duration) % 60
    let milliseconds = Int((duration.truncatingRemainder(dividingBy: 1)) * 1000)
    
    if hours > 0 {
        return String(format: "%d:%02d:%02d.%03d", hours, minutes, seconds, milliseconds)
    } else {
        return String(format: "%02d:%02d.%03d", minutes, seconds, milliseconds)
    }
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

// MARK: - Two-Finger Double-Tap Gesture

/// A custom gesture that detects a two-finger double-tap
struct TwoFingerDoubleTapGesture: UIViewRepresentable {
    let action: () -> Void
    
    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        view.backgroundColor = .clear
        
        let tapGesture = UITapGestureRecognizer(
            target: context.coordinator,
            action: #selector(Coordinator.handleTap)
        )
        tapGesture.numberOfTapsRequired = 2
        tapGesture.numberOfTouchesRequired = 2
        view.addGestureRecognizer(tapGesture)
        
        return view
    }
    
    func updateUIView(_ uiView: UIView, context: Context) {}
    
    func makeCoordinator() -> Coordinator {
        Coordinator(action: action)
    }
    
    class Coordinator: NSObject {
        let action: () -> Void
        
        init(action: @escaping () -> Void) {
            self.action = action
        }
        
        @objc func handleTap() {
            action()
        }
    }
}

/// View modifier extension for two-finger double-tap
extension View {
    /// Add a two-finger double-tap gesture to the view
    func onTwoFingerDoubleTap(perform action: @escaping () -> Void) -> some View {
        self.overlay(
            TwoFingerDoubleTapGesture(action: action)
                .allowsHitTesting(true)
        )
    }
}