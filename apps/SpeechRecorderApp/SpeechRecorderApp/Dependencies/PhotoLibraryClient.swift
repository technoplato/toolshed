/**
 HOW:
   Use via @Dependency(\.photoLibrary) in TCA reducers.
   
   ```swift
   @Dependency(\.photoLibrary) var photoLibrary
   
   // Request authorization
   let status = await photoLibrary.requestAuthorization()
   
   // Start observing new photos
   for await asset in await photoLibrary.observeNewPhotos() {
       // Handle new photo/screenshot
   }
   
   // Fetch thumbnail for display
   let image = await photoLibrary.fetchThumbnail(assetIdentifier, size)
   ```
   
   [Inputs]
   - Asset identifier for fetching thumbnails
   - Target size for thumbnails
   
   [Outputs]
   - AsyncStream of PhotoAsset for new photos/screenshots
   - Optional UIImage for thumbnails
   
   [Side Effects]
   - Requests photo library permission
   - Observes PHPhotoLibrary changes

 WHO:
   AI Agent, Developer
   (Context: Phase 6 - Screenshot/Photo Synchronization)

 WHAT:
   Dependency client for photo library observation.
   Wraps PHPhotoLibrary to observe new photos and screenshots
   taken during recording sessions.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/PhotoLibraryClient.swift

 WHY:
   To provide a testable interface for photo library observation.
   Following TCA patterns, this allows mocking in tests while
   providing real implementation in production.
   
   This enables the app to:
   1. Detect photos/screenshots taken during recording
   2. Display them inline immediately
   3. Show them again during playback at the correct timestamp
 */

import ComposableArchitecture
import Foundation
import UIKit

// MARK: - Photo Asset

/// Represents a photo or screenshot from the photo library
struct PhotoAsset: Equatable, Sendable, Identifiable {
    /// Unique identifier from PHAsset
    var id: String
    
    /// When the photo was created
    var creationDate: Date
    
    /// Type of media (photo or screenshot)
    var mediaType: MediaType
    
    /// Local identifier for fetching the full image
    var localIdentifier: String
    
    enum MediaType: String, Equatable, Sendable, Codable {
        case photo
        case screenshot
    }
}

// MARK: - Photo Library Client

/// Dependency client for photo library observation
@DependencyClient
struct PhotoLibraryClient: Sendable {
    /// Request photo library authorization
    var requestAuthorization: @Sendable () async -> AuthorizationStatus = { .notDetermined }
    
    /// Get current authorization status
    var authorizationStatus: @Sendable () -> AuthorizationStatus = { .notDetermined }
    
    /// Start observing new photos and screenshots
    /// Returns a stream of new photo assets
    var observeNewPhotos: @Sendable () async -> AsyncStream<PhotoAsset> = { AsyncStream { $0.finish() } }
    
    /// Stop observing photo library changes
    var stopObserving: @Sendable () async -> Void = {}
    
    /// Fetch thumbnail image for an asset
    var fetchThumbnail: @Sendable (_ assetIdentifier: String, _ size: CGSize) async -> UIImage? = { _, _ in nil }
    
    /// Fetch full-size image for an asset
    var fetchFullImage: @Sendable (_ assetIdentifier: String) async -> UIImage? = { _ in nil }
    
    // MARK: - Types
    
    enum AuthorizationStatus: Equatable, Sendable {
        case notDetermined
        case restricted
        case denied
        case authorized
        case limited
    }
    
    enum Failure: Error, Equatable, Sendable {
        case notAuthorized
        case assetNotFound
        case fetchFailed
    }
}

// MARK: - Test Dependency Key

extension PhotoLibraryClient: TestDependencyKey {
    /// Preview implementation that simulates photo library
    static var previewValue: Self {
        let isObserving = LockIsolated(false)
        
        return Self(
            requestAuthorization: { .authorized },
            authorizationStatus: { .authorized },
            observeNewPhotos: {
                AsyncStream { continuation in
                    Task {
                        isObserving.setValue(true)
                        
                        /// Simulate periodic photo captures
                        var photoCount = 0
                        while isObserving.value {
                            try? await Task.sleep(for: .seconds(5))
                            guard isObserving.value else { break }
                            
                            photoCount += 1
                            let asset = PhotoAsset(
                                id: "preview-\(photoCount)",
                                creationDate: Date(),
                                mediaType: photoCount % 2 == 0 ? .screenshot : .photo,
                                localIdentifier: "preview-\(photoCount)"
                            )
                            continuation.yield(asset)
                        }
                        
                        continuation.finish()
                    }
                }
            },
            stopObserving: {
                isObserving.setValue(false)
            },
            fetchThumbnail: { _, _ in
                /// Return a placeholder image for previews
                UIImage(systemName: "photo")
            },
            fetchFullImage: { _ in
                /// Return a placeholder image for previews
                UIImage(systemName: "photo.fill")
            }
        )
    }
    
    /// Test implementation with unimplemented closures
    static let testValue = Self()
}

// MARK: - Dependency Values Extension

extension DependencyValues {
    /// Access the photo library client
    var photoLibrary: PhotoLibraryClient {
        get { self[PhotoLibraryClient.self] }
        set { self[PhotoLibraryClient.self] = newValue }
    }
}