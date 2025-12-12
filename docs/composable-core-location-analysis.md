# Composable Core Location - Comprehensive Analysis

**Date:** December 10, 2025  
**Purpose:** Analysis for updating composable-core-location to latest Point-Free dependencies

---

## Executive Summary

The `composable-core-location` library is significantly outdated, using TCA version 0.43.0 while the current TCA is 1.x with Swift 6 support. The library needs a complete modernization to adopt:

- Modern `@DependencyClient` macro pattern
- `DependencyKey` / `TestDependencyKey` protocols
- Swift 6 language mode and concurrency
- Updated Effect types (no more `EffectPublisher`)

---

## 1. Current State Summary

### Package.swift Configuration

| Property            | Current Value                               | Latest Value                         |
| ------------------- | ------------------------------------------- | ------------------------------------ |
| Swift Tools Version | 5.6                                         | 6.0                                  |
| TCA Dependency      | 0.43.0                                      | 1.x (uses swift-dependencies 1.4.0+) |
| Platforms           | iOS 13+, macOS 10.15+, tvOS 13+, watchOS 6+ | Same (compatible)                    |

### Current Dependencies

```swift
.package(
  url: "https://github.com/pointfreeco/swift-composable-architecture",
  .upToNextMajor(from: "0.43.0"))
```

### Latest TCA Dependencies (for reference)

```swift
.package(url: "https://github.com/pointfreeco/swift-dependencies", from: "1.4.0"),
.package(url: "https://github.com/pointfreeco/swift-sharing", "1.0.4"..<"3.0.0"),
// Plus many others...
```

---

## 2. Library Structure

### Source Files (`Sources/ComposableCoreLocation/`)

| File                                                                                                                                             | Purpose                                          | Needs Update                   |
| ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------ | ------------------------------ |
| [`Interface.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Interface.swift)                                       | Main `LocationManager` struct with all endpoints | **Major**                      |
| [`Live.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Live.swift)                                                 | Live implementation with `CLLocationManager`     | **Major**                      |
| [`Failing.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Failing.swift)                                           | Failing test implementation                      | **Remove** (replaced by macro) |
| [`Internal/Deprecations.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Internal/Deprecations.swift)               | Deprecated APIs                                  | **Remove**                     |
| [`Internal/Exports.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Internal/Exports.swift)                         | Re-exports                                       | **Update**                     |
| [`Models/Location.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Models/Location.swift)                           | Location wrapper type                            | Minor (add Sendable)           |
| [`Models/Region.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Models/Region.swift)                               | Region wrapper type                              | Minor (add Sendable)           |
| [`Models/Heading.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Models/Heading.swift)                             | Heading wrapper type                             | Minor (add Sendable)           |
| [`Models/Beacon.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Models/Beacon.swift)                               | Beacon wrapper type                              | Minor (add Sendable)           |
| [`Models/Visit.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Models/Visit.swift)                                 | Visit wrapper type                               | Minor (add Sendable)           |
| [`Models/AccuracyAuthorization.swift`](../references/composable-core-location/Sources/ComposableCoreLocation/Models/AccuracyAuthorization.swift) | Accuracy authorization enum                      | Minor (add Sendable)           |

### Test Files (`Tests/ComposableCoreLocationTests/`)

| File                                                                                                                                              | Purpose                       | Needs Update |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------ |
| [`ComposableCoreLocationTests.swift`](../references/composable-core-location/Tests/ComposableCoreLocationTests/ComposableCoreLocationTests.swift) | Model encoding/equality tests | Minor        |

### Example Files (`Examples/LocationManager/`)

| File                                                                                                                                     | Purpose                 | Needs Update |
| ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | ------------ |
| [`Common/AppCore.swift`](../references/composable-core-location/Examples/LocationManager/Common/AppCore.swift)                           | Example TCA reducer     | **Major**    |
| [`Common/LocalSearchClient/`](../references/composable-core-location/Examples/LocationManager/Common/LocalSearchClient/)                 | Local search dependency | **Major**    |
| [`Mobile/LocationManagerView.swift`](../references/composable-core-location/Examples/LocationManager/Mobile/LocationManagerView.swift)   | iOS view                | **Major**    |
| [`Desktop/LocationManagerView.swift`](../references/composable-core-location/Examples/LocationManager/Desktop/LocationManagerView.swift) | macOS view              | **Major**    |
| [`Package.swift`](../references/composable-core-location/Examples/Package.swift)                                                         | Example package         | **Update**   |

---

## 3. Current API Patterns (Outdated)

### Current Pattern: Struct with Closure Properties

```swift
// Current: Interface.swift
public struct LocationManager {
  public var accuracyAuthorization: () -> AccuracyAuthorization?
  public var authorizationStatus: () -> CLAuthorizationStatus
  public var delegate: () -> EffectPublisher<Action, Never>
  public var requestLocation: () -> EffectPublisher<Never, Never>
  // ... many more closure properties
}
```

### Current Pattern: Manual Failing Implementation

```swift
// Current: Failing.swift
extension LocationManager {
  public static let failing = Self(
    accuracyAuthorization: {
      XCTFail("A failing endpoint was accessed: 'LocationManager.accuracyAuthorization'")
      return nil
    },
    // ... manually defined for each endpoint
  )
}
```

### Current Pattern: Environment-based Dependency Injection

```swift
// Current: AppCore.swift (Example)
public struct AppEnvironment {
  public var localSearch: LocalSearchClient
  public var locationManager: LocationManager
}

public let appReducer = AnyReducer<AppState, AppAction, AppEnvironment> {
  state, action, environment in
  // Uses environment.locationManager
}
```

### Current Pattern: EffectPublisher with Combine

```swift
// Current: Live.swift
let delegate = EffectPublisher<Action, Never>.run { subscriber in
  let delegate = LocationManagerDelegate(subscriber)
  manager.delegate = delegate
  return AnyCancellable { _ = delegate }
}
.share()
.eraseToEffect()
```

---

## 4. Modern TCA Patterns (Target)

### Modern Pattern: @DependencyClient Macro

```swift
// Target: Interface.swift
import DependenciesMacros

@DependencyClient
public struct LocationManager: Sendable {
  public var accuracyAuthorization: @Sendable () -> AccuracyAuthorization? = { nil }
  public var authorizationStatus: @Sendable () -> CLAuthorizationStatus = { .notDetermined }
  public var delegate: @Sendable () async -> AsyncStream<Action> = { .finished }
  public var requestLocation: @Sendable () async -> Void
  // ... endpoints with default values or unimplemented
}
```

### Modern Pattern: DependencyKey Protocol

```swift
// Target: TestKey.swift (new file)
import Dependencies

extension DependencyValues {
  public var locationManager: LocationManager {
    get { self[LocationManager.self] }
    set { self[LocationManager.self] = newValue }
  }
}

extension LocationManager: TestDependencyKey {
  public static let previewValue = Self()
  public static let testValue = Self()
}
```

### Modern Pattern: DependencyKey for Live Value

```swift
// Target: LiveKey.swift (new file)
import Dependencies

extension LocationManager: DependencyKey {
  public static var liveValue: Self {
    // Live implementation
  }
}
```

### Modern Pattern: @Dependency Property Wrapper

```swift
// Target: Modern reducer usage
@Reducer
struct AppFeature {
  @Dependency(\.locationManager) var locationManager

  var body: some ReducerOf<Self> {
    Reduce { state, action in
      switch action {
      case .requestLocation:
        return .run { _ in
          await locationManager.requestLocation()
        }
      }
    }
  }
}
```

### Modern Pattern: AsyncStream for Delegates

```swift
// Target: Live.swift
public static var liveValue: Self {
  let manager = CLLocationManager()

  return Self(
    delegate: {
      AsyncStream { continuation in
        let delegate = Delegate(continuation: continuation)
        manager.delegate = delegate
        continuation.onTermination = { _ in
          _ = delegate  // prevent deallocation
        }
      }
    },
    requestLocation: {
      manager.requestLocation()
    }
    // ...
  )
}
```

---

## 5. Specific Changes Required

### 5.1 Package.swift Changes

```swift
// FROM:
// swift-tools-version:5.6
.package(url: "https://github.com/pointfreeco/swift-composable-architecture", .upToNextMajor(from: "0.43.0"))

// TO:
// swift-tools-version:6.0
.package(url: "https://github.com/pointfreeco/swift-composable-architecture", from: "1.17.0"),
// OR just swift-dependencies if we want minimal dependency:
.package(url: "https://github.com/pointfreeco/swift-dependencies", from: "1.4.0"),
```

### 5.2 Interface.swift Changes

| Current                                | Target                                                      |
| -------------------------------------- | ----------------------------------------------------------- |
| `public struct LocationManager`        | `@DependencyClient public struct LocationManager: Sendable` |
| `() -> EffectPublisher<Action, Never>` | `@Sendable () async -> AsyncStream<Action>`                 |
| `() -> EffectPublisher<Never, Never>`  | `@Sendable () async -> Void`                                |
| Manual closure properties              | Macro-generated with defaults                               |
| `LocationManager.Action` enum          | Keep but add `Sendable` conformance                         |
| `LocationManager.Error` struct         | Keep but add `Sendable` conformance                         |

### 5.3 Live.swift Changes

| Current                                              | Target                                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------- |
| `public static var live: Self`                       | `extension LocationManager: DependencyKey { static var liveValue: Self }` |
| `EffectPublisher<Action, Never>.run { subscriber in` | `AsyncStream { continuation in`                                           |
| `subscriber.send(.didUpdateLocations(...))`          | `continuation.yield(.didUpdateLocations(...))`                            |
| `AnyCancellable { }`                                 | `continuation.onTermination = { }`                                        |
| `.fireAndForget { }`                                 | Direct async call                                                         |

### 5.4 Failing.swift - REMOVE

The `@DependencyClient` macro automatically generates unimplemented/failing versions. This file should be deleted entirely.

### 5.5 Deprecations.swift - REMOVE

All deprecated APIs should be removed in a major version update.

### 5.6 New Files to Create

| File            | Purpose                                                              |
| --------------- | -------------------------------------------------------------------- |
| `TestKey.swift` | `DependencyValues` extension and `TestDependencyKey` conformance     |
| `LiveKey.swift` | `DependencyKey` conformance with `liveValue` (or keep in Live.swift) |

### 5.7 Model Updates (All Models)

Add `Sendable` conformance to all model types:

```swift
// Current:
public struct Location {

// Target:
public struct Location: Sendable {
```

### 5.8 Exports.swift Changes

```swift
// Current:
@_exported import ComposableArchitecture
@_exported import CoreLocation

// Target:
@_exported import Dependencies
@_exported import DependenciesMacros
@_exported import CoreLocation
```

---

## 6. Example App Changes

### AppCore.swift - Complete Rewrite Required

```swift
// FROM (Current):
public struct AppEnvironment {
  public var localSearch: LocalSearchClient
  public var locationManager: LocationManager
}

public let appReducer = AnyReducer<AppState, AppAction, AppEnvironment> {
  state, action, environment in
  // ...
}

// TO (Target):
@Reducer
public struct AppFeature {
  @ObservableState
  public struct State: Equatable {
    // ...
  }

  public enum Action {
    // ...
  }

  @Dependency(\.locationManager) var locationManager
  @Dependency(\.localSearch) var localSearch

  public var body: some ReducerOf<Self> {
    Reduce { state, action in
      // ...
    }
  }
}
```

---

## 7. Breaking Changes Summary

1. **API Signature Changes**: All closure-based endpoints become async functions
2. **Effect Type Changes**: `EffectPublisher<Never, Never>` → `Void` async functions
3. **Delegate Pattern**: `EffectPublisher<Action, Never>` → `AsyncStream<Action>`
4. **Dependency Injection**: Environment-based → `@Dependency` property wrapper
5. **Reducer Pattern**: `AnyReducer` → `@Reducer` macro
6. **Failing Implementation**: Manual → Macro-generated
7. **Sendable Requirements**: All types must be `Sendable`

---

## 8. Recommended Update Approach

### Phase 1: Package Infrastructure

1. Update `Package.swift` to Swift 6.0 tools version
2. Update TCA dependency to 1.17.0+
3. Add `DependenciesMacros` product dependency
4. Update platform requirements if needed

### Phase 2: Core Library

1. Add `Sendable` conformance to all model types
2. Rewrite `Interface.swift` with `@DependencyClient` macro
3. Rewrite `Live.swift` with `DependencyKey` and async patterns
4. Create `TestKey.swift` with `TestDependencyKey` conformance
5. Delete `Failing.swift`
6. Delete `Internal/Deprecations.swift`
7. Update `Internal/Exports.swift`

### Phase 3: Tests

1. Update test imports
2. Verify model tests still pass
3. Add new tests for dependency registration

### Phase 4: Examples

1. Rewrite `AppCore.swift` with `@Reducer` macro
2. Update `LocalSearchClient` to modern pattern
3. Update views to use modern Store APIs
4. Update example `Package.swift`

### Phase 5: Documentation

1. Update `README.md` with modern usage examples
2. Update inline documentation
3. Add migration guide for existing users

---

## 9. Files Modification Summary

| File                                                         | Action                | Priority |
| ------------------------------------------------------------ | --------------------- | -------- |
| `Package.swift`                                              | Update                | High     |
| `Sources/ComposableCoreLocation/Interface.swift`             | Rewrite               | High     |
| `Sources/ComposableCoreLocation/Live.swift`                  | Rewrite               | High     |
| `Sources/ComposableCoreLocation/Failing.swift`               | Delete                | High     |
| `Sources/ComposableCoreLocation/Internal/Deprecations.swift` | Delete                | High     |
| `Sources/ComposableCoreLocation/Internal/Exports.swift`      | Update                | High     |
| `Sources/ComposableCoreLocation/TestKey.swift`               | Create                | High     |
| `Sources/ComposableCoreLocation/Models/*.swift`              | Update (add Sendable) | Medium   |
| `Tests/ComposableCoreLocationTests/*.swift`                  | Update                | Medium   |
| `Examples/LocationManager/Common/AppCore.swift`              | Rewrite               | Medium   |
| `Examples/LocationManager/Common/LocalSearchClient/*.swift`  | Rewrite               | Medium   |
| `Examples/LocationManager/Mobile/*.swift`                    | Update                | Low      |
| `Examples/LocationManager/Desktop/*.swift`                   | Update                | Low      |
| `Examples/Package.swift`                                     | Update                | Low      |
| `README.md`                                                  | Rewrite               | Medium   |

---

## 10. Reference Implementations

For implementation guidance, refer to:

- **Modern Client Pattern**: [`references/isowords/Sources/AudioPlayerClient/Client.swift`](../references/isowords/Sources/AudioPlayerClient/Client.swift)
- **DependencyKey Pattern**: [`references/isowords/Sources/AudioPlayerClient/TestKey.swift`](../references/isowords/Sources/AudioPlayerClient/TestKey.swift)
- **Live Implementation**: [`references/isowords/Sources/AudioPlayerClient/LiveKey.swift`](../references/isowords/Sources/AudioPlayerClient/LiveKey.swift)
- **DependencyKey Protocol**: [`references/swift-dependencies/Sources/Dependencies/DependencyKey.swift`](../references/swift-dependencies/Sources/Dependencies/DependencyKey.swift)
- **TCA Package Structure**: [`references/swift-composable-architecture/Package.swift`](../references/swift-composable-architecture/Package.swift)

---

## 11. Estimated Effort

| Phase                           | Estimated Time  |
| ------------------------------- | --------------- |
| Phase 1: Package Infrastructure | 1-2 hours       |
| Phase 2: Core Library           | 4-6 hours       |
| Phase 3: Tests                  | 1-2 hours       |
| Phase 4: Examples               | 3-4 hours       |
| Phase 5: Documentation          | 2-3 hours       |
| **Total**                       | **11-17 hours** |

---

## 12. Risks and Considerations

1. **Breaking Changes**: This is a major version update; all existing users will need to migrate
2. **Swift 6 Concurrency**: Strict concurrency checking may reveal additional issues
3. **Platform Compatibility**: Ensure async/await patterns work on all supported platforms
4. **CLLocationManager Thread Safety**: The live implementation needs careful handling for main actor requirements
5. **Delegate Lifecycle**: AsyncStream continuation management requires careful memory handling
