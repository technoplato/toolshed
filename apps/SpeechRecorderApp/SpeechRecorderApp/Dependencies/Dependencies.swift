/**
 HOW:
   Import and use dependencies via @Dependency property wrapper.
   
   [Inputs]
   - None
   
   [Outputs]
   - Dependency definitions
   
   [Side Effects]
   - None

 WHO:
   AI Agent, Developer
   (Context: Additional dependencies for SpeechRecorderApp)

 WHAT:
   Additional dependency definitions for the app.
   Includes temporaryDirectory and openSettings.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/Dependencies.swift

 WHY:
   To provide additional testable dependencies.
   Following TCA patterns for dependency injection.
 */

import Dependencies
import Foundation
import UIKit

// MARK: - Temporary Directory

extension DependencyValues {
    /// Access the temporary directory
    var temporaryDirectory: @Sendable () -> URL {
        get { self[TemporaryDirectoryKey.self] }
        set { self[TemporaryDirectoryKey.self] = newValue }
    }
    
    private enum TemporaryDirectoryKey: DependencyKey {
        static let liveValue: @Sendable () -> URL = {
            URL(fileURLWithPath: NSTemporaryDirectory())
        }
    }
}

// MARK: - Open Settings

extension DependencyValues {
    /// Open the app settings
    var openSettings: @Sendable () async -> Void {
        get { self[OpenSettingsKey.self] }
        set { self[OpenSettingsKey.self] = newValue }
    }
    
    private enum OpenSettingsKey: DependencyKey {
        static let liveValue: @Sendable () async -> Void = {
            await MainActor.run {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
        }
    }
}