/**
 HOW:
   Used as the root reducer for the application.
   
   ```swift
   let store = Store(initialState: AppFeature.State()) {
       AppFeature()
   }
   ```
   
   [Inputs]
   - Child feature actions
   
   [Outputs]
   - Composed state from child features
   
   [Side Effects]
   - Delegates to child features

 WHO:
   AI Agent, Developer
   (Context: Root app feature for SpeechRecorderApp)

 WHAT:
   The root TCA reducer that composes all child features.
   Currently composes RecordingsListFeature.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/AppFeature.swift

 WHY:
   To provide a single root reducer for the application.
   Follows TCA composition patterns for feature modularity.
 */

import ComposableArchitecture

@Reducer
struct AppFeature {
    
    // MARK: - State
    
    @ObservableState
    struct State: Equatable {
        /// The recordings list feature state
        var recordingsList = RecordingsListFeature.State()
    }
    
    // MARK: - Action
    
    enum Action: Sendable {
        /// Recordings list feature actions
        case recordingsList(RecordingsListFeature.Action)
    }
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        Scope(state: \.recordingsList, action: \.recordingsList) {
            RecordingsListFeature()
        }
    }
}