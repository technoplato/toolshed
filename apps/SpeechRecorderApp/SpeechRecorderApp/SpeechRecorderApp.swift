/**
 HOW:
   This is the app entry point. Run with Xcode or:
   `xcodebuild -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 16' build`
   
   [Inputs]
   - None
   
   [Outputs]
   - SwiftUI App
   
   [Side Effects]
   - Launches the application

 WHO:
   AI Agent, Developer
   (Context: App entry point for SpeechRecorderApp)

 WHAT:
   The main app entry point using SwiftUI App protocol.
   Sets up the root store and initial view.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/SpeechRecorderApp.swift

 WHY:
   Standard SwiftUI app entry point.
   Initializes the TCA store at the app level.
 */

import ComposableArchitecture
import SwiftUI

@main
struct SpeechRecorderApp: App {
    /// The root store for the application
    static let store = Store(initialState: AppFeature.State()) {
      AppFeature()
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView(store: Self.store)
        }
    }
}
