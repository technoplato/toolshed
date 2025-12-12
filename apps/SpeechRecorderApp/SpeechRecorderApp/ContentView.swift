/**
 HOW:
   Used as the root view of the application.
   
   [Inputs]
   - store: StoreOf<AppFeature>
   
   [Outputs]
   - SwiftUI View
   
   [Side Effects]
   - None

 WHO:
   AI Agent, Developer
   (Context: Root content view for SpeechRecorderApp)

 WHAT:
   The main content view that hosts the app's navigation.
   Shows the recordings list with recording capability.
   Manages the collapsible recording modal at the app level.
   
   **Migration Note (2025-12-12):**
   FIXED: Now uses activeRecording with isRecordingExpanded boolean.
   This ensures only ONE RecordingFeature reducer runs, and effects
   continue when the modal is minimized.
   
   The previous Destination pattern caused duplicate state and effects
   to stop when minimizing.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-12
   [Change Log:
     - 2025-12-12: Fixed minimized recording bug by using isRecordingExpanded
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/ContentView.swift

 WHY:
   Standard SwiftUI content view pattern.
   Provides the root navigation structure for the app.
   Recording modal is managed here so it persists when minimized.
   
   Using isRecordingExpanded boolean instead of Destination:
   - Single source of truth for recording state (activeRecording)
   - Effects continue running when modal is minimized
   - Simpler architecture with less state synchronization
 */

import ComposableArchitecture
import SwiftUI

struct ContentView: View {
    @Bindable var store: StoreOf<AppFeature>
    
    var body: some View {
        ZStack(alignment: .bottom) {
            NavigationStack {
                RecordingsListView(
                    store: store.scope(state: \.recordingsList, action: \.recordingsList)
                )
            }
            
            /// Floating recording indicator (shown when recording is minimized)
            /// Only show when there's an active recording but isRecordingExpanded is false
            if let activeRecording = store.activeRecording,
               !store.isRecordingExpanded {
                FloatingRecordingIndicator(
                    duration: activeRecording.duration,
                    isPaused: activeRecording.isPaused,
                    onTap: { store.send(.floatingIndicatorTapped) }
                )
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
        .animation(.spring(response: 0.3), value: store.isRecordingExpanded)
        .fullScreenCover(
            isPresented: $store.isRecordingExpanded
        ) {
            /// Scope to activeRecording - the SINGLE source of truth
            if let recordingStore = store.scope(
                state: \.activeRecording,
                action: \.activeRecording
            ) {
                RecordingView(store: recordingStore)
                    .gesture(
                        DragGesture()
                            .onEnded { value in
                                /// Swipe down to minimize
                                if value.translation.height > 100 {
                                    store.send(.minimizeRecording)
                                }
                            }
                    )
            }
        }
    }
}

#Preview {
    ContentView(
        store: Store(initialState: AppFeature.State()) {
            AppFeature()
        }
    )
}

#Preview("With Active Recording (Minimized)") {
    ContentView(
        store: Store(
            initialState: AppFeature.State(
                activeRecording: RecordingFeature.State(),
                isRecordingExpanded: false
            )
        ) {
            AppFeature()
        }
    )
}

#Preview("With Active Recording (Expanded)") {
    ContentView(
        store: Store(
            initialState: AppFeature.State(
                activeRecording: RecordingFeature.State(),
                isRecordingExpanded: true
            )
        ) {
            AppFeature()
        }
    )
}
