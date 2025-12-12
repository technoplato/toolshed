/**
 HOW:
   Use in SwiftUI views with StoreOf<FullscreenImageFeature>.
   Presented as a fullscreen modal when user double-taps an image.
   
   [Inputs]
   - assetIdentifier: The Photos library asset ID
   - mediaId: The UUID of the TimestampedMedia
   
   [Outputs]
   - Full resolution image display
   - Delegate action for dismissal
   
   [Side Effects]
   - Fetches full resolution image from Photos library

 WHO:
   AI Agent, Developer
   (Context: TCA reducer for fullscreen image viewing)

 WHAT:
   TCA reducer for displaying images in fullscreen with zoom/pan support.
   Uses @Presents pattern for modal presentation from parent.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/FullscreenImageFeature.swift

 WHY:
   To provide a proper TCA-based fullscreen image viewer that follows
   tree-based navigation patterns with @Presents and PresentationAction.
 */

import ComposableArchitecture
import Foundation
import UIKit

@Reducer
struct FullscreenImageFeature {
    
    // MARK: - State
    
    @ObservableState
    struct State: Equatable, Sendable {
        /// The Photos library asset identifier
        let assetIdentifier: String
        
        /// The UUID of the TimestampedMedia
        let mediaId: UUID
        
        /// The loaded full-resolution image
        var image: UIImage?
        
        /// Whether the image is currently loading
        var isLoading: Bool = true
    }
    
    // MARK: - Action
    
    enum Action: Sendable {
        /// View appeared - start loading the image
        case onAppear
        
        /// Image finished loading
        case imageLoaded(UIImage?)
        
        /// User tapped the close button
        case closeButtonTapped
        
        /// Delegate actions for parent feature
        case delegate(Delegate)
        
        enum Delegate: Equatable, Sendable {
            case didClose
        }
    }
    
    // MARK: - Dependencies
    
    @Dependency(\.photoLibrary) var photoLibrary
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        Reduce { state, action in
            switch action {
            case .onAppear:
                state.isLoading = true
                return .run { [assetId = state.assetIdentifier] send in
                    let image = await photoLibrary.fetchFullImage(assetId)
                    await send(.imageLoaded(image))
                }
                
            case let .imageLoaded(image):
                state.image = image
                state.isLoading = false
                return .none
                
            case .closeButtonTapped:
                return .send(.delegate(.didClose))
                
            case .delegate:
                return .none
            }
        }
    }
}