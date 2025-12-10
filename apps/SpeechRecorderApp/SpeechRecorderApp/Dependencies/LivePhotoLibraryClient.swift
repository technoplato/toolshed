/**
 HOW:
   This is the live implementation of PhotoLibraryClient.
   It uses PHPhotoLibrary to observe new photos and screenshots.
   
   [Inputs]
   - PHPhotoLibrary for observing changes
   - PHImageManager for fetching images
   
   [Outputs]
   - Real photo assets from the device's photo library
   
   [Side Effects]
   - Registers as PHPhotoLibraryChangeObserver
   - Fetches images from photo library

 WHO:
   AI Agent, Developer
   (Context: Phase 6 - Screenshot/Photo Synchronization)

 WHAT:
   Live implementation of PhotoLibraryClient using PhotoKit.
   Observes PHPhotoLibrary for new photos and screenshots.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Dependencies/LivePhotoLibraryClient.swift

 WHY:
   To provide real photo library observation in production.
   Uses PHPhotoLibraryChangeObserver to detect new photos/screenshots
   taken during recording sessions.
 */

import ComposableArchitecture
import Foundation
import Photos
import UIKit

// MARK: - Live Photo Library Client

extension PhotoLibraryClient: DependencyKey {
    static var liveValue: Self {
        /// Actor to manage photo library observation state
        let observer = PhotoLibraryObserver()
        
        return Self(
            requestAuthorization: {
                let status = await PHPhotoLibrary.requestAuthorization(for: .readWrite)
                return status.toClientStatus()
            },
            authorizationStatus: {
                PHPhotoLibrary.authorizationStatus(for: .readWrite).toClientStatus()
            },
            observeNewPhotos: {
                await observer.startObserving()
            },
            stopObserving: {
                await observer.stopObserving()
            },
            fetchThumbnail: { assetIdentifier, size in
                await fetchImage(for: assetIdentifier, targetSize: size)
            },
            fetchFullImage: { assetIdentifier in
                await fetchImage(for: assetIdentifier, targetSize: PHImageManagerMaximumSize)
            }
        )
    }
}

// MARK: - Photo Library Observer

/// Actor that manages PHPhotoLibrary observation
private actor PhotoLibraryObserver {
    private var changeObserver: PhotoChangeObserver?
    private var continuation: AsyncStream<PhotoAsset>.Continuation?
    private var lastFetchDate: Date?
    
    func startObserving() -> AsyncStream<PhotoAsset> {
        /// Stop any existing observation
        stopObservingSync()
        
        /// Record the start time to filter only new photos
        lastFetchDate = Date()
        
        return AsyncStream { continuation in
            self.continuation = continuation
            
            /// Create and register the change observer
            let observer = PhotoChangeObserver { [weak self] in
                Task {
                    await self?.checkForNewPhotos()
                }
            }
            
            self.changeObserver = observer
            PHPhotoLibrary.shared().register(observer)
            
            continuation.onTermination = { [weak self] _ in
                Task {
                    await self?.stopObserving()
                }
            }
        }
    }
    
    func stopObserving() {
        stopObservingSync()
    }
    
    private func stopObservingSync() {
        if let observer = changeObserver {
            PHPhotoLibrary.shared().unregisterChangeObserver(observer)
            changeObserver = nil
        }
        continuation?.finish()
        continuation = nil
    }
    
    private func checkForNewPhotos() {
        guard let lastDate = lastFetchDate else { return }
        
        /// Fetch photos created after our start time
        let fetchOptions = PHFetchOptions()
        fetchOptions.predicate = NSPredicate(
            format: "creationDate > %@",
            lastDate as NSDate
        )
        fetchOptions.sortDescriptors = [
            NSSortDescriptor(key: "creationDate", ascending: true)
        ]
        
        let results = PHAsset.fetchAssets(with: .image, options: fetchOptions)
        
        results.enumerateObjects { asset, _, _ in
            let photoAsset = PhotoAsset(
                id: asset.localIdentifier,
                creationDate: asset.creationDate ?? Date(),
                mediaType: self.determineMediaType(for: asset),
                localIdentifier: asset.localIdentifier
            )
            
            self.continuation?.yield(photoAsset)
        }
        
        /// Update last fetch date to avoid duplicates
        lastFetchDate = Date()
    }
    
    private func determineMediaType(for asset: PHAsset) -> PhotoAsset.MediaType {
        /// Check if this is a screenshot
        /// Screenshots typically have specific characteristics:
        /// - mediaSubtypes contains .photoScreenshot (iOS 9+)
        if asset.mediaSubtypes.contains(.photoScreenshot) {
            return .screenshot
        }
        return .photo
    }
}

// MARK: - Photo Change Observer

/// NSObject wrapper for PHPhotoLibraryChangeObserver
private final class PhotoChangeObserver: NSObject, PHPhotoLibraryChangeObserver, @unchecked Sendable {
    private let onChange: @Sendable () -> Void
    
    init(onChange: @escaping @Sendable () -> Void) {
        self.onChange = onChange
        super.init()
    }
    
    func photoLibraryDidChange(_ changeInstance: PHChange) {
        onChange()
    }
}

// MARK: - Image Fetching

private func fetchImage(for assetIdentifier: String, targetSize: CGSize) async -> UIImage? {
    /// Fetch the asset
    let fetchResult = PHAsset.fetchAssets(
        withLocalIdentifiers: [assetIdentifier],
        options: nil
    )
    
    guard let asset = fetchResult.firstObject else {
        return nil
    }
    
    /// Request the image
    return await withCheckedContinuation { continuation in
        let options = PHImageRequestOptions()
        options.deliveryMode = .highQualityFormat
        options.isNetworkAccessAllowed = true
        options.isSynchronous = false
        
        PHImageManager.default().requestImage(
            for: asset,
            targetSize: targetSize,
            contentMode: .aspectFit,
            options: options
        ) { image, _ in
            continuation.resume(returning: image)
        }
    }
}

// MARK: - Authorization Status Conversion

private extension PHAuthorizationStatus {
    func toClientStatus() -> PhotoLibraryClient.AuthorizationStatus {
        switch self {
        case .notDetermined:
            return .notDetermined
        case .restricted:
            return .restricted
        case .denied:
            return .denied
        case .authorized:
            return .authorized
        case .limited:
            return .limited
        @unknown default:
            return .notDetermined
        }
    }
}