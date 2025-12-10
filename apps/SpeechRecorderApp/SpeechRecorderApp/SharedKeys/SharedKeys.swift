/**
 HOW:
   Use with @Shared property wrapper:
   
   ```swift
   @Shared(.recordings) var recordings: [Recording] = []
   ```
   
   [Inputs]
   - None
   
   [Outputs]
   - Shared key for file storage
   
   [Side Effects]
   - Reads/writes to documents directory

 WHO:
   AI Agent, Developer
   (Context: Swift Sharing keys for persistence)

 WHAT:
   Defines shared keys for persisting app data using Swift Sharing.
   Uses .fileStorage for JSON persistence to the documents directory.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/SharedKeys/SharedKeys.swift

 WHY:
   To provide type-safe, reusable persistence keys.
   Follows Swift Sharing patterns for file-based persistence.
 */

import Foundation
import Sharing

// MARK: - Recordings Key

extension SharedReaderKey where Self == FileStorageKey<[Recording]> {
    /// Shared key for the list of recordings
    static var recordings: Self {
        .fileStorage(.documentsDirectory.appending(component: "recordings.json"))
    }
}

// MARK: - URL Extensions

extension URL {
    /// The documents directory for the app
    static var documentsDirectory: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
    
    /// The recordings directory within documents
    static var recordingsDirectory: URL {
        documentsDirectory.appending(component: "Recordings")
    }
}