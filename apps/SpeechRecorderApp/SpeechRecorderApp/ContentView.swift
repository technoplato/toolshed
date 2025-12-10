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
   Currently shows the recordings list with recording capability.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/ContentView.swift

 WHY:
   Standard SwiftUI content view pattern.
   Provides the root navigation structure for the app.
 */

import ComposableArchitecture
import SwiftUI

struct ContentView: View {
    @Bindable var store: StoreOf<AppFeature>
    
    var body: some View {
        NavigationStack {
            RecordingsListView(
                store: store.scope(state: \.recordingsList, action: \.recordingsList)
            )
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