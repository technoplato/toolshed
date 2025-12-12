/**
 HOW:
   Use in SwiftUI views to show a LIVE indicator:
   
   ```swift
   LiveBadge()
   ```
   
   [Inputs]
   - None
   
   [Outputs]
   - SwiftUI View
   
   [Side Effects]
   - None

 WHO:
   AI Agent, Developer
   (Context: LIVE badge for active recordings)

 WHAT:
   A small badge that indicates a recording is currently live/active.
   Shows a pulsing red dot with "LIVE" text.
   
   Inspired by Otter.ai's LIVE indicator on the home screen.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/LiveBadge.swift

 WHY:
   To visually indicate which recording is currently active
   when the user is browsing the recordings list.
 */

import SwiftUI

struct LiveBadge: View {
    @State private var isAnimating = false
    
    var body: some View {
        HStack(spacing: 4) {
            /// Pulsing red dot
            Circle()
                .fill(Color.red)
                .frame(width: 6, height: 6)
                .scaleEffect(isAnimating ? 1.2 : 1.0)
                .opacity(isAnimating ? 0.7 : 1.0)
            
            /// LIVE text
            Text("LIVE")
                .font(.caption2.weight(.bold))
                .foregroundColor(.red)
        }
        .padding(.horizontal, 6)
        .padding(.vertical, 3)
        .background(
            Capsule()
                .fill(Color.red.opacity(0.15))
        )
        .onAppear {
            withAnimation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true)) {
                isAnimating = true
            }
        }
    }
}

// MARK: - Preview

#Preview {
    VStack(spacing: 20) {
        LiveBadge()
        
        HStack {
            Text("My Recording")
                .font(.headline)
            LiveBadge()
            Spacer()
        }
        .padding()
        .background(Color(.systemBackground))
    }
    .padding()
    .background(Color.gray.opacity(0.2))
}