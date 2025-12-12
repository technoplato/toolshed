/**
 HOW:
   Use in SwiftUI views to display a real-time audio waveform:
   
   ```swift
   AudioWaveformView(levels: audioLevels, isRecording: true)
   ```
   
   [Inputs]
   - levels: Array of Float values (0.0 to 1.0) representing audio levels
   - isRecording: Whether recording is active (affects animation)
   - isPaused: Whether recording is paused
   - barColor: Color for the waveform bars (default: red)
   
   [Outputs]
   - SwiftUI View displaying animated waveform bars
   
   [Side Effects]
   - None

 WHO:
   AI Agent, Developer
   (Context: Audio waveform visualization for recording UI)

 WHAT:
   A compact audio waveform visualization component inspired by Voice Memos.
   Displays a series of vertical bars that animate based on audio levels.
   Designed to be small and unobtrusive at the bottom of the recording screen.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/AudioWaveformView.swift

 WHY:
   To provide visual feedback of audio input during recording.
   Helps users confirm their microphone is working and capturing audio.
   Inspired by Apple Voice Memos app's waveform display.
 */

import SwiftUI

/// A compact audio waveform visualization component
struct AudioWaveformView: View {
    /// Array of audio levels (0.0 to 1.0)
    let levels: [Float]
    
    /// Whether recording is currently active
    let isRecording: Bool
    
    /// Whether recording is paused
    let isPaused: Bool
    
    /// Color for the waveform bars
    var barColor: Color = .red
    
    /// Number of bars to display
    private let barCount = 30
    
    /// Minimum bar height as a fraction of total height
    private let minBarHeight: CGFloat = 0.1
    
    var body: some View {
        GeometryReader { geometry in
            HStack(spacing: 2) {
                ForEach(0..<barCount, id: \.self) { index in
                    waveformBar(
                        at: index,
                        totalHeight: geometry.size.height
                    )
                }
            }
        }
        .frame(height: 32)
    }
    
    /// Creates a single waveform bar at the given index
    private func waveformBar(at index: Int, totalHeight: CGFloat) -> some View {
        let level = levelForBar(at: index)
        let barHeight = max(minBarHeight, CGFloat(level)) * totalHeight
        
        return RoundedRectangle(cornerRadius: 1.5)
            .fill(barColor.opacity(isPaused ? 0.5 : 1.0))
            .frame(width: 3, height: barHeight)
            .animation(.easeInOut(duration: 0.1), value: level)
    }
    
    /// Gets the audio level for a specific bar index
    private func levelForBar(at index: Int) -> Float {
        guard !levels.isEmpty else {
            /// Return a small random value for idle state
            return isRecording && !isPaused ? Float.random(in: 0.05...0.15) : 0.1
        }
        
        /// Map bar index to levels array
        let levelIndex = Int(Float(index) / Float(barCount) * Float(levels.count))
        let clampedIndex = min(max(0, levelIndex), levels.count - 1)
        
        return levels[clampedIndex]
    }
}

/// A waveform view that maintains a rolling buffer of audio levels
struct RollingWaveformView: View {
    /// Current audio level (0.0 to 1.0)
    let currentLevel: Float
    
    /// Whether recording is currently active
    let isRecording: Bool
    
    /// Whether recording is paused
    let isPaused: Bool
    
    /// Color for the waveform bars
    var barColor: Color = .red
    
    /// Number of bars to display
    private let barCount = 40
    
    /// Rolling buffer of audio levels
    @State private var levels: [Float] = []
    
    var body: some View {
        AudioWaveformView(
            levels: levels,
            isRecording: isRecording,
            isPaused: isPaused,
            barColor: barColor
        )
        .onChange(of: currentLevel) { _, newLevel in
            updateLevels(with: newLevel)
        }
        .onAppear {
            /// Initialize with empty levels
            levels = Array(repeating: 0.1, count: barCount)
        }
    }
    
    /// Updates the rolling buffer with a new level
    private func updateLevels(with newLevel: Float) {
        guard isRecording && !isPaused else { return }
        
        var newLevels = levels
        newLevels.append(newLevel)
        
        /// Keep only the most recent levels
        if newLevels.count > barCount {
            newLevels.removeFirst(newLevels.count - barCount)
        }
        
        levels = newLevels
    }
}

// MARK: - Previews

#Preview("Waveform - Recording") {
    AudioWaveformView(
        levels: (0..<30).map { _ in Float.random(in: 0.1...0.9) },
        isRecording: true,
        isPaused: false
    )
    .padding()
}

#Preview("Waveform - Paused") {
    AudioWaveformView(
        levels: (0..<30).map { _ in Float.random(in: 0.1...0.9) },
        isRecording: true,
        isPaused: true
    )
    .padding()
}

#Preview("Waveform - Idle") {
    AudioWaveformView(
        levels: [],
        isRecording: false,
        isPaused: false
    )
    .padding()
}

#Preview("Rolling Waveform") {
    RollingWaveformView(
        currentLevel: 0.5,
        isRecording: true,
        isPaused: false
    )
    .padding()
}