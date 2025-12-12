# Comprehensive Guide to Swift Composable Architecture Best Practices

This guide provides a complete reference for building applications with Point-Free's Swift Composable Architecture (TCA). It covers reducer patterns, navigation, effects, modularization, testing strategies, and dependency management, with examples extracted from official documentation, case studies, SyncUps, and isowords.

> **📚 Source References**
>
> This guide is compiled from official Point-Free documentation and production examples. All code examples include references to both:
>
> - **Local paths**: Files in our `references/` submodules for offline exploration
> - **GitHub links**: Official repositories for the latest versions
>
> **Reference Repositories:**
>
> - Swift Composable Architecture: [`references/swift-composable-architecture/`](../references/swift-composable-architecture/) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture)
> - SyncUps Example: [`references/swift-composable-architecture/Examples/SyncUps/`](../references/swift-composable-architecture/Examples/SyncUps/) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/tree/main/Examples/SyncUps)
> - Case Studies: [`references/swift-composable-architecture/Examples/CaseStudies/`](../references/swift-composable-architecture/Examples/CaseStudies/) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/tree/main/Examples/CaseStudies)
> - isowords: [`references/isowords/`](../references/isowords/) | [GitHub](https://github.com/pointfreeco/isowords)
> - Swift Sharing: [`references/swift-sharing/`](../references/swift-sharing/) | [GitHub](https://github.com/pointfreeco/swift-sharing)

## Table of Contents

- [Comprehensive Guide to Swift Composable Architecture Best Practices](#comprehensive-guide-to-swift-composable-architecture-best-practices)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
    - [Core Principles](#core-principles)
    - [Key Benefits](#key-benefits)
  - [Reducer Fundamentals](#reducer-fundamentals)
    - [The @Reducer Macro](#the-reducer-macro)
    - [@ObservableState for State](#observablestate-for-state)
    - [Action Patterns](#action-patterns)
    - [Reducer Body Composition](#reducer-body-composition)
  - [Effect Patterns](#effect-patterns)
    - [Basic Effects with .run](#basic-effects-with-run)
    - [Effect Cancellation](#effect-cancellation)
    - [Long-Living Effects](#long-living-effects)
    - [Debouncing Effects](#debouncing-effects)
    - [Effect Merging](#effect-merging)
  - [Navigation Patterns](#navigation-patterns)
    - [Stack-Based Navigation](#stack-based-navigation)
    - [Multiple Destinations (Sheets, Alerts, Popovers)](#multiple-destinations-sheets-alerts-popovers)
    - [Programmatic Dismissal](#programmatic-dismissal)
    - [Delegate Actions for Child-to-Parent Communication](#delegate-actions-for-child-to-parent-communication)
  - [Dependency Management](#dependency-management)
    - [The @Dependency Property Wrapper](#the-dependency-property-wrapper)
    - [Overriding Dependencies in Tests](#overriding-dependencies-in-tests)
  - [Comprehensive Dependency Client Examples](#comprehensive-dependency-client-examples)
    - [Example 1: Build (Minimal)](#example-1-build-minimal---single-file)
    - [Example 2: DeviceId (Minimal)](#example-2-deviceid-minimal---icloud-persistence)
    - [Example 3: FeedbackGeneratorClient (Simple)](#example-3-feedbackgeneratorclient-simple---haptics)
    - [Example 4: FileClient (Simple)](#example-4-fileclient-simple---json-helpers)
    - [Example 5: RemoteNotificationsClient (Simple)](#example-5-remotenotificationsclient-simple---push-notifications)
    - [Example 6: UserDefaultsClient (Medium)](#example-6-userdefaultsclient-medium---typed-key-value)
    - [Example 7: UIApplicationClient (Medium)](#example-7-uiapplicationclient-medium---mainactor)
    - [Example 8: LowPowerModeClient (AsyncStream)](#example-8-lowpowermodeclient-asyncstream-based)
    - [Example 9: AudioPlayerClient (Complex)](#example-9-audioplayerclient-complex---actor-based)
    - [Example 10: ComposableStoreKit (Complex)](#example-10-composablestorekit-complex---delegate-bridging)
    - [Example 11: ComposableGameCenter (Very Complex)](#example-11-composablegamecenter-very-complex---nested-clients)
    - [Example 12: ComposableUserNotifications (Medium)](#example-12-composableusernotifications-medium---delegate-events)
    - [Example 13: ApiClient (Complex)](#example-13-apiclient-complex---route-based-override)
    - [Example 14: DictionaryClient (Simple)](#example-14-dictionaryclient-simple---optional-lookup)
    - [Example 15: ServerConfigClient (Simple)](#example-15-serverconfigclient-simple---factory-pattern)
    - [Example 16: LocalDatabaseClient (Complex)](#example-16-localdatabaseclient-complex---database-with-mock)
    - [Dependency Client Pattern Summary](#dependency-client-pattern-summary)
    - [Best Practices for Dependency Clients](#best-practices-for-dependency-clients)
  - [Testing Strategies](#testing-strategies)
    - [TestStore Basics](#teststore-basics)
    - [Exhaustive vs Non-Exhaustive Testing](#exhaustive-vs-non-exhaustive-testing)
    - [Testing Effects with TestClock](#testing-effects-with-testclock)
    - [Testing Navigation](#testing-navigation)
    - [Testing Shared State](#testing-shared-state)
    - [Integration Testing](#integration-testing)
  - [Modularization Patterns](#modularization-patterns)
    - [isowords Module Structure](#isowords-module-structure)
    - [Feature Module Pattern](#feature-module-pattern)
    - [Shared Models Module](#shared-models-module)
    - [Client Modules](#client-modules)
    - [Helper Modules](#helper-modules)
    - [Preview Apps](#preview-apps)
  - [Higher-Order Reducers](#higher-order-reducers)
    - [Filter Reducer](#filter-reducer)
    - [Recursive Reducers](#recursive-reducers)
    - [Custom Reducer Modifiers](#custom-reducer-modifiers)
  - [Binding Patterns](#binding-patterns)
    - [BindingReducer](#bindingreducer)
    - [Two-Way Bindings in Views](#two-way-bindings-in-views)
    - [onChange Modifier](#onchange-modifier)
  - [Real-World Patterns from isowords](#real-world-patterns-from-isowords)
    - [Complex Game State Management](#complex-game-state-management)
    - [App Delegate Integration](#app-delegate-integration)
    - [Settings Feature Pattern](#settings-feature-pattern)
  - [Best Practices Summary](#best-practices-summary)
    - [State Design](#state-design)
    - [Action Design](#action-design)
    - [Effect Design](#effect-design)
    - [Testing](#testing)
    - [Modularization](#modularization)
  - [Reference Quick Links](#reference-quick-links)
    - [Local Repository References](#local-repository-references)
    - [External Documentation Links](#external-documentation-links)
    - [Key Source Files](#key-source-files)

---

## Overview

> **📖 Source Documentation**
>
> - Local: [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/GettingStarted.md`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/GettingStarted.md)
> - External: [TCA Documentation](https://pointfreeco.github.io/swift-composable-architecture/main/documentation/composablearchitecture/)

The Composable Architecture (TCA) is a library for building applications in a consistent and understandable way, with composition, testing, and ergonomics in mind. It can be used in SwiftUI, UIKit, and more, and on any Apple platform (iOS, macOS, tvOS, and watchOS).

### Core Principles

1. **Single Source of Truth**: The entire app's state is held in a single `Store`
2. **Unidirectional Data Flow**: State changes only through actions processed by reducers
3. **Explicit Side Effects**: All effects are returned as values from reducers
4. **Controlled Dependencies**: External services are injected and controllable
5. **Composability**: Large features are built from smaller, reusable components

### Key Benefits

- **Testability**: Every aspect of the application can be tested, including effects
- **Modularity**: Features can be developed and tested in isolation
- **Predictability**: State changes are deterministic and traceable
- **Ergonomics**: Modern Swift features like macros reduce boilerplate

---

## Reducer Fundamentals

> **📖 Source Documentation**
>
> - Local: [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Reducers.md`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Reducers.md)
> - Case Study: [`references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Counter.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Counter.swift)
> - GitHub: [Counter Case Study](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Counter.swift)

### The @Reducer Macro

The `@Reducer` macro is the foundation of every TCA feature. It generates conformance to the `Reducer` protocol and provides compile-time safety.

```swift
// Source: references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Counter.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Counter.swift

@Reducer
struct CounterFeature {
  @ObservableState
  struct State: Equatable {
    var count = 0
  }

  enum Action {
    case decrementButtonTapped
    case incrementButtonTapped
  }

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .decrementButtonTapped:
        state.count -= 1
        return .none
      case .incrementButtonTapped:
        state.count += 1
        return .none
      }
    }
  }
}
```

**Key Points:**
- `@Reducer` macro annotates the feature type
- `State` is nested inside and marked with `@ObservableState`
- `Action` is an enum of all possible user actions
- `body` returns a reducer that processes actions

### @ObservableState for State

The `@ObservableState` macro enables SwiftUI observation without `@Published` properties:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpsList.swift:17-26
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpsList.swift#L17-L26

@ObservableState
struct State: Equatable {
  @Presents var destination: Destination.State?
  @Shared(.syncUps) var syncUps: IdentifiedArrayOf<SyncUp>
}
```

**Key Points:**
- Replaces `@Published` for automatic view updates
- Works with `@Presents` for optional child state
- Works with `@Shared` for shared/persisted state
- State must conform to `Equatable` for testing

### Action Patterns

Actions should be descriptive and represent user intent or system events:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpDetail.swift:27-45
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpDetail.swift#L27-L45

enum Action: Sendable {
  case cancelEditButtonTapped
  case deleteButtonTapped
  case deleteMeetings(atOffsets: IndexSet)
  case destination(PresentationAction<Destination.Action>)
  case doneEditingButtonTapped
  case editButtonTapped
  case startMeetingButtonTapped
  
  /// Delegate actions for parent communication
  @CasePathable
  enum Delegate {
    case startMeeting(syncUp: SyncUp)
  }
  case delegate(Delegate)
}
```

**Best Practices:**
- Use past tense for user actions (`buttonTapped`, not `tapButton`)
- Group related actions with nested enums
- Use `Delegate` enum for child-to-parent communication
- Mark actions as `Sendable` for concurrency safety

### Reducer Body Composition

Complex reducers are composed from smaller pieces:

```swift
// Source: references/isowords/Sources/GameCore/GameCore.swift (simplified)
// GitHub: https://github.com/pointfreeco/isowords/blob/main/Sources/GameCore/GameCore.swift

@Reducer
struct Game {
  var body: some Reducer<State, Action> {
    /// Core game logic
    self.core
      /// React to state changes
      .onChange(of: \.selectedWord) { _, selectedWord in
        Reduce { state, _ in
          state.selectedWordIsValid = /* validation */
          return .none
        }
      }
      /// Handle presented destinations
      .ifLet(\.$destination, action: \.destination) {
        Destination.body
      }
  }

  /// Separate computed property for core logic
  @ReducerBuilder<State, Action>
  var core: some Reducer<State, Action> {
    Reduce { state, action in
      /// Main reducer logic
    }
    /// Compose child reducers
    Scope(state: \.wordSubmitButtonFeature, action: \.wordSubmitButton) {
      WordSubmitButtonFeature()
    }
  }
}
```

**Composition Operators:**
- `Reduce { }`: The main reducer logic
- `Scope(state:action:)`: Embed child reducer
- `.ifLet(\.$destination, action:)`: Optional child reducer
- `.forEach(\.path, action:)`: Collection of child reducers
- `.onChange(of:)`: React to state changes
- `CombineReducers { }`: Combine multiple reducers

---

## Effect Patterns

> **📖 Source Documentation**
>
> - Local: [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Effects.md`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Effects.md)
> - Case Studies: [`references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Basics.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Basics.swift)
> - GitHub: [Effects Case Studies](https://github.com/pointfreeco/swift-composable-architecture/tree/main/Examples/CaseStudies/SwiftUICaseStudies)

### Basic Effects with .run

The `.run` effect is the primary way to perform async work:

```swift
// Source: references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Basics.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Basics.swift

@Reducer
struct EffectsBasics {
  @Dependency(\.continuousClock) var clock
  @Dependency(\.factClient) var factClient

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .incrementButtonTapped:
        state.count += 1
        state.numberFactAlert = nil
        return .none

      case .numberFactButtonTapped:
        state.isNumberFactRequestInFlight = true
        state.numberFactAlert = nil
        return .run { [count = state.count] send in
          /// Perform async work
          try await self.clock.sleep(for: .seconds(1))
          let fact = try await self.factClient.fetch(count)
          /// Send result back to reducer
          await send(.numberFactResponse(.success(fact)))
        } catch: { error, send in
          /// Handle errors
          await send(.numberFactResponse(.failure(error)))
        }

      case let .numberFactResponse(.success(fact)):
        state.isNumberFactRequestInFlight = false
        state.numberFactAlert = fact
        return .none

      case .numberFactResponse(.failure):
        state.isNumberFactRequestInFlight = false
        return .none
      }
    }
  }
}
```

**Key Points:**
- Capture state values in the closure: `[count = state.count]`
- Use `send` to dispatch actions back to the reducer
- Handle errors with the `catch:` parameter
- Dependencies are accessed via `@Dependency`

### Effect Cancellation

Cancel in-flight effects using cancellation IDs:

```swift
// Source: references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Cancellation.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Cancellation.swift

@Reducer
struct EffectsCancellation {
  /// Define cancellation IDs as a private enum
  private enum CancelID { case factRequest }

  @Dependency(\.factClient) var factClient

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .cancelButtonTapped:
        state.isFactRequestInFlight = false
        /// Cancel the effect by ID
        return .cancel(id: CancelID.factRequest)

      case .stepperChanged(let value):
        state.count = value
        state.currentFact = nil
        state.isFactRequestInFlight = false
        /// Cancel any pending request when count changes
        return .cancel(id: CancelID.factRequest)

      case .factButtonTapped:
        state.isFactRequestInFlight = true
        state.currentFact = nil
        return .run { [count = state.count] send in
          let fact = try await self.factClient.fetch(count)
          await send(.factResponse(.success(fact)))
        } catch: { error, send in
          await send(.factResponse(.failure(error)))
        }
        /// Make the effect cancellable
        .cancellable(id: CancelID.factRequest)

      case let .factResponse(.success(fact)):
        state.isFactRequestInFlight = false
        state.currentFact = fact
        return .none

      case .factResponse(.failure):
        state.isFactRequestInFlight = false
        return .none
      }
    }
  }
}
```

**Key Points:**
- Define `CancelID` as a private enum for type safety
- Use `.cancellable(id:)` to make effects cancellable
- Use `.cancel(id:)` to cancel effects
- Cancellation is automatic when the store is deallocated

### Long-Living Effects

For effects that run for the lifetime of a feature:

```swift
// Source: references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-LongLiving.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-LongLiving.swift

@Reducer
struct LongLivingEffects {
  @Dependency(\.screenshots) var screenshots

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .task:
        /// Start long-living effect when view appears
        return .run { send in
          for await _ in await self.screenshots() {
            await send(.userDidTakeScreenshot)
          }
        }

      case .userDidTakeScreenshot:
        state.screenshotCount += 1
        return .none
      }
    }
  }
}

/// In the view
struct LongLivingEffectsView: View {
  let store: StoreOf<LongLivingEffects>

  var body: some View {
    Form {
      Text("Screenshots: \(store.screenshotCount)")
    }
    /// Start the effect when view appears
    .task { await store.send(.task).finish() }
  }
}
```

**Understanding the Pattern:**

This pattern ties an effect's lifetime to the view's lifetime using three key components:

1. **SwiftUI's `.task` modifier**: A built-in modifier that starts an async task when the view appears and automatically cancels it when the view disappears.

2. **`store.send(.task)`**: Sends the `.task` action to the store, which returns a `StoreTask` representing the effect. This is the handle to the running effect.

3. **`.finish()`**: Awaits the completion of the effect. This is the crucial piece that keeps the task alive.

**Why `.finish()` is Critical:**

Without `.finish()`, the task would return immediately after sending the action, and the effect would be orphaned:

```swift
// ❌ BAD - Effect is orphaned, may not be cancelled properly
.task { store.send(.task) }

// ✅ GOOD - Effect lifetime is tied to view lifetime
.task { await store.send(.task).finish() }
```

By awaiting `.finish()`, you ensure:
- The effect runs for the entire lifetime of the view
- The effect is properly cancelled when the view disappears (SwiftUI cancels the `.task` modifier's async context, which in turn cancels the TCA effect)
- No memory leaks or zombie effects

**Key Points:**
- Use `.task` action triggered by SwiftUI's `.task` modifier
- Use `await store.send(.task).finish()` to wait for effect completion
- The effect is automatically cancelled when the view disappears
- Use `for await` for async sequences
- The `.finish()` method is essential for proper lifecycle management

**Common Use Cases:**
- Listening to NotificationCenter notifications
- Observing system state changes (low power mode, network status)
- WebSocket connections
- Real-time data streams
- Timer-based updates

**How `.finish()` Works with Infinite AsyncSequences:**

A common question is: "If the effect is listening to an AsyncSequence that never ends (like NotificationCenter), how does `.finish()` ever complete?"

The answer is: **it doesn't complete naturally - it gets cancelled**. Here's the lifecycle:

```swift
// The effect runs an infinite loop
return .run { send in
  for await _ in await self.screenshots() {  // This loop never ends naturally
    await send(.userDidTakeScreenshotNotification)
  }
  // This line is never reached unless cancelled
}
```

**The Cancellation Flow:**

1. **View appears** → SwiftUI's `.task` modifier starts
2. **`.task` sends action** → `store.send(.task)` returns a `StoreTask`
3. **`.finish()` awaits** → The task is now "held" by the `.task` modifier
4. **Effect runs** → The `for await` loop listens to the AsyncSequence
5. **View disappears** → SwiftUI cancels the `.task` modifier's async context
6. **Cancellation propagates** → Swift's structured concurrency cancels the `StoreTask`
7. **Effect is cancelled** → The `for await` loop throws `CancellationError` and exits
8. **`.finish()` returns** → The await completes (via cancellation, not natural completion)

**Key Insight:** The `.finish()` method doesn't wait for the effect to "succeed" - it waits for the effect to **terminate**, whether by completion, error, or cancellation. For long-living effects, cancellation is the expected termination path.

**What Happens Without `.finish()`:**

```swift
// ❌ BAD - The task returns immediately
.task {
  store.send(.task)  // Fire and forget - returns immediately
  // The .task modifier's async context ends here
  // But the effect is still running somewhere!
}
```

Without `.finish()`:
- The `.task` modifier's async context ends immediately after `send()` returns
- The effect is now "orphaned" - it's running but not tied to the view's lifecycle
- When the view disappears, SwiftUI has nothing to cancel
- The effect may continue running indefinitely (memory leak, zombie effect)

**With `.finish()`:**

```swift
// ✅ GOOD - The task is held until cancelled
.task {
  await store.send(.task).finish()  // Awaits until effect terminates
  // This line is reached when the view disappears and the effect is cancelled
}
```

With `.finish()`:
- The `.task` modifier's async context is held open by the `await`
- When the view disappears, SwiftUI cancels this context
- The cancellation propagates to the `StoreTask`, which cancels the effect
- The `for await` loop receives `CancellationError` and exits
- `.finish()` returns, and the `.task` modifier completes cleanly

**Handling Cancellation and Cleanup Within Effects:**

When your effect needs to perform cleanup (close connections, release resources, save state), you need to detect and handle cancellation explicitly. Here are the patterns:

**Pattern 1: Using `defer` for Guaranteed Cleanup**

```swift
return .run { send in
  /// Setup resources
  let connection = await openWebSocketConnection()
  
  /// defer runs when the scope exits, whether normally or via cancellation
  defer {
    connection.close()
    print("Connection closed - cleanup complete")
  }
  
  /// This loop will exit when cancelled
  for await message in connection.messages {
    await send(.messageReceived(message))
  }
  /// If we reach here naturally, defer still runs
}
```

**Pattern 2: Using `do/catch` to Detect Cancellation**

```swift
return .run { send in
  let recorder = AudioRecorder()
  await recorder.startRecording()
  
  do {
    for await level in recorder.audioLevels {
      await send(.audioLevelChanged(level))
    }
  } catch is CancellationError {
    /// Cancellation detected - perform cleanup
    await recorder.stopRecording()
    await send(.recordingStopped)
    print("Recording stopped due to cancellation")
  } catch {
    /// Handle other errors
    await send(.recordingFailed(error))
  }
}
```

**Pattern 3: Combining `defer` and `do/catch`**

```swift
return .run { send in
  let session = await createSession()
  
  /// Guaranteed cleanup
  defer {
    session.invalidate()
  }
  
  do {
    for await event in session.events {
      await send(.sessionEvent(event))
    }
  } catch is CancellationError {
    /// Cancellation-specific handling (e.g., notify server)
    await session.notifyDisconnect(reason: .userCancelled)
  }
  /// defer runs after catch block completes
}
```

**Pattern 4: Using `withTaskCancellationHandler`**

For more complex scenarios where you need immediate notification of cancellation:

```swift
return .run { send in
  await withTaskCancellationHandler {
    /// Main work
    for await value in someAsyncSequence {
      await send(.valueReceived(value))
    }
  } onCancel: {
    /// Called immediately when cancellation is requested
    /// Note: This runs concurrently with the main work
    /// Use for signaling, not for cleanup that depends on main work state
    print("Cancellation requested!")
  }
}
```

**Pattern 5: Checking Cancellation Status**

For long-running loops that don't use `for await`:

```swift
return .run { send in
  while !Task.isCancelled {
    let data = await fetchNextBatch()
    await send(.batchReceived(data))
    try await Task.sleep(for: .seconds(1))
  }
  /// Loop exited due to cancellation
  await send(.streamEnded)
}
```

**Real-World Example: WebSocket with Cleanup**

```swift
@Reducer
struct WebSocketFeature {
  @Dependency(\.webSocket) var webSocket
  
  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .task:
        return .run { send in
          let socket = await self.webSocket.connect()
          
          /// Guaranteed cleanup on any exit
          defer {
            Task { await socket.close(code: .normalClosure) }
          }
          
          do {
            /// Send connected status
            await send(.connectionStatusChanged(.connected))
            
            /// Listen for messages until cancelled
            for await message in socket.messages {
              await send(.messageReceived(message))
            }
            
            /// Natural completion (server closed connection)
            await send(.connectionStatusChanged(.disconnected))
            
          } catch is CancellationError {
            /// View disappeared - clean disconnect
            await send(.connectionStatusChanged(.disconnected))
            
          } catch {
            /// Connection error
            await send(.connectionStatusChanged(.error(error)))
          }
        }
        
      case .messageReceived(let message):
        state.messages.append(message)
        return .none
        
      case .connectionStatusChanged(let status):
        state.connectionStatus = status
        return .none
      }
    }
  }
}
```

**Key Takeaways for Cleanup:**

| Technique | When to Use | Runs On |
|-----------|-------------|---------|
| `defer` | Guaranteed cleanup regardless of exit path | Scope exit (normal, error, or cancellation) |
| `catch is CancellationError` | Cancellation-specific logic | Only on cancellation |
| `withTaskCancellationHandler` | Immediate cancellation notification | Concurrently with main work |
| `Task.isCancelled` | Polling in non-async loops | Manual check points |

**Important Notes:**

1. **`defer` is your friend**: It runs regardless of how the scope exits, making it ideal for resource cleanup.

2. **`CancellationError` is thrown by `for await`**: When the task is cancelled, the async sequence's iterator throws `CancellationError`, causing the loop to exit.

3. **Cleanup order matters**: `defer` blocks run in reverse order of declaration, and they run after any `catch` blocks.

4. **Don't swallow cancellation**: If you catch `CancellationError`, the cancellation is handled. If you need to propagate it, rethrow it.

5. **Async cleanup in `defer`**: If you need async cleanup in `defer`, wrap it in a `Task`:
   ```swift
   defer {
     Task { await asyncCleanup() }
   }
   ```

### Debouncing Effects

Debounce rapid actions to prevent excessive work:

```swift
// Source: references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Debounce.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Debounce.swift

@Reducer
struct DebounceFeature {
  private enum CancelID { case search }

  @Dependency(\.mainQueue) var mainQueue
  @Dependency(\.searchClient) var searchClient

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case let .searchTextChanged(query):
        state.searchQuery = query
        guard !query.isEmpty else {
          state.results = []
          return .cancel(id: CancelID.search)
        }
        return .run { send in
          let results = try await self.searchClient.search(query)
          await send(.searchResponse(.success(results)))
        } catch: { error, send in
          await send(.searchResponse(.failure(error)))
        }
        /// Debounce for 300ms
        .debounce(id: CancelID.search, for: .milliseconds(300), scheduler: self.mainQueue)

      case let .searchResponse(.success(results)):
        state.results = results
        return .none

      case .searchResponse(.failure):
        state.results = []
        return .none
      }
    }
  }
}
```

**Key Points:**
- Use `.debounce(id:for:scheduler:)` to delay effect execution
- Subsequent actions with the same ID cancel previous debounced effects
- Requires a scheduler dependency for testability

### Effect Merging

Combine multiple effects:

```swift
// Merge multiple effects
return .merge(
  .run { send in
    await send(.firstEffectCompleted)
  },
  .run { send in
    await send(.secondEffectCompleted)
  }
)

// Concatenate effects (run sequentially)
return .concatenate(
  .run { send in
    await send(.firstEffectCompleted)
  },
  .run { send in
    await send(.secondEffectCompleted)
  }
)
```

---

## Navigation Patterns

> **📖 Source Documentation**
>
> - Local: [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Navigation.md`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Navigation.md)
> - Stack Navigation: [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/StackBasedNavigation.md`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/StackBasedNavigation.md)
> - Case Study: [`references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/04-NavigationStack.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/04-NavigationStack.swift)
> - GitHub: [Navigation Case Studies](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/04-NavigationStack.swift)

### Stack-Based Navigation

Use `@Reducer enum Path` for navigation stacks:

```swift
// Source: references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/04-NavigationStack.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/04-NavigationStack.swift

@Reducer
struct NavigationStackFeature {
  /// Define all possible navigation destinations
  @Reducer
  enum Path {
    case detail(DetailFeature)
    case settings(SettingsFeature)
    case profile(ProfileFeature)
  }

  @ObservableState
  struct State: Equatable {
    /// Stack of navigation destinations
    var path = StackState<Path.State>()
    var items: [Item] = []
  }

  enum Action {
    /// Stack actions
    case path(StackActionOf<Path>)
    case goToDetailButtonTapped(Item)
    case goToSettingsButtonTapped
  }

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case let .goToDetailButtonTapped(item):
        /// Push a new screen onto the stack
        state.path.append(.detail(DetailFeature.State(item: item)))
        return .none

      case .goToSettingsButtonTapped:
        state.path.append(.settings(SettingsFeature.State()))
        return .none

      case .path:
        return .none
      }
    }
    /// Compose path reducer
    .forEach(\.path, action: \.path)
  }
}

/// View with NavigationStack
struct NavigationStackView: View {
  @Bindable var store: StoreOf<NavigationStackFeature>

  var body: some View {
    NavigationStack(path: $store.scope(state: \.path, action: \.path)) {
      List(store.items) { item in
        /// Declarative navigation with state
        NavigationLink(state: NavigationStackFeature.Path.State.detail(
          DetailFeature.State(item: item)
        )) {
          Text(item.name)
        }
      }
    } destination: { store in
      /// Switch on destination type
      switch store.case {
      case let .detail(store):
        DetailView(store: store)
      case let .settings(store):
        SettingsView(store: store)
      case let .profile(store):
        ProfileView(store: store)
      }
    }
  }
}
```

**Key Points:**
- `@Reducer enum Path` defines all possible destinations
- `StackState<Path.State>` holds the navigation stack
- `.forEach(\.path, action: \.path)` composes child reducers
- `NavigationLink(state:)` for declarative navigation
- `store.case` for switching on destination type

### Multiple Destinations (Sheets, Alerts, Popovers)

Use `@Reducer enum Destination` for multiple presentation types:

```swift
// Source: references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/04-Navigation-Multiple-Destinations.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/04-Navigation-Multiple-Destinations.swift

@Reducer
struct MultipleDestinationsFeature {
  @Reducer(state: .equatable)
  enum Destination {
    /// Alert with custom actions
    case alert(AlertState<Alert>)
    /// Sheet presentation
    case addItem(AddItemFeature)
    /// Drill-down navigation
    case detail(DetailFeature)
    /// Confirmation dialog
    case confirmationDialog(ConfirmationDialogState<ConfirmationDialog>)

    enum Alert: Equatable {
      case confirmDelete
      case cancel
    }

    enum ConfirmationDialog: Equatable {
      case delete
      case duplicate
    }
  }

  @ObservableState
  struct State: Equatable {
    /// Single optional for all destinations
    @Presents var destination: Destination.State?
    var items: [Item] = []
  }

  enum Action {
    case destination(PresentationAction<Destination.Action>)
    case addButtonTapped
    case deleteButtonTapped
    case itemTapped(Item)
  }

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .addButtonTapped:
        state.destination = .addItem(AddItemFeature.State())
        return .none

      case .deleteButtonTapped:
        state.destination = .alert(.delete)
        return .none

      case let .itemTapped(item):
        state.destination = .detail(DetailFeature.State(item: item))
        return .none

      case .destination(.presented(.alert(.confirmDelete))):
        /// Handle alert action
        state.items.removeAll()
        return .none

      case .destination:
        return .none
      }
    }
    /// Compose destination reducer
    .ifLet(\.$destination, action: \.destination)
  }
}

/// View with multiple presentation types
struct MultipleDestinationsView: View {
  @Bindable var store: StoreOf<MultipleDestinationsFeature>

  var body: some View {
    List(store.items) { item in
      Button(item.name) {
        store.send(.itemTapped(item))
      }
    }
    /// Sheet presentation
    .sheet(item: $store.scope(state: \.destination?.addItem, action: \.destination.addItem)) { store in
      AddItemView(store: store)
    }
    /// Navigation destination
    .navigationDestination(item: $store.scope(state: \.destination?.detail, action: \.destination.detail)) { store in
      DetailView(store: store)
    }
    /// Alert
    .alert($store.scope(state: \.destination?.alert, action: \.destination.alert))
    /// Confirmation dialog
    .confirmationDialog($store.scope(state: \.destination?.confirmationDialog, action: \.destination.confirmationDialog))
  }
}
```

**Key Points:**
- Single `@Presents var destination` for all presentation types
- Compile-time guarantee that only one destination is active
- `.ifLet(\.$destination, action:)` composes the destination reducer
- Use `$store.scope(state: \.destination?.case, action:)` for bindings

### Programmatic Dismissal

Use `@Dependency(\.dismiss)` for programmatic dismissal:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpDetail.swift:47-50
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpDetail.swift#L47-L50

@Reducer
struct SyncUpDetail {
  @Dependency(\.dismiss) var dismiss

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .destination(.presented(.alert(.confirmDeletion))):
        @Shared(.syncUps) var syncUps
        $syncUps.withLock { _ = $0.remove(id: state.syncUp.id) }
        /// Dismiss after deletion
        return .run { _ in await self.dismiss() }

      // ...
      }
    }
  }
}
```

**Key Points:**
- `@Dependency(\.dismiss)` provides programmatic dismissal
- Call `await self.dismiss()` in an effect
- Works with sheets, navigation stacks, and popovers

### Delegate Actions for Child-to-Parent Communication

Use delegate actions for child-to-parent communication:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpDetail.swift:38-42
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpDetail.swift#L38-L42

/// Child feature
@Reducer
struct SyncUpDetail {
  enum Action: Sendable {
    // ... other actions
    
    /// Delegate actions for parent
    @CasePathable
    enum Delegate {
      case startMeeting(syncUp: SyncUp)
    }
    case delegate(Delegate)
  }

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .startMeetingButtonTapped:
        /// Send delegate action to parent
        return .send(.delegate(.startMeeting(syncUp: state.syncUp)))
      // ...
      }
    }
  }
}

/// Parent feature
@Reducer
struct AppFeature {
  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      /// Handle delegate action from child
      case let .path(.element(id: _, action: .detail(.delegate(.startMeeting(syncUp))))):
        state.path.append(.record(RecordMeeting.State(syncUp: Shared(syncUp))))
        return .none
      // ...
      }
    }
    .forEach(\.path, action: \.path)
  }
}
```

**Key Points:**
- Define `Delegate` enum inside child's `Action`
- Use `@CasePathable` for pattern matching
- Parent handles delegate actions in its reducer
- Enables loose coupling between features

### Understanding Action Case Paths: A First-Principles Guide

When working with TCA navigation and destinations, action case paths can seem confusing at first. This section breaks down exactly how actions flow through nested reducers and how to read complex action paths like `.destination(.presented(.alert(.confirmDelete)))`.

#### The Fundamental Problem: Nested Enums

In TCA, actions are enums. When you have parent-child relationships, you end up with **nested enums**. Consider this hierarchy:

```
AppFeature
  └── destination (optional child)
        └── alert (one possible destination)
              └── confirmDelete (one possible alert action)
```

Each level of nesting adds another layer to the action path.

#### Building Blocks: How Actions Are Structured

**Step 1: A Simple Feature's Actions**

```swift
/// A simple feature with no children
@Reducer
struct SimpleFeature {
  enum Action {
    case buttonTapped
    case textChanged(String)
  }
}
```

Actions are flat - just `buttonTapped` or `textChanged("hello")`.

**Step 2: Adding a Child Feature**

When you embed a child feature, you need to wrap its actions:

```swift
@Reducer
struct ParentFeature {
  enum Action {
    case buttonTapped
    /// Child's actions are wrapped in a case
    case child(ChildFeature.Action)
  }
}
```

Now to reference the child's `buttonTapped`, you write: `.child(.buttonTapped)`

**Step 3: Adding Navigation Destinations**

TCA provides `PresentationAction` to wrap destination actions with additional semantics:

```swift
@Reducer
struct ParentFeature {
  @Reducer
  enum Destination {
    case detail(DetailFeature)
    case alert(AlertState<Alert>)
    
    enum Alert {
      case confirmDelete
      case cancel
    }
  }
  
  enum Action {
    /// PresentationAction wraps Destination.Action
    case destination(PresentationAction<Destination.Action>)
  }
}
```

#### Anatomy of PresentationAction

`PresentationAction` is an enum with two cases:

```swift
public enum PresentationAction<Action> {
  /// The destination was dismissed (user swiped away, tapped outside, etc.)
  case dismiss
  
  /// The destination sent an action while presented
  case presented(Action)
}
```

This is why you see `.destination(.presented(...))` - you're saying:
1. `.destination` - This is a destination action
2. `.presented(...)` - The destination is currently presented and sent this action
3. `(...)` - The actual action from the destination

#### Reading Complex Action Paths

Let's decode `.destination(.presented(.alert(.confirmDelete)))`:

```
.destination(.presented(.alert(.confirmDelete)))
     │              │        │         │
     │              │        │         └── The alert button that was tapped
     │              │        └── Which destination case (alert vs detail vs sheet)
     │              └── The destination is presented (not dismissed)
     └── This is a destination-related action
```

**Visual Breakdown:**

```
Action
  └── destination: PresentationAction<Destination.Action>
        ├── .dismiss                    → User dismissed the destination
        └── .presented(Destination.Action)
              ├── .detail(DetailFeature.Action)
              │     ├── .buttonTapped
              │     └── .delegate(Delegate)
              │           └── .startMeeting(syncUp:)
              └── .alert(Alert)
                    ├── .confirmDelete  ← This is our target!
                    └── .cancel
```

#### Pattern Matching in Reducers

When handling these nested actions, you pattern match from outside-in:

```swift
var body: some ReducerOf<Self> {
  Reduce { state, action in
    switch action {
    /// Match the full path
    case .destination(.presented(.alert(.confirmDelete))):
      /// Handle delete confirmation
      state.items.removeAll()
      return .none
      
    /// Match any alert action
    case .destination(.presented(.alert)):
      /// Handle any other alert action
      return .none
      
    /// Match any presented destination
    case .destination(.presented):
      /// Handle any destination action
      return .none
      
    /// Match dismiss
    case .destination(.dismiss):
      /// Destination was dismissed
      return .none
      
    /// Catch-all for destination
    case .destination:
      return .none
      
    /// Other actions...
    case .buttonTapped:
      return .none
    }
  }
}
```

**Important:** Swift matches patterns top-to-bottom, so put specific cases before general ones.

#### Stack Navigation Action Paths

For `NavigationStack` with `StackState`, the pattern is slightly different:

```swift
/// Stack action includes element ID
case .path(.element(id: let id, action: .detail(.delegate(.startMeeting(let syncUp))))):
  /// Handle delegate from a specific stack element
  state.path.append(.record(RecordMeeting.State(syncUp: Shared(syncUp))))
  return .none

/// Match any action from any detail screen
case .path(.element(id: _, action: .detail)):
  return .none

/// Match pop action (user navigated back)
case .path(.popFrom(id: let id)):
  /// Element was popped from stack
  return .none

/// Match push action
case .path(.push(id: let id, state: let state)):
  /// Element was pushed onto stack
  return .none
```

**Stack Action Structure:**

```
StackAction<Path.State, Path.Action>
  ├── .element(id: StackElementID, action: Path.Action)
  │     └── The action from a specific element in the stack
  ├── .popFrom(id: StackElementID)
  │     └── An element was popped (back navigation)
  └── .push(id: StackElementID, state: Path.State)
        └── An element was pushed (forward navigation)
```

#### Why This Design?

**1. Type Safety**
Every action path is fully typed. The compiler ensures you can't accidentally handle an action that doesn't exist.

**2. Exhaustive Handling**
Swift's exhaustive switch ensures you handle all cases (or explicitly ignore them with `case .destination: return .none`).

**3. Composition**
Child features don't know about their parents. The parent wraps child actions, enabling loose coupling.

**4. Testability**
You can send any action path in tests:

```swift
await store.send(.destination(.presented(.alert(.confirmDelete)))) {
  $0.items = []
}
```

**5. Deep Linking**
Since all navigation is state-driven, you can construct any navigation state programmatically:

```swift
/// Deep link directly to a detail screen with an alert showing
state.destination = .detail(DetailFeature.State(
  item: item,
  destination: .alert(.confirmDeletion)
))
```

#### Common Patterns and Their Meanings

| Pattern | Meaning |
|---------|---------|
| `.destination(.dismiss)` | User dismissed the destination (swipe, tap outside) |
| `.destination(.presented(.someCase))` | Destination sent an action while visible |
| `.path(.element(id:, action:))` | Action from a specific stack element |
| `.path(.popFrom(id:))` | User navigated back from an element |
| `.child(.delegate(.someAction))` | Child requesting parent to do something |
| `.binding(\.someProperty)` | Two-way binding changed a property |

#### Debugging Action Paths

When you're unsure what action path to match, use a catch-all with a print:

```swift
case let .destination(action):
  print("Destination action: \(action)")
  return .none
```

Or use TCA's built-in reducer debugging:

```swift
var body: some ReducerOf<Self> {
  Reduce { state, action in
    // ...
  }
  ._printChanges()  /// Prints all actions and state changes
}
```

#### Quick Reference: Building Action Paths

```swift
/// Simple action
.buttonTapped

/// Child feature action
.child(.buttonTapped)

/// Presented destination action
.destination(.presented(.detail(.buttonTapped)))

/// Alert action
.destination(.presented(.alert(.confirmDelete)))

/// Delegate from child
.child(.delegate(.didFinish))

/// Stack element action
.path(.element(id: id, action: .detail(.buttonTapped)))

/// Stack element delegate
.path(.element(id: id, action: .detail(.delegate(.startMeeting(syncUp)))))

/// Binding action
.binding(\.text)
```

---

## Dependency Management

> **📖 Source Documentation**
>
> - Local: [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/DependencyManagement.md`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/DependencyManagement.md)
> - Dependencies Library: [`references/swift-dependencies/`](../references/swift-dependencies/)
> - isowords Clients: [`references/isowords/Sources/`](../references/isowords/Sources/)
> - GitHub: [swift-dependencies](https://github.com/pointfreeco/swift-dependencies)

Dependency management is a cornerstone of TCA applications. The `@DependencyClient` macro and `@Dependency` property wrapper provide a powerful, type-safe way to inject dependencies that can be easily swapped for testing and previews.

### The @Dependency Property Wrapper

Access dependencies in reducers:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUps/RecordMeeting.swift:35-38
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/RecordMeeting.swift#L35-L38

@Reducer
struct RecordMeeting {
  @Dependency(\.continuousClock) var clock
  @Dependency(\.dismiss) var dismiss
  @Dependency(\.speechClient) var speechClient
  @Dependency(\.uuid) var uuid

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .onTask:
        return .run { send in
          /// Use dependencies
          let status = await self.speechClient.authorizationStatus()
          await send(.speechResult(.success(status)))
          
          /// Timer using clock dependency
          for await _ in self.clock.timer(interval: .seconds(1)) {
            await send(.timerTick)
          }
        }
      // ...
      }
    }
  }
}
```

### Overriding Dependencies in Tests

Override dependencies in tests:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpsListTests.swift:14-22
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUpsTests/SyncUpsListTests.swift#L14-L22

@Test
func add() async throws {
  let store = TestStore(initialState: SyncUpsList.State()) {
    SyncUpsList()
  } withDependencies: {
    /// Override dependencies for this test
    $0.uuid = .incrementing
  }

  // ... test assertions
}
```

---

## Comprehensive Dependency Client Examples

This section provides 16 complete dependency client examples from isowords, ranging from minimal single-file clients to complex hierarchical clients with nested sub-clients. Each example demonstrates different patterns and best practices.

### Example Categories

| Complexity | Examples | Key Patterns |
|------------|----------|--------------|
| **Minimal** | Build, DeviceId | Single-file, 1-2 endpoints |
| **Simple** | FeedbackGeneratorClient, FileClient, RemoteNotificationsClient | 2-3 endpoints, basic patterns |
| **Medium** | UserDefaultsClient, UIApplicationClient, UserNotificationClient | 5-9 endpoints, override helpers |
| **Complex** | AudioPlayerClient, StoreKitClient, ApiClient | 8+ endpoints, actors, streaming |
| **Very Complex** | GameCenterClient | Nested sub-clients, hierarchical structure |
| **Specialized** | LowPowerModeClient, ServerConfigClient, LocalDatabaseClient, DictionaryClient | AsyncStream, factory patterns, database |

---

### Example 1: Build (Minimal - Single File)

A minimal dependency for accessing build information with type-safe Tagged types.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/Build/Build.swift`](../references/isowords/Sources/Build/Build.swift)
> - GitHub: [Build.swift](https://github.com/pointfreeco/isowords/blob/main/Sources/Build/Build.swift)

```swift
// Build.swift - Complete single-file dependency
import Dependencies
import DependenciesMacros
import IssueReporting
import Tagged

/// Type-safe build number using Tagged
public typealias BuildNumber = Tagged<((), build: ()), Int>

@DependencyClient
public struct Build: Sendable {
  /// Get the current build number
  public var number: @Sendable () -> BuildNumber = { 0 }
  /// Get the git SHA
  public var gitSha: @Sendable () -> String = { "" }
}

extension Build: DependencyKey {
  /// Live implementation reads from Bundle
  public static var liveValue: Self {
    Self(
      number: {
        .init(
          rawValue: (Bundle.main.infoDictionary?["CFBundleVersion"] as? String)
            .flatMap(Int.init)
            ?? 0
        )
      },
      gitSha: {
        Bundle.main.infoDictionary?["GitSHA"] as? String ?? ""
      }
    )
  }
}

extension Build: TestDependencyKey {
  public static let previewValue = Self()
  public static let testValue = Self()
}

extension DependencyValues {
  public var build: Build {
    get { self[Build.self] }
    set { self[Build.self] = newValue }
  }
}
```

**Key Patterns:**
- Single file contains interface, live, test, and DependencyValues extension
- Uses `Tagged` for type-safe identifiers
- Default values provided inline with closures
- `DependencyKey` for live value, `TestDependencyKey` for test/preview

---

### Example 2: DeviceId (Minimal - iCloud Persistence)

A minimal dependency that persists device ID to iCloud for cross-device identification.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/DeviceId/DeviceId.swift`](../references/isowords/Sources/DeviceId/DeviceId.swift)
> - GitHub: [DeviceId.swift](https://github.com/pointfreeco/isowords/blob/main/Sources/DeviceId/DeviceId.swift)

```swift
// DeviceId.swift - Complete single-file dependency
import Dependencies
import DependenciesMacros
import Foundation
import IssueReporting

@DependencyClient
public struct DeviceIdentifier: Sendable {
  /// Get or create a persistent device ID
  public var id: @Sendable () -> UUID = { UUID() }
}

extension DeviceIdentifier: DependencyKey {
  public static var liveValue: Self {
    Self {
      /// Try to get from iCloud first
      if let uuidString = NSUbiquitousKeyValueStore.default.string(forKey: deviceIdKey),
         let uuid = UUID(uuidString: uuidString)
      {
        return uuid
      }
      
      /// Generate new UUID and persist to iCloud
      let uuid = UUID()
      NSUbiquitousKeyValueStore.default.set(uuid.uuidString, forKey: deviceIdKey)
      return uuid
    }
  }
}

extension DeviceIdentifier: TestDependencyKey {
  public static let previewValue = Self { .init() }
  public static let testValue = Self()
}

extension DependencyValues {
  public var deviceId: DeviceIdentifier {
    get { self[DeviceIdentifier.self] }
    set { self[DeviceIdentifier.self] = newValue }
  }
}

private let deviceIdKey = "co.pointfree.device-id"
```

**Key Patterns:**
- Uses `NSUbiquitousKeyValueStore` for iCloud persistence
- Lazy initialization with fallback to new UUID
- Private constant for storage key

---

### Example 3: FeedbackGeneratorClient (Simple - Haptics)

A simple client for haptic feedback with just 2 endpoints.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/FeedbackGeneratorClient/`](../references/isowords/Sources/FeedbackGeneratorClient/)
> - GitHub: [FeedbackGeneratorClient](https://github.com/pointfreeco/isowords/tree/main/Sources/FeedbackGeneratorClient)

```swift
// Client.swift - Interface
import DependenciesMacros

@DependencyClient
public struct FeedbackGeneratorClient {
  /// Trigger selection changed haptic
  public var selectionChanged: @Sendable () async -> Void
  /// Trigger medium impact haptic
  public var impactOccurred: @Sendable () async -> Void
}
```

```swift
// LiveKey.swift - Live implementation
import Dependencies
import UIKit

extension FeedbackGeneratorClient: DependencyKey {
  public static let liveValue = Self(
    selectionChanged: {
      await MainActor.run {
        UISelectionFeedbackGenerator().selectionChanged()
      }
    },
    impactOccurred: {
      await MainActor.run {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
      }
    }
  )
}
```

```swift
// TestKey.swift - Test/Preview values
import Dependencies

extension DependencyValues {
  public var feedbackGenerator: FeedbackGeneratorClient {
    get { self[FeedbackGeneratorClient.self] }
    set { self[FeedbackGeneratorClient.self] = newValue }
  }
}

extension FeedbackGeneratorClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension FeedbackGeneratorClient {
  public static let noop = Self(
    selectionChanged: {},
    impactOccurred: {}
  )
}
```

**Key Patterns:**
- Uses `@MainActor.run` for UIKit APIs
- Simple `noop` static property for previews
- Separate files for interface, live, and test

---

### Example 4: FileClient (Simple - JSON Helpers)

A file system client with JSON encoding/decoding helpers and override methods for testing.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/FileClient/`](../references/isowords/Sources/FileClient/)
> - GitHub: [FileClient](https://github.com/pointfreeco/isowords/tree/main/Sources/FileClient)

```swift
// Client.swift - Interface with JSON helpers
import ClientModels
import DependenciesMacros
import Foundation

@DependencyClient
public struct FileClient: Sendable {
  public var delete: @Sendable (String) throws -> Void
  public var load: @Sendable (String) throws -> Data
  public var save: @Sendable (String, Data) throws -> Void

  /// Convenience method for loading JSON
  public func loadSavedGames() throws -> SavedGamesState {
    try JSONDecoder().decode(
      SavedGamesState.self,
      from: self.load(savedGamesFileName)
    )
  }

  /// Convenience method for saving JSON
  public func save(games: SavedGamesState) throws {
    try self.save(
      savedGamesFileName,
      JSONEncoder().encode(games)
    )
  }
}

private let savedGamesFileName = "saved-games"
```

```swift
// LiveKey.swift - Live implementation
import Dependencies
import Foundation

extension FileClient: DependencyKey {
  public static var liveValue: Self {
    let documentDirectory = FileManager.default
      .urls(for: .documentDirectory, in: .userDomainMask)
      .first!

    return Self(
      delete: { fileName in
        try FileManager.default.removeItem(
          at: documentDirectory.appendingPathComponent(fileName)
        )
      },
      load: { fileName in
        try Data(
          contentsOf: documentDirectory.appendingPathComponent(fileName)
        )
      },
      save: { fileName, data in
        try data.write(
          to: documentDirectory.appendingPathComponent(fileName)
        )
      }
    )
  }
}
```

```swift
// TestKey.swift - Test values with override helpers
import Dependencies
import Foundation
import XCTestDynamicOverlay

extension DependencyValues {
  public var fileClient: FileClient {
    get { self[FileClient.self] }
    set { self[FileClient.self] = newValue }
  }
}

extension FileClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension FileClient {
  public static let noop = Self(
    delete: { _ in },
    load: { _ in Data() },
    save: { _, _ in }
  )

  /// Override load for specific file
  public mutating func override(load fileName: String, with data: Data) {
    let fulfill = expectation(description: "load")
    self.load = { @Sendable [self] requestedFileName in
      if requestedFileName == fileName {
        fulfill()
        return data
      } else {
        return try self.load(requestedFileName)
      }
    }
  }
}
```

**Key Patterns:**
- Convenience methods for common operations (JSON encoding/decoding)
- `override` method for test mocking with expectations
- Uses `expectation(description:)` for test verification

---

### Example 5: RemoteNotificationsClient (Simple - Push Notifications)

A simple client for push notification registration.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/RemoteNotificationsClient/`](../references/isowords/Sources/RemoteNotificationsClient/)
> - GitHub: [RemoteNotificationsClient](https://github.com/pointfreeco/isowords/tree/main/Sources/RemoteNotificationsClient)

```swift
// Interface.swift
import DependenciesMacros
import Foundation

@DependencyClient
public struct RemoteNotificationsClient {
  public var isRegistered: @Sendable () async -> Bool = { false }
  public var register: @Sendable () async -> Void
  public var unregister: @Sendable () async -> Void
}
```

```swift
// LiveKey.swift
import Dependencies
import UIKit

extension RemoteNotificationsClient: DependencyKey {
  public static let liveValue = Self(
    isRegistered: {
      await MainActor.run {
        UIApplication.shared.isRegisteredForRemoteNotifications
      }
    },
    register: {
      await MainActor.run {
        UIApplication.shared.registerForRemoteNotifications()
      }
    },
    unregister: {
      await MainActor.run {
        UIApplication.shared.unregisterForRemoteNotifications()
      }
    }
  )
}
```

```swift
// TestKey.swift
import Dependencies

extension DependencyValues {
  public var remoteNotifications: RemoteNotificationsClient {
    get { self[RemoteNotificationsClient.self] }
    set { self[RemoteNotificationsClient.self] = newValue }
  }
}

extension RemoteNotificationsClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension RemoteNotificationsClient {
  public static let noop = Self(
    isRegistered: { false },
    register: {},
    unregister: {}
  )
}
```

**Key Patterns:**
- Wraps `UIApplication` APIs with `@MainActor.run`
- Simple boolean return for status check
- Default value provided for `isRegistered`

---

### Example 6: UserDefaultsClient (Medium - Typed Key-Value)

A comprehensive UserDefaults wrapper with typed accessors and override helpers.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/UserDefaultsClient/`](../references/isowords/Sources/UserDefaultsClient/)
> - GitHub: [UserDefaultsClient](https://github.com/pointfreeco/isowords/tree/main/Sources/UserDefaultsClient)

```swift
// Interface.swift
import DependenciesMacros
import Foundation

@DependencyClient
public struct UserDefaultsClient: Sendable {
  public var boolForKey: @Sendable (String) -> Bool = { _ in false }
  public var dataForKey: @Sendable (String) -> Data?
  public var doubleForKey: @Sendable (String) -> Double = { _ in 0 }
  public var integerForKey: @Sendable (String) -> Int = { _ in 0 }
  public var remove: @Sendable (String) async -> Void
  public var setBool: @Sendable (Bool, String) async -> Void
  public var setData: @Sendable (Data?, String) async -> Void
  public var setDouble: @Sendable (Double, String) async -> Void
  public var setInteger: @Sendable (Int, String) async -> Void
}
```

```swift
// LiveKey.swift
import Dependencies
import Foundation

extension UserDefaultsClient: DependencyKey {
  public static let liveValue = Self(
    boolForKey: { UserDefaults.standard.bool(forKey: $0) },
    dataForKey: { UserDefaults.standard.data(forKey: $0) },
    doubleForKey: { UserDefaults.standard.double(forKey: $0) },
    integerForKey: { UserDefaults.standard.integer(forKey: $0) },
    remove: { UserDefaults.standard.removeObject(forKey: $0) },
    setBool: { UserDefaults.standard.set($0, forKey: $1) },
    setData: { UserDefaults.standard.set($0, forKey: $1) },
    setDouble: { UserDefaults.standard.set($0, forKey: $1) },
    setInteger: { UserDefaults.standard.set($0, forKey: $1) }
  )
}
```

```swift
// TestKey.swift
import Dependencies
import Foundation
import XCTestDynamicOverlay

extension DependencyValues {
  public var userDefaults: UserDefaultsClient {
    get { self[UserDefaultsClient.self] }
    set { self[UserDefaultsClient.self] = newValue }
  }
}

extension UserDefaultsClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension UserDefaultsClient {
  public static let noop = Self(
    boolForKey: { _ in false },
    dataForKey: { _ in nil },
    doubleForKey: { _ in 0 },
    integerForKey: { _ in 0 },
    remove: { _ in },
    setBool: { _, _ in },
    setData: { _, _ in },
    setDouble: { _, _ in },
    setInteger: { _, _ in }
  )

  /// Override bool for specific key
  public mutating func override(bool value: Bool, forKey key: String) {
    let fulfill = expectation(description: "boolForKey")
    self.boolForKey = { @Sendable [self] requestedKey in
      if requestedKey == key {
        fulfill()
        return value
      } else {
        return self.boolForKey(requestedKey)
      }
    }
  }

  /// Override integer for specific key
  public mutating func override(integer value: Int, forKey key: String) {
    let fulfill = expectation(description: "integerForKey")
    self.integerForKey = { @Sendable [self] requestedKey in
      if requestedKey == key {
        fulfill()
        return value
      } else {
        return self.integerForKey(requestedKey)
      }
    }
  }
}
```

**Key Patterns:**
- Typed accessors for different value types
- Multiple `override` methods for different types
- Uses `expectation(description:)` for test verification
- Captures `self` in closures for fallback behavior

---

### Example 7: UIApplicationClient (Medium - @MainActor)

A client wrapping UIApplication APIs with proper main actor handling.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/UIApplicationClient/`](../references/isowords/Sources/UIApplicationClient/)
> - GitHub: [UIApplicationClient](https://github.com/pointfreeco/isowords/tree/main/Sources/UIApplicationClient)

```swift
// Client.swift
import ComposableArchitecture
import UIKit

@DependencyClient
public struct UIApplicationClient: Sendable {
  public var alternateIconName: @Sendable () async -> String?
  public var open: @Sendable (URL, [UIApplication.OpenExternalURLOptionsKey: Any]) async -> Bool = { _, _ in false }
  public var openSettingsURLString: @Sendable () async -> String = { "" }
  public var setAlternateIconName: @Sendable (String?) async throws -> Void
  public var setUserInterfaceStyle: @Sendable (UIUserInterfaceStyle) async -> Void
  public var supportsAlternateIcons: @Sendable () async -> Bool = { false }
  public var windows: @Sendable () async -> [UIWindow] = { [] }
}
```

```swift
// LiveKey.swift
import Dependencies
import UIKit

extension UIApplicationClient: DependencyKey {
  public static let liveValue = Self(
    alternateIconName: {
      await MainActor.run {
        UIApplication.shared.alternateIconName
      }
    },
    open: { url, options in
      await MainActor.run {
        await UIApplication.shared.open(url, options: options)
      }
    },
    openSettingsURLString: {
      await MainActor.run {
        UIApplication.openSettingsURLString
      }
    },
    setAlternateIconName: { iconName in
      try await MainActor.run {
        try await UIApplication.shared.setAlternateIconName(iconName)
      }
    },
    setUserInterfaceStyle: { userInterfaceStyle in
      await MainActor.run {
        for window in UIApplication.shared.connectedScenes
          .compactMap({ $0 as? UIWindowScene })
          .flatMap(\.windows)
        {
          window.overrideUserInterfaceStyle = userInterfaceStyle
        }
      }
    },
    supportsAlternateIcons: {
      await MainActor.run {
        UIApplication.shared.supportsAlternateIcons
      }
    },
    windows: {
      await MainActor.run {
        UIApplication.shared.connectedScenes
          .compactMap { $0 as? UIWindowScene }
          .flatMap(\.windows)
      }
    }
  )
}
```

```swift
// TestKey.swift
import Dependencies

extension DependencyValues {
  public var applicationClient: UIApplicationClient {
    get { self[UIApplicationClient.self] }
    set { self[UIApplicationClient.self] = newValue }
  }
}

extension UIApplicationClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension UIApplicationClient {
  public static let noop = Self(
    alternateIconName: { nil },
    open: { _, _ in false },
    openSettingsURLString: { "" },
    setAlternateIconName: { _ in },
    setUserInterfaceStyle: { _ in },
    supportsAlternateIcons: { false },
    windows: { [] }
  )
}
```

**Key Patterns:**
- All UIKit calls wrapped in `@MainActor.run`
- Handles window scene iteration for multi-window support
- Async/throws for icon setting

---

### Example 8: LowPowerModeClient (AsyncStream-Based)

A client that streams low power mode changes using AsyncStream.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/LowPowerModeClient/`](../references/isowords/Sources/LowPowerModeClient/)
> - GitHub: [LowPowerModeClient](https://github.com/pointfreeco/isowords/tree/main/Sources/LowPowerModeClient)

```swift
// Client.swift
import ComposableArchitecture

@DependencyClient
public struct LowPowerModeClient: Sendable {
  /// Stream of low power mode changes
  public var start: @Sendable () async -> AsyncStream<Bool> = { .finished }
}
```

```swift
// LiveKey.swift
import Dependencies
import Foundation

extension LowPowerModeClient: DependencyKey {
  public static let liveValue = Self(
    start: {
      AsyncStream { continuation in
        /// Yield initial value
        continuation.yield(ProcessInfo.processInfo.isLowPowerModeEnabled)

        /// Listen for changes via NotificationCenter
        let task = Task {
          for await _ in NotificationCenter.default.notifications(
            named: .NSProcessInfoPowerStateDidChange
          ) {
            continuation.yield(ProcessInfo.processInfo.isLowPowerModeEnabled)
          }
        }

        continuation.onTermination = { _ in
          task.cancel()
        }
      }
    }
  )
}
```

```swift
// TestKey.swift
import Dependencies

extension DependencyValues {
  public var lowPowerMode: LowPowerModeClient {
    get { self[LowPowerModeClient.self] }
    set { self[LowPowerModeClient.self] = newValue }
  }
}

extension LowPowerModeClient: TestDependencyKey {
  public static let previewValue = Self.false
  public static let testValue = Self()
}

extension LowPowerModeClient {
  /// Static convenience for always false
  public static let `false` = Self(
    start: { AsyncStream { $0.yield(false) } }
  )

  /// Static convenience for always true
  public static let `true` = Self(
    start: { AsyncStream { $0.yield(true) } }
  )

  /// Static convenience for alternating values
  public static let backAndForth = Self(
    start: {
      AsyncStream { continuation in
        Task {
          var isLowPowerMode = false
          while !Task.isCancelled {
            try? await Task.sleep(nanoseconds: NSEC_PER_SEC * 3)
            isLowPowerMode.toggle()
            continuation.yield(isLowPowerMode)
          }
        }
      }
    }
  )
}
```

**Key Patterns:**
- Uses `AsyncStream` for continuous value streaming
- Bridges `NotificationCenter` to async stream
- Static convenience values (`.true`, `.false`, `.backAndForth`)
- Proper cancellation handling with `onTermination`

---

### Example 9: AudioPlayerClient (Complex - Actor-Based)

A complex audio client using an actor for thread-safe AVFoundation management.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/AudioPlayerClient/`](../references/isowords/Sources/AudioPlayerClient/)
> - GitHub: [AudioPlayerClient](https://github.com/pointfreeco/isowords/tree/main/Sources/AudioPlayerClient)

```swift
// Client.swift
import DependenciesMacros
import Foundation

@DependencyClient
public struct AudioPlayerClient: Sendable {
  public var load: @Sendable (AudioPlayerClient.Sound) async throws -> Void
  public var loop: @Sendable (AudioPlayerClient.Sound) async throws -> Void
  public var play: @Sendable (AudioPlayerClient.Sound) async throws -> Void
  public var secondaryAudioShouldBeSilencedHint: @Sendable () async -> Bool = { false }
  public var setGlobalVolumeForMusic: @Sendable (Float) async -> Void
  public var setGlobalVolumeForSoundEffects: @Sendable (Float) async -> Void
  public var setVolume: @Sendable (AudioPlayerClient.Sound, Float) async -> Void
  public var stop: @Sendable (AudioPlayerClient.Sound) async -> Void

  public struct Sound: Hashable, Sendable {
    public let category: Category
    public let name: String

    public enum Category: Hashable, Sendable {
      case music
      case soundEffect
    }

    public init(category: Category, name: String) {
      self.category = category
      self.name = name
    }
  }
}
```

```swift
// LiveKey.swift
import AVFoundation
import Dependencies

extension AudioPlayerClient: DependencyKey {
  public static var liveValue: Self {
    /// Actor for thread-safe audio management
    let audioActor = AudioActor()

    return Self(
      load: { sound in
        try await audioActor.load(sound: sound)
      },
      loop: { sound in
        try await audioActor.loop(sound: sound)
      },
      play: { sound in
        try await audioActor.play(sound: sound)
      },
      secondaryAudioShouldBeSilencedHint: {
        await audioActor.secondaryAudioShouldBeSilencedHint()
      },
      setGlobalVolumeForMusic: { volume in
        await audioActor.setGlobalVolume(volume, for: .music)
      },
      setGlobalVolumeForSoundEffects: { volume in
        await audioActor.setGlobalVolume(volume, for: .soundEffect)
      },
      setVolume: { sound, volume in
        await audioActor.setVolume(sound: sound, volume: volume)
      },
      stop: { sound in
        await audioActor.stop(sound: sound)
      }
    )
  }
}

/// Thread-safe actor for AVFoundation
private actor AudioActor {
  var players: [AudioPlayerClient.Sound: AVAudioPlayer] = [:]
  var globalVolumes: [AudioPlayerClient.Sound.Category: Float] = [
    .music: 1,
    .soundEffect: 1,
  ]

  func load(sound: AudioPlayerClient.Sound) throws {
    guard self.players[sound] == nil else { return }
    let player = try self.makePlayer(sound: sound)
    player.prepareToPlay()
    self.players[sound] = player
  }

  func play(sound: AudioPlayerClient.Sound) throws {
    let player = try self.player(for: sound)
    player.currentTime = 0
    player.play()
  }

  func loop(sound: AudioPlayerClient.Sound) throws {
    let player = try self.player(for: sound)
    player.numberOfLoops = -1
    player.play()
  }

  func stop(sound: AudioPlayerClient.Sound) {
    self.players[sound]?.stop()
  }

  func setVolume(sound: AudioPlayerClient.Sound, volume: Float) {
    self.players[sound]?.volume = volume * (self.globalVolumes[sound.category] ?? 1)
  }

  func setGlobalVolume(_ volume: Float, for category: AudioPlayerClient.Sound.Category) {
    self.globalVolumes[category] = volume
    for (sound, player) in self.players where sound.category == category {
      player.volume = volume
    }
  }

  func secondaryAudioShouldBeSilencedHint() -> Bool {
    AVAudioSession.sharedInstance().secondaryAudioShouldBeSilencedHint
  }

  private func player(for sound: AudioPlayerClient.Sound) throws -> AVAudioPlayer {
    if let player = self.players[sound] {
      return player
    }
    let player = try self.makePlayer(sound: sound)
    self.players[sound] = player
    return player
  }

  private func makePlayer(sound: AudioPlayerClient.Sound) throws -> AVAudioPlayer {
    let url = Bundle.module.url(forResource: sound.name, withExtension: "mp3")!
    let player = try AVAudioPlayer(contentsOf: url)
    player.volume = self.globalVolumes[sound.category] ?? 1
    return player
  }
}
```

```swift
// TestKey.swift
import Dependencies

extension DependencyValues {
  public var audioPlayer: AudioPlayerClient {
    get { self[AudioPlayerClient.self] }
    set { self[AudioPlayerClient.self] = newValue }
  }
}

extension AudioPlayerClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension AudioPlayerClient {
  public static let noop = Self(
    load: { _ in },
    loop: { _ in },
    play: { _ in },
    secondaryAudioShouldBeSilencedHint: { false },
    setGlobalVolumeForMusic: { _ in },
    setGlobalVolumeForSoundEffects: { _ in },
    setVolume: { _, _ in },
    stop: { _ in }
  )
}
```

**Key Patterns:**
- Uses Swift `actor` for thread-safe state management
- Nested `Sound` type with category enum
- Lazy player creation with caching
- Global volume management per category
- Uses `Bundle.module` for SPM resources

---

### Example 10: ComposableStoreKit (Complex - Delegate Bridging)

A StoreKit client that bridges delegate callbacks to AsyncStream.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/ComposableStoreKit/`](../references/isowords/Sources/ComposableStoreKit/)
> - GitHub: [ComposableStoreKit](https://github.com/pointfreeco/isowords/tree/main/Sources/ComposableStoreKit)

```swift
// Client.swift
import DependenciesMacros
import StoreKit

@DependencyClient
public struct StoreKitClient: Sendable {
  public var addPayment: @Sendable (SKPayment) async -> Void
  public var appStoreReceiptURL: @Sendable () -> URL?
  public var isAuthorizedForPayments: @Sendable () -> Bool = { false }
  public var fetchProducts: @Sendable (Set<String>) async throws -> ProductsResponse
  public var finishTransaction: @Sendable (PaymentTransaction) async -> Void
  /// Stream of payment transaction events
  public var observer: @Sendable () -> AsyncStream<PaymentTransactionObserverEvent> = { .finished }
  public var requestReview: @Sendable () async -> Void
  public var restoreCompletedTransactions: @Sendable () async -> Void

  public struct ProductsResponse: Equatable, Sendable {
    public var invalidProductIdentifiers: [String]
    public var products: [Product]
  }

  public struct Product: Equatable, Identifiable, Sendable {
    public var id: String { self.productIdentifier }
    public var localizedDescription: String
    public var localizedTitle: String
    public var price: NSDecimalNumber
    public var priceLocale: Locale
    public var productIdentifier: String
  }

  public struct PaymentTransaction: Equatable, Sendable {
    public var error: NSError?
    public var original: PaymentTransaction?
    public var payment: Payment
    public var rawValue: SKPaymentTransaction?
    public var transactionDate: Date?
    public var transactionIdentifier: String?
    public var transactionState: SKPaymentTransactionState
  }

  public struct Payment: Equatable, Sendable {
    public var applicationUsername: String?
    public var productIdentifier: String
    public var quantity: Int
    public var requestData: Data?
    public var simulatesAskToBuyInSandbox: Bool
  }

  public enum PaymentTransactionObserverEvent: Equatable, Sendable {
    case removedTransactions([PaymentTransaction])
    case restoreCompletedTransactionsFailed(NSError)
    case restoreCompletedTransactionsFinished(transactions: [PaymentTransaction])
    case updatedTransactions([PaymentTransaction])
  }
}
```

```swift
// LiveKey.swift (simplified)
import Dependencies
import StoreKit

extension StoreKitClient: DependencyKey {
  public static var liveValue: Self {
    /// Delegate that bridges to AsyncStream
    let observer = Observer()

    return Self(
      addPayment: { payment in
        SKPaymentQueue.default().add(payment)
      },
      appStoreReceiptURL: {
        Bundle.main.appStoreReceiptURL
      },
      isAuthorizedForPayments: {
        SKPaymentQueue.canMakePayments()
      },
      fetchProducts: { productIdentifiers in
        try await withCheckedThrowingContinuation { continuation in
          let request = SKProductsRequest(productIdentifiers: productIdentifiers)
          let delegate = ProductsRequestDelegate(continuation: continuation)
          request.delegate = delegate
          request.start()
        }
      },
      finishTransaction: { transaction in
        guard let rawValue = transaction.rawValue else { return }
        SKPaymentQueue.default().finishTransaction(rawValue)
      },
      observer: {
        /// Return stream from delegate
        observer.stream
      },
      requestReview: {
        await MainActor.run {
          if let scene = UIApplication.shared.connectedScenes
            .first(where: { $0.activationState == .foregroundActive }) as? UIWindowScene
          {
            SKStoreReviewController.requestReview(in: scene)
          }
        }
      },
      restoreCompletedTransactions: {
        SKPaymentQueue.default().restoreCompletedTransactions()
      }
    )
  }
}

/// Delegate that bridges SKPaymentTransactionObserver to AsyncStream
private class Observer: NSObject, SKPaymentTransactionObserver, Sendable {
  let (stream, continuation) = AsyncStream<StoreKitClient.PaymentTransactionObserverEvent>.makeStream()

  override init() {
    super.init()
    SKPaymentQueue.default().add(self)
  }

  func paymentQueue(_ queue: SKPaymentQueue, updatedTransactions transactions: [SKPaymentTransaction]) {
    continuation.yield(.updatedTransactions(transactions.map(PaymentTransaction.init)))
  }

  func paymentQueue(_ queue: SKPaymentQueue, removedTransactions transactions: [SKPaymentTransaction]) {
    continuation.yield(.removedTransactions(transactions.map(PaymentTransaction.init)))
  }

  func paymentQueueRestoreCompletedTransactionsFinished(_ queue: SKPaymentQueue) {
    continuation.yield(.restoreCompletedTransactionsFinished(
      transactions: queue.transactions.map(PaymentTransaction.init)
    ))
  }

  func paymentQueue(_ queue: SKPaymentQueue, restoreCompletedTransactionsFailedWithError error: Error) {
    continuation.yield(.restoreCompletedTransactionsFailed(error as NSError))
  }
}
```

```swift
// TestKey.swift
import Dependencies

extension DependencyValues {
  public var storeKit: StoreKitClient {
    get { self[StoreKitClient.self] }
    set { self[StoreKitClient.self] = newValue }
  }
}

extension StoreKitClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension StoreKitClient {
  public static let noop = Self(
    addPayment: { _ in },
    appStoreReceiptURL: { nil },
    isAuthorizedForPayments: { false },
    fetchProducts: { _ in try await Task.never() },
    finishTransaction: { _ in },
    observer: { .finished },
    requestReview: {},
    restoreCompletedTransactions: {}
  )
}
```

**Key Patterns:**
- Bridges delegate pattern to `AsyncStream`
- Uses `AsyncStream.makeStream()` for continuation-based streaming
- Nested types for products, transactions, payments
- `@CasePathable` enum for observer events
- Uses `Task.never()` for noop async throwing functions

---

### Example 11: ComposableGameCenter (Very Complex - Nested Clients)

A hierarchical client with multiple nested sub-clients for Game Center functionality.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/ComposableGameCenter/`](../references/isowords/Sources/ComposableGameCenter/)
> - GitHub: [ComposableGameCenter](https://github.com/pointfreeco/isowords/tree/main/Sources/ComposableGameCenter)

```swift
// Interface.swift
import DependenciesMacros
import GameKit

@DependencyClient
public struct GameCenterClient: Sendable {
  /// Nested client for local player operations
  public var localPlayer: LocalPlayerClient = .init()
  /// Nested client for turn-based matches
  public var turnBasedMatch: TurnBasedMatchClient = .init()
  /// Nested client for turn-based match participants
  public var turnBasedMatchmakerViewController: TurnBasedMatchmakerViewControllerClient = .init()

  /// Nested LocalPlayerClient
  @DependencyClient
  public struct LocalPlayerClient: Sendable {
    public var authenticate: @Sendable () async throws -> Void
    public var listener: @Sendable () -> AsyncStream<ListenerEvent> = { .finished }
    public var localPlayer: @Sendable () -> LocalPlayer = { .notAuthenticated }

    @CasePathable
    public enum ListenerEvent: Sendable {
      case turnBased(TurnBasedEvent)

      @CasePathable
      public enum TurnBasedEvent: Sendable {
        case matchEnded(TurnBasedMatch)
        case receivedExchangeCancellation(GKTurnBasedExchange, TurnBasedMatch)
        case receivedExchangeReplies([GKTurnBasedExchangeReply], GKTurnBasedExchange, TurnBasedMatch)
        case receivedExchangeRequest(GKTurnBasedExchange, TurnBasedMatch)
        case receivedTurnEventForMatch(TurnBasedMatch, didBecomeActive: Bool)
        case wantsToQuitMatch(TurnBasedMatch)
      }
    }
  }

  /// Nested TurnBasedMatchClient
  @DependencyClient
  public struct TurnBasedMatchClient: Sendable {
    public var endMatchInTurn: @Sendable (TurnBasedMatchData) async throws -> Void
    public var endTurn: @Sendable (TurnBasedMatchData) async throws -> Void
    public var load: @Sendable (String) async throws -> TurnBasedMatch
    public var loadMatches: @Sendable () async throws -> [TurnBasedMatch]
    public var participantQuitInTurn: @Sendable (TurnBasedMatchData, Date) async throws -> Void
    public var participantQuitOutOfTurn: @Sendable (String, GKTurnBasedMatch.Outcome) async throws -> Void
    public var rematch: @Sendable (String) async throws -> TurnBasedMatch
    public var remove: @Sendable (String) async throws -> Void
    public var saveCurrentTurn: @Sendable (String, Data) async throws -> Void
    public var sendReminder: @Sendable (TurnBasedMatchData) async throws -> Void
  }

  /// Nested TurnBasedMatchmakerViewControllerClient
  @DependencyClient
  public struct TurnBasedMatchmakerViewControllerClient: Sendable {
    public var present: @Sendable (GKMatchRequest) async -> AsyncStream<DelegateEvent> = { _ in .finished }

    @CasePathable
    public enum DelegateEvent: Sendable {
      case didFailWithError(NSError)
      case didFindMatch(TurnBasedMatch)
      case wasCancelled
    }
  }
}
```

```swift
// LiveKey.swift (simplified)
import Dependencies
import GameKit

extension GameCenterClient: DependencyKey {
  public static var liveValue: Self {
    /// Actor for managing view controller presentation
    let presenter = Presenter()

    return Self(
      localPlayer: .init(
        authenticate: {
          try await withCheckedThrowingContinuation { continuation in
            GKLocalPlayer.local.authenticateHandler = { viewController, error in
              if let error = error {
                continuation.resume(throwing: error)
              } else if viewController != nil {
                /// Need to present view controller
                continuation.resume(throwing: GameCenterError.needsAuthentication)
              } else {
                continuation.resume()
              }
            }
          }
        },
        listener: {
          AsyncStream { continuation in
            let delegate = TurnBasedEventListener(continuation: continuation)
            GKLocalPlayer.local.register(delegate)
            continuation.onTermination = { _ in
              GKLocalPlayer.local.unregisterListener(delegate)
            }
          }
        },
        localPlayer: {
          LocalPlayer(rawValue: GKLocalPlayer.local)
        }
      ),
      turnBasedMatch: .init(
        endMatchInTurn: { data in
          try await data.match.endMatchInTurn(
            withMatch: data.matchData,
            scores: data.scores.map(\.rawValue),
            achievements: data.achievements.map(\.rawValue),
            completionHandler: { _ in }
          )
        },
        load: { matchId in
          TurnBasedMatch(rawValue: try await GKTurnBasedMatch.load(withID: matchId))
        },
        loadMatches: {
          try await GKTurnBasedMatch.loadMatches().map(TurnBasedMatch.init)
        }
        // ... more implementations
      ),
      turnBasedMatchmakerViewController: .init(
        present: { request in
          await presenter.present(request: request)
        }
      )
    )
  }
}

/// Actor for managing view controller presentation
private actor Presenter {
  func present(request: GKMatchRequest) -> AsyncStream<GameCenterClient.TurnBasedMatchmakerViewControllerClient.DelegateEvent> {
    AsyncStream { continuation in
      Task { @MainActor in
        let viewController = GKTurnBasedMatchmakerViewController(matchRequest: request)
        let delegate = MatchmakerDelegate(continuation: continuation)
        viewController.turnBasedMatchmakerDelegate = delegate
        
        /// Present the view controller
        UIApplication.shared.connectedScenes
          .compactMap { $0 as? UIWindowScene }
          .first?.windows.first?.rootViewController?
          .present(viewController, animated: true)
      }
    }
  }
}
```

```swift
// TestKey.swift
import Dependencies

extension DependencyValues {
  public var gameCenter: GameCenterClient {
    get { self[GameCenterClient.self] }
    set { self[GameCenterClient.self] = newValue }
  }
}

extension GameCenterClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension GameCenterClient {
  public static let noop = Self(
    localPlayer: .noop,
    turnBasedMatch: .noop,
    turnBasedMatchmakerViewController: .noop
  )
}

extension GameCenterClient.LocalPlayerClient {
  public static let noop = Self(
    authenticate: {},
    listener: { .finished },
    localPlayer: { .notAuthenticated }
  )
}

extension GameCenterClient.TurnBasedMatchClient {
  public static let noop = Self(
    endMatchInTurn: { _ in },
    endTurn: { _ in },
    load: { _ in try await Task.never() },
    loadMatches: { [] },
    participantQuitInTurn: { _, _ in },
    participantQuitOutOfTurn: { _, _ in },
    rematch: { _ in try await Task.never() },
    remove: { _ in },
    saveCurrentTurn: { _, _ in },
    sendReminder: { _ in }
  )
}

extension GameCenterClient.TurnBasedMatchmakerViewControllerClient {
  public static let noop = Self(
    present: { _ in .finished }
  )
}
```

**Key Patterns:**
- Hierarchical nested clients for logical grouping
- Each nested client has its own `@DependencyClient` macro
- `@CasePathable` enums for event types
- Actor for managing view controller lifecycle
- Separate `noop` for each nested client
- Bridges GameKit delegates to AsyncStream

---

### Example 12: ComposableUserNotifications (Medium - Delegate Events)

A client for user notifications with delegate event streaming.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/ComposableUserNotifications/`](../references/isowords/Sources/ComposableUserNotifications/)
> - GitHub: [ComposableUserNotifications](https://github.com/pointfreeco/isowords/tree/main/Sources/ComposableUserNotifications)

```swift
// Interface.swift
import CasePaths
import DependenciesMacros
import UserNotifications

@DependencyClient
public struct UserNotificationClient: Sendable {
  public var add: @Sendable (UNNotificationRequest) async throws -> Void
  public var delegate: @Sendable () -> AsyncStream<DelegateEvent> = { .finished }
  public var getNotificationSettings: @Sendable () async -> Notification.Settings = { .init(authorizationStatus: .notDetermined) }
  public var removeDeliveredNotificationsWithIdentifiers: @Sendable ([String]) async -> Void
  public var removePendingNotificationRequestsWithIdentifiers: @Sendable ([String]) async -> Void
  public var requestAuthorization: @Sendable (UNAuthorizationOptions) async throws -> Bool

  @CasePathable
  public enum DelegateEvent: Sendable {
    case didReceiveResponse(Notification.Response, completionHandler: @Sendable () -> Void)
    case openSettingsForNotification(Notification?)
    case willPresentNotification(Notification, completionHandler: @Sendable (UNNotificationPresentationOptions) -> Void)
  }

  public struct Notification: Equatable, Sendable {
    public var date: Date
    public var request: UNNotificationRequest

    public struct Response: Equatable, Sendable {
      public var notification: Notification

      public init(notification: Notification) {
        self.notification = notification
      }

      public init(rawValue: UNNotificationResponse) {
        self.notification = Notification(rawValue: rawValue.notification)
      }
    }

    public struct Settings: Equatable, Sendable {
      public var authorizationStatus: UNAuthorizationStatus

      public init(authorizationStatus: UNAuthorizationStatus) {
        self.authorizationStatus = authorizationStatus
      }

      public init(rawValue: UNNotificationSettings) {
        self.authorizationStatus = rawValue.authorizationStatus
      }
    }
  }
}
```

```swift
// LiveKey.swift
import Dependencies
import UserNotifications

extension UserNotificationClient: DependencyKey {
  public static var liveValue: Self {
    let center = UNUserNotificationCenter.current()

    return Self(
      add: { request in
        try await center.add(request)
      },
      delegate: {
        AsyncStream { continuation in
          let delegate = Delegate(continuation: continuation)
          center.delegate = delegate
          continuation.onTermination = { _ in
            _ = delegate  /// Keep delegate alive
          }
        }
      },
      getNotificationSettings: {
        await Notification.Settings(rawValue: center.notificationSettings())
      },
      removeDeliveredNotificationsWithIdentifiers: { identifiers in
        center.removeDeliveredNotifications(withIdentifiers: identifiers)
      },
      removePendingNotificationRequestsWithIdentifiers: { identifiers in
        center.removePendingNotificationRequests(withIdentifiers: identifiers)
      },
      requestAuthorization: { options in
        try await center.requestAuthorization(options: options)
      }
    )
  }
}

/// Delegate that bridges UNUserNotificationCenterDelegate to AsyncStream
private class Delegate: NSObject, UNUserNotificationCenterDelegate, Sendable {
  let continuation: AsyncStream<UserNotificationClient.DelegateEvent>.Continuation

  init(continuation: AsyncStream<UserNotificationClient.DelegateEvent>.Continuation) {
    self.continuation = continuation
  }

  func userNotificationCenter(
    _ center: UNUserNotificationCenter,
    didReceive response: UNNotificationResponse,
    withCompletionHandler completionHandler: @escaping () -> Void
  ) {
    self.continuation.yield(
      .didReceiveResponse(
        .init(rawValue: response),
        completionHandler: completionHandler
      )
    )
  }

  func userNotificationCenter(
    _ center: UNUserNotificationCenter,
    willPresent notification: UNNotification,
    withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
  ) {
    self.continuation.yield(
      .willPresentNotification(
        .init(rawValue: notification),
        completionHandler: completionHandler
      )
    )
  }

  func userNotificationCenter(
    _ center: UNUserNotificationCenter,
    openSettingsFor notification: UNNotification?
  ) {
    self.continuation.yield(
      .openSettingsForNotification(notification.map(UserNotificationClient.Notification.init))
    )
  }
}
```

```swift
// TestKey.swift
import Dependencies

extension DependencyValues {
  public var userNotifications: UserNotificationClient {
    get { self[UserNotificationClient.self] }
    set { self[UserNotificationClient.self] = newValue }
  }
}

extension UserNotificationClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension UserNotificationClient {
  public static let noop = Self(
    add: { _ in },
    delegate: { .finished },
    getNotificationSettings: { .init(authorizationStatus: .notDetermined) },
    removeDeliveredNotificationsWithIdentifiers: { _ in },
    removePendingNotificationRequestsWithIdentifiers: { _ in },
    requestAuthorization: { _ in false }
  )
}
```

**Key Patterns:**
- `@CasePathable` enum for delegate events
- Completion handlers passed through events
- Wrapper types for UNNotification types
- Delegate kept alive via closure capture

---

### Example 13: ApiClient (Complex - Route-Based Override)

A comprehensive API client with route-based override helpers for testing.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/ApiClient/`](../references/isowords/Sources/ApiClient/)
> - GitHub: [ApiClient](https://github.com/pointfreeco/isowords/tree/main/Sources/ApiClient)

```swift
// Client.swift
import CasePaths
import DependenciesMacros
import Foundation
import SharedModels

@DependencyClient
public struct ApiClient: Sendable {
  public var apiRequest: @Sendable (ServerRoute.Api.Route) async throws -> (Data, URLResponse)
  public var authenticate: @Sendable (ServerRoute.AuthenticateRequest) async throws -> CurrentPlayerEnvelope
  public var baseUrl: @Sendable () -> URL = { URL(string: "http://localhost:9876")! }
  public var currentPlayer: @Sendable () async -> CurrentPlayerEnvelope?
  public var logout: @Sendable () async -> Void
  public var refreshCurrentPlayer: @Sendable () async throws -> CurrentPlayerEnvelope
  public var request: @Sendable (ServerRoute) async throws -> (Data, URLResponse)
  public var setBaseUrl: @Sendable (URL) async -> Void

  /// Convenience method for typed API requests
  public func apiRequest<A: Decodable>(
    route: ServerRoute.Api.Route,
    as: A.Type = A.self,
    file: StaticString = #file,
    line: UInt = #line
  ) async throws -> A {
    let (data, _) = try await self.apiRequest(route)
    do {
      return try apiDecode(A.self, from: data)
    } catch {
      throw ApiError.decoding(error, file: file, line: line)
    }
  }
}
```

```swift
// TestKey.swift
import CasePaths
import Dependencies
import Foundation
import XCTestDynamicOverlay

extension DependencyValues {
  public var apiClient: ApiClient {
    get { self[ApiClient.self] }
    set { self[ApiClient.self] = newValue }
  }
}

extension ApiClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension ApiClient {
  public static let noop = Self(
    apiRequest: { _ in try await Task.never() },
    authenticate: { _ in try await Task.never() },
    currentPlayer: { nil },
    logout: {},
    refreshCurrentPlayer: { try await Task.never() },
    request: { _ in try await Task.never() },
    setBaseUrl: { _ in }
  )

  /// Override specific API route with response
  public mutating func override<Value>(
    routeCase: CaseKeyPath<ServerRoute.Api.Route, Value>,
    withResponse response: @escaping @Sendable (Value) async throws -> (Data, URLResponse)
  ) {
    let fulfill = expectation(description: "route")
    self.apiRequest = { @Sendable [self] route in
      if let value = route[case: routeCase] {
        fulfill()
        return try await response(value)
      } else {
        return try await self.apiRequest(route)
      }
    }
  }

  /// Override specific API route with encoded value
  public mutating func override<Value, A: Encodable>(
    routeCase: CaseKeyPath<ServerRoute.Api.Route, Value>,
    withResponse response: @escaping @Sendable (Value) async throws -> A
  ) {
    self.override(routeCase: routeCase) { value in
      (try apiEncode(response(value)), .init())
    }
  }
}
```

**Key Patterns:**
- Uses `CaseKeyPath` for type-safe route matching
- `Task.never()` for noop async throwing functions
- Multiple override methods for different response types
- Convenience method for typed decoding with error location

---

### Example 14: DictionaryClient (Simple - Optional Lookup)

A dictionary client with optional lookup and nested enum.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/DictionaryClient/`](../references/isowords/Sources/DictionaryClient/)
> - GitHub: [DictionaryClient](https://github.com/pointfreeco/isowords/tree/main/Sources/DictionaryClient)

```swift
// Client.swift
import DependenciesMacros
import SharedModels

@DependencyClient
public struct DictionaryClient {
  public var contains: (String, Language) -> Bool = { _, _ in false }
  public var load: (Language) throws -> Bool
  public var lookup: ((String, Language) -> Lookup?)?
  public var randomCubes: (Language) -> Puzzle = { _ in .mock }
  public var unload: (Language) -> Void

  public enum Lookup: Equatable {
    case prefix
    case word
  }
}
```

```swift
// TestKey.swift
import Dependencies
import SharedModels

extension DependencyValues {
  public var dictionary: DictionaryClient {
    get { self[DictionaryClient.self] }
    set { self[DictionaryClient.self] = newValue }
  }
}

extension DictionaryClient: TestDependencyKey {
  public static let previewValue = Self.everyString
  public static let testValue = Self()
}

extension DictionaryClient {
  /// Convenience value that accepts any string >= 3 chars
  public static let everyString = Self(
    contains: { word, _ in word.count >= 3 },
    load: { _ in true },
    lookup: nil,
    randomCubes: { _ in fatalError() },
    unload: { _ in }
  )
}
```

**Key Patterns:**
- Optional closure (`lookup`) for optional functionality
- Nested `Lookup` enum for return type
- Static convenience value (`everyString`) for testing
- Uses `fatalError()` for unimplemented test paths

---

### Example 15: ServerConfigClient (Simple - Factory Pattern)

A server config client with factory-based live implementation.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/ServerConfigClient/`](../references/isowords/Sources/ServerConfigClient/)
> - GitHub: [ServerConfigClient](https://github.com/pointfreeco/isowords/tree/main/Sources/ServerConfigClient)

```swift
// Client.swift
import DependenciesMacros
@_exported import ServerConfig

@DependencyClient
public struct ServerConfigClient {
  public var config: () -> ServerConfig = { ServerConfig() }
  public var refresh: @Sendable () async throws -> ServerConfig
}
```

```swift
// LiveKey.swift
import ComposableArchitecture
import Foundation
import ServerConfig

extension ServerConfigClient {
  /// Factory method for creating live client with custom fetch
  public static func live(
    fetch: @escaping @Sendable () async throws -> ServerConfig
  ) -> Self {
    Self(
      config: {
        /// Try to load from UserDefaults cache
        (UserDefaults.standard.object(forKey: serverConfigKey) as? Data)
          .flatMap { try? jsonDecoder.decode(ServerConfig.self, from: $0) }
          ?? ServerConfig()
      },
      refresh: {
        /// Fetch and cache to UserDefaults
        let config = try await fetch()
        if let data = try? jsonEncoder.encode(config) {
          UserDefaults.standard.set(data, forKey: serverConfigKey)
        }
        return config
      }
    )
  }
}

let jsonDecoder = JSONDecoder()
let jsonEncoder = JSONEncoder()

private let serverConfigKey = "co.pointfree.serverConfigKey"
```

```swift
// TestKey.swift
import Dependencies

extension DependencyValues {
  public var serverConfig: ServerConfigClient {
    get { self[ServerConfigClient.self] }
    set { self[ServerConfigClient.self] = newValue }
  }
}

extension ServerConfigClient: TestDependencyKey {
  public static let previewValue = Self.noop
  public static let testValue = Self()
}

extension ServerConfigClient {
  public static let noop = Self(
    config: { .init() },
    refresh: { try await Task.never() }
  )
}
```

**Key Patterns:**
- Factory method (`live(fetch:)`) for dependency injection
- UserDefaults caching with JSON encoding
- `@_exported import` for re-exporting types
- `Task.never()` for noop async throwing

---

### Example 16: LocalDatabaseClient (Complex - Database with Mock)

A database client with in-memory option and ActorIsolated mock.

> **📁 Source Files**
> - Local: [`references/isowords/Sources/LocalDatabaseClient/`](../references/isowords/Sources/LocalDatabaseClient/)
> - GitHub: [LocalDatabaseClient](https://github.com/pointfreeco/isowords/tree/main/Sources/LocalDatabaseClient)

```swift
// Interface.swift
import ComposableArchitecture
import Foundation
import SharedModels

@DependencyClient
public struct LocalDatabaseClient {
  public var fetchGamesForWord: @Sendable (String) async throws -> [LocalDatabaseClient.Game]
  public var fetchStats: @Sendable () async throws -> Stats
  public var fetchVocab: @Sendable () async throws -> Vocab
  public var migrate: @Sendable () async throws -> Void
  public var playedGamesCount: @Sendable (GameContext) async throws -> Int
  public var saveGame: @Sendable (CompletedGame) async throws -> Void

  /// Nested types for database entities
  public struct Game: Equatable {
    public var id: Int
    public var completedGame: CompletedGame
    public var gameMode: GameMode
    public var secondsPlayed: Int
    public var startedAt: Date
  }

  public struct Stats: Equatable {
    public var averageWordLength: Double?
    public var gamesPlayed = 0
    public var highestScoringWord: Word?
    public var highScoreTimed: Int?
    public var highScoreUnlimited: Int?
    public var longestWord: String?
    public var secondsPlayed = 0
    public var wordsFound = 0

    public struct Word: Equatable {
      public var letters: String
      public var score: Int
    }
  }

  public struct Vocab: Equatable {
    public var words: [Word]

    public struct Word: Equatable {
      public var letters: String
      public var playCount: Int
      public var score: Int
    }
  }

  public enum GameContext: String, Codable {
    case dailyChallenge
    case shared
    case solo
    case turnBased

    public init(gameContext: CompletedGame.GameContext) {
      switch gameContext {
      case .dailyChallenge: self = .dailyChallenge
      case .shared: self = .shared
      case .solo: self = .solo
      case .turnBased: self = .turnBased
      }
    }
  }
}

extension LocalDatabaseClient {
  /// Noop implementation using Task.never()
  public static let noop = Self(
    fetchGamesForWord: { _ in try await Task.never() },
    fetchStats: { try await Task.never() },
    fetchVocab: { try await Task.never() },
    migrate: {},
    playedGamesCount: { _ in try await Task.never() },
    saveGame: { _ in try await Task.never() }
  )
}
```

```swift
// InMemory.swift
#if DEBUG
import Foundation

extension LocalDatabaseClient {
  /// In-memory database for testing
  public static let inMemory = Self.live(path: URL(string: ":memory:")!)
}
#endif
```

```swift
// TestKey.swift
import ComposableArchitecture
import SharedModels

extension DependencyValues {
  public var database: LocalDatabaseClient {
    get { self[LocalDatabaseClient.self] }
    set { self[LocalDatabaseClient.self] = newValue }
  }
}

extension LocalDatabaseClient: TestDependencyKey {
  public static let previewValue = Self.mock
  public static let testValue = Self()
}

extension LocalDatabaseClient {
  /// Mock implementation with ActorIsolated state
  public static var mock: Self {
    let games = ActorIsolated<[CompletedGame]>([])

    return Self(
      fetchGamesForWord: { _ in [] },
      fetchStats: { Stats() },
      fetchVocab: { Vocab(words: []) },
      migrate: {},
      playedGamesCount: { _ in 10 },
      saveGame: { game in await games.withValue { $0.append(game) } }
    )
  }
}
```

**Key Patterns:**
- Multiple nested types for database entities
- `ActorIsolated` for thread-safe mock state
- In-memory database option for testing (`#if DEBUG`)
- `Task.never()` for noop async throwing
- Enum with `init(from:)` for type conversion

---

### Dependency Client Pattern Summary

| Pattern | When to Use | Examples |
|---------|-------------|----------|
| **Single-file** | Simple clients with 1-3 endpoints | Build, DeviceId |
| **Three-file** | Standard clients (Interface, Live, Test) | Most clients |
| **Actor-based** | Thread-safe state management | AudioPlayerClient |
| **AsyncStream** | Continuous value streaming | LowPowerModeClient, StoreKitClient |
| **Nested clients** | Hierarchical functionality | GameCenterClient |
| **Factory method** | Configurable live implementation | ServerConfigClient |
| **Override helpers** | Test mocking with expectations | FileClient, UserDefaultsClient, ApiClient |
| **Static convenience** | Common test configurations | LowPowerModeClient (`.true`, `.false`) |
| **Task.never()** | Noop for async throwing | ApiClient, ServerConfigClient |
| **ActorIsolated** | Thread-safe mock state | LocalDatabaseClient |

### Best Practices for Dependency Clients

1. **Use `@DependencyClient` macro** - Generates unimplemented defaults automatically
2. **Separate interface from implementation** - Interface in one file, live in another
3. **Provide `noop` for previews** - SwiftUI previews shouldn't make real calls
4. **Use `Task.never()` for async throwing noop** - Prevents accidental execution
5. **Add override helpers for testing** - Makes test setup cleaner
6. **Use `@MainActor.run` for UIKit** - Ensures main thread execution
7. **Bridge delegates to AsyncStream** - Modern async interface for delegate patterns
8. **Use actors for thread-safe state** - Especially for AVFoundation, Core Data
9. **Group related functionality** - Use nested clients for hierarchical APIs
10. **Use `@CasePathable` for events** - Enables pattern matching on event types

---

## Testing Strategies

> **📖 Source Documentation**
>
> - Local: [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Testing.md`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Testing.md)
> - SyncUps Tests: [`references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/)
> - GitHub: [SyncUps Tests](https://github.com/pointfreeco/swift-composable-architecture/tree/main/Examples/SyncUps/SyncUpsTests)

### TestStore Basics

Use `TestStore` for exhaustive testing:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpsListTests.swift:11-37
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUpsTests/SyncUpsListTests.swift#L11-L37

@MainActor
struct SyncUpsListTests {
  /// Enable deterministic async testing
  init() { uncheckedUseMainSerialExecutor = true }

  @Test
  func add() async throws {
    let store = TestStore(initialState: SyncUpsList.State()) {
      SyncUpsList()
    } withDependencies: {
      $0.uuid = .incrementing
    }

    var syncUp = SyncUp(
      id: SyncUp.ID(UUID(0)),
      attendees: [Attendee(id: Attendee.ID(UUID(1)))]
    )

    /// Send action and assert state changes
    await store.send(.addSyncUpButtonTapped) {
      $0.destination = .add(SyncUpForm.State(syncUp: syncUp))
    }

    syncUp.title = "Engineering"
    await store.send(\.destination.add.binding.syncUp, syncUp) {
      $0.destination?.modify(\.add) { $0.syncUp.title = "Engineering" }
    }

    await store.send(.confirmAddSyncUpButtonTapped) {
      $0.destination = nil
      /// Assert shared state mutation
      $0.$syncUps.withLock { $0 = [syncUp] }
    }
  }
}
```

**Key Points:**
- Use `@MainActor` and `uncheckedUseMainSerialExecutor = true`
- `TestStore` requires exhaustive state assertions
- Use trailing closure to assert state changes
- Use `$0.$sharedValue.withLock` for shared state

### Exhaustive vs Non-Exhaustive Testing

Choose the right testing mode:

```swift
// Exhaustive testing (default) - must assert all state changes
await store.send(.action) {
  $0.property = newValue
}

// Non-exhaustive testing - skip some assertions
store.exhaustivity = .off
await store.send(.action)
#expect(store.state.property == expectedValue)

// Or use withExhaustivity
await store.withExhaustivity(.off) {
  await store.send(.action)
}
```

**When to use non-exhaustive:**
- Integration tests with many state changes
- Testing specific behaviors without full state assertions
- Debugging complex flows

### Testing Effects with TestClock

Control time in tests:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/RecordMeetingTests.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUpsTests/RecordMeetingTests.swift

@Test
func timerTicks() async {
  let clock = TestClock()
  
  let store = TestStore(
    initialState: RecordMeeting.State(syncUp: Shared(value: .mock))
  ) {
    RecordMeeting()
  } withDependencies: {
    $0.continuousClock = clock
    $0.speechClient.authorizationStatus = { .denied }
  }

  await store.send(.onTask)
  
  /// Advance time manually
  await clock.advance(by: .seconds(1))
  await store.receive(\.timerTick) {
    $0.secondsElapsed = 1
  }

  await clock.advance(by: .seconds(1))
  await store.receive(\.timerTick) {
    $0.secondsElapsed = 2
  }
}
```

**Key Points:**
- Use `TestClock` for time-based effects
- `clock.advance(by:)` to control time
- `store.receive` to assert received actions

### Testing Navigation

Test navigation state changes:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpDetailTests.swift:11-35
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUpsTests/SyncUpDetailTests.swift#L11-L35

@Test
func edit() async {
  var syncUp = SyncUp.mock

  let store = TestStore(
    initialState: SyncUpDetail.State(syncUp: Shared(value: syncUp))
  ) {
    SyncUpDetail()
  } withDependencies: {
    $0.uuid = .incrementing
  }

  /// Test navigation to edit sheet
  await store.send(.editButtonTapped) {
    $0.destination = .edit(SyncUpForm.State(syncUp: syncUp))
  }

  syncUp.title = "Blob's Meeting"
  await store.send(\.destination.edit.binding.syncUp, syncUp) {
    $0.destination?.modify(\.edit) { $0.syncUp.title = "Blob's Meeting" }
  }

  await store.send(.doneEditingButtonTapped) {
    $0.destination = nil
    /// Assert shared state was updated
    $0.$syncUp.withLock { $0.title = "Blob's Meeting" }
  }
}
```

### Testing Shared State

Test features with shared state:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/SyncUpDetailTests.swift:117-135
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUpsTests/SyncUpDetailTests.swift#L117-L135

@Test
func delete() async throws {
  let syncUp = SyncUp.mock

  /// Override shared state for this test
  @Shared(.syncUps) var syncUps = [syncUp]
  defer { #expect(syncUps == []) }

  /// Get derived shared reference
  let sharedSyncUp = try #require(Shared($syncUps[id: syncUp.id]))

  let store = TestStore(
    initialState: SyncUpDetail.State(syncUp: sharedSyncUp)
  ) {
    SyncUpDetail()
  }

  await store.send(.deleteButtonTapped) {
    $0.destination = .alert(.deleteSyncUp)
  }

  await store.send(\.destination.alert.confirmDeletion) {
    $0.destination = nil
  }

  /// Verify dismissal
  #expect(store.isDismissed)
}
```

**Key Points:**
- Override `@Shared` at test start
- Use `defer` to verify final state
- Use `Shared($collection[id:])` for derived references
- Check `store.isDismissed` for dismissal

### Integration Testing

Test multiple features together:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/AppFeatureTests.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUpsTests/AppFeatureTests.swift

@Test
func recordMeetingFlow() async throws {
  let syncUp = SyncUp.mock
  @Shared(.syncUps) var syncUps = [syncUp]

  let store = TestStore(initialState: AppFeature.State()) {
    AppFeature()
  } withDependencies: {
    $0.continuousClock = ImmediateClock()
    $0.speechClient.authorizationStatus = { .denied }
    $0.uuid = .incrementing
  }

  /// Navigate to detail
  await store.send(\.syncUpsList.syncUpTapped, syncUp) {
    $0.path[id: 0] = .detail(SyncUpDetail.State(syncUp: Shared($syncUps[id: syncUp.id])!))
  }

  /// Start meeting
  await store.send(\.path[id: 0].detail.startMeetingButtonTapped)
  
  /// Receive delegate action
  await store.receive(\.path[id: 0].detail.delegate.startMeeting) {
    $0.path[id: 1] = .record(RecordMeeting.State(syncUp: Shared($syncUps[id: syncUp.id])!))
  }

  // ... continue testing the flow
}
```

---

## Modularization Patterns

> **📖 Source Documentation**
>
> - isowords Package.swift: [`references/isowords/Package.swift`](../references/isowords/Package.swift)
> - GitHub: [isowords Package.swift](https://github.com/pointfreeco/isowords/blob/main/Package.swift)

### isowords Module Structure

isowords demonstrates hyper-modularization with 86+ modules:

```
isowords/
├── Sources/
│   ├── AppFeature/           # Main app feature
│   ├── HomeFeature/          # Home screen
│   ├── GameCore/             # Core game logic
│   ├── GameOverFeature/      # Game over screen
│   ├── SettingsFeature/      # Settings
│   ├── LeaderboardFeature/   # Leaderboards
│   ├── OnboardingFeature/    # Onboarding flow
│   │
│   ├── ApiClient/            # API client interface
│   ├── ApiClientLive/        # Live API implementation
│   ├── AudioPlayerClient/    # Audio playback
│   ├── FileClient/           # File system access
│   ├── UserDefaultsClient/   # UserDefaults wrapper
│   │
│   ├── SharedModels/         # Shared data models
│   ├── ClientModels/         # Client-specific models
│   ├── ServerRouter/         # Shared routing
│   │
│   ├── Styleguide/           # UI components
│   ├── SwiftUIHelpers/       # SwiftUI utilities
│   ├── TcaHelpers/           # TCA utilities
│   │
│   └── TestHelpers/          # Test utilities
│
├── Tests/
│   ├── AppFeatureTests/
│   ├── GameCoreTests/
│   └── ...
│
└── App/
    ├── Previews/             # Preview apps
    │   ├── CubeCorePreview/
    │   ├── HomeFeaturePreview/
    │   └── ...
    └── isowords.xcodeproj
```

### Feature Module Pattern

Each feature is a self-contained module:

```swift
// Package.swift target definition
.target(
  name: "SettingsFeature",
  dependencies: [
    "ApiClient",
    "AudioPlayerClient",
    "Build",
    "ComposableStoreKit",
    "FileClient",
    "ServerConfigClient",
    "StatsFeature",
    "Styleguide",
    "SwiftUIHelpers",
    "TcaHelpers",
    "UIApplicationClient",
    "UserDefaultsClient",
    "UserSettingsClient",
    .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
  ],
  resources: [.process("Resources/")]
)
```

**Feature Module Contents:**
- Reducer with State, Action, and body
- SwiftUI View
- Any feature-specific models
- Resources (images, strings, etc.)

### Shared Models Module

Centralize shared data types:

```swift
// Source: references/isowords/Sources/SharedModels/
// GitHub: https://github.com/pointfreeco/isowords/tree/main/Sources/SharedModels

// Package.swift
.target(
  name: "SharedModels",
  dependencies: [
    "Build",
    "FirstPartyMocks",
    .product(name: "CasePaths", package: "swift-case-paths"),
    .product(name: "CustomDump", package: "swift-custom-dump"),
    .product(name: "Tagged", package: "swift-tagged"),
  ]
)
```

**Shared Models Include:**
- Core domain types (User, Game, Score, etc.)
- API request/response types
- Enums shared between client and server
- Type-safe identifiers using Tagged

### Client Modules

Separate interface from implementation:

```swift
// ApiClient/Client.swift - Interface
@DependencyClient
public struct ApiClient: Sendable {
  public var apiRequest: @Sendable (ServerRoute.Api.Route) async throws -> (Data, URLResponse)
  // ...
}

// ApiClientLive/Live.swift - Implementation
extension ApiClient: DependencyKey {
  public static var liveValue: Self {
    @Dependency(\.urlSession) var urlSession
    
    return Self(
      apiRequest: { route in
        let request = try router.request(for: .api(.init(route: route)))
        return try await urlSession.data(for: request)
      },
      // ...
    )
  }
}
```

**Benefits:**
- Features depend only on interface
- Easy to swap implementations
- Testable without network
- Clear separation of concerns

### Helper Modules

Create utility modules for reusable code:

```swift
// Source: references/isowords/Sources/TcaHelpers/
// GitHub: https://github.com/pointfreeco/isowords/tree/main/Sources/TcaHelpers

// TcaHelpers/FilterReducer.swift
extension Reducer {
  @inlinable
  public func filter(
    _ predicate: @escaping (State, Action) -> Bool
  ) -> some ReducerOf<Self> {
    _FilterReducer(base: self, predicate: predicate)
  }
}

@Reducer
public struct _FilterReducer<Base: Reducer> {
  @usableFromInline
  let base: Base

  @usableFromInline
  let predicate: (Base.State, Base.Action) -> Bool

  @inlinable
  public func reduce(
    into state: inout Base.State, action: Base.Action
  ) -> EffectOf<Base> {
    guard self.predicate(state, action) else { return .none }
    return self.base.reduce(into: &state, action: action)
  }
}
```

### Preview Apps

Create mini-apps for isolated feature development:

```swift
// Source: references/isowords/App/Previews/OnboardingPreview/OnboardingPreviewApp.swift
// GitHub: https://github.com/pointfreeco/isowords/blob/main/App/Previews/OnboardingPreview/OnboardingPreviewApp.swift

import ComposableArchitecture
import OnboardingFeature
import SwiftUI

@main
struct OnboardingPreviewApp: App {
  var body: some Scene {
    WindowGroup {
      OnboardingView(
        store: Store(initialState: Onboarding.State(presentationStyle: .firstLaunch)) {
          Onboarding()
        }
      )
    }
  }
}
```

**Benefits:**
- Faster build times (only build needed modules)
- Stable SwiftUI previews
- Test features in isolation
- Debug specific flows easily

---

## Higher-Order Reducers

> **📖 Source Documentation**
>
> - Case Study: [`references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/05-HigherOrderReducers-Recursion.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/05-HigherOrderReducers-Recursion.swift)
> - isowords TcaHelpers: [`references/isowords/Sources/TcaHelpers/`](../references/isowords/Sources/TcaHelpers/)
> - GitHub: [TcaHelpers](https://github.com/pointfreeco/isowords/tree/main/Sources/TcaHelpers)

### Filter Reducer

Conditionally run reducers based on state/action:

```swift
// Source: references/isowords/Sources/TcaHelpers/FilterReducer.swift
// GitHub: https://github.com/pointfreeco/isowords/blob/main/Sources/TcaHelpers/FilterReducer.swift

extension Reducer {
  /// Filter actions based on a predicate
  @inlinable
  public func filter(
    _ predicate: @escaping (State, Action) -> Bool
  ) -> some ReducerOf<Self> {
    _FilterReducer(base: self, predicate: predicate)
  }
}

@Reducer
public struct _FilterReducer<Base: Reducer> {
  @usableFromInline
  let base: Base

  @usableFromInline
  let predicate: (Base.State, Base.Action) -> Bool

  @inlinable
  public func reduce(
    into state: inout Base.State, action: Base.Action
  ) -> EffectOf<Base> {
    guard self.predicate(state, action) else { return .none }
    return self.base.reduce(into: &state, action: action)
  }
}

/// Usage in isowords GameCore
var body: some Reducer<State, Action> {
  self.core
    /// Only process actions when it's the player's turn
    .filterActionsForYourTurn()
}

extension Reducer where State == Game.State, Action == Game.Action {
  func filterActionsForYourTurn() -> some ReducerOf<Self> {
    self.filter { state, action in
      /// Allow certain actions regardless of turn
      switch action {
      case .destination, .gameCenter, .activeGames:
        return true
      default:
        return state.isYourTurn
      }
    }
  }
}
```

### Recursive Reducers

Handle tree-like data structures:

```swift
// Source: references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/05-HigherOrderReducers-Recursion.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/05-HigherOrderReducers-Recursion.swift

@Reducer
struct Nested {
  @ObservableState
  struct State: Equatable, Identifiable {
    let id: UUID
    var name: String = ""
    var children: IdentifiedArrayOf<State> = []
  }

  /// Indirect case for recursive actions
  indirect enum Action {
    case addChildButtonTapped
    case child(IdentifiedActionOf<Nested>)
    case deleteChildren(IndexSet)
    case nameTextFieldChanged(String)
  }

  @Dependency(\.uuid) var uuid

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .addChildButtonTapped:
        state.children.append(State(id: self.uuid()))
        return .none

      case .child:
        return .none

      case let .deleteChildren(indexSet):
        state.children.remove(atOffsets: indexSet)
        return .none

      case let .nameTextFieldChanged(name):
        state.name = name
        return .none
      }
    }
    /// Recursively apply self to children
    .forEach(\.children, action: \.child) {
      Self()
    }
  }
}
```

**Key Points:**
- Use `indirect enum` for recursive actions
- Use `IdentifiedArrayOf<State>` for children
- Apply `Self()` in `.forEach` for recursion

### Custom Reducer Modifiers

Create reusable reducer modifiers:

```swift
// Source: references/isowords/Sources/GameCore/Sounds.swift (conceptual)
// GitHub: https://github.com/pointfreeco/isowords/blob/main/Sources/GameCore/Sounds.swift

extension Reducer where State == Game.State, Action == Game.Action {
  /// Add sound effects to game actions
  func sounds() -> some ReducerOf<Self> {
    CombineReducers {
      self
      Reduce { state, action in
        switch action {
        case .wordSubmitButton(.delegate(.confirmSubmit)):
          return .run { _ in
            @Dependency(\.audioPlayer) var audioPlayer
            await audioPlayer.play(.wordSubmit)
          }
        case .cubeSelected:
          return .run { _ in
            @Dependency(\.audioPlayer) var audioPlayer
            await audioPlayer.play(.cubeSelect)
          }
        default:
          return .none
        }
      }
    }
  }
}

/// Usage
var body: some Reducer<State, Action> {
  self.core
    .sounds()
}
```

---

## Binding Patterns

> **📖 Source Documentation**
>
> - Local: [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Bindings.md`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/Articles/Bindings.md)
> - Case Study: [`references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Bindings-Basics.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Bindings-Basics.swift)

### BindingReducer

Handle binding actions automatically:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpForm.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpForm.swift

@Reducer
struct SyncUpForm {
  @ObservableState
  struct State: Equatable {
    var focus: Field? = .title
    var syncUp: SyncUp

    enum Field: Hashable {
      case attendee(Attendee.ID)
      case title
    }
  }

  enum Action: BindableAction {
    case addAttendeeButtonTapped
    case binding(BindingAction<State>)
    case deleteAttendees(atOffsets: IndexSet)
  }

  var body: some ReducerOf<Self> {
    /// Handle all binding actions
    BindingReducer()
    
    Reduce { state, action in
      switch action {
      case .addAttendeeButtonTapped:
        let attendee = Attendee(id: Attendee.ID())
        state.syncUp.attendees.append(attendee)
        state.focus = .attendee(attendee.id)
        return .none

      case .binding:
        return .none

      case let .deleteAttendees(atOffsets: indices):
        state.syncUp.attendees.remove(atOffsets: indices)
        return .none
      }
    }
  }
}
```

**Key Points:**
- Conform `Action` to `BindableAction`
- Add `case binding(BindingAction<State>)`
- Include `BindingReducer()` in body
- Handle `.binding` case (usually returns `.none`)

### Two-Way Bindings in Views

Create bindings from store:

```swift
// Source: references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpForm.swift
// GitHub: https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpForm.swift

struct SyncUpFormView: View {
  @Bindable var store: StoreOf<SyncUpForm>
  @FocusState var focus: SyncUpForm.State.Field?

  var body: some View {
    Form {
      Section {
        /// Two-way binding with .sending
        TextField("Title", text: $store.syncUp.title.sending(\.binding))
        
        /// Or use the shorthand
        TextField("Title", text: $store.syncUp.title)
        
        HStack {
          Slider(value: $store.syncUp.duration.minutes, in: 5...30, step: 1) {
            Text("Length")
          }
          Spacer()
          Text(store.syncUp.duration.formatted(.units()))
        }
        
        ThemePicker(selection: $store.syncUp.theme)
      }
      
      Section {
        ForEach($store.syncUp.attendees) { $attendee in
          TextField("Name", text: $attendee.name)
            .focused($focus, equals: .attendee(attendee.id))
        }
        .onDelete { indices in
          store.send(.deleteAttendees(atOffsets: indices))
        }
      }
    }
    /// Sync focus state
    .bind($store.focus, to: $focus)
  }
}
```

### onChange Modifier

React to state changes:

```swift
// Source: references/isowords/Sources/GameCore/GameCore.swift (simplified)
// GitHub: https://github.com/pointfreeco/isowords/blob/main/Sources/GameCore/GameCore.swift

var body: some Reducer<State, Action> {
  CombineReducers {
    BindingReducer()
    
    Reduce { state, action in
      // ... main logic
    }
  }
  /// React when selected word changes
  .onChange(of: \.selectedWord) { oldValue, newValue in
    Reduce { state, _ in
      state.selectedWordIsValid = self.dictionary.contains(newValue)
      return .none
    }
  }
  /// React when user settings change
  .onChange(of: \.userSettings) { _, userSettings in
    Reduce { state, _ in
      state.enableHaptics = userSettings.enableHaptics
      return .none
    }
  }
}
```

---

## Real-World Patterns from isowords

> **📖 Source**
>
> - isowords: [`references/isowords/`](../references/isowords/)
> - GitHub: [isowords](https://github.com/pointfreeco/isowords)

### Complex Game State Management

isowords demonstrates managing complex game state:

```swift
// Source: references/isowords/Sources/GameCore/GameCore.swift (simplified)
// GitHub: https://github.com/pointfreeco/isowords/blob/main/Sources/GameCore/GameCore.swift

@Reducer
public struct Game {
  /// Multiple destination types with ephemeral cases
  @Reducer(state: .equatable)
  public enum Destination {
    case alert(AlertState<Alert>)
    /// Ephemeral - doesn't need state persistence
    @ReducerCaseEphemeral
    case bottomMenu(BottomMenuState<BottomMenu>)
    case gameOver(GameOver)
    case settings(Settings)
    case upgradeInterstitial(UpgradeInterstitial)

    public enum Alert: Equatable { /* ... */ }
    public enum BottomMenu: Equatable { /* ... */ }
  }

  @ObservableState
  public struct State: Equatable {
    @Presents public var destination: Destination.State?
    @Shared(.userSettings) public var userSettings = UserSettings()
    
    public var cubes: Puzzle
    public var gameMode: GameMode
    public var moves: Moves
    public var selectedWord: String
    public var selectedWordIsValid: Bool
    // ... many more properties
  }

  public var body: some Reducer<State, Action> {
    self.core
      /// React to word selection changes
      .onChange(of: \.selectedWord) { _, selectedWord in
        Reduce { state, _ in
          state.selectedWordIsValid = self.dictionary.contains(selectedWord)
          return .none
        }
      }
      /// Filter actions based on turn
      .filterActionsForYourTurn()
      /// Handle destinations
      .ifLet(\.$destination, action: \.destination) {
        Destination.body
          .dependency(\.dismissGame, self.dismiss)
      }
      /// Add sound effects
      .sounds()
  }

  /// Core logic separated for clarity
  @ReducerBuilder<State, Action>
  var core: some Reducer<State, Action> {
    Reduce { state, action in
      switch action {
      // ... extensive game logic
      }
    }
    /// Compose child features
    Scope(state: \.wordSubmitButtonFeature, action: \.wordSubmitButton) {
      WordSubmitButtonFeature()
    }
    GameOverLogic()
    TurnBasedLogic()
    ActiveGamesTray()
  }
}
```

**Key Patterns:**
- `@ReducerCaseEphemeral` for transient UI state
- Separate `core` computed property for main logic
- Multiple child reducers composed with `Scope`
- Custom reducer modifiers (`.filterActionsForYourTurn()`, `.sounds()`)
- `@Shared` for persisted user settings

### App Delegate Integration

Handle app lifecycle events:

```swift
// Source: references/isowords/Sources/AppFeature/AppDelegate.swift (simplified)
// GitHub: https://github.com/pointfreeco/isowords/blob/main/Sources/AppFeature/AppDelegate.swift

@Reducer
public struct AppDelegateReducer {
  public enum Action {
    case didFinishLaunching
    case didRegisterForRemoteNotifications(Result<Data, Error>)
    case userNotifications(UserNotificationClient.DelegateEvent)
  }

  @Dependency(\.apiClient) var apiClient
  @Dependency(\.userNotifications) var userNotifications

  public var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .didFinishLaunching:
        return .run { send in
          /// Request notification permissions
          let settings = await self.userNotifications.getNotificationSettings()
          if settings.authorizationStatus == .authorized {
            await MainActor.run {
              UIApplication.shared.registerForRemoteNotifications()
            }
          }
          
          /// Start listening for notification events
          for await event in self.userNotifications.delegate() {
            await send(.userNotifications(event))
          }
        }

      case let .didRegisterForRemoteNotifications(.success(tokenData)):
        return .run { _ in
          try await self.apiClient.registerPushToken(tokenData)
        }

      case .didRegisterForRemoteNotifications(.failure):
        return .none

      case .userNotifications:
        return .none
      }
    }
  }
}

/// Compose into main app reducer
@Reducer
public struct AppFeature {
  public var body: some ReducerOf<Self> {
    Scope(state: \.appDelegate, action: \.appDelegate) {
      AppDelegateReducer()
    }
    
    Reduce { state, action in
      // ... main app logic
    }
  }
}
```

### Settings Feature Pattern

Comprehensive settings with multiple sections:

```swift
// Source: references/isowords/Sources/SettingsFeature/Settings.swift (simplified)
// GitHub: https://github.com/pointfreeco/isowords/blob/main/Sources/SettingsFeature/Settings.swift

@Reducer
public struct Settings {
  @Reducer
  public enum Destination {
    case alert(AlertState<Alert>)
    case developer(Developer)
    case leaderboard(Leaderboard)
    case stats(Stats)
    case purchaseConfirmation(PurchaseConfirmation)

    public enum Alert: Equatable {
      case confirmLogout
      case confirmRestore
    }
  }

  @ObservableState
  public struct State: Equatable {
    @Presents public var destination: Destination.State?
    @Shared(.userSettings) public var userSettings = UserSettings()
    @SharedReader(.build) public var build = Build()
    
    public var isPurchasing = false
    public var isRestoring = false
    
    /// Computed properties for derived state
    public var isFullGamePurchased: Bool {
      self.fullGameProduct?.purchased ?? false
    }
  }

  public var body: some ReducerOf<Self> {
    CombineReducers {
      BindingReducer()
      
      Reduce { state, action in
        switch action {
        case .binding(\.userSettings.enableHaptics):
          /// React to haptics toggle
          return .run { [enabled = state.userSettings.enableHaptics] _ in
            @Dependency(\.feedbackGenerator) var feedbackGenerator
            if enabled {
              await feedbackGenerator.selectionChanged()
            }
          }

        case .logoutButtonTapped:
          state.destination = .alert(.confirmLogout)
          return .none

        case .destination(.presented(.alert(.confirmLogout))):
          return .run { _ in
            @Dependency(\.apiClient) var apiClient
            await apiClient.logout()
          }

        // ... more cases
        }
      }
    }
    .ifLet(\.$destination, action: \.destination)
  }
}
```

---

## Best Practices Summary

### State Design

1. **Use `@ObservableState`** for automatic SwiftUI observation
2. **Use `IdentifiedArrayOf`** instead of plain arrays for collections
3. **Use `@Presents`** for optional child state
4. **Use `@Shared`** for persisted or shared state
5. **Keep state flat** - avoid deep nesting
6. **Make state `Equatable`** for testing

### Action Design

1. **Use past tense** for user actions (`buttonTapped`, not `tapButton`)
2. **Group related actions** with nested enums
3. **Use `Delegate` enum** for child-to-parent communication
4. **Mark actions as `Sendable`** for concurrency safety
5. **Use `BindableAction`** for forms with many bindings

### Effect Design

1. **Capture state values** in effect closures
2. **Use cancellation IDs** for cancellable effects
3. **Use `TestClock`** for time-based effects
4. **Handle errors** with the `catch:` parameter
5. **Use `.debounce`** for rapid user input

### Testing

1. **Use `@MainActor`** and `uncheckedUseMainSerialExecutor = true`
2. **Override dependencies** in `withDependencies`
3. **Use `TestClock`** for time control
4. **Use exhaustive testing** for critical paths
5. **Use non-exhaustive testing** for integration tests
6. **Test shared state** with `$0.$sharedValue.withLock`

### Modularization

1. **Separate interface from implementation** for clients
2. **Create feature modules** with reducer + view
3. **Create shared models module** for domain types
4. **Create helper modules** for reusable utilities
5. **Create preview apps** for isolated development
6. **Keep dependencies minimal** per module

---

## Reference Quick Links

### Local Repository References

| Resource | Local Path |
|----------|------------|
| TCA Documentation | [`references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/`](../references/swift-composable-architecture/Sources/ComposableArchitecture/Documentation.docc/) |
| SyncUps Example | [`references/swift-composable-architecture/Examples/SyncUps/`](../references/swift-composable-architecture/Examples/SyncUps/) |
| Case Studies | [`references/swift-composable-architecture/Examples/CaseStudies/`](../references/swift-composable-architecture/Examples/CaseStudies/) |
| isowords | [`references/isowords/`](../references/isowords/) |
| Swift Sharing | [`references/swift-sharing/`](../references/swift-sharing/) |
| Swift Dependencies | [`references/swift-dependencies/`](../references/swift-dependencies/) |

### External Documentation Links

| Resource | URL |
|----------|-----|
| TCA Documentation | [pointfreeco.github.io/swift-composable-architecture](https://pointfreeco.github.io/swift-composable-architecture/main/documentation/composablearchitecture/) |
| Swift Sharing | [swiftpackageindex.com/pointfreeco/swift-sharing](https://swiftpackageindex.com/pointfreeco/swift-sharing/main/documentation/sharing/) |
| Swift Dependencies | [swiftpackageindex.com/pointfreeco/swift-dependencies](https://swiftpackageindex.com/pointfreeco/swift-dependencies/main/documentation/dependencies/) |
| Point-Free Videos | [pointfree.co](https://www.pointfree.co) |
| isowords GitHub | [github.com/pointfreeco/isowords](https://github.com/pointfreeco/isowords) |

### Key Source Files

| Topic | Local Path | GitHub Link |
|-------|------------|-------------|
| Counter (Basic) | [`Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Counter.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Counter.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/01-GettingStarted-Counter.swift) |
| Effects Basics | [`Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Basics.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Basics.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Basics.swift) |
| Effects Cancellation | [`Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Cancellation.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Cancellation.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/03-Effects-Cancellation.swift) |
| Navigation Stack | [`Examples/CaseStudies/SwiftUICaseStudies/04-NavigationStack.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/04-NavigationStack.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/04-NavigationStack.swift) |
| Multiple Destinations | [`Examples/CaseStudies/SwiftUICaseStudies/04-Navigation-Multiple-Destinations.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/04-Navigation-Multiple-Destinations.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/04-Navigation-Multiple-Destinations.swift) |
| Recursive Reducers | [`Examples/CaseStudies/SwiftUICaseStudies/05-HigherOrderReducers-Recursion.swift`](../references/swift-composable-architecture/Examples/CaseStudies/SwiftUICaseStudies/05-HigherOrderReducers-Recursion.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/CaseStudies/SwiftUICaseStudies/05-HigherOrderReducers-Recursion.swift) |
| SyncUpsList | [`Examples/SyncUps/SyncUps/SyncUpsList.swift`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpsList.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpsList.swift) |
| SyncUpDetail | [`Examples/SyncUps/SyncUps/SyncUpDetail.swift`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/SyncUpDetail.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/SyncUpDetail.swift) |
| RecordMeeting | [`Examples/SyncUps/SyncUps/RecordMeeting.swift`](../references/swift-composable-architecture/Examples/SyncUps/SyncUps/RecordMeeting.swift) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/blob/main/Examples/SyncUps/SyncUps/RecordMeeting.swift) |
| SyncUps Tests | [`Examples/SyncUps/SyncUpsTests/`](../references/swift-composable-architecture/Examples/SyncUps/SyncUpsTests/) | [GitHub](https://github.com/pointfreeco/swift-composable-architecture/tree/main/Examples/SyncUps/SyncUpsTests) |
| isowords GameCore | [`isowords/Sources/GameCore/GameCore.swift`](../references/isowords/Sources/GameCore/GameCore.swift) | [GitHub](https://github.com/pointfreeco/isowords/blob/main/Sources/GameCore/GameCore.swift) |
| isowords ApiClient | [`isowords/Sources/ApiClient/Client.swift`](../references/isowords/Sources/ApiClient/Client.swift) | [GitHub](https://github.com/pointfreeco/isowords/blob/main/Sources/ApiClient/Client.swift) |
| isowords TcaHelpers | [`isowords/Sources/TcaHelpers/`](../references/isowords/Sources/TcaHelpers/) | [GitHub](https://github.com/pointfreeco/isowords/tree/main/Sources/TcaHelpers) |
| isowords Package.swift | [`isowords/Package.swift`](../references/isowords/Package.swift) | [GitHub](https://github.com/pointfreeco/isowords/blob/main/Package.swift) |

---

## Related Guides

- [Swift Sharing State Comprehensive Guide](./swift-sharing-state-comprehensive-guide.md) - Detailed guide on `@Shared` and persistence strategies