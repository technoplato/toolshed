/**
 HOW:
   Use in SwiftUI views with StoreOf<FullscreenTranscriptFeature>.
   Presented as a fullscreen modal when user double-taps with two fingers.
   
   [Inputs]
   - liveTranscription: Shared reference to LiveTranscriptionState from parent
   
   [Outputs]
   - Full screen transcript display with pinch-to-zoom
   - Delegate action for dismissal
   
   [Side Effects]
   - Persists text size preference to UserDefaults

 WHO:
   AI Agent, Developer
   (Context: TCA reducer for fullscreen transcript viewing)

 WHAT:
   TCA reducer for displaying transcripts in fullscreen with pinch-to-zoom.
   Uses @Shared for:
   - liveTranscription: Derived from parent, auto-syncs transcription updates
   - textSize: Persisted to UserDefaults
   
   Entry/exit via two-finger double-tap gesture.
   
   **Pattern Source:** Recipe 4 in swift-sharing-state-comprehensive-guide.md
   Child receives derived @Shared reference from parent, changes propagate automatically.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-11
   [Change Log:
     - 2025-12-11: Migrated to use @Shared(.liveTranscription) for automatic sync
   ]

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderApp/Features/FullscreenTranscriptFeature.swift

 WHY:
   To provide a distraction-free reading experience for transcripts.
   Inspired by Otter.ai's fullscreen mode but without settings UI.
   
   Using @Shared for liveTranscription ensures:
   - Automatic synchronization with parent's transcription updates
   - No manual syncing needed in parent reducer
   - Follows TCA best practices for shared state
 */

import ComposableArchitecture
import Foundation
import Sharing

@Reducer
struct FullscreenTranscriptFeature {
    
    // MARK: - Constants
    
    /// Minimum text size (16pt)
    static let minTextSize: Double = 16.0
    
    /// Maximum text size (48pt)
    static let maxTextSize: Double = 48.0
    
    /// Default text size (24pt)
    static let defaultTextSize: Double = 24.0
    
    // MARK: - State
    
    @ObservableState
    struct State: Equatable, Sendable {
        /// Live transcription state - shared with parent (RecordingFeature)
        /// This is a derived reference that auto-syncs with parent updates
        @Shared(.liveTranscription) var liveTranscription: LiveTranscriptionState
        
        /// The current text size (persisted to UserDefaults)
        @Shared(.fullscreenTextSize) var textSize: Double
        
        /// Whether auto-scroll is enabled
        var isAutoScrollEnabled: Bool = true
        
        /// Convenience accessors for the view
        var segments: [TranscriptionSegment] {
            liveTranscription.segments
        }
        
        var words: [TimestampedWord] {
            liveTranscription.words
        }
        
        var volatileText: String? {
            liveTranscription.volatileText
        }
        
        var currentTime: TimeInterval {
            liveTranscription.currentTime
        }
        
        var currentWordIndex: Int? {
            liveTranscription.currentWordIndex
        }
        
        /// Initialize with shared reference from parent
        init(liveTranscription: Shared<LiveTranscriptionState>) {
            self._liveTranscription = liveTranscription
        }
        
        /// Default initializer for previews/tests
        init() {
            // Uses default from SharedKey
        }
    }
    
    // MARK: - Action
    
    enum Action: Sendable, BindableAction {
        /// Binding action for @Shared state
        case binding(BindingAction<State>)
        
        /// User pinched to zoom - adjust text size
        case pinchGestureChanged(scale: Double)
        
        /// User double-tapped with two fingers to exit
        case twoFingerDoubleTapped
        
        /// User scrolled manually
        case userDidScroll
        
        /// User tapped resume auto-scroll
        case resumeAutoScrollTapped
        
        /// Delegate actions for parent feature
        case delegate(Delegate)
        
        enum Delegate: Equatable, Sendable {
            case didClose
        }
    }
    
    // MARK: - Reducer Body
    
    var body: some Reducer<State, Action> {
        BindingReducer()
        
        Reduce { state, action in
            switch action {
            case .binding:
                return .none
                
            case let .pinchGestureChanged(scale):
                /// The scale is already the ratio of new size to current size
                /// So we just multiply current size by scale and clamp
                let newSize = min(max(state.textSize * scale, Self.minTextSize), Self.maxTextSize)
                state.$textSize.withLock { $0 = newSize }
                return .none
                
            case .twoFingerDoubleTapped:
                return .send(.delegate(.didClose))
                
            case .userDidScroll:
                state.isAutoScrollEnabled = false
                return .none
                
            case .resumeAutoScrollTapped:
                state.isAutoScrollEnabled = true
                return .none
                
            case .delegate:
                return .none
            }
        }
    }
}