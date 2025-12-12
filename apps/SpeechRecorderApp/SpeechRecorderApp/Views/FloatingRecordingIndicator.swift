/**
 HOW:
   Use in SwiftUI views to show a floating recording indicator bar:
   
   ```swift
   FloatingRecordingIndicator(
       duration: store.activeRecording?.duration ?? 0,
       isPaused: store.activeRecording?.isPaused ?? false,
       onTap: { store.send(.floatingIndicatorTapped) }
   )
   ```
   
   [Inputs]
   - duration: Current recording duration
   - isPaused: Whether recording is paused
   - onTap: Action when user taps the indicator
   
   [Outputs]
   - SwiftUI View
   
   [Side Effects]
   - None

 WHO:
   AI Agent, Developer
   (Context: Floating recording indicator for minimized recording)

 WHAT:
   A floating bar that appears at the bottom of the screen when
   a recording is minimized. Shows recording status, duration,
   and allows tapping to expand back to full recording view.
   
   Inspired by Otter.ai's floating recording indicator.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/FloatingRecordingIndicator.swift

 WHY:
   To allow users to continue browsing the app while recording.
   The floating indicator provides quick access back to the recording.
 */

import SwiftUI

struct FloatingRecordingIndicator: View {
    let duration: TimeInterval
    let isPaused: Bool
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                /// Recording indicator dot (blinking when recording, solid when paused)
                Circle()
                    .fill(isPaused ? Color.orange : Color.red)
                    .frame(width: 12, height: 12)
                    .opacity(isPaused ? 1.0 : (Int(duration).isMultiple(of: 2) ? 1.0 : 0.3))
                    .animation(.easeInOut(duration: 0.5), value: duration)
                
                /// Duration display
                Text(formatDuration(duration))
                    .font(.subheadline.monospacedDigit().weight(.medium))
                    .foregroundColor(.white)
                
                Spacer()
                
                /// Status text
                Text(isPaused ? "Paused" : "Recording")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.8))
                
                /// Expand icon
                Image(systemName: "chevron.up")
                    .font(.caption.weight(.semibold))
                    .foregroundColor(.white.opacity(0.8))
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(
                Capsule()
                    .fill(Color.black.opacity(0.9))
                    .shadow(color: .black.opacity(0.3), radius: 8, x: 0, y: 4)
            )
        }
        .buttonStyle(.plain)
        .padding(.horizontal, 20)
        .padding(.bottom, 8)
    }
    
    private func formatDuration(_ duration: TimeInterval) -> String {
        let hours = Int(duration) / 3600
        let minutes = (Int(duration) % 3600) / 60
        let seconds = Int(duration) % 60
        
        if hours > 0 {
            return String(format: "%d:%02d:%02d", hours, minutes, seconds)
        } else {
            return String(format: "%d:%02d", minutes, seconds)
        }
    }
}

// MARK: - Preview

#Preview("Recording") {
    VStack {
        Spacer()
        FloatingRecordingIndicator(
            duration: 125,
            isPaused: false,
            onTap: {}
        )
    }
    .background(Color.gray.opacity(0.2))
}

#Preview("Paused") {
    VStack {
        Spacer()
        FloatingRecordingIndicator(
            duration: 65,
            isPaused: true,
            onTap: {}
        )
    }
    .background(Color.gray.opacity(0.2))
}