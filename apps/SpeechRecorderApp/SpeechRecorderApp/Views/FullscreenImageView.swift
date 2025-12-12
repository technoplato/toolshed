/**
 HOW:
   Present as fullscreen cover from PlaybackView.
   
   [Inputs]
   - StoreOf<FullscreenImageFeature>
   
   [Outputs]
   - Fullscreen image with close button
   
   [Side Effects]
   - None

 WHO:
   AI Agent, Developer

 WHAT:
   SwiftUI view for displaying fullscreen images with zoom support.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Views/FullscreenImageView.swift

 WHY:
   To display images captured during recording in fullscreen.
 */

import ComposableArchitecture
import SwiftUI

struct FullscreenImageView: View {
    @Bindable var store: StoreOf<FullscreenImageFeature>
    
    var body: some View {
        NavigationStack {
            ZStack {
                Color.black.ignoresSafeArea()
                
                if store.isLoading {
                    ProgressView()
                        .tint(.white)
                } else if let image = store.image {
                    Image(uiImage: image)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                } else {
                    VStack {
                        Image(systemName: "photo")
                            .font(.largeTitle)
                            .foregroundColor(.gray)
                        Text("Unable to load image")
                            .foregroundColor(.gray)
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        store.send(.closeButtonTapped)
                    }
                }
            }
            .toolbarBackground(.visible, for: .navigationBar)
            .toolbarBackground(Color.black.opacity(0.8), for: .navigationBar)
            .toolbarColorScheme(.dark, for: .navigationBar)
        }
        .onAppear {
            store.send(.onAppear)
        }
    }
}

// MARK: - Preview

#Preview {
    FullscreenImageView(
        store: Store(
            initialState: FullscreenImageFeature.State(
                assetIdentifier: "preview-asset",
                mediaId: UUID()
            )
        ) {
            FullscreenImageFeature()
        }
    )
}