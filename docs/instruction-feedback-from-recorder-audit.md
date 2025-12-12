# Instruction Feedback from Phase 2.1 TCA Audit

**Date:** 2025-12-12  
**Context:** Refactoring AppFeature to use the `@Reducer enum Destination` pattern  
**Files Modified:** `AppFeature.swift`, `ContentView.swift`

---

## Issues Encountered

### 1. TCA Macro Syntax Discrepancy (High Impact)

**Problem:** Task instructions showed `@Reducer enum Destination` syntax, but the actual TCA library uses `@Reducer(state: .equatable) enum Destination`.

**Evidence:** The isowords reference code at [`references/isowords/Sources/AppFeature/AppView.swift`](references/isowords/Sources/AppFeature/AppView.swift) uses the correct syntax:

```swift
@Reducer(state: .equatable)
enum Destination {
  case game(Game)
  case onboarding(Onboarding)
  // ...
}
```

**Impact:** Without the `(state: .equatable)` parameter, the macro doesn't generate the necessary `Destination.State` enum with proper `Equatable` conformance, causing compilation errors.

**Recommendation:** Update [`docs/tca-best-practices-comprehensive-guide.md`](docs/tca-best-practices-comprehensive-guide.md) lines 920-1019 to show the actual macro syntax with `(state: .equatable)` parameter.

---

### 2. Preview Code Type Inference Issue (Medium Impact)

**Problem:** When using `@Reducer(state: .equatable) enum Destination`, the macro generates a separate `Destination.State` enum type. This makes it difficult to create SwiftUI previews that show the destination state already presented.

**What was attempted:**

```swift
// Attempt 1: Direct case construction
destination: .expandedRecording(RecordingFeature.State())
// Error: Swift couldn't infer the type

// Attempt 2: Fully qualified type
destination: AppFeature.Destination.State.expandedRecording(RecordingFeature.State())
// Error: "type of expression is ambiguous"
```

**Resolution:** Removed the expanded recording preview and left a comment explaining why:

```swift
// Note: Preview with destination presented is complex due to @Reducer enum macro
// type inference. Use the collapsed state preview for development.
```

**Recommendation:** Add a note to the TCA best practices guide that preview code for destination states is problematic when using `@Reducer enum Destination`, and suggest alternatives:
- Use runtime presentation in previews (tap to present)
- Create a dedicated preview helper that constructs the state correctly
- Document the exact type path needed for the generated enum

---

### 3. iPhone Simulator Name Instability (Low Impact but Recurring)

**Problem:** Task specified `iPhone 16` but system had `iPhone 17`.

**Build command that failed:**
```bash
xcodebuild build -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 16'
```

**Recommendation:** Add to AGENTS.md or create a project-specific build script that auto-detects available simulators:

```bash
# Get first available iPhone simulator
SIMULATOR=$(xcrun simctl list devices available | grep "iPhone" | head -1 | sed 's/.*(\([^)]*\)).*/\1/')
xcodebuild build -scheme SpeechRecorderApp -destination "id=$SIMULATOR"
```

---

### 4. Missing "Current State" Context (Medium Impact)

**Problem:** Task said "Currently, AppFeature likely uses `isRecordingExpanded: Bool`" - the word "likely" meant the agent had to read the file to confirm what actually existed.

**What was required:** Reading `AppFeature.swift` to discover the actual current implementation before making changes.

**Recommendation:** For refactoring tasks, include exact current code with line numbers to eliminate the need for file reads to confirm what exists:

```markdown
## Current State (AppFeature.swift lines 15-25)
```swift
struct State: Equatable {
    var isRecordingExpanded: Bool = false
    var recording: RecordingFeature.State = .init()
    // ...
}
```

## Target State
```swift
struct State: Equatable {
    @Presents var destination: Destination.State?
    // ...
}
```
```

---

### 5. Deprecation Warnings Not Mentioned (Low Impact)

**Problem:** Build succeeded but showed deprecation warnings for `@Reducer(state:action:)` syntax.

**Warning observed:**
```
warning: '@Reducer(state:action:)' is deprecated: Use '@Reducer' without arguments...
```

**Recommendation:** Either:
1. Update to non-deprecated syntax in the instructions, or
2. Add a note that deprecation warnings are expected and can be addressed in a follow-up task

---

## What Worked Well

### Reference to isowords Production TCA App
The reference to [`references/isowords/Sources/AppFeature/AppView.swift`](references/isowords/Sources/AppFeature/AppView.swift) was invaluable for understanding the correct macro syntax and patterns.

### Clear File Scope
Specifying exactly 2 files to modify (`AppFeature.swift` and `ContentView.swift`) prevented scope creep and made the task tractable.

### Build Verification Command Provided
Having the exact `xcodebuild` command (even with the wrong simulator name) made verification straightforward.

### Delegate Action Note
The note about delegate actions being addressed in a later phase was good foresight - it prevented the agent from trying to solve everything at once.

---

## Summary of Recommendations

| Issue | Priority | Action |
|-------|----------|--------|
| TCA Macro Syntax | High | Update `tca-best-practices-comprehensive-guide.md` with correct `(state: .equatable)` syntax |
| Preview Type Inference | Medium | Add documentation about preview limitations with `@Reducer enum` |
| Simulator Names | Low | Add auto-detection script or use simulator ID instead of name |
| Current State Context | Medium | Include exact code snippets with line numbers in refactoring tasks |
| Deprecation Warnings | Low | Document expected warnings or update to non-deprecated syntax |