/**
 HOW:
   Run tests with: `xcodebuild test -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 17'`
   Or use SweetPad: `sweetpad.build.test`
   
   [Inputs]
   - None (unit tests)
   
   [Outputs]
   - Test results
   
   [Side Effects]
   - None (uses mocked dependencies)

 WHO:
   AI Agent, Developer
   (Context: TDD for PhotoLibraryClient dependency)

 WHAT:
   Unit tests for the PhotoLibraryClient dependency.
   Tests authorization, photo observation, and thumbnail fetching.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/PhotoLibraryClientTests.swift

 WHY:
   TDD approach - write tests first to define expected behavior.
   These tests verify the PhotoLibraryClient handles all
   photo library operations correctly.
 */

import ComposableArchitecture
import Foundation
import Testing
import UIKit
@testable import SpeechRecorderApp

@Suite("PhotoLibraryClient Tests")
struct PhotoLibraryClientTests {
    
    // MARK: - Authorization Tests
    
    @Test("Request authorization returns authorized status")
    func requestAuthorizationReturnsAuthorized() async {
        let client = PhotoLibraryClient(
            requestAuthorization: { .authorized },
            authorizationStatus: { .authorized },
            observeNewPhotos: { AsyncStream { _ in } },
            stopObserving: { },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { _ in nil }
        )
        
        let status = await client.requestAuthorization()
        #expect(status == .authorized)
    }
    
    @Test("Request authorization returns denied status")
    func requestAuthorizationReturnsDenied() async {
        let client = PhotoLibraryClient(
            requestAuthorization: { .denied },
            authorizationStatus: { .denied },
            observeNewPhotos: { AsyncStream { _ in } },
            stopObserving: { },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { _ in nil }
        )
        
        let status = await client.requestAuthorization()
        #expect(status == .denied)
    }
    
    @Test("Request authorization returns limited status")
    func requestAuthorizationReturnsLimited() async {
        let client = PhotoLibraryClient(
            requestAuthorization: { .limited },
            authorizationStatus: { .limited },
            observeNewPhotos: { AsyncStream { _ in } },
            stopObserving: { },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { _ in nil }
        )
        
        let status = await client.requestAuthorization()
        #expect(status == .limited)
    }
    
    @Test("Authorization status returns current status")
    func authorizationStatusReturnsCurrent() {
        let client = PhotoLibraryClient(
            requestAuthorization: { .authorized },
            authorizationStatus: { .restricted },
            observeNewPhotos: { AsyncStream { _ in } },
            stopObserving: { },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { _ in nil }
        )
        
        let status = client.authorizationStatus()
        #expect(status == .restricted)
    }
    
    // MARK: - Photo Observation Tests
    
    @Test("Observe new photos returns stream of photo assets")
    func observeNewPhotosReturnsStream() async {
        let testAsset = PhotoAsset(
            id: "test-1",
            creationDate: Date(),
            mediaType: .photo,
            localIdentifier: "test-1"
        )
        
        let client = PhotoLibraryClient(
            requestAuthorization: { .authorized },
            authorizationStatus: { .authorized },
            observeNewPhotos: {
                AsyncStream { continuation in
                    continuation.yield(testAsset)
                    continuation.finish()
                }
            },
            stopObserving: { },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { _ in nil }
        )
        
        var receivedAssets: [PhotoAsset] = []
        for await asset in await client.observeNewPhotos() {
            receivedAssets.append(asset)
        }
        
        #expect(receivedAssets.count == 1)
        #expect(receivedAssets.first?.id == "test-1")
        #expect(receivedAssets.first?.mediaType == .photo)
    }
    
    @Test("Observe new photos detects screenshots")
    func observeNewPhotosDetectsScreenshots() async {
        let screenshotAsset = PhotoAsset(
            id: "screenshot-1",
            creationDate: Date(),
            mediaType: .screenshot,
            localIdentifier: "screenshot-1"
        )
        
        let client = PhotoLibraryClient(
            requestAuthorization: { .authorized },
            authorizationStatus: { .authorized },
            observeNewPhotos: {
                AsyncStream { continuation in
                    continuation.yield(screenshotAsset)
                    continuation.finish()
                }
            },
            stopObserving: { },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { _ in nil }
        )
        
        var receivedAssets: [PhotoAsset] = []
        for await asset in await client.observeNewPhotos() {
            receivedAssets.append(asset)
        }
        
        #expect(receivedAssets.first?.mediaType == .screenshot)
    }
    
    @Test("Stop observing terminates stream")
    func stopObservingTerminatesStream() async {
        let stopCalled = LockIsolated(false)
        
        let client = PhotoLibraryClient(
            requestAuthorization: { .authorized },
            authorizationStatus: { .authorized },
            observeNewPhotos: { AsyncStream { _ in } },
            stopObserving: { stopCalled.setValue(true) },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { _ in nil }
        )
        
        await client.stopObserving()
        
        #expect(stopCalled.value)
    }
    
    // MARK: - Thumbnail Fetching Tests
    
    @Test("Fetch thumbnail returns image for valid asset")
    func fetchThumbnailReturnsImage() async {
        let testImage = UIImage(systemName: "photo")!
        
        let client = PhotoLibraryClient(
            requestAuthorization: { .authorized },
            authorizationStatus: { .authorized },
            observeNewPhotos: { AsyncStream { _ in } },
            stopObserving: { },
            fetchThumbnail: { identifier, size in
                if identifier == "valid-asset" {
                    return testImage
                }
                return nil
            },
            fetchFullImage: { _ in nil }
        )
        
        let thumbnail = await client.fetchThumbnail("valid-asset", CGSize(width: 100, height: 100))
        
        #expect(thumbnail != nil)
    }
    
    @Test("Fetch thumbnail returns nil for invalid asset")
    func fetchThumbnailReturnsNilForInvalid() async {
        let client = PhotoLibraryClient(
            requestAuthorization: { .authorized },
            authorizationStatus: { .authorized },
            observeNewPhotos: { AsyncStream { _ in } },
            stopObserving: { },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { _ in nil }
        )
        
        let thumbnail = await client.fetchThumbnail("invalid-asset", CGSize(width: 100, height: 100))
        
        #expect(thumbnail == nil)
    }
    
    @Test("Fetch full image returns image for valid asset")
    func fetchFullImageReturnsImage() async {
        let testImage = UIImage(systemName: "photo.fill")!
        
        let client = PhotoLibraryClient(
            requestAuthorization: { .authorized },
            authorizationStatus: { .authorized },
            observeNewPhotos: { AsyncStream { _ in } },
            stopObserving: { },
            fetchThumbnail: { _, _ in nil },
            fetchFullImage: { identifier in
                if identifier == "valid-asset" {
                    return testImage
                }
                return nil
            }
        )
        
        let image = await client.fetchFullImage("valid-asset")
        
        #expect(image != nil)
    }
}

// MARK: - PhotoAsset Tests

@Suite("PhotoAsset Tests")
struct PhotoAssetTests {
    
    @Test("PhotoAsset is identifiable")
    func photoAssetIsIdentifiable() {
        let asset = PhotoAsset(
            id: "test-id",
            creationDate: Date(),
            mediaType: .photo,
            localIdentifier: "local-id"
        )
        
        #expect(asset.id == "test-id")
    }
    
    @Test("PhotoAsset is equatable")
    func photoAssetIsEquatable() {
        let date = Date()
        let asset1 = PhotoAsset(
            id: "test-id",
            creationDate: date,
            mediaType: .photo,
            localIdentifier: "local-id"
        )
        let asset2 = PhotoAsset(
            id: "test-id",
            creationDate: date,
            mediaType: .photo,
            localIdentifier: "local-id"
        )
        
        #expect(asset1 == asset2)
    }
    
    @Test("PhotoAsset media types are distinct")
    func photoAssetMediaTypesAreDistinct() {
        let photo = PhotoAsset(
            id: "photo-1",
            creationDate: Date(),
            mediaType: .photo,
            localIdentifier: "photo-1"
        )
        let screenshot = PhotoAsset(
            id: "screenshot-1",
            creationDate: Date(),
            mediaType: .screenshot,
            localIdentifier: "screenshot-1"
        )
        
        #expect(photo.mediaType != screenshot.mediaType)
        #expect(photo.mediaType == .photo)
        #expect(screenshot.mediaType == .screenshot)
    }
}