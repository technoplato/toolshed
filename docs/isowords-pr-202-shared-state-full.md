# isowords PR #202: Shared State

## PR Metadata

- **Title**: Shared state
- **Author**: Brandon Williams (@mbrandonw)
- **Created**: 2024-04-08
- **State**: OPEN (not merged)
- **Additions**: 860 lines
- **Deletions**: 1,426 lines
- **Changed Files**: 80

## Description

This PR builds upon #200 (which we will merge soon) in order to start making use of `@Shared` throughout the code base. The main thing left to do is fix tests.

## Full Diff

```diff
diff --git a/.swiftpm/xcode/xcshareddata/xcschemes/DailyChallengeHelpers.xcscheme b/.swiftpm/xcode/xcshareddata/xcschemes/DailyChallengeHelpers.xcscheme
new file mode 100644
index 00000000..69bd31f5
--- /dev/null
+++ b/.swiftpm/xcode/xcshareddata/xcschemes/DailyChallengeHelpers.xcscheme
@@ -0,0 +1,67 @@
+<?xml version="1.0" encoding="UTF-8"?>
+<Scheme
+   LastUpgradeVersion = "1530"
+   version = "1.7">
+   <BuildAction
+      parallelizeBuildables = "YES"
+      buildImplicitDependencies = "YES"
+      buildArchitectures = "Automatic">
+      <BuildActionEntries>
+         <BuildActionEntry
+            buildForTesting = "YES"
+            buildForRunning = "YES"
+            buildForProfiling = "YES"
+            buildForArchiving = "YES"
+            buildForAnalyzing = "YES">
+            <BuildableReference
+               BuildableIdentifier = "primary"
+               BlueprintIdentifier = "DailyChallengeHelpers"
+               BuildableName = "DailyChallengeHelpers"
+               BlueprintName = "DailyChallengeHelpers"
+               ReferencedContainer = "container:">
+            </BuildableReference>
+         </BuildActionEntry>
+      </BuildActionEntries>
+   </BuildAction>
+   <TestAction
+      buildConfiguration = "Debug"
+      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
+      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
+      shouldUseLaunchSchemeArgsEnv = "YES"
+      shouldAutocreateTestPlan = "YES">
+   </TestAction>
+   <LaunchAction
+      buildConfiguration = "Debug"
+      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
+      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
+      launchStyle = "0"
+      useCustomWorkingDirectory = "NO"
+      ignoresPersistentStateOnLaunch = "NO"
+      debugDocumentVersioning = "YES"
+      debugServiceExtension = "internal"
+      allowLocationSimulation = "YES">
+   </LaunchAction>
+   <ProfileAction
+      buildConfiguration = "Release"
+      shouldUseLaunchSchemeArgsEnv = "YES"
+      savedToolIdentifier = ""
+      useCustomWorkingDirectory = "NO"
+      debugDocumentVersioning = "YES">
+      <MacroExpansion>
+         <BuildableReference
+            BuildableIdentifier = "primary"
+            BlueprintIdentifier = "DailyChallengeHelpers"
+            BuildableName = "DailyChallengeHelpers"
+            BlueprintName = "DailyChallengeHelpers"
+            ReferencedContainer = "container:">
+         </BuildableReference>
+      </MacroExpansion>
+   </ProfileAction>
+   <AnalyzeAction
+      buildConfiguration = "Debug">
+   </AnalyzeAction>
+   <ArchiveAction
+      buildConfiguration = "Release"
+      revealArchiveInOrganizer = "YES">
+   </ArchiveAction>
+</Scheme>
diff --git a/.swiftpm/xcode/xcshareddata/xcschemes/UserSettings.xcscheme b/.swiftpm/xcode/xcshareddata/xcschemes/UserSettings.xcscheme
new file mode 100644
index 00000000..b83b463d
--- /dev/null
+++ b/.swiftpm/xcode/xcshareddata/xcschemes/UserSettings.xcscheme
@@ -0,0 +1,67 @@
+<?xml version="1.0" encoding="UTF-8"?>
+<Scheme
+   LastUpgradeVersion = "1530"
+   version = "1.7">
+   <BuildAction
+      parallelizeBuildables = "YES"
+      buildImplicitDependencies = "YES"
+      buildArchitectures = "Automatic">
+      <BuildActionEntries>
+         <BuildActionEntry
+            buildForTesting = "YES"
+            buildForRunning = "YES"
+            buildForProfiling = "YES"
+            buildForArchiving = "YES"
+            buildForAnalyzing = "YES">
+            <BuildableReference
+               BuildableIdentifier = "primary"
+               BlueprintIdentifier = "UserSettings"
+               BuildableName = "UserSettings"
+               BlueprintName = "UserSettings"
+               ReferencedContainer = "container:">
+            </BuildableReference>
+         </BuildActionEntry>
+      </BuildActionEntries>
+   </BuildAction>
+   <TestAction
+      buildConfiguration = "Debug"
+      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
+      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
+      shouldUseLaunchSchemeArgsEnv = "YES"
+      shouldAutocreateTestPlan = "YES">
+   </TestAction>
+   <LaunchAction
+      buildConfiguration = "Debug"
+      selectedDebuggerIdentifier = "Xcode.DebuggerFoundation.Debugger.LLDB"
+      selectedLauncherIdentifier = "Xcode.DebuggerFoundation.Launcher.LLDB"
+      launchStyle = "0"
+      useCustomWorkingDirectory = "NO"
+      ignoresPersistentStateOnLaunch = "NO"
+      debugDocumentVersioning = "YES"
+      debugServiceExtension = "internal"
+      allowLocationSimulation = "YES">
+   </LaunchAction>
+   <ProfileAction
+      buildConfiguration = "Release"
+      shouldUseLaunchSchemeArgsEnv = "YES"
+      savedToolIdentifier = ""
+      useCustomWorkingDirectory = "NO"
+      debugDocumentVersioning = "YES">
+      <MacroExpansion>
+         <BuildableReference
+            BuildableIdentifier = "primary"
+            BlueprintIdentifier = "UserSettings"
+            BuildableName = "UserSettings"
+            BlueprintName = "UserSettings"
+            ReferencedContainer = "container:">
+         </BuildableReference>
+      </MacroExpansion>
+   </ProfileAction>
+   <AnalyzeAction
+      buildConfiguration = "Debug">
+   </AnalyzeAction>
+   <ArchiveAction
+      buildConfiguration = "Release"
+      revealArchiveInOrganizer = "YES">
+   </ArchiveAction>
+</Scheme>
diff --git a/App/Previews/CubeCorePreview/CubeCorePreviewApp.swift b/App/Previews/CubeCorePreview/CubeCorePreviewApp.swift
index 6090cca0..2dd71699 100644
--- a/App/Previews/CubeCorePreview/CubeCorePreviewApp.swift
+++ b/App/Previews/CubeCorePreview/CubeCorePreviewApp.swift
@@ -12,7 +12,6 @@ struct CubeCorePreviewApp: App {
           initialState: CubeSceneView.ViewState(
             cubes: .mock,
             enableGyroMotion: false,
-            isOnLowPowerMode: false,
             nub: nil,
             playedWords: [],
             selectedFaceCount: 0,
diff --git a/App/Previews/CubePreviewPreview/CubePreviewPreviewApp.swift b/App/Previews/CubePreviewPreview/CubePreviewPreviewApp.swift
index 168f3cc4..e8d2dbde 100644
--- a/App/Previews/CubePreviewPreview/CubePreviewPreviewApp.swift
+++ b/App/Previews/CubePreviewPreview/CubePreviewPreviewApp.swift
@@ -19,7 +19,6 @@ struct CubePreviewPreviewApp: App {
         store: Store(
           initialState: CubePreview.State(
             cubes: .mock,
-            isOnLowPowerMode: false,
             moveIndex: 0,
             moves: [
               .init(
diff --git a/App/Previews/GameOverPreview/GameOverPreviewApp.swift b/App/Previews/GameOverPreview/GameOverPreviewApp.swift
index d2e886eb..b3ae83be 100644
--- a/App/Previews/GameOverPreview/GameOverPreviewApp.swift
+++ b/App/Previews/GameOverPreview/GameOverPreviewApp.swift
@@ -66,7 +66,6 @@ extension StoreOf<GameOver> {
           .appendingPathComponent("co.pointfree.Isowords")
           .appendingPathComponent("Isowords.sqlite3")
       )
-      $0.fileClient = .noop
       $0.remoteNotifications = .noop
       $0.serverConfig = .noop
       $0.userDefaults.boolForKey = { _ in false }
diff --git a/App/Previews/SettingsPreview/SettingsPreviewApp.swift b/App/Previews/SettingsPreview/SettingsPreviewApp.swift
index 65ef3eac..726fb60f 100644
--- a/App/Previews/SettingsPreview/SettingsPreviewApp.swift
+++ b/App/Previews/SettingsPreview/SettingsPreviewApp.swift
@@ -2,13 +2,11 @@ import ApiClient
 import AudioPlayerClient
 import ComposableStoreKit
 import ComposableUserNotifications
-import FileClient
 import RemoteNotificationsClient
-import ServerConfigClient
+import ServerConfigPersistenceKey
 import SettingsFeature
 import Styleguide
 import SwiftUI
-import UserDefaultsClient
 
 @main
 struct SettingsPreviewApp: App {
diff --git a/App/iOS/App.swift b/App/iOS/App.swift
index 48c8ca8b..4d30ad1f 100644
--- a/App/iOS/App.swift
+++ b/App/iOS/App.swift
@@ -7,7 +7,7 @@ import Build
 import ComposableArchitecture
 import DictionarySqliteClient
 import ServerConfig
-import ServerConfigClient
+import ServerConfigPersistenceKey
 import Styleguide
 import SwiftUI
 import UIApplicationClient
@@ -25,7 +25,6 @@ final class AppDelegate: NSObject, UIApplicationDelegate {
           .appendingPathComponent("co.pointfree.Isowords")
           .appendingPathComponent("Isowords.sqlite3")
       )
-      $0.serverConfig = .live(apiClient: $0.apiClient, build: $0.build)
     }
   }
 
@@ -74,14 +73,3 @@ struct IsowordsApp: App {
 extension AudioPlayerClient {
   static let liveValue = Self.live(bundles: [AppAudioLibrary.bundle, AppClipAudioLibrary.bundle])
 }
-
-extension ServerConfigClient {
-  static func live(apiClient: ApiClient, build: Build) -> Self {
-    .live(
-      fetch: {
-        try await apiClient
-          .apiRequest(route: .config(build: build.number()), as: ServerConfig.self)
-      }
-    )
-  }
-}
diff --git a/App/isowords.xcodeproj/project.xcworkspace/xcshareddata/WorkspaceSettings.xcsettings b/App/isowords.xcodeproj/project.xcworkspace/xcshareddata/WorkspaceSettings.xcsettings
index 08de0be8..54782e32 100644
--- a/App/isowords.xcodeproj/project.xcworkspace/xcshareddata/WorkspaceSettings.xcsettings
+++ b/App/isowords.xcodeproj/project.xcworkspace/xcshareddata/WorkspaceSettings.xcsettings
@@ -3,6 +3,6 @@
 <plist version="1.0">
 <dict>
 	<key>IDEWorkspaceSharedSettings_AutocreateContextsIfNeeded</key>
-	<false/>
+	<true/>
 </dict>
 </plist>
diff --git a/App/isowords.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved b/App/isowords.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved
index d2cb4c1a..8e1c9cf5 100644
--- a/App/isowords.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved
+++ b/App/isowords.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved
@@ -113,8 +113,8 @@
       "kind" : "remoteSourceControl",
       "location" : "https://github.com/pointfreeco/swift-composable-architecture",
       "state" : {
-        "revision" : "115fe5af41d333b6156d4924d7c7058bc77fd580",
-        "version" : "1.9.2"
+        "branch" : "shared-state-generics",
+        "revision" : "4ce58fb2274c60ada9b21e8542d6ab86764f3782"
       }
     },
     {
@@ -129,7 +129,7 @@
     {
       "identity" : "swift-crypto",
       "kind" : "remoteSourceControl",
-      "location" : "https://github.com/apple/swift-crypto.git",
+      "location" : "https://github.com/apple/swift-crypto",
       "state" : {
         "revision" : "ddb07e896a2a8af79512543b1c7eb9797f8898a5",
         "version" : "1.1.7"
diff --git a/App/isowords.xcodeproj/xcshareddata/xcschemes/isowords.xcscheme b/App/isowords.xcodeproj/xcshareddata/xcschemes/isowords.xcscheme
index ce1bcdda..97d01f34 100644
--- a/App/isowords.xcodeproj/xcshareddata/xcschemes/isowords.xcscheme
+++ b/App/isowords.xcodeproj/xcshareddata/xcschemes/isowords.xcscheme
@@ -132,6 +132,76 @@
                ReferencedContainer = "container:..">
             </BuildableReference>
          </BuildActionEntry>
+         <BuildActionEntry
+            buildForTesting = "YES"
+            buildForRunning = "NO"
+            buildForProfiling = "NO"
+            buildForArchiving = "NO"
+            buildForAnalyzing = "NO">
+            <BuildableReference
+               BuildableIdentifier = "primary"
+               BlueprintIdentifier = "LeaderboardFeatureTests"
+               BuildableName = "LeaderboardFeatureTests"
+               BlueprintName = "LeaderboardFeatureTests"
+               ReferencedContainer = "container:..">
+            </BuildableReference>
+         </BuildActionEntry>
+         <BuildActionEntry
+            buildForTesting = "YES"
+            buildForRunning = "NO"
+            buildForProfiling = "NO"
+            buildForArchiving = "NO"
+            buildForAnalyzing = "NO">
+            <BuildableReference
+               BuildableIdentifier = "primary"
+               BlueprintIdentifier = "MultiplayerFeatureTests"
+               BuildableName = "MultiplayerFeatureTests"
+               BlueprintName = "MultiplayerFeatureTests"
+               ReferencedContainer = "container:..">
+            </BuildableReference>
+         </BuildActionEntry>
+         <BuildActionEntry
+            buildForTesting = "YES"
+            buildForRunning = "NO"
+            buildForProfiling = "NO"
+            buildForArchiving = "NO"
+            buildForAnalyzing = "NO">
+            <BuildableReference
+               BuildableIdentifier = "primary"
+               BlueprintIdentifier = "OnboardingFeatureTests"
+               BuildableName = "OnboardingFeatureTests"
+               BlueprintName = "OnboardingFeatureTests"
+               ReferencedContainer = "container:..">
+            </BuildableReference>
+         </BuildActionEntry>
+         <BuildActionEntry
+            buildForTesting = "YES"
+            buildForRunning = "NO"
+            buildForProfiling = "NO"
+            buildForArchiving = "NO"
+            buildForAnalyzing = "NO">
+            <BuildableReference
+               BuildableIdentifier = "primary"
+               BlueprintIdentifier = "SettingsFeatureTests"
+               BuildableName = "SettingsFeatureTests"
+               BlueprintName = "SettingsFeatureTests"
+               ReferencedContainer = "container:..">
+            </BuildableReference>
+         </BuildActionEntry>
+         <BuildActionEntry
+            buildForTesting = "YES"
+            buildForRunning = "NO"
+            buildForProfiling = "NO"
+            buildForArchiving = "NO"
+            buildForAnalyzing = "NO">
+            <BuildableReference
+               BuildableIdentifier = "primary"
+               BlueprintIdentifier = "ServerRouterTests"
+               BuildableName = "ServerRouterTests"
+               BlueprintName = "ServerRouterTests"
+               ReferencedContainer = "container:..">
+            </BuildableReference>
+         </BuildActionEntry>
       </BuildActionEntries>
    </BuildAction>
    <TestAction
@@ -210,56 +280,6 @@
                ReferencedContainer = "container:..">
             </BuildableReference>
          </TestableReference>
-         <TestableReference
-            skipped = "NO">
-            <BuildableReference
-               BuildableIdentifier = "primary"
-               BlueprintIdentifier = "LeaderboardFeatureTests"
-               BuildableName = "LeaderboardFeatureTests"
-               BlueprintName = "LeaderboardFeatureTests"
-               ReferencedContainer = "container:..">
-            </BuildableReference>
-         </TestableReference>
-         <TestableReference
-            skipped = "NO">
-            <BuildableReference
-               BuildableIdentifier = "primary"
-               BlueprintIdentifier = "MultiplayerFeatureTests"
-               BuildableName = "MultiplayerFeatureTests"
-               BlueprintName = "MultiplayerFeatureTests"
-               ReferencedContainer = "container:..">
-            </BuildableReference>
-         </TestableReference>
-         <TestableReference
-            skipped = "NO">
-            <BuildableReference
-               BuildableIdentifier = "primary"
-               BlueprintIdentifier = "OnboardingFeatureTests"
-               BuildableName = "OnboardingFeatureTests"
-               BlueprintName = "OnboardingFeatureTests"
-               ReferencedContainer = "container:..">
-            </BuildableReference>
-         </TestableReference>
-         <TestableReference
-            skipped = "NO">
-            <BuildableReference
-               BuildableIdentifier = "primary"
-               BlueprintIdentifier = "SettingsFeatureTests"
-               BuildableName = "SettingsFeatureTests"
-               BlueprintName = "SettingsFeatureTests"
-               ReferencedContainer = "container:..">
-            </BuildableReference>
-         </TestableReference>
-         <TestableReference
-            skipped = "NO">
-            <BuildableReference
-               BuildableIdentifier = "primary"
-               BlueprintIdentifier = "ServerRouterTests"
-               BuildableName = "ServerRouterTests"
-               BlueprintName = "ServerRouterTests"
-               ReferencedContainer = "container:..">
-            </BuildableReference>
-         </TestableReference>
          <TestableReference
             skipped = "NO">
             <BuildableReference
@@ -280,26 +300,6 @@
                ReferencedContainer = "container:..">
             </BuildableReference>
          </TestableReference>
-         <TestableReference
-            skipped = "NO">
-            <BuildableReference
-               BuildableIdentifier = "primary"
-               BlueprintIdentifier = "AppFeatureTests"
-               BuildableName = "AppFeatureTests"
-               BlueprintName = "AppFeatureTests"
-               ReferencedContainer = "container:..">
-            </BuildableReference>
-         </TestableReference>
-         <TestableReference
-            skipped = "NO">
-            <BuildableReference
-               BuildableIdentifier = "primary"
-               BlueprintIdentifier = "AppStoreSnapshotTests"
-               BuildableName = "AppStoreSnapshotTests"
-               BlueprintName = "AppStoreSnapshotTests"
-               ReferencedContainer = "container:..">
-            </BuildableReference>
-         </TestableReference>
          <TestableReference
             skipped = "NO">
             <BuildableReference
diff --git a/Package.swift b/Package.swift
index b9538df5..67c3a8b1 100644
--- a/Package.swift
+++ b/Package.swift
@@ -28,7 +28,10 @@ var package = Package(
   dependencies: [
     .package(url: "https://github.com/apple/swift-crypto", from: "1.1.6"),
     .package(url: "https://github.com/pointfreeco/swift-case-paths", from: "1.1.0"),
-    .package(url: "https://github.com/pointfreeco/swift-composable-architecture", from: "1.9.2"),
+    .package(
+      url: "https://github.com/pointfreeco/swift-composable-architecture",
+      branch: "shared-state-generics"
+    ),
     .package(url: "https://github.com/pointfreeco/swift-custom-dump", from: "1.0.0"),
     .package(url: "https://github.com/pointfreeco/swift-dependencies", from: "1.1.0"),
     .package(url: "https://github.com/pointfreeco/swift-gen", from: "0.3.0"),
@@ -43,8 +46,7 @@ var package = Package(
     .target(
       name: "Build",
       dependencies: [
-        .product(name: "Dependencies", package: "swift-dependencies"),
-        .product(name: "DependenciesMacros", package: "swift-dependencies"),
+        .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
         .product(name: "Tagged", package: "swift-tagged"),
         .product(name: "XCTestDynamicOverlay", package: "xctest-dynamic-overlay"),
       ]
@@ -110,9 +112,7 @@ var package = Package(
     ),
     .target(
       name: "ServerConfig",
-      dependencies: [
-        "Build"
-      ]
+      dependencies: ["Build"]
     ),
     .target(
       name: "ServerRouter",
@@ -203,7 +203,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
     .library(name: "DeviceId", targets: ["DeviceId"]),
     .library(name: "DictionaryFileClient", targets: ["DictionaryFileClient"]),
     .library(name: "FeedbackGeneratorClient", targets: ["FeedbackGeneratorClient"]),
-    .library(name: "FileClient", targets: ["FileClient"]),
     .library(name: "GameCore", targets: ["GameCore"]),
     .library(name: "GameOverFeature", targets: ["GameOverFeature"]),
     .library(name: "HapticsCore", targets: ["HapticsCore"]),
@@ -211,14 +210,13 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
     .library(name: "IntegrationTestHelpers", targets: ["IntegrationTestHelpers"]),
     .library(name: "LeaderboardFeature", targets: ["LeaderboardFeature"]),
     .library(name: "LocalDatabaseClient", targets: ["LocalDatabaseClient"]),
-    .library(name: "LowPowerModeClient", targets: ["LowPowerModeClient"]),
     .library(name: "MultiplayerFeature", targets: ["MultiplayerFeature"]),
     .library(name: "NotificationHelpers", targets: ["NotificationHelpers"]),
     .library(name: "NotificationsAuthAlert", targets: ["NotificationsAuthAlert"]),
     .library(name: "OnboardingFeature", targets: ["OnboardingFeature"]),
     .library(name: "RemoteNotificationsClient", targets: ["RemoteNotificationsClient"]),
     .library(name: "SelectionSoundsCore", targets: ["SelectionSoundsCore"]),
-    .library(name: "ServerConfigClient", targets: ["ServerConfigClient"]),
+    .library(name: "ServerConfigPersistenceKey", targets: ["ServerConfigPersistenceKey"]),
     .library(name: "SettingsFeature", targets: ["SettingsFeature"]),
     .library(name: "SharedSwiftUIEnvironment", targets: ["SharedSwiftUIEnvironment"]),
     .library(name: "SoloFeature", targets: ["SoloFeature"]),
@@ -227,10 +225,9 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
     .library(name: "SwiftUIHelpers", targets: ["SwiftUIHelpers"]),
     .library(name: "TcaHelpers", targets: ["TcaHelpers"]),
     .library(name: "TrailerFeature", targets: ["TrailerFeature"]),
-    .library(name: "UserSettingsClient", targets: ["UserSettingsClient"]),
+    .library(name: "UserSettings", targets: ["UserSettings"]),
     .library(name: "UIApplicationClient", targets: ["UIApplicationClient"]),
     .library(name: "UpgradeInterstitialFeature", targets: ["UpgradeInterstitialFeature"]),
-    .library(name: "UserDefaultsClient", targets: ["UserDefaultsClient"]),
     .library(name: "VocabFeature", targets: ["VocabFeature"]),
   ])
   package.targets.append(contentsOf: [
@@ -295,12 +292,10 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "DeviceId",
         "DictionarySqliteClient",
         "FeedbackGeneratorClient",
-        "FileClient",
         "GameOverFeature",
         "HomeFeature",
         "LeaderboardFeature",
         "LocalDatabaseClient",
-        "LowPowerModeClient",
         "MultiplayerFeature",
         "NotificationHelpers",
         "OnboardingFeature",
@@ -312,7 +307,7 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "StatsFeature",
         "TcaHelpers",
         "UIApplicationClient",
-        "UserSettingsClient",
+        "UserSettings",
         "VocabFeature",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
         .product(name: "Gen", package: "swift-gen"),
@@ -367,13 +362,12 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
       dependencies: [
         "ApiClient",
         "Build",
-        "ServerConfigClient",
+        "ServerConfigPersistenceKey",
         "SharedModels",
         "Styleguide",
         "SwiftUIHelpers",
         "TcaHelpers",
         "UIApplicationClient",
-        "UserDefaultsClient",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
         .product(name: "Overture", package: "swift-overture"),
       ]
@@ -449,10 +443,9 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "CubeCore",
         "FeedbackGeneratorClient",
         "HapticsCore",
-        "LowPowerModeClient",
         "SelectionSoundsCore",
         "SharedModels",
-        "UserSettingsClient",
+        "UserSettings",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
       ]
     ),
@@ -503,7 +496,7 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
       name: "DailyChallengeHelpers",
       dependencies: [
         "ApiClient",
-        "FileClient",
+        "ClientModels",
         "SharedModels",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
       ]
@@ -519,10 +512,8 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "GameCore",
         "DictionaryClient",
         "FeedbackGeneratorClient",
-        "LowPowerModeClient",
         "OnboardingFeature",
         "SharedModels",
-        "UserDefaultsClient",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
       ]
     ),
@@ -557,15 +548,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         .product(name: "XCTestDynamicOverlay", package: "xctest-dynamic-overlay"),
       ]
     ),
-    .target(
-      name: "FileClient",
-      dependencies: [
-        "ClientModels",
-        "XCTestDebugSupport",
-        .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
-        .product(name: "XCTestDynamicOverlay", package: "xctest-dynamic-overlay"),
-      ]
-    ),
     .target(
       name: "GameCore",
       dependencies: [
@@ -582,9 +564,7 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "DictionaryClient",
         "GameOverFeature",
         "FeedbackGeneratorClient",
-        "FileClient",
         "HapticsCore",
-        "LowPowerModeClient",
         "PuzzleGen",
         "RemoteNotificationsClient",
         "SelectionSoundsCore",
@@ -594,7 +574,7 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "TcaHelpers",
         "UIApplicationClient",
         "UpgradeInterstitialFeature",
-        "UserSettingsClient",
+        "UserSettings",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
       ],
       resources: [.process("Resources/")]
@@ -616,7 +596,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "ClientModels",
         "ComposableStoreKit",
         "DailyChallengeHelpers",
-        "FileClient",
         "FirstPartyMocks",
         "LocalDatabaseClient",
         "NotificationHelpers",
@@ -626,7 +605,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "SwiftUIHelpers",
         "TcaHelpers",
         "UpgradeInterstitialFeature",
-        "UserDefaultsClient",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
       ]
     ),
@@ -678,12 +656,10 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "DailyChallengeFeature",
         "DateHelpers",
         "DeviceId",
-        "FileClient",
         "LeaderboardFeature",
         "LocalDatabaseClient",
-        "LowPowerModeClient",
         "MultiplayerFeature",
-        "ServerConfigClient",
+        "ServerConfigPersistenceKey",
         "SettingsFeature",
         "SharedModels",
         "SoloFeature",
@@ -692,7 +668,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "TcaHelpers",
         "UIApplicationClient",
         "UpgradeInterstitialFeature",
-        "UserDefaultsClient",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
         .product(name: "Overture", package: "swift-overture"),
       ]
@@ -720,10 +695,9 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "ApiClient",
         "AudioPlayerClient",
         "CubePreview",
-        "LowPowerModeClient",
         "Styleguide",
         "SwiftUIHelpers",
-        "UserSettingsClient",
+        "UserSettings",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
         .product(name: "Overture", package: "swift-overture"),
       ]
@@ -746,12 +720,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         .product(name: "Overture", package: "swift-overture"),
       ]
     ),
-    .target(
-      name: "LowPowerModeClient",
-      dependencies: [
-        .product(name: "ComposableArchitecture", package: "swift-composable-architecture")
-      ]
-    ),
     .target(
       name: "MultiplayerFeature",
       dependencies: [
@@ -794,7 +762,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "GameCore",
         "DictionaryClient",
         "FeedbackGeneratorClient",
-        "LowPowerModeClient",
         "PuzzleGen",
         "SharedModels",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
@@ -823,7 +790,7 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
       ]
     ),
     .target(
-      name: "ServerConfigClient",
+      name: "ServerConfigPersistenceKey",
       dependencies: [
         "ServerConfig",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
@@ -838,18 +805,15 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "Build",
         "ComposableStoreKit",
         "ComposableUserNotifications",
-        "FileClient",
         "LocalDatabaseClient",
-        "LowPowerModeClient",
         "RemoteNotificationsClient",
-        "ServerConfigClient",
+        "ServerConfigPersistenceKey",
         "StatsFeature",
         "Styleguide",
         "SwiftUIHelpers",
         "TcaHelpers",
         "UIApplicationClient",
-        "UserDefaultsClient",
-        "UserSettingsClient",
+        "UserSettings",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
         .product(name: "XCTestDynamicOverlay", package: "xctest-dynamic-overlay"),
       ],
@@ -871,7 +835,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
       name: "SoloFeature",
       dependencies: [
         "ClientModels",
-        "FileClient",
         "SharedModels",
         "Styleguide",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
@@ -921,19 +884,17 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "GameCore",
         "DictionaryClient",
         "FeedbackGeneratorClient",
-        "LowPowerModeClient",
         "OnboardingFeature",
         "SharedModels",
         "TcaHelpers",
-        "UserDefaultsClient",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
       ]
     ),
     .target(
-      name: "UserSettingsClient",
+      name: "UserSettings",
       dependencies: [
         "Styleguide",
-        .product(name: "Dependencies", package: "swift-dependencies"),
+        .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
       ]
     ),
     .target(
@@ -946,7 +907,7 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
       name: "UpgradeInterstitialFeature",
       dependencies: [
         "ComposableStoreKit",
-        "ServerConfigClient",
+        "ServerConfigPersistenceKey",
         "Styleguide",
         "SwiftUIHelpers",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
@@ -962,13 +923,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
       ],
       exclude: ["__Snapshots__"]
     ),
-    .target(
-      name: "UserDefaultsClient",
-      dependencies: [
-        .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
-        .product(name: "XCTestDynamicOverlay", package: "xctest-dynamic-overlay"),
-      ]
-    ),
     .target(
       name: "VocabFeature",
       dependencies: [
@@ -976,7 +930,6 @@ if ProcessInfo.processInfo.environment["TEST_SERVER"] == nil {
         "CubePreview",
         "FeedbackGeneratorClient",
         "LocalDatabaseClient",
-        "LowPowerModeClient",
         "SharedModels",
         .product(name: "ComposableArchitecture", package: "swift-composable-architecture"),
       ]
diff --git a/Sources/ActiveGamesFeature/ActiveGamesView.swift b/Sources/ActiveGamesFeature/ActiveGamesView.swift
index f6df6e9c..d2c8bba8 100644
--- a/Sources/ActiveGamesFeature/ActiveGamesView.swift
+++ b/Sources/ActiveGamesFeature/ActiveGamesView.swift
@@ -8,14 +8,12 @@ import SwiftUI
 
 @ObservableState
 public struct ActiveGamesState: Equatable {
-  public var savedGames: SavedGamesState
+  @Shared(.savedGames) public var savedGames = SavedGamesState()
   public var turnBasedMatches: [ActiveTurnBasedMatch]
 
   public init(
-    savedGames: SavedGamesState = .init(),
     turnBasedMatches: [ActiveTurnBasedMatch] = []
-  ) {
-    self.savedGames = savedGames
+  ) { 
     self.turnBasedMatches = turnBasedMatches
   }
 
@@ -342,31 +340,26 @@ private let relativeDateFormatter = RelativeDateTimeFormatter()
 
   struct ActiveGamesView_Previews: PreviewProvider {
     static var previews: some View {
-      Preview {
+      @Shared(.savedGames) var savedGames = SavedGamesState(
+        dailyChallengeUnlimited: update(.mock) {
+          $0?.moves = [.highScoringMove]
+          $0?.gameContext = .dailyChallenge(.init(rawValue: .dailyChallengeId))
+        },
+        unlimited: update(.mock) {
+          $0?.moves = [.highScoringMove]
+          $0?.gameStartTime = Date().addingTimeInterval(-60 * 60 * 7)
+        }
+      )
+
+      return Preview {
         ScrollView {
           ActiveGamesView(
-            store: Store(
-              initialState: ActiveGamesState(
-                savedGames: SavedGamesState(
-                  dailyChallengeUnlimited: update(.mock) {
-                    $0?.moves = [.highScoringMove]
-                    $0?.gameContext = .dailyChallenge(.init(rawValue: .dailyChallengeId))
-                  },
-                  unlimited: update(.mock) {
-                    $0?.moves = [.highScoringMove]
-                    $0?.gameStartTime = Date().addingTimeInterval(-60 * 60 * 7)
-                  }
-                ),
-                turnBasedMatches: []
-              )
-            ) {
-            },
+            store: Store(initialState: ActiveGamesState()) {},
             showMenuItems: true
           )
           ActiveGamesView(
             store: Store(
               initialState: ActiveGamesState(
-                savedGames: .init(),
                 turnBasedMatches: [
                   .init(
                     id: "1",
diff --git a/Sources/AppFeature/AppDelegate.swift b/Sources/AppFeature/AppDelegate.swift
index 31061143..84f116dd 100644
--- a/Sources/AppFeature/AppDelegate.swift
+++ b/Sources/AppFeature/AppDelegate.swift
@@ -3,6 +3,8 @@ import ComposableArchitecture
 import ComposableUserNotifications
 import Foundation
 import SettingsFeature
+import UserSettings
+import Build
 
 @Reducer
 public struct AppDelegateReducer {
@@ -18,12 +20,11 @@ public struct AppDelegateReducer {
 
   @Dependency(\.apiClient) var apiClient
   @Dependency(\.audioPlayer) var audioPlayer
-  @Dependency(\.build.number) var buildNumber
   @Dependency(\.dictionary.load) var loadDictionary
   @Dependency(\.remoteNotifications.register) var registerForRemoteNotifications
   @Dependency(\.applicationClient.setUserInterfaceStyle) var setUserInterfaceStyle
   @Dependency(\.userNotifications) var userNotifications
-  @Dependency(\.userSettings) var userSettings
+  @Shared(.build) var build = Build()
 
   public init() {}
 
@@ -65,6 +66,8 @@ public struct AppDelegateReducer {
             }
 
             group.addTask {
+              @Shared(.userSettings) var userSettings = UserSettings()
+
               await self.audioPlayer.setGlobalVolumeForSoundEffects(userSettings.soundEffectsVolume)
               await self.audioPlayer.setGlobalVolumeForMusic(
                 self.audioPlayer.secondaryAudioShouldBeSilencedHint()
@@ -88,7 +91,7 @@ public struct AppDelegateReducer {
               .register(
                 .init(
                   authorizationStatus: .init(rawValue: settings.authorizationStatus.rawValue),
-                  build: self.buildNumber(),
+                  build: self.build.number,
                   token: token
                 )
               )
diff --git a/Sources/AppFeature/AppView.swift b/Sources/AppFeature/AppView.swift
index dcf417e4..7223f7b0 100644
--- a/Sources/AppFeature/AppView.swift
+++ b/Sources/AppFeature/AppView.swift
@@ -2,6 +2,7 @@ import ClientModels
 import ComposableArchitecture
 import ComposableStoreKit
 import CubeCore
+import DailyChallengeFeature
 import GameCore
 import HomeFeature
 import NotificationHelpers
@@ -9,6 +10,7 @@ import OnboardingFeature
 import SharedModels
 import Styleguide
 import SwiftUI
+import ServerConfigPersistenceKey
 
 @Reducer
 public struct AppReducer {
@@ -22,7 +24,11 @@ public struct AppReducer {
   public struct State: Equatable {
     public var appDelegate: AppDelegateReducer.State
     @Presents public var destination: Destination.State?
+    @SharedReader(.hasShownFirstLaunchOnboarding) var hasShownFirstLaunchOnboarding = false
     public var home: Home.State
+    @Shared(.installationTime) var installationTime = 0
+    @SharedReader(.serverConfig) var serverConfig = ServerConfig()
+    @Shared(.savedGames) var savedGames = SavedGamesState()
 
     public init(
       appDelegate: AppDelegateReducer.State = AppDelegateReducer.State(),
@@ -42,18 +48,14 @@ public struct AppReducer {
     case gameCenter(GameCenterAction)
     case home(Home.Action)
     case paymentTransaction(StoreKitClient.PaymentTransactionObserverEvent)
-    case savedGamesLoaded(Result<SavedGamesState, Error>)
     case verifyReceiptResponse(Result<ReceiptFinalizationEnvelope, Error>)
   }
 
-  @Dependency(\.fileClient) var fileClient
   @Dependency(\.gameCenter.turnBasedMatch.load) var loadTurnBasedMatch
   @Dependency(\.database.migrate) var migrate
   @Dependency(\.mainRunLoop.now.date) var now
   @Dependency(\.dictionary.randomCubes) var randomCubes
   @Dependency(\.remoteNotifications) var remoteNotifications
-  @Dependency(\.serverConfig.refresh) var refreshServerConfig
-  @Dependency(\.userDefaults) var userDefaults
   @Dependency(\.userNotifications) var userNotifications
 
   public init() {}
@@ -67,23 +69,15 @@ public struct AppReducer {
 
           switch (game.gameContext, game.gameMode) {
           case (.dailyChallenge, .unlimited):
-            state.home.savedGames.dailyChallengeUnlimited = InProgressGame(gameState: game)
+            state.savedGames.dailyChallengeUnlimited = InProgressGame(gameState: game)
           case (.shared, .unlimited), (.solo, .unlimited):
-            state.home.savedGames.unlimited = InProgressGame(gameState: game)
+            state.savedGames.unlimited = InProgressGame(gameState: game)
           case (.turnBased, _), (_, .timed):
             return .none
           }
           return .none
         }
       }
-      .onChange(of: \.home.savedGames) { _, savedGames in
-        Reduce { _, action in
-          if case .savedGamesLoaded(.success) = action { return .none }
-          return .run { _ in
-            try await self.fileClient.save(games: savedGames)
-          }
-        }
-      }
 
     GameCenterLogic()
     StoreKitLogic()
@@ -100,23 +94,14 @@ public struct AppReducer {
     Reduce { state, action in
       switch action {
       case .appDelegate(.didFinishLaunching):
-        if !self.userDefaults.hasShownFirstLaunchOnboarding {
+        if !state.hasShownFirstLaunchOnboarding {
           state.destination = .onboarding(Onboarding.State(presentationStyle: .firstLaunch))
         }
-
-        return .run { send in
-          async let migrate: Void = self.migrate()
-          if self.userDefaults.installationTime <= 0 {
-            await self.userDefaults.setInstallationTime(
-              self.now.timeIntervalSinceReferenceDate
-            )
-          }
-          await send(
-            .savedGamesLoaded(
-              Result { try await self.fileClient.loadSavedGames() }
-            )
-          )
-          _ = try await migrate
+        if state.installationTime <= 0 {
+          state.installationTime = self.now.timeIntervalSinceReferenceDate
+        }
+        return .run { _ in
+          try await self.migrate()
         }
 
       case let .appDelegate(.userNotifications(.didReceiveResponse(response, completionHandler))):
@@ -128,7 +113,7 @@ public struct AppReducer {
         {
           switch pushNotificationContent {
           case .dailyChallengeEndsSoon:
-            if let inProgressGame = state.home.savedGames.dailyChallengeUnlimited {
+            if let inProgressGame = state.savedGames.dailyChallengeUnlimited {
               state.destination = .game(Game.State(inProgressGame: inProgressGame))
             } else {
               // TODO: load/retry
@@ -136,7 +121,7 @@ public struct AppReducer {
 
           case .dailyChallengeReport:
             state.destination = nil
-            state.home.destination = .dailyChallenge(.init())
+            state.home.destination = .dailyChallenge(DailyChallengeReducer.State())
           }
         }
 
@@ -153,9 +138,9 @@ public struct AppReducer {
         guard let game = state.destination?.game else { return .none }
         switch (game.gameContext, game.gameMode) {
         case (.dailyChallenge, .unlimited):
-          state.home.savedGames.dailyChallengeUnlimited = nil
+          state.savedGames.dailyChallengeUnlimited = nil
         case (.solo, .unlimited):
-          state.home.savedGames.unlimited = nil
+          state.savedGames.unlimited = nil
         default:
           break
         }
@@ -163,7 +148,7 @@ public struct AppReducer {
 
       case .destination(.presented(.game(.activeGames(.dailyChallengeTapped)))),
         .home(.activeGames(.dailyChallengeTapped)):
-        guard let inProgressGame = state.home.savedGames.dailyChallengeUnlimited
+        guard let inProgressGame = state.savedGames.dailyChallengeUnlimited
         else { return .none }
 
         state.destination = .game(Game.State(inProgressGame: inProgressGame))
@@ -171,7 +156,7 @@ public struct AppReducer {
 
       case .destination(.presented(.game(.activeGames(.soloTapped)))),
         .home(.activeGames(.soloTapped)):
-        guard let inProgressGame = state.home.savedGames.unlimited
+        guard let inProgressGame = state.savedGames.unlimited
         else { return .none }
 
         state.destination = .game(Game.State(inProgressGame: inProgressGame))
@@ -214,7 +199,7 @@ public struct AppReducer {
       ),
         .home(.destination(.presented(.solo(.gameButtonTapped(.unlimited))))):
         state.destination = .game(
-          state.home.savedGames.unlimited
+          state.savedGames.unlimited
             .map { Game.State(inProgressGame: $0) }
             ?? Game.State(
               cubes: self.randomCubes(.en),
@@ -243,29 +228,18 @@ public struct AppReducer {
         state.destination = .game(Game.State(inProgressGame: inProgressGame))
         return .none
 
-      case let .home(.dailyChallengeResponse(.success(dailyChallenges))):
-        if dailyChallenges.unlimited?.dailyChallenge.id
-          != state.home.savedGames.dailyChallengeUnlimited?.gameContext.dailyChallenge
-        {
-          state.home.savedGames.dailyChallengeUnlimited = nil
-          return .run { [savedGames = state.home.savedGames] _ in
-            try await self.fileClient.save(games: savedGames)
-          }
-        }
-        return .none
-
       case .home(.howToPlayButtonTapped):
         state.destination = .onboarding(Onboarding.State(presentationStyle: .help))
         return .none
 
       case .didChangeScenePhase(.active):
-        return .run { _ in
+        return .run { [serverConfig = state.$serverConfig] _ in
           async let register: Void = registerForRemoteNotificationsAsync(
             remoteNotifications: self.remoteNotifications,
             userNotifications: self.userNotifications
           )
-          async let refresh = self.refreshServerConfig()
-          _ = try await (register, refresh)
+          async let refresh: Void = serverConfig.persistence.reload()
+          _ = await (register, refresh)
         } catch: { _, _ in
         }
 
@@ -281,13 +255,6 @@ public struct AppReducer {
       case .paymentTransaction:
         return .none
 
-      case .savedGamesLoaded(.failure):
-        return .none
-
-      case let .savedGamesLoaded(.success(savedGames)):
-        state.home.savedGames = savedGames
-        return .none
-
       case .verifyReceiptResponse:
         return .none
       }
diff --git a/Sources/Build/Build.swift b/Sources/Build/Build.swift
index 43eb6ed1..7fc624a9 100644
--- a/Sources/Build/Build.swift
+++ b/Sources/Build/Build.swift
@@ -1,44 +1,20 @@
-import Dependencies
-import DependenciesMacros
+import ComposableArchitecture
 import Foundation
 import Tagged
 
-@DependencyClient
-public struct Build {
-  public var gitSha: () -> String = { "deadbeef" }
-  public var number: () -> Number = { 0 }
+public struct Build: Equatable, Sendable {
+  public var gitSha = Bundle.main.infoDictionary?["GitSHA"] as? String ?? ""
+  public var number = Number(
+    rawValue: (Bundle.main.infoDictionary?["CFBundleVersion"] as? String)
+      .flatMap(Int.init)
+      ?? 0)
+  public init() {}
 
   public typealias Number = Tagged<((), number: ()), Int>
 }
 
-extension DependencyValues {
-  public var build: Build {
-    get { self[Build.self] }
-    set { self[Build.self] = newValue }
+extension PersistenceReaderKey where Self == InMemoryKey<Build> {
+  public static var build: Self {
+    inMemory("build")
   }
 }
-
-extension Build: TestDependencyKey {
-  public static let previewValue = Self.noop
-  public static let testValue = Self()
-}
-
-extension Build: DependencyKey {
-  public static let liveValue = Self(
-    gitSha: { Bundle.main.infoDictionary?["GitSHA"] as? String ?? "" },
-    number: {
-      .init(
-        rawValue: (Bundle.main.infoDictionary?["CFBundleVersion"] as? String)
-          .flatMap(Int.init)
-          ?? 0
-      )
-    }
-  )
-}
-
-extension Build {
-  public static let noop = Self(
-    gitSha: { "deadbeef" },
-    number: { 0 }
-  )
-}
diff --git a/Sources/ChangelogFeature/ChangeView.swift b/Sources/ChangelogFeature/ChangeView.swift
index 76d9bc0d..484c3fd1 100644
--- a/Sources/ChangelogFeature/ChangeView.swift
+++ b/Sources/ChangelogFeature/ChangeView.swift
@@ -1,6 +1,6 @@
 import Build
 import ComposableArchitecture
-import ServerConfigClient
+import ServerConfigPersistenceKey
 import SwiftUI
 import Tagged
 
diff --git a/Sources/ChangelogFeature/ChangelogView.swift b/Sources/ChangelogFeature/ChangelogView.swift
index 1e7da081..dfebd2c3 100644
--- a/Sources/ChangelogFeature/ChangelogView.swift
+++ b/Sources/ChangelogFeature/ChangelogView.swift
@@ -1,7 +1,7 @@
 import ApiClient
 import Build
 import ComposableArchitecture
-import ServerConfigClient
+import ServerConfigPersistenceKey
 import SharedModels
 import Styleguide
 import SwiftUI
@@ -12,10 +12,12 @@ import UIApplicationClient
 public struct ChangelogReducer {
   @ObservableState
   public struct State: Equatable {
+    @SharedReader(.build) var build = Build()
     public var changelog: IdentifiedArrayOf<Change.State>
     public var currentBuild: Build.Number
     public var isRequestInFlight: Bool
     public var isUpdateButtonVisible: Bool
+    @SharedReader(.serverConfig) var serverConfig = ServerConfig()
 
     public init(
       changelog: IdentifiedArrayOf<Change.State> = [],
@@ -46,9 +48,7 @@ public struct ChangelogReducer {
   }
 
   @Dependency(\.apiClient) var apiClient
-  @Dependency(\.build.number) var buildNumber
   @Dependency(\.applicationClient.open) var openURL
-  @Dependency(\.serverConfig) var serverConfig
 
   public init() {}
 
@@ -68,13 +68,13 @@ public struct ChangelogReducer {
             .map { offset, change in
               Change.State(
                 change: change,
-                isExpanded: offset == 0 || self.buildNumber() <= change.build
+                isExpanded: offset == 0 || state.build.number <= change.build
               )
             }
         )
         state.isRequestInFlight = false
         state.isUpdateButtonVisible =
-          self.buildNumber() < (changelog.changes.map(\.build).max() ?? 0)
+        state.build.number < (changelog.changes.map(\.build).max() ?? 0)
 
         return .none
 
@@ -83,15 +83,15 @@ public struct ChangelogReducer {
         return .none
 
       case .task:
-        state.currentBuild = self.buildNumber()
+        state.currentBuild = state.build.number
         state.isRequestInFlight = true
 
-        return .run { send in
+        return .run { [build = state.build] send in
           await send(
             .changelogResponse(
               Result {
                 try await self.apiClient.apiRequest(
-                  route: .changelog(build: self.buildNumber()),
+                  route: .changelog(build: build.number),
                   as: Changelog.self
                 )
               }
@@ -100,11 +100,8 @@ public struct ChangelogReducer {
         }
 
       case .updateButtonTapped:
-        return .run { _ in
-          _ = await self.openURL(
-            self.serverConfig.config().appStoreUrl.absoluteURL,
-            [:]
-          )
+        return .run { [url = state.serverConfig.appStoreUrl.absoluteURL] _ in
+          _ = await self.openURL(url, [:])
         }
       }
     }
@@ -186,8 +183,6 @@ public struct ChangelogView: View {
               return apiClient
             }()
             $0.applicationClient = .noop
-            $0.build.number = { 98 }
-            $0.serverConfig = .noop
           }
         )
         .navigationStyle(
diff --git a/Sources/ClientModels/AppStorage.swift b/Sources/ClientModels/AppStorage.swift
index 0ce53b62..0f162a3c 100644
--- a/Sources/ClientModels/AppStorage.swift
+++ b/Sources/ClientModels/AppStorage.swift
@@ -1,55 +1,55 @@
 import SwiftUI
 
-extension AppStorageKey where Value == Bool {
-  public static let enableCubeShadow = Self(key: "enableCubeShadow", defaultValue: true)
-  public static let showSceneStatistics = Self(key: "showSceneStatistics", defaultValue: false)
+extension _AppStorageKey where Value == Bool {
+  public static let enableCubeShadow = _AppStorageKey(key: "enableCubeShadow", defaultValue: true)
+  public static let showSceneStatistics = _AppStorageKey(key: "showSceneStatistics", defaultValue: false)
 }
 
-public struct AppStorageKey<Value> {
+public struct _AppStorageKey<Value> {
   public let key: String
   public let defaultValue: Value
 }
 
 extension AppStorage {
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Bool {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Bool {
     self.init(wrappedValue: key.defaultValue, key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Int {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Int {
     self.init(wrappedValue: key.defaultValue, key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Double {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Double {
     self.init(wrappedValue: key.defaultValue, key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == String {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == String {
     self.init(wrappedValue: key.defaultValue, key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Data {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Data {
     self.init(wrappedValue: key.defaultValue, key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil)
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil)
   where Value: RawRepresentable, Value.RawValue == Int {
     self.init(wrappedValue: key.defaultValue, key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil)
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil)
   where Value: RawRepresentable, Value.RawValue == String {
     self.init(wrappedValue: key.defaultValue, key.key, store: store)
   }
 }
 
 extension AppStorage where Value: ExpressibleByNilLiteral {
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Bool? {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Bool? {
     self.init(key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Int? {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Int? {
     self.init(key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Double? {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Double? {
     self.init(key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == String? {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == String? {
     self.init(key.key, store: store)
   }
-  public init(_ key: AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Data? {
+  public init(_ key: _AppStorageKey<Value>, store: UserDefaults? = nil) where Value == Data? {
     self.init(key.key, store: store)
   }
 }
diff --git a/Sources/ClientModels/AppStoragePersistenceKeys.swift b/Sources/ClientModels/AppStoragePersistenceKeys.swift
new file mode 100644
index 00000000..7a2e487f
--- /dev/null
+++ b/Sources/ClientModels/AppStoragePersistenceKeys.swift
@@ -0,0 +1,22 @@
+import ComposableArchitecture
+
+extension PersistenceReaderKey where Self == AppStorageKey<Double> {
+  public static var installationTime: Self {
+    appStorage("installationTimeKey")
+  }
+}
+extension PersistenceReaderKey where Self == AppStorageKey<Bool> {
+  public static var hasShownFirstLaunchOnboarding: Self {
+    AppStorageKey("hasShownFirstLaunchOnboardingKey")
+  }
+}
+extension PersistenceReaderKey where Self == AppStorageKey<Int> {
+  public static var multiplayerOpensCount: Self {
+    AppStorageKey("multiplayerOpensCount")
+  }
+}
+extension PersistenceReaderKey where Self == AppStorageKey<Double> {
+  public static var lastReviewRequest: Self {
+    AppStorageKey("last-review-request-timeinterval")
+  }
+}
diff --git a/Sources/ClientModels/SavedGamesState.swift b/Sources/ClientModels/SavedGamesState.swift
index 5a160971..016368ed 100644
--- a/Sources/ClientModels/SavedGamesState.swift
+++ b/Sources/ClientModels/SavedGamesState.swift
@@ -1,3 +1,5 @@
+import ComposableArchitecture
+
 public struct SavedGamesState: Codable, Equatable {
   public var dailyChallengeUnlimited: InProgressGame?
   public var unlimited: InProgressGame?
@@ -10,3 +12,9 @@ public struct SavedGamesState: Codable, Equatable {
     self.unlimited = unlimited
   }
 }
+
+extension PersistenceReaderKey where Self == FileStorageKey<SavedGamesState> {
+  public static var savedGames: Self {
+    fileStorage(.documentsDirectory.appending(path: "saved-games.json"))
+  }
+}
diff --git a/Sources/CubeCore/CubeSceneView.swift b/Sources/CubeCore/CubeSceneView.swift
index 17065821..2dbf6c6f 100644
--- a/Sources/CubeCore/CubeSceneView.swift
+++ b/Sources/CubeCore/CubeSceneView.swift
@@ -13,7 +13,6 @@ public class CubeSceneView: SCNView, UIGestureRecognizerDelegate {
 
     public var cubes: ViewPuzzle
     public var enableGyroMotion: Bool
-    public var isOnLowPowerMode: Bool
     public var nub: NubState?
     public var playedWords: [PlayedWord]
     public var selectedFaceCount: Int
@@ -23,7 +22,6 @@ public class CubeSceneView: SCNView, UIGestureRecognizerDelegate {
     public init(
       cubes: ViewPuzzle,
       enableGyroMotion: Bool,
-      isOnLowPowerMode: Bool,
       nub: NubState?,
       playedWords: [PlayedWord],
       selectedFaceCount: Int,
@@ -32,7 +30,6 @@ public class CubeSceneView: SCNView, UIGestureRecognizerDelegate {
     ) {
       self.cubes = cubes
       self.enableGyroMotion = enableGyroMotion
-      self.isOnLowPowerMode = isOnLowPowerMode
       self.nub = nub
       self.playedWords = playedWords
       self.selectedFaceCount = selectedFaceCount
@@ -81,6 +78,9 @@ public class CubeSceneView: SCNView, UIGestureRecognizerDelegate {
   private let viewStore: ViewStore<ViewState, ViewAction>
   private var worldScale: Float = 1.0
 
+  @Published var isLowPowerEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled {
+    didSet { self.update() }
+  }
   var enableCubeShadow = true {
     didSet { self.update() }
   }
@@ -115,6 +115,12 @@ public class CubeSceneView: SCNView, UIGestureRecognizerDelegate {
     gameCubeNode.scale = .init(worldScale, worldScale, worldScale)
     self.scene?.rootNode.addChildNode(self.gameCubeNode)
 
+    NotificationCenter.default.publisher(for: .NSProcessInfoPowerStateDidChange)
+      .sink { [weak self] _ in
+        self?.isLowPowerEnabled = ProcessInfo.processInfo.isLowPowerModeEnabled
+      }
+      .store(in: &cancellables)
+
     self.viewStore.publisher.cubes
       .sink { cubes in
         SCNTransaction.begin()
@@ -189,16 +195,16 @@ public class CubeSceneView: SCNView, UIGestureRecognizerDelegate {
     ambientLightNode.light = ambientLight
     self.scene?.rootNode.addChildNode(ambientLightNode)
 
-    self.viewStore.publisher
-      .map { ($0.enableGyroMotion, $0.isOnLowPowerMode) }
+    self.viewStore.publisher.map(\.enableGyroMotion)
+      .combineLatest(self.$isLowPowerEnabled)
       .removeDuplicates(by: ==)
-      .sink { [weak self] enableGyroMotion, isOnLowPowerMode in
+      .sink { [weak self] enableGyroMotion, isLowPowerEnabled in
         guard let self = self else { return }
 
         self.showsStatistics = self.showSceneStatistics
-        light.castsShadow = self.enableCubeShadow && !isOnLowPowerMode
+        light.castsShadow = self.enableCubeShadow && !isLowPowerEnabled
 
-        if isOnLowPowerMode || !enableGyroMotion {
+        if isLowPowerEnabled || !enableGyroMotion {
           self.stopMotionManager()
         } else {
           self.startMotionManager()
@@ -289,7 +295,7 @@ public class CubeSceneView: SCNView, UIGestureRecognizerDelegate {
   // TODO: rename
   private func update() {
     self.showsStatistics = self.showSceneStatistics
-    self.light.castsShadow = self.enableCubeShadow && !self.viewStore.isOnLowPowerMode
+    self.light.castsShadow = self.enableCubeShadow && !self.isLowPowerEnabled
   }
 
   deinit {
diff --git a/Sources/CubePreview/CubePreviewView.swift b/Sources/CubePreview/CubePreviewView.swift
index 07669e69..dd62e686 100644
--- a/Sources/CubePreview/CubePreviewView.swift
+++ b/Sources/CubePreview/CubePreviewView.swift
@@ -2,43 +2,33 @@ import Bloom
 import ComposableArchitecture
 import CubeCore
 import HapticsCore
-import LowPowerModeClient
 import Overture
 import SelectionSoundsCore
 import SharedModels
 import SwiftUI
-import UserSettingsClient
+import UserSettings
 
 @Reducer
 public struct CubePreview {
   @ObservableState
   public struct State: Equatable {
     var cubes: Puzzle
-    var enableGyroMotion: Bool
-    var isAnimationReduced: Bool
-    var isOnLowPowerMode: Bool
     var moveIndex: Int
     var moves: Moves
     var nub: CubeSceneView.ViewState.NubState
     var selectedCubeFaces: [IndexedCubeFace]
+    @Shared(.userSettings) var userSettings = UserSettings()
 
     public init(
       cubes: ArchivablePuzzle,
-      isOnLowPowerMode: Bool = false,
       moveIndex: Int,
       moves: Moves,
       nub: CubeSceneView.ViewState.NubState = .init(),
       selectedCubeFaces: [IndexedCubeFace] = []
     ) {
-      @Dependency(\.userSettings) var userSettings
-
       var cubes = Puzzle(archivableCubes: cubes)
       apply(moves: moves[0..<moveIndex], to: &cubes)
       self.cubes = cubes
-
-      self.enableGyroMotion = userSettings.enableGyroMotion
-      self.isAnimationReduced = userSettings.enableReducedAnimation
-      self.isOnLowPowerMode = isOnLowPowerMode
       self.moveIndex = moveIndex
       self.moves = moves
       self.nub = nub
@@ -83,8 +73,7 @@ public struct CubePreview {
             }
           }
         },
-        enableGyroMotion: self.enableGyroMotion,
-        isOnLowPowerMode: self.isOnLowPowerMode,
+        enableGyroMotion: self.userSettings.enableGyroMotion,
         nub: self.nub,
         playedWords: [],
         selectedFaceCount: self.selectedCubeFaces.count,
@@ -110,14 +99,11 @@ public struct CubePreview {
   public enum Action: BindableAction {
     case binding(BindingAction<State>)
     case cubeScene(CubeSceneView.ViewAction)
-    case lowPowerModeResponse(Bool)
     case tap
     case task
   }
 
-  @Dependency(\.lowPowerMode) var lowPowerMode
   @Dependency(\.mainQueue) var mainQueue
-  @Dependency(\.userSettings) var userSettings
 
   public init() {}
 
@@ -133,10 +119,6 @@ public struct CubePreview {
       case .cubeScene:
         return .none
 
-      case let .lowPowerModeResponse(isOn):
-        state.isOnLowPowerMode = isOn
-        return .none
-
       case .tap:
         state.nub.location = .offScreenRight
         switch state.moves[state.moveIndex].type {
@@ -151,12 +133,6 @@ public struct CubePreview {
         return .run { [move = state.moves[state.moveIndex], nub = state.nub] send in
           var nub = nub
 
-          await send(
-            .lowPowerModeResponse(
-              await self.lowPowerMode.start().first(where: { _ in true }) ?? false
-            )
-          )
-
           try await self.mainQueue.sleep(for: .seconds(1))
 
           var accumulatedSelectedFaces: [IndexedCubeFace] = []
@@ -210,7 +186,7 @@ public struct CubePreview {
       }
     }
     .haptics(
-      isEnabled: { _ in self.userSettings.enableHaptics },
+      isEnabled: \.userSettings.enableHaptics,
       triggerOnChangeOf: \.selectedCubeFaces
     )
     .selectionSounds(
@@ -262,7 +238,7 @@ public struct CubePreviewView: View {
           .task { await store.send(.task).finish() }
       }
       .background {
-        if !store.isAnimationReduced {
+        if !store.userSettings.enableReducedAnimation {
           BloomBackground(
             size: proxy.size,
             word: store.selectedWordString
diff --git a/Sources/DailyChallengeFeature/DailyChallengeView.swift b/Sources/DailyChallengeFeature/DailyChallengeView.swift
index 08602325..70706a28 100644
--- a/Sources/DailyChallengeFeature/DailyChallengeView.swift
+++ b/Sources/DailyChallengeFeature/DailyChallengeView.swift
@@ -25,20 +25,18 @@ public struct DailyChallengeReducer {
     public var dailyChallenges: [FetchTodaysDailyChallengeResponse]
     @Presents public var destination: Destination.State?
     public var gameModeIsLoading: GameMode?
-    public var inProgressDailyChallengeUnlimited: InProgressGame?
+    @Shared(.savedGames) public var savedGames = SavedGamesState()
     public var userNotificationSettings: UserNotificationClient.Notification.Settings?
 
     public init(
       dailyChallenges: [FetchTodaysDailyChallengeResponse] = [],
       destination: Destination.State? = nil,
       gameModeIsLoading: GameMode? = nil,
-      inProgressDailyChallengeUnlimited: InProgressGame? = nil,
       userNotificationSettings: UserNotificationClient.Notification.Settings? = nil
     ) {
       self.dailyChallenges = dailyChallenges
       self.destination = destination
       self.gameModeIsLoading = gameModeIsLoading
-      self.inProgressDailyChallengeUnlimited = inProgressDailyChallengeUnlimited
       self.userNotificationSettings = userNotificationSettings
     }
 
@@ -66,7 +64,6 @@ public struct DailyChallengeReducer {
   }
 
   @Dependency(\.apiClient) var apiClient
-  @Dependency(\.fileClient) var fileClient
   @Dependency(\.mainRunLoop.now.date) var now
   @Dependency(\.userNotifications.getNotificationSettings) var getUserNotificationSettings
 
@@ -108,7 +105,7 @@ public struct DailyChallengeReducer {
           isPlayable = !challenge.yourResult.started
         case .unlimited:
           isPlayable =
-            !challenge.yourResult.started || state.inProgressDailyChallengeUnlimited != nil
+          !challenge.yourResult.started || state.savedGames.dailyChallengeUnlimited != nil
         }
 
         guard isPlayable
@@ -123,12 +120,7 @@ public struct DailyChallengeReducer {
           await send(
             .startDailyChallengeResponse(
               Result {
-                try await startDailyChallengeAsync(
-                  challenge,
-                  apiClient: self.apiClient,
-                  date: { self.now },
-                  fileClient: self.fileClient
-                )
+                try await startDailyChallenge(challenge)
               }
             )
           )
@@ -258,7 +250,7 @@ public struct DailyChallengeView: View {
   var unlimitedState: ButtonState {
     .init(
       fetchedResponse: store.dailyChallenges.unlimited,
-      inProgressGame: store.inProgressDailyChallengeUnlimited
+      inProgressGame: store.savedGames.dailyChallengeUnlimited
     )
   }
 
@@ -459,16 +451,15 @@ private struct RingEffect: GeometryEffect {
 
   struct DailyChallengeView_Previews: PreviewProvider {
     static var previews: some View {
+      @Shared(.savedGames) var savedGames = SavedGamesState()
+      let _ = savedGames.dailyChallengeUnlimited = update(.mock) {
+        $0?.moves = [.highScoringMove]
+      }
+
       Preview {
         NavigationView {
           DailyChallengeView(
-            store: .init(
-              initialState: DailyChallengeReducer.State(
-                inProgressDailyChallengeUnlimited: update(.mock) {
-                  $0?.moves = [.highScoringMove]
-                }
-              )
-            ) {
+            store: .init(initialState: DailyChallengeReducer.State()) {
               DailyChallengeReducer()
             } withDependencies: {
               $0.userNotifications.getNotificationSettings = {
diff --git a/Sources/DailyChallengeHelpers/DailyChallengeHelpers.swift b/Sources/DailyChallengeHelpers/DailyChallengeHelpers.swift
index 0efc5241..a4222066 100644
--- a/Sources/DailyChallengeHelpers/DailyChallengeHelpers.swift
+++ b/Sources/DailyChallengeHelpers/DailyChallengeHelpers.swift
@@ -2,7 +2,6 @@ import ApiClient
 import ClientModels
 import Combine
 import ComposableArchitecture
-import FileClient
 import Foundation
 import SharedModels
 
@@ -11,20 +10,20 @@ public enum DailyChallengeError: Error, Equatable {
   case couldNotFetch(nextStartsAt: Date)
 }
 
-public func startDailyChallengeAsync(
-  _ challenge: FetchTodaysDailyChallengeResponse,
-  apiClient: ApiClient,
-  date: @escaping () -> Date,
-  fileClient: FileClient
+public func startDailyChallenge(
+  _ challenge: FetchTodaysDailyChallengeResponse
 ) async throws -> InProgressGame {
+  @Dependency(\.apiClient) var apiClient
+  @Dependency(\.date.now) var now
+  @Shared(.savedGames) var savedGames = SavedGamesState()
+
   guard challenge.yourResult.rank == nil
   else {
     throw DailyChallengeError.alreadyPlayed(endsAt: challenge.dailyChallenge.endsAt)
   }
-
   guard
     challenge.dailyChallenge.gameMode == .unlimited,
-    let game = try? await fileClient.loadSavedGames().dailyChallengeUnlimited
+    let game = savedGames.dailyChallengeUnlimited
   else {
     do {
       return try await InProgressGame(
@@ -37,9 +36,8 @@ public func startDailyChallengeAsync(
           ),
           as: StartDailyChallengeResponse.self
         ),
-        date: date()
+        date: now
       )
-
     } catch {
       throw DailyChallengeError.couldNotFetch(nextStartsAt: challenge.dailyChallenge.endsAt)
     }
diff --git a/Sources/DemoFeature/Demo.swift b/Sources/DemoFeature/Demo.swift
index 3cf8f61b..4e595232 100644
--- a/Sources/DemoFeature/Demo.swift
+++ b/Sources/DemoFeature/Demo.swift
@@ -60,12 +60,9 @@ public struct Demo {
       Scope(state: \.game, action: \.game) {
         Game().transformDependency(\.self) {
           $0.database = .noop
-          $0.fileClient = .noop
           $0.gameCenter = .noop
           $0.remoteNotifications = .noop
-          $0.serverConfig = .noop
           $0.storeKit = .noop
-          $0.userDefaults = .noop
           $0.userNotifications = .noop
         }
       }
diff --git a/Sources/FileClient/Client.swift b/Sources/FileClient/Client.swift
deleted file mode 100644
index 7f38a397..00000000
--- a/Sources/FileClient/Client.swift
+++ /dev/null
@@ -1,17 +0,0 @@
-import DependenciesMacros
-import Foundation
-
-@DependencyClient
-public struct FileClient {
-  public var delete: @Sendable (String) async throws -> Void
-  public var load: @Sendable (String) async throws -> Data
-  public var save: @Sendable (String, Data) async throws -> Void
-
-  public func load<A: Decodable>(_ type: A.Type, from fileName: String) async throws -> A {
-    try await JSONDecoder().decode(A.self, from: self.load(fileName))
-  }
-
-  public func save<A: Encodable>(_ data: A, to fileName: String) async throws {
-    try await self.save(fileName, JSONEncoder().encode(data))
-  }
-}
diff --git a/Sources/FileClient/FileClientEffects.swift b/Sources/FileClient/FileClientEffects.swift
deleted file mode 100644
index c83cfff4..00000000
--- a/Sources/FileClient/FileClientEffects.swift
+++ /dev/null
@@ -1,13 +0,0 @@
-import ClientModels
-
-extension FileClient {
-  public func loadSavedGames() async throws -> SavedGamesState {
-    try await self.load(SavedGamesState.self, from: savedGamesFileName)
-  }
-
-  public func save(games: SavedGamesState) async throws {
-    try await self.save(games, to: savedGamesFileName)
-  }
-}
-
-public let savedGamesFileName = "saved-games"
diff --git a/Sources/FileClient/LiveKey.swift b/Sources/FileClient/LiveKey.swift
deleted file mode 100644
index d353aad1..00000000
--- a/Sources/FileClient/LiveKey.swift
+++ /dev/null
@@ -1,28 +0,0 @@
-import Dependencies
-import Foundation
-
-extension FileClient: DependencyKey {
-  public static let liveValue = {
-    let documentDirectory = FileManager.default
-      .urls(for: .documentDirectory, in: .userDomainMask)
-      .first!
-
-    return Self(
-      delete: {
-        try FileManager.default.removeItem(
-          at: documentDirectory.appendingPathComponent($0).appendingPathExtension("json")
-        )
-      },
-      load: {
-        try Data(
-          contentsOf: documentDirectory.appendingPathComponent($0).appendingPathExtension("json")
-        )
-      },
-      save: {
-        try $1.write(
-          to: documentDirectory.appendingPathComponent($0).appendingPathExtension("json")
-        )
-      }
-    )
-  }()
-}
diff --git a/Sources/FileClient/TestKey.swift b/Sources/FileClient/TestKey.swift
deleted file mode 100644
index f9a9d10b..00000000
--- a/Sources/FileClient/TestKey.swift
+++ /dev/null
@@ -1,35 +0,0 @@
-import Dependencies
-import Foundation
-import XCTestDebugSupport
-
-extension DependencyValues {
-  public var fileClient: FileClient {
-    get { self[FileClient.self] }
-    set { self[FileClient.self] = newValue }
-  }
-}
-
-extension FileClient: TestDependencyKey {
-  public static let previewValue = Self.noop
-  public static let testValue = Self()
-}
-
-extension FileClient {
-  public static let noop = Self(
-    delete: { _ in },
-    load: { _ in throw CancellationError() },
-    save: { _, _ in }
-  )
-
-  public mutating func override<A: Encodable>(load file: String, _ data: A) {
-    let fulfill = expectation(description: "FileClient.load(\(file))")
-    self.load = { @Sendable[self] in
-      if $0 == file {
-        fulfill()
-        return try JSONEncoder().encode(data)
-      } else {
-        return try await load($0)
-      }
-    }
-  }
-}
diff --git a/Sources/GameCore/CubeSceneViewState.swift b/Sources/GameCore/CubeSceneViewState.swift
index ea46084e..7b68b0a9 100644
--- a/Sources/GameCore/CubeSceneViewState.swift
+++ b/Sources/GameCore/CubeSceneViewState.swift
@@ -44,8 +44,7 @@ extension CubeSceneView.ViewState {
           }
         }
       },
-      enableGyroMotion: game.enableGyroMotion,
-      isOnLowPowerMode: game.isOnLowPowerMode,
+      enableGyroMotion: game.userSettings.enableGyroMotion,
       nub: nub,
       playedWords: game.playedWords,
       selectedFaceCount: game.selectedWord.count,
diff --git a/Sources/GameCore/Drawer.swift b/Sources/GameCore/Drawer.swift
index 23627eb7..76197773 100644
--- a/Sources/GameCore/Drawer.swift
+++ b/Sources/GameCore/Drawer.swift
@@ -3,7 +3,6 @@ import ComposableArchitecture
 
 @Reducer
 public struct ActiveGamesTray {
-  @Dependency(\.fileClient) var fileClient
   @Dependency(\.gameCenter) var gameCenter
   @Dependency(\.mainRunLoop.now.date) var now
 
@@ -32,11 +31,8 @@ public struct ActiveGamesTray {
         .destination,
         .gameCenter,
         .gameLoaded,
-        .lowPowerModeChanged,
         .matchesLoaded(.failure),
-        .savedGamesLoaded(.failure),
-        .timerTick,
-        .userSettingsUpdated:
+        .timerTick:
 
         return .none
 
@@ -50,10 +46,6 @@ public struct ActiveGamesTray {
       case .task:
         return self.activeGameEffects
 
-      case let .savedGamesLoaded(.success(savedGames)):
-        state.activeGames.savedGames = savedGames
-        return .none
-
       case .trayButtonTapped:
         guard state.isTrayAvailable else { return .none }
         state.isTrayVisible.toggle()
@@ -73,15 +65,6 @@ public struct ActiveGamesTray {
             animation: .default
           )
         }
-
-        group.addTask {
-          await send(
-            .savedGamesLoaded(
-              Result { try await self.fileClient.loadSavedGames() }
-            ),
-            animation: .default
-          )
-        }
       }
     }
   }
diff --git a/Sources/GameCore/GameCore.swift b/Sources/GameCore/GameCore.swift
index 40ae2aa3..07a95b8b 100644
--- a/Sources/GameCore/GameCore.swift
+++ b/Sources/GameCore/GameCore.swift
@@ -9,7 +9,6 @@ import Dependencies
 import DictionaryClient
 import GameOverFeature
 import HapticsCore
-import LowPowerModeClient
 import Overture
 import SettingsFeature
 import SharedModels
@@ -17,7 +16,7 @@ import SwiftUI
 import Tagged
 import TcaHelpers
 import UpgradeInterstitialFeature
-import UserSettingsClient
+import UserSettings
 
 @Reducer
 public struct Game {
@@ -54,11 +53,8 @@ public struct Game {
     public var gameCurrentTime: Date
     public var gameMode: GameMode
     public var gameStartTime: Date
-    public var enableGyroMotion: Bool
-    public var isAnimationReduced: Bool
     public var isDemo: Bool
     public var isGameLoaded: Bool
-    public var isOnLowPowerMode: Bool
     public var isPanning: Bool
     public var isTrayVisible: Bool
     public var language: Language
@@ -67,7 +63,9 @@ public struct Game {
     public var secondsPlayed: Int
     public var selectedWord: [IndexedCubeFace]
     public var selectedWordIsValid: Bool
+    @Shared(.userSettings) public var userSettings = UserSettings()
     public var wordSubmitButton: WordSubmitButtonFeature.ButtonState
+    @Shared(.multiplayerOpensCount) var multiplayerOpensCount = 0
 
     public init(
       activeGames: ActiveGamesState = .init(),
@@ -81,7 +79,6 @@ public struct Game {
       isDemo: Bool = false,
       isGameLoaded: Bool = false,
       isPanning: Bool = false,
-      isOnLowPowerMode: Bool = false,
       isTrayVisible: Bool = false,
       language: Language = .en,
       moves: Moves = [],
@@ -91,20 +88,16 @@ public struct Game {
       selectedWordIsValid: Bool = false,
       wordSubmit: WordSubmitButtonFeature.ButtonState = .init()
     ) {
-      @Dependency(\.userSettings) var userSettings
       self.activeGames = activeGames
       self.cubes = cubes
       self.cubeStartedShakingAt = cubeStartedShakingAt
       self.destination = destination
-      self.enableGyroMotion = userSettings.enableGyroMotion
       self.gameContext = gameContext
       self.gameCurrentTime = gameCurrentTime
       self.gameMode = gameMode
       self.gameStartTime = gameStartTime
-      self.isAnimationReduced = userSettings.enableReducedAnimation
       self.isDemo = isDemo
       self.isGameLoaded = isGameLoaded
-      self.isOnLowPowerMode = isOnLowPowerMode
       self.isPanning = isPanning
       self.isTrayVisible = isTrayVisible
       self.language = language
@@ -148,17 +141,14 @@ public struct Game {
     case doubleTap(index: LatticePoint)
     case gameCenter(GameCenterAction)
     case gameLoaded
-    case lowPowerModeChanged(Bool)
     case matchesLoaded(Result<[TurnBasedMatch], Error>)
     case menuButtonTapped
     case task
     case pan(UIGestureRecognizer.State, PanData?)
-    case savedGamesLoaded(Result<SavedGamesState, Error>)
     case submitButtonTapped(reaction: Move.Reaction?)
     case tap(UIGestureRecognizer.State, IndexedCubeFace?)
     case timerTick(Date)
     case trayButtonTapped
-    case userSettingsUpdated(UserSettings)
     case wordSubmitButton(WordSubmitButtonFeature.Action)
   }
 
@@ -173,12 +163,8 @@ public struct Game {
   @Dependency(\.dismiss) var dismiss
   @Dependency(\.dictionary.contains) var dictionaryContains
   @Dependency(\.gameCenter) var gameCenter
-  @Dependency(\.lowPowerMode) var lowPowerMode
   @Dependency(\.mainQueue) var mainQueue
   @Dependency(\.mainRunLoop) var mainRunLoop
-  @Dependency(\.serverConfig.config) var serverConfig
-  @Dependency(\.userDefaults) var userDefaults
-  @Dependency(\.userSettings) var userSettings
 
   public init() {}
 
@@ -305,10 +291,6 @@ public struct Game {
           }
         }
 
-      case let .lowPowerModeChanged(isOn):
-        state.isOnLowPowerMode = isOn
-        return .none
-
       case .matchesLoaded:
         return .none
 
@@ -319,26 +301,19 @@ public struct Game {
       case .task:
         guard !state.isGameOver else { return .none }
         state.gameCurrentTime = self.date()
-
-        return .run { [gameContext = state.gameContext] send in
+        if state.gameContext.is(\.turnBased) {
+          state.multiplayerOpensCount += 1
+        }
+        return .run { [multiplayerOpensCount = state.multiplayerOpensCount, gameContext = state.gameContext] send in
           await withThrowingTaskGroup(of: Void.self) { group in
-            group.addTask {
-              for await isLowPower in await self.lowPowerMode.start() {
-                await send(.lowPowerModeChanged(isLowPower))
-              }
-            }
-
             if gameContext.is(\.turnBased) {
               group.addTask {
-                let playedGamesCount = await self.userDefaults
-                  .incrementMultiplayerOpensCount()
                 let isFullGamePurchased = self.currentPlayer()?.appleReceipt != nil
                 guard
                   !isFullGamePurchased,
                   shouldShowInterstitial(
-                    gamePlayedCount: playedGamesCount,
-                    gameContext: .init(gameContext: gameContext),
-                    serverConfig: self.serverConfig()
+                    gamePlayedCount: multiplayerOpensCount,
+                    gameContext: .init(gameContext: gameContext)
                   )
                 else { return }
                 try await self.mainRunLoop.sleep(for: .seconds(3))
@@ -350,12 +325,6 @@ public struct Game {
               try await self.mainQueue.sleep(for: 0.5)
               await send(.gameLoaded)
             }
-
-            group.addTask {
-              for await userSettings in self.userSettings.stream() {
-                await send(.userSettingsUpdated(userSettings))
-              }
-            }
           }
           for music in AudioPlayerClient.Sound.allMusic {
             await self.audioPlayer.stop(music)
@@ -397,9 +366,6 @@ public struct Game {
         state.isPanning = false
         return .none
 
-      case .savedGamesLoaded:
-        return .none
-
       case let .submitButtonTapped(reaction: reaction),
         let .wordSubmitButton(.delegate(.confirmSubmit(reaction: reaction))):
 
@@ -511,11 +477,6 @@ public struct Game {
       case .trayButtonTapped:
         return .none
 
-      case let .userSettingsUpdated(userSettings):
-        state.enableGyroMotion = userSettings.enableGyroMotion
-        state.isAnimationReduced = userSettings.enableReducedAnimation
-        return .none
-
       case .wordSubmitButton:
         return .none
       }
@@ -665,17 +626,16 @@ extension DependencyValues {
     self = Self.test
     self.apiClient = .noop
     self.audioPlayer = previousValues.audioPlayer
-    self.build = .noop
+    //self.build = .noop
     self.database = .noop
     self.date = previousValues.date
     self.dictionary = previousValues.dictionary
     self.feedbackGenerator = previousValues.feedbackGenerator
-    self.fileClient = .noop
     self.gameCenter = .noop
     self.mainRunLoop = previousValues.mainRunLoop
     self.mainQueue = previousValues.mainQueue
     self.remoteNotifications = .noop
-    self.serverConfig = .noop
+    //self.serverConfig = .noop
     self.storeKit = .noop
     self.userNotifications = .noop
   }
diff --git a/Sources/GameCore/TurnBased.swift b/Sources/GameCore/TurnBased.swift
index b297a7eb..94a367f3 100644
--- a/Sources/GameCore/TurnBased.swift
+++ b/Sources/GameCore/TurnBased.swift
@@ -189,14 +189,11 @@ extension Reducer where State == Game.State, Action == Game.Action {
         .doubleTap,
         .gameCenter,
         .gameLoaded,
-        .lowPowerModeChanged,
         .matchesLoaded,
         .menuButtonTapped,
         .task,
-        .savedGamesLoaded,
         .timerTick,
         .trayButtonTapped,
-        .userSettingsUpdated,
         .wordSubmitButton:
         return true
       }
diff --git a/Sources/GameCore/Views/GameFooterView.swift b/Sources/GameCore/Views/GameFooterView.swift
index 49de9ea8..5ec47ecb 100644
--- a/Sources/GameCore/Views/GameFooterView.swift
+++ b/Sources/GameCore/Views/GameFooterView.swift
@@ -22,7 +22,7 @@ public struct GameFooterView: View {
         store: store
       )
       .transition(
-        store.isAnimationReduced
+        store.userSettings.enableReducedAnimation
           ? .opacity
           : AnyTransition.offset(y: 50)
             .combined(with: .opacity)
diff --git a/Sources/GameCore/Views/GameView.swift b/Sources/GameCore/Views/GameView.swift
index 7c33d2cc..32e62eff 100644
--- a/Sources/GameCore/Views/GameView.swift
+++ b/Sources/GameCore/Views/GameView.swift
@@ -71,7 +71,7 @@ public struct GameView<Content>: View where Content: View {
             )
             .ignoresSafeArea()
             .transition(
-              store.isAnimationReduced
+              store.userSettings.enableReducedAnimation
                 ? .opacity
                 : .asymmetric(insertion: .offset(y: 50), removal: .offset(y: 50))
                   .combined(with: .opacity)
@@ -126,7 +126,7 @@ public struct GameView<Content>: View where Content: View {
       }
       .frame(maxWidth: .infinity, maxHeight: .infinity)
       .background {
-        if !store.isAnimationReduced {
+        if !store.userSettings.enableReducedAnimation {
           BloomBackground(
             size: proxy.size,
             word: store.selectedWordString
diff --git a/Sources/GameOverFeature/GameOverView.swift b/Sources/GameOverFeature/GameOverView.swift
index a93559c5..42bde9bf 100644
--- a/Sources/GameOverFeature/GameOverView.swift
+++ b/Sources/GameOverFeature/GameOverView.swift
@@ -13,7 +13,6 @@ import Styleguide
 import SwiftUI
 import SwiftUIHelpers
 import UpgradeInterstitialFeature
-import UserDefaultsClient
 
 @Reducer
 public struct GameOver {
@@ -128,12 +127,10 @@ public struct GameOver {
   @Dependency(\.audioPlayer) var audioPlayer
   @Dependency(\.database) var database
   @Dependency(\.dismissGame) var dismissGame
-  @Dependency(\.fileClient) var fileClient
   @Dependency(\.mainRunLoop) var mainRunLoop
-  @Dependency(\.storeKit.requestReview) var requestReview
-  @Dependency(\.serverConfig.config) var serverConfig
-  @Dependency(\.userDefaults) var userDefaults
+  @Dependency(\.storeKit) var storeKit
   @Dependency(\.userNotifications.getNotificationSettings) var getUserNotificationSettings
+  @Shared(.lastReviewRequest) public var lastReviewRequest = 0
 
   public init() {}
 
@@ -146,8 +143,8 @@ public struct GameOver {
             .contains(state.userNotificationSettings?.authorizationStatus),
           case .dailyChallenge = state.completedGame.gameContext
         else {
-          return .run { send in
-            try? await self.requestReviewAsync()
+          return .run { _ in
+            try await self.requestReview()
             await self.dismissGame(animation: .default)
           }
         }
@@ -185,12 +182,7 @@ public struct GameOver {
             await send(
               .startDailyChallengeResponse(
                 Result {
-                  try await startDailyChallengeAsync(
-                    challenge,
-                    apiClient: self.apiClient,
-                    date: { self.mainRunLoop.now.date },
-                    fileClient: self.fileClient
-                  )
+                  try await startDailyChallenge(challenge)
                 }
               )
             )
@@ -207,7 +199,7 @@ public struct GameOver {
       case .destination(.dismiss)
       where state.destination.is(\.some.notificationsAuthAlert):
         return .run { _ in
-          try? await self.requestReviewAsync()
+          try await self.requestReview()
           await self.dismissGame(animation: .default)
         }
 
@@ -330,8 +322,7 @@ public struct GameOver {
                 !isFullGamePurchased,
                 shouldShowInterstitial(
                   gamePlayedCount: playedGamesCount,
-                  gameContext: .init(gameContext: completedGame.gameContext),
-                  serverConfig: self.serverConfig()
+                  gameContext: .init(gameContext: completedGame.gameContext)
                 )
               else { return }
               await send(.delayedShowUpgradeInterstitial, animation: .easeIn)
@@ -362,23 +353,18 @@ public struct GameOver {
     }
   }
 
-  private func requestReviewAsync() async throws {
+  private func requestReview() async throws {
     let stats = try await self.database.fetchStats()
-    let hasRequestedReviewBefore =
-      self.userDefaults.doubleForKey(lastReviewRequestTimeIntervalKey) != 0
+    let hasRequestedReviewBefore = self.lastReviewRequest != 0
     let timeSinceLastReviewRequest =
-      self.mainRunLoop.now.date.timeIntervalSince1970
-      - self.userDefaults.doubleForKey(lastReviewRequestTimeIntervalKey)
+    self.mainRunLoop.now.date.timeIntervalSince1970 - self.lastReviewRequest
     let weekInSeconds: Double = 60 * 60 * 24 * 7
 
     if stats.gamesPlayed >= 3
       && (!hasRequestedReviewBefore || timeSinceLastReviewRequest >= weekInSeconds)
     {
-      await self.requestReview()
-      await self.userDefaults.setDouble(
-        self.mainRunLoop.now.date.timeIntervalSince1970,
-        lastReviewRequestTimeIntervalKey
-      )
+      await self.storeKit.requestReview()
+      self.lastReviewRequest = self.mainRunLoop.now.date.timeIntervalSince1970
     }
   }
 }
diff --git a/Sources/HomeFeature/Home.swift b/Sources/HomeFeature/Home.swift
index ad59735b..a04be50b 100644
--- a/Sources/HomeFeature/Home.swift
+++ b/Sources/HomeFeature/Home.swift
@@ -8,12 +8,12 @@ import DeviceId
 import LeaderboardFeature
 import MultiplayerFeature
 import Overture
-import ServerConfigClient
+import ServerConfigPersistenceKey
 import SettingsFeature
 import SharedModels
 import SoloFeature
 import SwiftUI
-import UserDefaultsClient
+import Build
 
 public struct ActiveMatchResponse: Equatable {
   public let matches: [ActiveTurnBasedMatch]
@@ -36,50 +36,44 @@ public struct Home {
   public struct State: Equatable {
     public var dailyChallenges: [FetchTodaysDailyChallengeResponse]?
     @Presents public var destination: Destination.State?
-    public var hasChangelog: Bool
     public var hasPastTurnBasedGames: Bool
     @Presents public var nagBanner: NagBanner.State?
-    public var savedGames: SavedGamesState {
-      didSet {
-        guard var dailyChallengeState = self.destination?.dailyChallenge
-        else { return }
-        dailyChallengeState.inProgressDailyChallengeUnlimited =
-          self.savedGames.dailyChallengeUnlimited
-        self.destination = .dailyChallenge(dailyChallengeState)
-      }
-    }
+    @Shared(.savedGames) public var savedGames = SavedGamesState()
     public var turnBasedMatches: [ActiveTurnBasedMatch]
     public var weekInReview: FetchWeekInReviewResponse?
+    @Shared(.installationTime) var installationTime = Date().timeIntervalSince1970
+    @Shared(.build) var build = Build()
+    //@SharedReader(.serverConfig) var serverConfig = ServerConfig()
+    @ObservationStateIgnored
+    @ServerConfig_ var serverConfig
+
+    public var hasChangelog: Bool {
+      self.serverConfig.newestBuild > self.build.number
+    }
 
     public var activeGames: ActiveGamesState {
       get {
-        .init(
-          savedGames: self.savedGames,
+        ActiveGamesState(
           turnBasedMatches: self.turnBasedMatches
         )
       }
       set {
-        self.savedGames = newValue.savedGames
         self.turnBasedMatches = newValue.turnBasedMatches
       }
     }
 
     public init(
       dailyChallenges: [FetchTodaysDailyChallengeResponse]? = nil,
-      hasChangelog: Bool = false,
       hasPastTurnBasedGames: Bool = false,
       nagBanner: NagBanner.State? = nil,
       destination: Destination.State? = nil,
-      savedGames: SavedGamesState = SavedGamesState(),
       turnBasedMatches: [ActiveTurnBasedMatch] = [],
       weekInReview: FetchWeekInReviewResponse? = nil
     ) {
       self.dailyChallenges = dailyChallenges
       self.destination = destination
-      self.hasChangelog = hasChangelog
       self.hasPastTurnBasedGames = hasPastTurnBasedGames
       self.nagBanner = nagBanner
-      self.savedGames = savedGames
       self.turnBasedMatches = turnBasedMatches
       self.weekInReview = weekInReview
     }
@@ -104,7 +98,6 @@ public struct Home {
     case leaderboardButtonTapped
     case multiplayerButtonTapped
     case nagBanner(PresentationAction<NagBanner.Action>)
-    case serverConfigResponse(ServerConfig)
     case settingsButtonTapped
     case soloButtonTapped
     case task
@@ -118,14 +111,12 @@ public struct Home {
   }
 
   @Dependency(\.apiClient) var apiClient
-  @Dependency(\.build.number) var buildNumber
   @Dependency(\.deviceId) var deviceId
   @Dependency(\.gameCenter) var gameCenter
   @Dependency(\.mainRunLoop.now.date) var now
   @Dependency(\.audioPlayer.play) var playSound
-  @Dependency(\.serverConfig) var serverConfig
   @Dependency(\.timeZone) var timeZone
-  @Dependency(\.userDefaults) var userDefaults
+  //@SharedReader(.serverConfig) var serverConfig = ServerConfig()
 
   public init() {}
 
@@ -208,8 +199,8 @@ public struct Home {
     case let .authenticationResponse(currentPlayerEnvelope):
       let now = self.now.timeIntervalSinceReferenceDate
       let itsNagTime =
-        Int(now - self.userDefaults.installationTime)
-        >= self.serverConfig.config().upgradeInterstitial.nagBannerAfterInstallDuration
+        Int(now - state.installationTime)
+      >= state.serverConfig.upgradeInterstitial.nagBannerAfterInstallDuration
       let isFullGamePurchased =
         currentPlayerEnvelope.appleReceipt?.receipt.originalPurchaseDate != nil
 
@@ -226,15 +217,17 @@ public struct Home {
 
     case .dailyChallengeButtonTapped:
       state.destination = .dailyChallenge(
-        .init(
-          dailyChallenges: state.dailyChallenges ?? [],
-          inProgressDailyChallengeUnlimited: state.savedGames.dailyChallengeUnlimited
-        )
+        DailyChallengeReducer.State(dailyChallenges: state.dailyChallenges ?? [])
       )
       return .none
 
     case let .dailyChallengeResponse(.success(dailyChallenges)):
       state.dailyChallenges = dailyChallenges
+      if dailyChallenges.unlimited?.dailyChallenge.id
+          != state.savedGames.dailyChallengeUnlimited?.gameContext.dailyChallenge
+      {
+        state.savedGames.dailyChallengeUnlimited = nil
+      }
       return .none
 
     case .dailyChallengeResponse(.failure):
@@ -250,10 +243,6 @@ public struct Home {
     case .howToPlayButtonTapped:
       return .none
 
-    case let .serverConfigResponse(serverConfig):
-      state.hasChangelog = serverConfig.newestBuild > self.buildNumber()
-      return .none
-
     case .leaderboardButtonTapped:
       state.destination = .leaderboard(Leaderboard.State())
       return .none
@@ -307,9 +296,8 @@ public struct Home {
       )
       await send(.authenticationResponse(currentPlayerEnvelope))
 
-      async let serverConfigResponse: Void = send(
-        .serverConfigResponse(self.serverConfig.refresh())
-      )
+      @ServerConfig_ var serverConfig
+      async let serverConfigResponse: Void = $serverConfig.reload()
 
       async let dailyChallengeResponse: Void = send(
         .dailyChallengeResponse(
diff --git a/Sources/LeaderboardFeature/Leaderboard.swift b/Sources/LeaderboardFeature/Leaderboard.swift
index 3eabf569..b8f84b45 100644
--- a/Sources/LeaderboardFeature/Leaderboard.swift
+++ b/Sources/LeaderboardFeature/Leaderboard.swift
@@ -4,7 +4,7 @@ import CubeCore
 import CubePreview
 import SharedModels
 import SwiftUI
-import UserSettingsClient
+import UserSettings
 
 public enum LeaderboardScope: CaseIterable, Equatable {
   case games
diff --git a/Sources/LowPowerModeClient/Client.swift b/Sources/LowPowerModeClient/Client.swift
deleted file mode 100644
index 9a1af71e..00000000
--- a/Sources/LowPowerModeClient/Client.swift
+++ /dev/null
@@ -1,6 +0,0 @@
-import DependenciesMacros
-
-@DependencyClient
-public struct LowPowerModeClient {
-  public var start: @Sendable () async -> AsyncStream<Bool> = { .finished }
-}
diff --git a/Sources/LowPowerModeClient/LiveKey.swift b/Sources/LowPowerModeClient/LiveKey.swift
deleted file mode 100644
index 331e8123..00000000
--- a/Sources/LowPowerModeClient/LiveKey.swift
+++ /dev/null
@@ -1,23 +0,0 @@
-import Dependencies
-import Foundation
-
-extension LowPowerModeClient: DependencyKey {
-  public static let liveValue = Self(
-    start: {
-      AsyncStream { continuation in
-        continuation.yield(ProcessInfo.processInfo.isLowPowerModeEnabled)
-        let task = Task {
-          let powerStateDidChange = NotificationCenter.default
-            .notifications(named: .NSProcessInfoPowerStateDidChange)
-            .map { _ in ProcessInfo.processInfo.isLowPowerModeEnabled }
-          for await isLowPowerModeEnabled in powerStateDidChange {
-            continuation.yield(isLowPowerModeEnabled)
-          }
-        }
-        continuation.onTermination = { _ in
-          task.cancel()
-        }
-      }
-    }
-  )
-}
diff --git a/Sources/LowPowerModeClient/TestKey.swift b/Sources/LowPowerModeClient/TestKey.swift
deleted file mode 100644
index 67f97658..00000000
--- a/Sources/LowPowerModeClient/TestKey.swift
+++ /dev/null
@@ -1,46 +0,0 @@
-import ComposableArchitecture
-import Foundation
-
-extension DependencyValues {
-  public var lowPowerMode: LowPowerModeClient {
-    get { self[LowPowerModeClient.self] }
-    set { self[LowPowerModeClient.self] = newValue }
-  }
-}
-
-extension LowPowerModeClient: TestDependencyKey {
-  public static let previewValue = Self.true
-  public static let testValue = Self()
-}
-
-extension LowPowerModeClient {
-  public static let `false` = Self(
-    start: { AsyncStream { $0.yield(false) } }
-  )
-
-  public static let `true` = Self(
-    start: { AsyncStream { $0.yield(true) } }
-  )
-
-  public static var backAndForth: Self {
-    Self(
-      start: {
-        AsyncStream<Bool> { continuation in
-          let isLowPowerModeEnabled = ActorIsolated(false)
-          Task {
-            await continuation.yield(isLowPowerModeEnabled.value)
-            for await _ in DispatchQueue.main.timer(interval: 2) {
-              let isLowPowerModeEnabled =
-                await isLowPowerModeEnabled
-                .withValue { isLowPowerModeEnabled -> Bool in
-                  isLowPowerModeEnabled.toggle()
-                  return isLowPowerModeEnabled
-                }
-              continuation.yield(isLowPowerModeEnabled)
-            }
-          }
-        }
-      }
-    )
-  }
-}
diff --git a/Sources/OnboardingFeature/OnboardingView.swift b/Sources/OnboardingFeature/OnboardingView.swift
index b10ada14..9df5b4f7 100644
--- a/Sources/OnboardingFeature/OnboardingView.swift
+++ b/Sources/OnboardingFeature/OnboardingView.swift
@@ -10,7 +10,7 @@ import SharedModels
 import Styleguide
 import SwiftUI
 import UIApplicationClient
-import UserDefaultsClient
+import UserSettings
 
 @Reducer
 public struct Onboarding {
@@ -20,6 +20,8 @@ public struct Onboarding {
     public var game: Game.State
     public var presentationStyle: PresentationStyle
     public var step: Step
+    @Shared(.userSettings) public var userSettings = UserSettings()
+    @Shared(.hasShownFirstLaunchOnboarding) var hasShownFirstLaunchOnboarding = false
 
     public init(
       alert: AlertState<Action.Alert>? = nil,
@@ -181,8 +183,6 @@ public struct Onboarding {
   @Dependency(\.dictionary) var dictionary
   @Dependency(\.feedbackGenerator) var feedbackGenerator
   @Dependency(\.mainQueue) var mainQueue
-  @Dependency(\.userDefaults) var userDefaults
-  @Dependency(\.userSettings) var userSettings
 
   public init() {}
 
@@ -204,8 +204,8 @@ public struct Onboarding {
         return .none
 
       case .delegate(.getStarted):
+        state.hasShownFirstLaunchOnboarding = true
         return .run { _ in
-          await self.userDefaults.setHasShownFirstLaunchOnboarding(true)
           await self.audioPlayer.stop(.onboardingBgMusic)
           Task.cancel(id: CancelID.delayedNextStep)
         }
@@ -268,7 +268,7 @@ public struct Onboarding {
         return .run { _ in await self.audioPlayer.play(.uiSfxTap) }
 
       case .skipButtonTapped:
-        guard !self.userDefaults.hasShownFirstLaunchOnboarding else {
+        guard !state.hasShownFirstLaunchOnboarding else {
           return .run { send in
             await send(.delegate(.getStarted), animation: .default)
             await self.audioPlayer.play(.uiSfxTap)
@@ -380,7 +380,7 @@ public struct Onboarding {
     Scope(state: \.game, action: \.game) {
       Game()
         .haptics(
-          isEnabled: { _ in self.userSettings.enableHaptics },
+          isEnabled: \.userSettings.enableHaptics,
           triggerOnChangeOf: \.selectedWord
         )
     }
diff --git a/Sources/ServerConfig/ServerConfig.swift b/Sources/ServerConfig/ServerConfig.swift
index 60732017..87f698c9 100644
--- a/Sources/ServerConfig/ServerConfig.swift
+++ b/Sources/ServerConfig/ServerConfig.swift
@@ -2,7 +2,7 @@ import Build
 import Foundation
 import Tagged
 
-public struct ServerConfig: Codable, Equatable, Hashable {
+public struct ServerConfig: Codable, Equatable, Hashable, Sendable {
   public var appId: String
   public var newestBuild: Build.Number
   public var forceUpgradeVersion: Int
@@ -23,13 +23,13 @@ public struct ServerConfig: Codable, Equatable, Hashable {
     self.upgradeInterstitial = upgradeInterstitial
   }
 
-  public struct ProductIdentifiers: Codable, Equatable, Hashable {
+  public struct ProductIdentifiers: Codable, Equatable, Hashable, Sendable {
     public var fullGame: String = "co.pointfree.isowords_testing.full_game"
 
     public static let `default` = Self()
   }
 
-  public struct UpgradeInterstitial: Codable, Equatable, Hashable {
+  public struct UpgradeInterstitial: Codable, Equatable, Hashable, Sendable {
     public var dailyChallengeTriggerEvery = 1
     public var duration = 10
     public var multiplayerGameTriggerEvery = 4
diff --git a/Sources/ServerConfigClient/Client.swift b/Sources/ServerConfigClient/Client.swift
deleted file mode 100644
index 2b85d77d..00000000
--- a/Sources/ServerConfigClient/Client.swift
+++ /dev/null
@@ -1,8 +0,0 @@
-import DependenciesMacros
-@_exported import ServerConfig
-
-@DependencyClient
-public struct ServerConfigClient {
-  public var config: () -> ServerConfig = { ServerConfig() }
-  public var refresh: @Sendable () async throws -> ServerConfig
-}
diff --git a/Sources/ServerConfigClient/LiveKey.swift b/Sources/ServerConfigClient/LiveKey.swift
deleted file mode 100644
index e419e8d1..00000000
--- a/Sources/ServerConfigClient/LiveKey.swift
+++ /dev/null
@@ -1,29 +0,0 @@
-import ComposableArchitecture
-import Foundation
-import ServerConfig
-
-extension ServerConfigClient {
-  public static func live(
-    fetch: @escaping @Sendable () async throws -> ServerConfig
-  ) -> Self {
-    Self(
-      config: {
-        (UserDefaults.standard.object(forKey: serverConfigKey) as? Data)
-          .flatMap { try? jsonDecoder.decode(ServerConfig.self, from: $0) }
-          ?? ServerConfig()
-      },
-      refresh: {
-        let config = try await fetch()
-        if let data = try? jsonEncoder.encode(config) {
-          UserDefaults.standard.set(data, forKey: serverConfigKey)
-        }
-        return config
-      }
-    )
-  }
-}
-
-let jsonDecoder = JSONDecoder()
-let jsonEncoder = JSONEncoder()
-
-private let serverConfigKey = "co.pointfree.serverConfigKey"
diff --git a/Sources/ServerConfigClient/TestKey.swift b/Sources/ServerConfigClient/TestKey.swift
deleted file mode 100644
index 3ba47878..00000000
--- a/Sources/ServerConfigClient/TestKey.swift
+++ /dev/null
@@ -1,20 +0,0 @@
-import Dependencies
-
-extension DependencyValues {
-  public var serverConfig: ServerConfigClient {
-    get { self[ServerConfigClient.self] }
-    set { self[ServerConfigClient.self] = newValue }
-  }
-}
-
-extension ServerConfigClient: TestDependencyKey {
-  public static let previewValue = Self.noop
-  public static let testValue = Self()
-}
-
-extension ServerConfigClient {
-  public static let noop = Self(
-    config: { .init() },
-    refresh: { try await Task.never() }
-  )
-}
diff --git a/Sources/ServerConfigPersistenceKey/ServerConfigPersistenceKey.swift b/Sources/ServerConfigPersistenceKey/ServerConfigPersistenceKey.swift
new file mode 100644
index 00000000..4696dce9
--- /dev/null
+++ b/Sources/ServerConfigPersistenceKey/ServerConfigPersistenceKey.swift
@@ -0,0 +1,83 @@
+import ApiClient
+import Build
+import ComposableArchitecture
+import Dependencies
+import Foundation
+@_exported import ServerConfig
+
+@propertyWrapper
+public struct ServerConfig_: Equatable {
+  @Shared(.fileStorage(.serverConfig)) var config = ServerConfig()
+
+  public init(config: ServerConfig = ServerConfig()) {
+    self.config = config
+  }
+
+  public var projectedValue: Self { self }
+
+  public var wrappedValue: ServerConfig {
+    get { config }
+    nonmutating set { config = newValue }
+  }
+
+  public func reload() async throws {
+    @Dependency(\.apiClient) var apiClient
+    @Shared(.build) var build = Build()
+    self.config = try await apiClient
+      .apiRequest(route: .config(build: build.number), as: ServerConfig.self)
+  }
+}
+
+extension PersistenceReaderKey where Self == ServerConfigKey {
+  public static var serverConfig: Self {
+    ServerConfigKey()
+  }
+}
+
+public struct ServerConfigKey: PersistenceReaderKey, Hashable, Sendable {
+  @Dependency(\.apiClient) var apiClient
+  @Shared(.build) var build = Build()
+  @Shared(.fileStorage(.serverConfig)) var config = ServerConfig()
+  let (stream, continuation) = AsyncStream<Void>.makeStream()
+
+  public init() {}
+
+  public func reload() async {
+    continuation.yield()
+  }
+
+  public func load(initialValue: ServerConfig?) -> ServerConfig? {
+    config
+  }
+
+  public func subscribe(
+    initialValue: ServerConfig?,
+    didSet: @escaping (ServerConfig?) -> Void
+  ) -> Shared<ServerConfig, Self>.Subscription {
+    let task = Task {
+      try await didSet(
+        apiClient
+          .apiRequest(route: .config(build: build.number), as: ServerConfig.self)
+      )
+      for await _ in stream {
+        let config =
+          try await apiClient
+          .apiRequest(route: .config(build: build.number), as: ServerConfig.self)
+        didSet(config)
+      }
+    }
+    return Shared.Subscription {
+      task.cancel()
+    }
+  }
+
+  public static func == (lhs: ServerConfigKey, rhs: ServerConfigKey) -> Bool {
+    true
+  }
+  public func hash(into hasher: inout Hasher) {
+  }
+}
+
+extension URL {
+  fileprivate static let serverConfig = documentsDirectory.appending(path: "server-config.json")
+}
diff --git a/Sources/SettingsFeature/AppearanceSettingsView.swift b/Sources/SettingsFeature/AppearanceSettingsView.swift
index caff2c9d..60583768 100644
--- a/Sources/SettingsFeature/AppearanceSettingsView.swift
+++ b/Sources/SettingsFeature/AppearanceSettingsView.swift
@@ -1,7 +1,7 @@
 import ComposableArchitecture
 import Styleguide
 import SwiftUI
-import UserSettingsClient
+import UserSettings
 
 struct AppearanceSettingsView: View {
   @Bindable var store: StoreOf<Settings>
diff --git a/Sources/SettingsFeature/Settings.swift b/Sources/SettingsFeature/Settings.swift
index 35f727a0..9cdc8cac 100644
--- a/Sources/SettingsFeature/Settings.swift
+++ b/Sources/SettingsFeature/Settings.swift
@@ -8,7 +8,8 @@ import SharedModels
 import StatsFeature
 import StoreKit
 import UIApplicationClient
-import UserSettingsClient
+import UserSettings
+import ServerConfigPersistenceKey
 
 public struct DeveloperSettings: Equatable {
   public var currentBaseUrl: BaseUrl
@@ -45,21 +46,21 @@ public struct Settings {
   @ObservableState
   public struct State: Equatable {
     @Presents public var alert: AlertState<Action.Alert>?
-    public var buildNumber: Build.Number?
+    @Shared(.build) var build = Build()
     public var developer: DeveloperSettings
     public var fullGameProduct: Result<StoreKitClient.Product, ProductError>?
     public var fullGamePurchasedAt: Date?
     public var isPurchasing: Bool
     public var isRestoring: Bool
+    @SharedReader(.serverConfig) var serverConfig = ServerConfig()
     public var stats: Stats.State
     public var userNotificationSettings: UserNotificationClient.Notification.Settings?
-    public var userSettings: UserSettings
+    @Shared(.userSettings) public var userSettings: UserSettings = UserSettings()
 
     public struct ProductError: Error, Equatable {}
 
     public init(
       alert: AlertState<Action.Alert>? = nil,
-      buildNumber: Build.Number? = nil,
       developer: DeveloperSettings = DeveloperSettings(),
       fullGameProduct: Result<StoreKitClient.Product, ProductError>? = nil,
       fullGamePurchasedAt: Date? = nil,
@@ -68,9 +69,7 @@ public struct Settings {
       stats: Stats.State = .init(),
       userNotificationSettings: UserNotificationClient.Notification.Settings? = nil
     ) {
-      @Dependency(\.userSettings) var userSettings
       self.alert = alert
-      self.buildNumber = buildNumber
       self.developer = developer
       self.fullGameProduct = fullGameProduct
       self.fullGamePurchasedAt = fullGamePurchasedAt
@@ -78,7 +77,6 @@ public struct Settings {
       self.isRestoring = isRestoring
       self.stats = stats
       self.userNotificationSettings = userNotificationSettings
-      self.userSettings = userSettings.get()
     }
 
     public var isFullGamePurchased: Bool {
@@ -111,13 +109,10 @@ public struct Settings {
   @Dependency(\.apiClient) var apiClient
   @Dependency(\.applicationClient) var applicationClient
   @Dependency(\.audioPlayer) var audioPlayer
-  @Dependency(\.build) var build
   @Dependency(\.mainQueue) var mainQueue
   @Dependency(\.remoteNotifications.register) var registerForRemoteNotifications
-  @Dependency(\.serverConfig.config) var serverConfig
   @Dependency(\.storeKit) var storeKit
   @Dependency(\.userNotifications) var userNotifications
-  @Dependency(\.userSettings) var userSettings
 
   public init() {}
 
@@ -287,9 +282,9 @@ public struct Settings {
           }
 
         case .leaveUsAReviewButtonTapped:
-          return .run { _ in
+          return .run { [url = state.serverConfig.appStoreReviewUrl] _ in
             _ = await self.applicationClient
-              .open(self.serverConfig().appStoreReviewUrl, [:])
+              .open(url, [:])
           }
 
         case .onDismiss:
@@ -326,7 +321,7 @@ public struct Settings {
           state.fullGameProduct =
             response.products
             .first {
-              $0.productIdentifier == self.serverConfig().productIdentifiers.fullGame
+              $0.productIdentifier == state.serverConfig.productIdentifiers.fullGame
             }
             .map(Result.success)
             ?? Result.failure(.init())
@@ -337,7 +332,7 @@ public struct Settings {
           return .none
 
         case .reportABugButtonTapped:
-          return .run { _ in
+          return .run { [build = state.build] _ in
             let currentPlayer = self.apiClient.currentPlayer()
             var components = URLComponents()
             components.scheme = "mailto"
@@ -350,7 +345,7 @@ public struct Settings {
 
 
                   ---
-                  Build: \(self.build.number()) (\(self.build.gitSha()))
+                  Build: \(build.number) (\(build.gitSha))
                   \(currentPlayer?.player.id.rawValue.uuidString ?? "")
                   """
               ),
@@ -381,7 +376,6 @@ public struct Settings {
             .appleReceipt?
             .receipt
             .originalPurchaseDate
-          state.buildNumber = self.build.number()
           state.stats.isAnimationReduced = state.userSettings.enableReducedAnimation
           state.userSettings.appIcon = self.applicationClient.alternateIconName()
             .flatMap(AppIcon.init(rawValue:))
@@ -399,7 +393,7 @@ public struct Settings {
           }
 
           return .merge(
-            .run { [shouldFetchProducts = !state.isFullGamePurchased] send in
+            .run { [serverConfig = state.serverConfig, shouldFetchProducts = !state.isFullGamePurchased] send in
               Task {
                 await withTaskCancellation(id: CancelID.paymentObserver, cancelInFlight: true) {
                   for await event in self.storeKit.observer() {
@@ -414,7 +408,7 @@ public struct Settings {
                   .productsResponse(
                     Result {
                       try await self.storeKit.fetchProducts([
-                        self.serverConfig().productIdentifiers.fullGame
+                        serverConfig.productIdentifiers.fullGame
                       ])
                     }
                   ),
@@ -456,14 +450,6 @@ public struct Settings {
       }
     }
     .ifLet(\.$alert, action: \.alert)
-    .onChange(of: \.userSettings) { _, userSettings in
-      Reduce { _, _ in
-        enum CancelID { case saveDebounce }
-
-        return .run { _ in await self.userSettings.set(userSettings) }
-          .debounce(id: CancelID.saveDebounce, for: .seconds(0.5), scheduler: self.mainQueue)
-      }
-    }
 
     Scope(state: \.stats, action: \.stats) {
       Stats()
diff --git a/Sources/SettingsFeature/SettingsView.swift b/Sources/SettingsFeature/SettingsView.swift
index 6f0962ac..dd96b67b 100644
--- a/Sources/SettingsFeature/SettingsView.swift
+++ b/Sources/SettingsFeature/SettingsView.swift
@@ -1,7 +1,7 @@
 import Build
 import ComposableArchitecture
 import ComposableStoreKit
-import ServerConfigClient
+import ServerConfigPersistenceKey
 import StatsFeature
 import Styleguide
 import SwiftUI
@@ -144,9 +144,7 @@ public struct SettingsView: View {
       #endif
 
       VStack(spacing: 6) {
-        if let buildNumber = store.buildNumber {
-          Text("Build \(buildNumber.rawValue)")
-        }
+        Text("Build \(store.build.number.rawValue)")
         Button {
           store.send(.reportABugButtonTapped)
         } label: {
diff --git a/Sources/SettingsFeature/SoundsSettingsView.swift b/Sources/SettingsFeature/SoundsSettingsView.swift
index 350aa560..606b3590 100644
--- a/Sources/SettingsFeature/SoundsSettingsView.swift
+++ b/Sources/SettingsFeature/SoundsSettingsView.swift
@@ -49,22 +49,18 @@ struct SoundsSettingsView: View {
 
 #if DEBUG
   import SwiftUIHelpers
-  import UserSettingsClient
+  import UserSettings
 
   struct SoundsSettingsView_Previews: PreviewProvider {
     static var previews: some View {
-      Preview {
+      @Shared(.userSettings) var userSettings = UserSettings()
+      userSettings = UserSettings(musicVolume: 0.5, soundEffectsVolume: 0.75)
+
+      return Preview {
         NavigationView {
           SoundsSettingsView(
             store: Store(initialState: Settings.State()) {
               Settings()
-            } withDependencies: {
-              $0.userSettings = .mock(
-                initialUserSettings: UserSettings(
-                  musicVolume: 0.5,
-                  soundEffectsVolume: 0.5
-                )
-              )
             }
           )
         }
diff --git a/Sources/SoloFeature/SoloView.swift b/Sources/SoloFeature/SoloView.swift
index dfae4583..d2d09136 100644
--- a/Sources/SoloFeature/SoloView.swift
+++ b/Sources/SoloFeature/SoloView.swift
@@ -1,6 +1,5 @@
 import ClientModels
 import ComposableArchitecture
-import FileClient
 import Overture
 import SharedModels
 import Styleguide
@@ -19,12 +18,8 @@ public struct Solo {
 
   public enum Action {
     case gameButtonTapped(GameMode)
-    case savedGamesLoaded(Result<SavedGamesState, Error>)
-    case task
   }
 
-  @Dependency(\.fileClient) var fileClient
-
   public init() {}
 
   public var body: some ReducerOf<Self> {
@@ -32,18 +27,6 @@ public struct Solo {
       switch action {
       case .gameButtonTapped:
         return .none
-
-      case .savedGamesLoaded(.failure):
-        return .none
-
-      case let .savedGamesLoaded(.success(savedGameState)):
-        state.inProgressGame = savedGameState.unlimited
-        return .none
-
-      case .task:
-        return .run { send in
-          await send(.savedGamesLoaded(Result { try await self.fileClient.loadSavedGames() }))
-        }
       }
     }
   }
@@ -104,7 +87,6 @@ public struct SoloView: View {
     }
     .adaptivePadding(.vertical)
     .screenEdgePadding(.horizontal)
-    .task { await store.send(.task).finish() }
     .navigationStyle(
       backgroundColor: self.colorScheme == .dark ? .isowordsBlack : .solo,
       foregroundColor: self.colorScheme == .dark ? .solo : .isowordsBlack,
diff --git a/Sources/TrailerFeature/Trailer.swift b/Sources/TrailerFeature/Trailer.swift
index f09a2a0c..d75b02d5 100644
--- a/Sources/TrailerFeature/Trailer.swift
+++ b/Sources/TrailerFeature/Trailer.swift
@@ -64,13 +64,11 @@ public struct Trailer {
         $0.build = .noop
         $0.database = .noop
         $0.feedbackGenerator = .noop
-        $0.fileClient = .noop
         $0.gameCenter = .noop
         $0.lowPowerMode = .false
         $0.remoteNotifications = .noop
         $0.serverConfig = .noop
         $0.storeKit = .noop
-        $0.userDefaults = .noop
         $0.userNotifications = .noop
       }
     }
diff --git a/Sources/UpgradeInterstitialFeature/UpgradeInterstitialView.swift b/Sources/UpgradeInterstitialFeature/UpgradeInterstitialView.swift
index 7683c040..41c9f19c 100644
--- a/Sources/UpgradeInterstitialFeature/UpgradeInterstitialView.swift
+++ b/Sources/UpgradeInterstitialFeature/UpgradeInterstitialView.swift
@@ -1,6 +1,6 @@
 import ComposableArchitecture
 import ComposableStoreKit
-import ServerConfigClient
+import ServerConfigPersistenceKey
 import StoreKit
 import Styleguide
 import SwiftUI
@@ -21,6 +21,7 @@ public struct UpgradeInterstitial {
     public var isDismissable: Bool
     public var isPurchasing: Bool
     public var secondsPassedCount: Int
+    @SharedReader(.serverConfig) var serverConfig = ServerConfig()
     public var upgradeInterstitialDuration: Int
 
     public init(
@@ -55,7 +56,6 @@ public struct UpgradeInterstitial {
 
   @Dependency(\.dismiss) var dismiss
   @Dependency(\.mainRunLoop) var mainRunLoop
-  @Dependency(\.serverConfig.config) var serverConfig
   @Dependency(\.storeKit) var storeKit
 
   public init() {}
@@ -93,7 +93,7 @@ public struct UpgradeInterstitial {
 
         guard
           event.isFullGamePurchased(
-            identifier: self.serverConfig().productIdentifiers.fullGame
+            identifier: state.serverConfig.productIdentifiers.fullGame
           )
         else { return .none }
         return .run { send in
@@ -103,9 +103,9 @@ public struct UpgradeInterstitial {
 
       case .task:
         state.upgradeInterstitialDuration =
-          self.serverConfig().upgradeInterstitial.duration
+        state.serverConfig.upgradeInterstitial.duration
 
-        return .run { [isDismissable = state.isDismissable] send in
+        return .run { [serverConfig = state.serverConfig, isDismissable = state.isDismissable] send in
           await withThrowingTaskGroup(of: Void.self) { group in
             group.addTask {
               for await event in self.storeKit.observer() {
@@ -115,11 +115,11 @@ public struct UpgradeInterstitial {
 
             group.addTask {
               let response = try await self.storeKit.fetchProducts([
-                self.serverConfig().productIdentifiers.fullGame
+                serverConfig.productIdentifiers.fullGame
               ])
               guard
                 let product = response.products.first(where: { product in
-                  product.productIdentifier == self.serverConfig().productIdentifiers.fullGame
+                  product.productIdentifier == serverConfig.productIdentifiers.fullGame
                 })
               else { return }
               await send(.fullGameProductResponse(product), animation: .default)
@@ -145,9 +145,9 @@ public struct UpgradeInterstitial {
 
       case .upgradeButtonTapped:
         state.isPurchasing = true
-        return .run { _ in
+        return .run { [serverConfig = state.serverConfig] _ in
           let payment = SKMutablePayment()
-          payment.productIdentifier = self.serverConfig().productIdentifiers.fullGame
+          payment.productIdentifier = serverConfig.productIdentifiers.fullGame
           payment.quantity = 1
           await self.storeKit.addPayment(payment)
         }
@@ -297,9 +297,9 @@ extension StoreKitClient.PaymentTransactionObserverEvent {
 
 public func shouldShowInterstitial(
   gamePlayedCount: Int,
-  gameContext: GameContext,
-  serverConfig: ServerConfig
+  gameContext: GameContext
 ) -> Bool {
+  @SharedReader(.serverConfig) var serverConfig = ServerConfig()
   let triggerCount = serverConfig.triggerCount(gameContext: gameContext)
   let triggerEvery = serverConfig.triggerEvery(gameContext: gameContext)
   return gamePlayedCount >= triggerCount
diff --git a/Sources/UserDefaultsClient/Interface.swift b/Sources/UserDefaultsClient/Interface.swift
deleted file mode 100644
index 5ad37db0..00000000
--- a/Sources/UserDefaultsClient/Interface.swift
+++ /dev/null
@@ -1,49 +0,0 @@
-import Dependencies
-import DependenciesMacros
-import Foundation
-
-extension DependencyValues {
-  public var userDefaults: UserDefaultsClient {
-    get { self[UserDefaultsClient.self] }
-    set { self[UserDefaultsClient.self] = newValue }
-  }
-}
-
-@DependencyClient
-public struct UserDefaultsClient {
-  public var boolForKey: @Sendable (String) -> Bool = { _ in false }
-  public var dataForKey: @Sendable (String) -> Data?
-  public var doubleForKey: @Sendable (String) -> Double = { _ in 0 }
-  public var integerForKey: @Sendable (String) -> Int = { _ in 0 }
-  public var remove: @Sendable (String) async -> Void
-  public var setBool: @Sendable (Bool, String) async -> Void
-  public var setData: @Sendable (Data?, String) async -> Void
-  public var setDouble: @Sendable (Double, String) async -> Void
-  public var setInteger: @Sendable (Int, String) async -> Void
-
-  public var hasShownFirstLaunchOnboarding: Bool {
-    self.boolForKey(hasShownFirstLaunchOnboardingKey)
-  }
-
-  public func setHasShownFirstLaunchOnboarding(_ bool: Bool) async {
-    await self.setBool(bool, hasShownFirstLaunchOnboardingKey)
-  }
-
-  public var installationTime: Double {
-    self.doubleForKey(installationTimeKey)
-  }
-
-  public func setInstallationTime(_ double: Double) async {
-    await self.setDouble(double, installationTimeKey)
-  }
-
-  public func incrementMultiplayerOpensCount() async -> Int {
-    let incremented = self.integerForKey(multiplayerOpensCount) + 1
-    await self.setInteger(incremented, multiplayerOpensCount)
-    return incremented
-  }
-}
-
-let hasShownFirstLaunchOnboardingKey = "hasShownFirstLaunchOnboardingKey"
-let installationTimeKey = "installationTimeKey"
-let multiplayerOpensCount = "multiplayerOpensCount"
diff --git a/Sources/UserDefaultsClient/LiveKey.swift b/Sources/UserDefaultsClient/LiveKey.swift
deleted file mode 100644
index 0ce23759..00000000
--- a/Sources/UserDefaultsClient/LiveKey.swift
+++ /dev/null
@@ -1,19 +0,0 @@
-import Dependencies
-import Foundation
-
-extension UserDefaultsClient: DependencyKey {
-  public static let liveValue: Self = {
-    let defaults = { UserDefaults(suiteName: "group.isowords")! }
-    return Self(
-      boolForKey: { defaults().bool(forKey: $0) },
-      dataForKey: { defaults().data(forKey: $0) },
-      doubleForKey: { defaults().double(forKey: $0) },
-      integerForKey: { defaults().integer(forKey: $0) },
-      remove: { defaults().removeObject(forKey: $0) },
-      setBool: { defaults().set($0, forKey: $1) },
-      setData: { defaults().set($0, forKey: $1) },
-      setDouble: { defaults().set($0, forKey: $1) },
-      setInteger: { defaults().set($0, forKey: $1) }
-    )
-  }()
-}
diff --git a/Sources/UserDefaultsClient/TestKey.swift b/Sources/UserDefaultsClient/TestKey.swift
deleted file mode 100644
index 64b6a005..00000000
--- a/Sources/UserDefaultsClient/TestKey.swift
+++ /dev/null
@@ -1,37 +0,0 @@
-import Dependencies
-import Foundation
-
-extension UserDefaultsClient: TestDependencyKey {
-  public static let previewValue = Self.noop
-  public static let testValue = Self()
-}
-
-extension UserDefaultsClient {
-  public static let noop = Self(
-    boolForKey: { _ in false },
-    dataForKey: { _ in nil },
-    doubleForKey: { _ in 0 },
-    integerForKey: { _ in 0 },
-    remove: { _ in },
-    setBool: { _, _ in },
-    setData: { _, _ in },
-    setDouble: { _, _ in },
-    setInteger: { _, _ in }
-  )
-
-  public mutating func override(bool: Bool, forKey key: String) {
-    self.boolForKey = { [self] in $0 == key ? bool : self.boolForKey($0) }
-  }
-
-  public mutating func override(data: Data, forKey key: String) {
-    self.dataForKey = { [self] in $0 == key ? data : self.dataForKey($0) }
-  }
-
-  public mutating func override(double: Double, forKey key: String) {
-    self.doubleForKey = { [self] in $0 == key ? double : self.doubleForKey($0) }
-  }
-
-  public mutating func override(integer: Int, forKey key: String) {
-    self.integerForKey = { [self] in $0 == key ? integer : self.integerForKey($0) }
-  }
-}
diff --git a/Sources/UserSettingsClient/AppIcon.swift b/Sources/UserSettings/AppIcon.swift
similarity index 100%
rename from Sources/UserSettingsClient/AppIcon.swift
rename to Sources/UserSettings/AppIcon.swift
diff --git a/Sources/UserSettingsClient/UserSettings.swift b/Sources/UserSettings/UserSettings.swift
similarity index 88%
rename from Sources/UserSettingsClient/UserSettings.swift
rename to Sources/UserSettings/UserSettings.swift
index a8f8401e..f6357005 100644
--- a/Sources/UserSettingsClient/UserSettings.swift
+++ b/Sources/UserSettings/UserSettings.swift
@@ -1,4 +1,4 @@
-import Styleguide
+import ComposableArchitecture
 import UIKit
 
 public struct UserSettings: Codable, Equatable {
@@ -73,8 +73,14 @@ public struct UserSettings: Codable, Equatable {
   }
 }
 
-extension URL {
-  public static let userSettings = Self.documentsDirectory
-    .appendingPathComponent("user-settings")
-    .appendingPathExtension("json")
+extension PersistenceReaderKey where Self == FileStorageKey<UserSettings> {
+  public static var userSettings: Self {
+    fileStorage(
+      FileManager.default
+        .urls(for: .documentDirectory, in: .userDomainMask)
+        .first!
+        .appendingPathComponent("user-settings")
+        .appendingPathExtension("json")
+    )
+  }
 }
diff --git a/Sources/UserSettingsClient/UserSettingsClient.swift b/Sources/UserSettingsClient/UserSettingsClient.swift
deleted file mode 100644
index 096b249a..00000000
--- a/Sources/UserSettingsClient/UserSettingsClient.swift
+++ /dev/null
@@ -1,81 +0,0 @@
-import Combine
-import Dependencies
-import UIKit
-
-@dynamicMemberLookup
-public struct UserSettingsClient {
-  public var get: @Sendable () -> UserSettings
-  public var set: @Sendable (UserSettings) async -> Void
-  public var stream: @Sendable () -> AsyncStream<UserSettings>
-
-  public subscript<Value>(dynamicMember keyPath: KeyPath<UserSettings, Value>) -> Value {
-    self.get()[keyPath: keyPath]
-  }
-
-  @_disfavoredOverload
-  public subscript<Value>(
-    dynamicMember keyPath: KeyPath<UserSettings, Value>
-  ) -> AsyncStream<Value> {
-    // TODO: This should probably remove duplicates.
-    self.stream().map { $0[keyPath: keyPath] }.eraseToStream()
-  }
-
-  public func modify(_ operation: (inout UserSettings) -> Void) async {
-    var userSettings = self.get()
-    operation(&userSettings)
-    await self.set(userSettings)
-  }
-}
-
-extension UserSettingsClient: DependencyKey {
-  public static var liveValue: UserSettingsClient {
-    let initialUserSettingsData = (try? Data(contentsOf: .userSettings)) ?? Data()
-    let initialUserSettings =
-      (try? JSONDecoder().decode(UserSettings.self, from: initialUserSettingsData))
-      ?? UserSettings()
-
-    let userSettings = LockIsolated(initialUserSettings)
-    let subject = PassthroughSubject<UserSettings, Never>()
-    return Self(
-      get: {
-        userSettings.value
-      },
-      set: { updatedUserSettings in
-        userSettings.withValue {
-          $0 = updatedUserSettings
-          subject.send(updatedUserSettings)
-          try? JSONEncoder().encode(updatedUserSettings).write(to: .userSettings)
-        }
-      },
-      stream: {
-        subject.values.eraseToStream()
-      }
-    )
-  }
-
-  public static let testValue = Self.mock()
-
-  public static func mock(initialUserSettings: UserSettings = UserSettings()) -> Self {
-    let userSettings = LockIsolated<UserSettings>(initialUserSettings)
-    let subject = PassthroughSubject<UserSettings, Never>()
-    return Self(
-      get: { userSettings.value },
-      set: { updatedUserSettings in
-        userSettings.withValue {
-          $0 = updatedUserSettings
-          subject.send(updatedUserSettings)
-        }
-      },
-      stream: {
-        subject.values.eraseToStream()
-      }
-    )
-  }
-}
-
-extension DependencyValues {
-  public var userSettings: UserSettingsClient {
-    get { self[UserSettingsClient.self] }
-    set { self[UserSettingsClient.self] = newValue }
-  }
-}
diff --git a/Tests/AppFeatureTests/Mocks/AppEnvironment.swift b/Tests/AppFeatureTests/Mocks/AppEnvironment.swift
index 282199ce..bc128d06 100644
--- a/Tests/AppFeatureTests/Mocks/AppEnvironment.swift
+++ b/Tests/AppFeatureTests/Mocks/AppEnvironment.swift
@@ -1,11 +1,9 @@
 import AppFeature
 import ClientModels
 import ComposableArchitecture
-import FileClient
 import Foundation
 import Overture
 import SettingsFeature
-import UserDefaultsClient
 
 extension DependencyValues {
   mutating func didFinishLaunching() {
@@ -16,7 +14,6 @@ extension DependencyValues {
     self.applicationClient.setUserInterfaceStyle = { _ in }
     self.database.migrate = {}
     self.dictionary.load = { _ in false }
-    self.fileClient.load = { @Sendable _ in try await Task.never() }
     self.gameCenter.localPlayer.authenticate = {}
     self.gameCenter.localPlayer.listener = { .finished }
     self.mainQueue = .immediate
diff --git a/Tests/AppFeatureTests/PersistenceTests.swift b/Tests/AppFeatureTests/PersistenceTests.swift
index d798225c..055ce2a0 100644
--- a/Tests/AppFeatureTests/PersistenceTests.swift
+++ b/Tests/AppFeatureTests/PersistenceTests.swift
@@ -15,10 +15,8 @@ import TestHelpers
 import XCTest
 
 @testable import AppFeature
-@testable import FileClient
 @testable import GameCore
 @testable import SoloFeature
-@testable import UserDefaultsClient
 
 class PersistenceTests: XCTestCase {
   @MainActor
@@ -37,7 +35,6 @@ class PersistenceTests: XCTestCase {
       $0.dictionary.contains = { word, _ in word == "CAB" }
       $0.dictionary.randomCubes = { _ in .mock }
       $0.feedbackGenerator = .noop
-      $0.fileClient.save = { @Sendable _, data in await saves.withValue { $0.append(data) } }
       $0.mainRunLoop = .immediate
       $0.mainQueue = .immediate
     }
@@ -151,7 +148,7 @@ class PersistenceTests: XCTestCase {
     let store = TestStore(
       initialState: AppReducer.State(
         destination: .game(update(.mock) { $0.gameMode = .unlimited }),
-        home: Home.State(savedGames: SavedGamesState(unlimited: .mock))
+        home: Home.State()
       )
     ) {
       AppReducer()
@@ -159,7 +156,6 @@ class PersistenceTests: XCTestCase {
       $0.audioPlayer.stop = { _ in }
       $0.database.saveGame = { _ in await didArchiveGame.setValue(true) }
       $0.gameCenter.localPlayer.localPlayer = { .notAuthenticated }
-      $0.fileClient.save = { @Sendable _, data in await saves.withValue { $0.append(data) } }
       $0.mainQueue = .immediate
     }
 
@@ -269,13 +265,9 @@ class PersistenceTests: XCTestCase {
       $0.audioPlayer.setGlobalVolumeForMusic = { _ in }
       $0.audioPlayer.setGlobalVolumeForSoundEffects = { _ in }
       $0.applicationClient.setUserInterfaceStyle = { _ in }
-      $0.fileClient.override(load: savedGamesFileName, savedGames)
     }
 
     let task = await store.send(.appDelegate(.didFinishLaunching))
-    await store.receive(\.savedGamesLoaded.success) {
-      $0.home.savedGames = savedGames
-    }
     await store.send(.home(.soloButtonTapped)) {
       $0.home.destination = .solo(.init(inProgressGame: .mock))
     }
@@ -300,12 +292,7 @@ class PersistenceTests: XCTestCase {
             )
           }
         ),
-        home: Home.State(
-          savedGames: SavedGamesState(
-            dailyChallengeUnlimited: .mock,
-            unlimited: .mock
-          )
-        )
+        home: Home.State()
       )
     ) {
       AppReducer()
diff --git a/Tests/AppFeatureTests/RemoteNotificationsTests.swift b/Tests/AppFeatureTests/RemoteNotificationsTests.swift
index 28e89267..8bce0c39 100644
--- a/Tests/AppFeatureTests/RemoteNotificationsTests.swift
+++ b/Tests/AppFeatureTests/RemoteNotificationsTests.swift
@@ -107,7 +107,6 @@ class RemoteNotificationsTests: XCTestCase {
       AppReducer()
     } withDependencies: {
       $0.didFinishLaunching()
-      $0.fileClient.save = { @Sendable _, _ in }
     }
 
     let delegate = AsyncStream<UserNotificationClient.DelegateEvent>.makeStream()
diff --git a/Tests/AppFeatureTests/TurnBasedTests.swift b/Tests/AppFeatureTests/TurnBasedTests.swift
index a70fe3dc..cf9cde60 100644
--- a/Tests/AppFeatureTests/TurnBasedTests.swift
+++ b/Tests/AppFeatureTests/TurnBasedTests.swift
@@ -86,8 +86,6 @@ class TurnBasedTests: XCTestCase {
         $0.dictionary.contains = { word, _ in word == "CAB" }
         $0.dictionary.randomCubes = { _ in .mock }
         $0.feedbackGenerator = .noop
-        $0.fileClient.save = { @Sendable _, _ in }
-        $0.fileClient.load = { @Sendable _ in try await Task.never() }
         $0.gameCenter.localPlayer.authenticate = {}
         $0.gameCenter.localPlayer.listener = { listener.stream }
         $0.gameCenter.localPlayer.localPlayer = { .mock }
@@ -321,7 +319,6 @@ class TurnBasedTests: XCTestCase {
           }
         }
         $0.deviceId.id = { .deviceId }
-        $0.fileClient.save = { @Sendable _, _ in }
         $0.gameCenter.localPlayer.authenticate = {}
         $0.gameCenter.localPlayer.listener = { listener.stream }
         $0.gameCenter.localPlayer.localPlayer = { .mock }
@@ -424,7 +421,6 @@ class TurnBasedTests: XCTestCase {
         }
         $0.build.number = { 42 }
         $0.deviceId.id = { .deviceId }
-        $0.fileClient.save = { @Sendable _, _ in }
         $0.gameCenter.localPlayer.authenticate = {}
         $0.gameCenter.localPlayer.listener = { listener.stream }
         $0.gameCenter.localPlayer.localPlayer = { .mock }
@@ -700,7 +696,6 @@ class TurnBasedTests: XCTestCase {
     } withDependencies: {
       $0.apiClient.currentPlayer = { nil }
       $0.dictionary.randomCubes = { _ in .mock }
-      $0.fileClient.load = { @Sendable _ in try await Task.never() }
       $0.gameCenter.localPlayer.localPlayer = {
         update(.authenticated) { $0.player = localParticipant.player! }
       }
diff --git a/Tests/AppStoreSnapshotTests/01-Solo.swift b/Tests/AppStoreSnapshotTests/01-Solo.swift
index 68327788..49b5d8d2 100644
--- a/Tests/AppStoreSnapshotTests/01-Solo.swift
+++ b/Tests/AppStoreSnapshotTests/01-Solo.swift
@@ -68,7 +68,6 @@ var gameplayAppStoreView: AnyView {
     isDemo: false,
     isGameLoaded: true,
     isPanning: false,
-    isOnLowPowerMode: false,
     isTrayVisible: false,
     language: .en,
     moves: moves,
diff --git a/Tests/AppStoreSnapshotTests/02-TurnBased.swift b/Tests/AppStoreSnapshotTests/02-TurnBased.swift
index 14dd6a08..ce3d45d2 100644
--- a/Tests/AppStoreSnapshotTests/02-TurnBased.swift
+++ b/Tests/AppStoreSnapshotTests/02-TurnBased.swift
@@ -35,7 +35,6 @@ var turnBasedAppStoreView: AnyView {
     isDemo: false,
     isGameLoaded: true,
     isPanning: false,
-    isOnLowPowerMode: false,
     isTrayVisible: false,
     language: .en,
     moves: moves,
diff --git a/Tests/AppStoreSnapshotTests/05-Home.swift b/Tests/AppStoreSnapshotTests/05-Home.swift
index 1aba6690..9be58b13 100644
--- a/Tests/AppStoreSnapshotTests/05-Home.swift
+++ b/Tests/AppStoreSnapshotTests/05-Home.swift
@@ -45,18 +45,6 @@ var homeAppStoreView: AnyView {
           ),
         ],
         hasPastTurnBasedGames: true,
-        savedGames: SavedGamesState(
-          dailyChallengeUnlimited: InProgressGame(
-            cubes: .mock,
-            gameContext: .dailyChallenge(.init(rawValue: .dailyChallengeId)),
-            gameMode: .unlimited,
-            gameStartTime: runLoop.now.date,
-            language: .en,
-            moves: Moves(),
-            secondsPlayed: 0
-          ),
-          unlimited: nil
-        ),
         turnBasedMatches: [
           ActiveTurnBasedMatch(
             id: "deadbeef",
diff --git a/Tests/ChangelogFeatureTests/ChangelogFeatureTests.swift b/Tests/ChangelogFeatureTests/ChangelogFeatureTests.swift
index 7a73a314..3d1ee3f2 100644
--- a/Tests/ChangelogFeatureTests/ChangelogFeatureTests.swift
+++ b/Tests/ChangelogFeatureTests/ChangelogFeatureTests.swift
@@ -4,7 +4,6 @@ import ServerConfig
 import XCTest
 
 @testable import ChangelogFeature
-@testable import UserDefaultsClient
 
 class ChangelogFeatureTests: XCTestCase {
   @MainActor
diff --git a/Tests/DailyChallengeFeatureTests/DailyChallengeFeatureTests.swift b/Tests/DailyChallengeFeatureTests/DailyChallengeFeatureTests.swift
index b76efd52..cde5349e 100644
--- a/Tests/DailyChallengeFeatureTests/DailyChallengeFeatureTests.swift
+++ b/Tests/DailyChallengeFeatureTests/DailyChallengeFeatureTests.swift
@@ -1,216 +1,203 @@
-import ApiClient
-import ClientModels
-import ComposableArchitecture
-import NotificationsAuthAlert
-import XCTest
-
-@testable import DailyChallengeFeature
-@testable import SharedModels
-
-class DailyChallengeFeatureTests: XCTestCase {
-  let mainQueue = DispatchQueue.test
-  let mainRunLoop = RunLoop.test
-
-  @MainActor
-  func testOnAppear() async {
-    let store = TestStore(initialState: DailyChallengeReducer.State()) {
-      DailyChallengeReducer()
-    } withDependencies: {
-      $0.apiClient.override(
-        route: .dailyChallenge(.today(language: .en)),
-        withResponse: { try await OK([FetchTodaysDailyChallengeResponse.played]) }
-      )
-      $0.mainRunLoop = .immediate
-      $0.userNotifications.getNotificationSettings = {
-        .init(authorizationStatus: .authorized)
-      }
-    }
-
-    await store.send(.task)
-
-    await store.receive(\.userNotificationSettingsResponse) {
-      $0.userNotificationSettings = .init(authorizationStatus: .authorized)
-    }
-    await store.receive(\.fetchTodaysDailyChallengeResponse.success) {
-      $0.dailyChallenges = [.played]
-    }
-  }
-
-  @MainActor
-  func testTapGameThatWasPlayed() async {
-    var dailyChallengeResponse = FetchTodaysDailyChallengeResponse.played
-    dailyChallengeResponse.dailyChallenge.endsAt = Date().addingTimeInterval(60 * 60 * 2 + 1)
-
-    let store = TestStore(
-      initialState: DailyChallengeReducer.State(dailyChallenges: [dailyChallengeResponse])
-    ) {
-      DailyChallengeReducer()
-    }
-
-    await store.send(.gameButtonTapped(.unlimited)) {
-      $0.destination = .alert(
-        .alreadyPlayed(nextStartsAt: Date().addingTimeInterval(60 * 60 * 2 + 1))
-      )
-    }
-  }
-
-  @MainActor
-  func testTapGameThatWasNotStarted() async {
-    var inProgressGame = InProgressGame.mock
-    inProgressGame.gameStartTime = self.mainRunLoop.now.date
-    inProgressGame.gameContext = .dailyChallenge(.init(rawValue: .dailyChallengeId))
-
-    let store = TestStore(
-      initialState: DailyChallengeReducer.State(dailyChallenges: [.notStarted])
-    ) {
-      DailyChallengeReducer()
-    } withDependencies: {
-      $0.mainRunLoop = self.mainRunLoop.eraseToAnyScheduler()
-      $0.apiClient.override(
-        route: .dailyChallenge(.start(gameMode: .unlimited, language: .en)),
-        withResponse: {
-          try await OK(
-            StartDailyChallengeResponse(
-              dailyChallenge: .init(
-                createdAt: .mock,
-                endsAt: .mock,
-                gameMode: .unlimited,
-                gameNumber: 42,
-                id: .init(rawValue: .dailyChallengeId),
-                language: .en,
-                puzzle: .mock
-              ),
-              dailyChallengePlayId: .init(rawValue: .deadbeef)
-            )
-          )
-        }
-      )
-      $0.fileClient.load = { @Sendable _ in
-        struct FileNotFound: Error {}
-        throw FileNotFound()
-      }
-    }
-
-    await store.send(.gameButtonTapped(.unlimited)) {
-      $0.gameModeIsLoading = .unlimited
-    }
-
-    await self.mainRunLoop.advance()
-    await store.receive(\.startDailyChallengeResponse.success) {
-      $0.gameModeIsLoading = nil
-    }
-    await store.receive(\.delegate.startGame)
-  }
-
-  @MainActor
-  func testTapGameThatWasStarted_NotPlayed_HasLocalGame() async {
-    var inProgressGame = InProgressGame.mock
-    inProgressGame.gameStartTime = .mock
-    inProgressGame.gameContext = .dailyChallenge(.init(rawValue: .dailyChallengeId))
-    inProgressGame.moves = [
-      .highScoringMove
-    ]
-
-    let store = TestStore(
-      initialState: DailyChallengeReducer.State(
-        dailyChallenges: [.started],
-        inProgressDailyChallengeUnlimited: inProgressGame
-      )
-    ) {
-      DailyChallengeReducer()
-    } withDependencies: {
-      $0.fileClient.load = { @Sendable [inProgressGame] _ in
-        try JSONEncoder().encode(SavedGamesState(dailyChallengeUnlimited: inProgressGame))
-      }
-      $0.mainRunLoop = .immediate
-    }
-
-    await store.send(.gameButtonTapped(.unlimited)) {
-      $0.gameModeIsLoading = .unlimited
-    }
-
-    await store.receive(\.startDailyChallengeResponse.success) {
-      $0.gameModeIsLoading = nil
-    }
-    await store.receive(\.delegate.startGame)
-  }
-
-  @MainActor
-  func testNotifications_OpenThenClose() async {
-    let store = TestStore(
-      initialState: DailyChallengeReducer.State()
-    ) {
-      DailyChallengeReducer()
-    }
-
-    await store.send(.notificationButtonTapped) {
-      $0.destination = .notificationsAuthAlert(NotificationsAuthAlert.State())
-    }
-    await store.send(.destination(.dismiss)) {
-      $0.destination = nil
-    }
-  }
-
-  @MainActor
-  func testNotifications_GrantAccess() async {
-    let didRegisterForRemoteNotifications = ActorIsolated(false)
-
-    let store = TestStore(initialState: DailyChallengeReducer.State()) {
-      DailyChallengeReducer()
-    } withDependencies: {
-      $0.userNotifications.getNotificationSettings = {
-        .init(authorizationStatus: .authorized)
-      }
-      $0.userNotifications.requestAuthorization = { _ in true }
-      $0.remoteNotifications.register = {
-        await didRegisterForRemoteNotifications.setValue(true)
-      }
-      $0.mainRunLoop = .immediate
-    }
-
-    await store.send(.notificationButtonTapped) {
-      $0.destination = .notificationsAuthAlert(NotificationsAuthAlert.State())
-    }
-    await store.send(
-      .destination(.presented(.notificationsAuthAlert(.turnOnNotificationsButtonTapped)))
-    )
-    await store.receive(
-      \.destination.notificationsAuthAlert.delegate.didChooseNotificationSettings
-    ) {
-      $0.userNotificationSettings = .init(authorizationStatus: .authorized)
-    }
-    await store.receive(\.destination.dismiss) {
-      $0.destination = nil
-    }
-
-    await didRegisterForRemoteNotifications.withValue { XCTAssertNoDifference($0, true) }
-  }
-
-  @MainActor
-  func testNotifications_DenyAccess() async {
-    let store = TestStore(initialState: DailyChallengeReducer.State()) {
-      DailyChallengeReducer()
-    } withDependencies: {
-      $0.userNotifications.getNotificationSettings = {
-        .init(authorizationStatus: .denied)
-      }
-      $0.userNotifications.requestAuthorization = { _ in false }
-      $0.mainRunLoop = .immediate
-    }
-
-    await store.send(.notificationButtonTapped) {
-      $0.destination = .notificationsAuthAlert(NotificationsAuthAlert.State())
-    }
-    await store.send(
-      .destination(.presented(.notificationsAuthAlert(.turnOnNotificationsButtonTapped)))
-    )
-    await store.receive(
-      \.destination.notificationsAuthAlert.delegate.didChooseNotificationSettings
-    ) {
-      $0.userNotificationSettings = .init(authorizationStatus: .denied)
-    }
-    await store.receive(\.destination.dismiss) {
-      $0.destination = nil
-    }
-  }
-}
+//import ApiClient
+//import ClientModels
+//import ComposableArchitecture
+//import NotificationsAuthAlert
+//import XCTest
+//
+//@testable import DailyChallengeFeature
+//@testable import SharedModels
+//
+//@MainActor
+//class DailyChallengeFeatureTests: XCTestCase {
+//  let mainQueue = DispatchQueue.test
+//  let mainRunLoop = RunLoop.test
+//
+//  func testOnAppear() async {
+//    let store = TestStore(initialState: DailyChallengeReducer.State()) {
+//      DailyChallengeReducer()
+//    } withDependencies: {
+//      $0.apiClient.override(
+//        route: .dailyChallenge(.today(language: .en)),
+//        withResponse: { try await OK([FetchTodaysDailyChallengeResponse.played]) }
+//      )
+//      $0.mainRunLoop = .immediate
+//      $0.userNotifications.getNotificationSettings = {
+//        .init(authorizationStatus: .authorized)
+//      }
+//    }
+//
+//    await store.send(.task)
+//
+//    await store.receive(\.userNotificationSettingsResponse) {
+//      $0.userNotificationSettings = .init(authorizationStatus: .authorized)
+//    }
+//    await store.receive(\.fetchTodaysDailyChallengeResponse.success) {
+//      $0.dailyChallenges = [.played]
+//    }
+//  }
+//
+//  func testTapGameThatWasPlayed() async {
+//    var dailyChallengeResponse = FetchTodaysDailyChallengeResponse.played
+//    dailyChallengeResponse.dailyChallenge.endsAt = Date().addingTimeInterval(60 * 60 * 2 + 1)
+//
+//    let store = TestStore(
+//      initialState: DailyChallengeReducer.State(dailyChallenges: [dailyChallengeResponse])
+//    ) {
+//      DailyChallengeReducer()
+//    }
+//
+//    await store.send(.gameButtonTapped(.unlimited)) {
+//      $0.destination = .alert(
+//        .alreadyPlayed(nextStartsAt: Date().addingTimeInterval(60 * 60 * 2 + 1))
+//      )
+//    }
+//  }
+//
+//  func testTapGameThatWasNotStarted() async {
+//    var inProgressGame = InProgressGame.mock
+//    inProgressGame.gameStartTime = self.mainRunLoop.now.date
+//    inProgressGame.gameContext = .dailyChallenge(.init(rawValue: .dailyChallengeId))
+//
+//    let store = TestStore(
+//      initialState: DailyChallengeReducer.State(dailyChallenges: [.notStarted])
+//    ) {
+//      DailyChallengeReducer()
+//    } withDependencies: {
+//      $0.mainRunLoop = self.mainRunLoop.eraseToAnyScheduler()
+//      $0.apiClient.override(
+//        route: .dailyChallenge(.start(gameMode: .unlimited, language: .en)),
+//        withResponse: {
+//          try await OK(
+//            StartDailyChallengeResponse(
+//              dailyChallenge: .init(
+//                createdAt: .mock,
+//                endsAt: .mock,
+//                gameMode: .unlimited,
+//                gameNumber: 42,
+//                id: .init(rawValue: .dailyChallengeId),
+//                language: .en,
+//                puzzle: .mock
+//              ),
+//              dailyChallengePlayId: .init(rawValue: .deadbeef)
+//            )
+//          )
+//        }
+//      )
+//    }
+//
+//    await store.send(.gameButtonTapped(.unlimited)) {
+//      $0.gameModeIsLoading = .unlimited
+//    }
+//
+//    await self.mainRunLoop.advance()
+//    await store.receive(\.startDailyChallengeResponse.success) {
+//      $0.gameModeIsLoading = nil
+//    }
+//    await store.receive(\.delegate.startGame)
+//  }
+//
+//  func testTapGameThatWasStarted_NotPlayed_HasLocalGame() async {
+//    var inProgressGame = InProgressGame.mock
+//    inProgressGame.gameStartTime = .mock
+//    inProgressGame.gameContext = .dailyChallenge(.init(rawValue: .dailyChallengeId))
+//    inProgressGame.moves = [
+//      .highScoringMove
+//    ]
+//
+//    let store = TestStore(
+//      initialState: DailyChallengeReducer.State(
+//        dailyChallenges: [.started],
+//        inProgressDailyChallengeUnlimited: inProgressGame
+//      )
+//    ) {
+//      DailyChallengeReducer()
+//    } withDependencies: {
+//      $0.mainRunLoop = .immediate
+//    }
+//
+//    await store.send(.gameButtonTapped(.unlimited)) {
+//      $0.gameModeIsLoading = .unlimited
+//    }
+//
+//    await store.receive(\.startDailyChallengeResponse.success) {
+//      $0.gameModeIsLoading = nil
+//    }
+//    await store.receive(\.delegate.startGame)
+//  }
+//
+//  func testNotifications_OpenThenClose() async {
+//    let store = TestStore(
+//      initialState: DailyChallengeReducer.State()
+//    ) {
+//      DailyChallengeReducer()
+//    }
+//
+//    await store.send(.notificationButtonTapped) {
+//      $0.destination = .notificationsAuthAlert(NotificationsAuthAlert.State())
+//    }
+//    await store.send(.destination(.dismiss)) {
+//      $0.destination = nil
+//    }
+//  }
+//
+//  func testNotifications_GrantAccess() async {
+//    let didRegisterForRemoteNotifications = ActorIsolated(false)
+//
+//    let store = TestStore(initialState: DailyChallengeReducer.State()) {
+//      DailyChallengeReducer()
+//    } withDependencies: {
+//      $0.userNotifications.getNotificationSettings = {
+//        .init(authorizationStatus: .authorized)
+//      }
+//      $0.userNotifications.requestAuthorization = { _ in true }
+//      $0.remoteNotifications.register = {
+//        await didRegisterForRemoteNotifications.setValue(true)
+//      }
+//      $0.mainRunLoop = .immediate
+//    }
+//
+//    await store.send(.notificationButtonTapped) {
+//      $0.destination = .notificationsAuthAlert(NotificationsAuthAlert.State())
+//    }
+//    await store.send(
+//      .destination(.presented(.notificationsAuthAlert(.turnOnNotificationsButtonTapped)))
+//    )
+//    await store.receive(
+//      \.destination.notificationsAuthAlert.delegate.didChooseNotificationSettings
+//    ) {
+//      $0.userNotificationSettings = .init(authorizationStatus: .authorized)
+//    }
+//    await store.receive(\.destination.dismiss) {
+//      $0.destination = nil
+//    }
+//
+//    await didRegisterForRemoteNotifications.withValue { XCTAssertNoDifference($0, true) }
+//  }
+//
+//  func testNotifications_DenyAccess() async {
+//    let store = TestStore(initialState: DailyChallengeReducer.State()) {
+//      DailyChallengeReducer()
+//    } withDependencies: {
+//      $0.userNotifications.getNotificationSettings = {
+//        .init(authorizationStatus: .denied)
+//      }
+//      $0.userNotifications.requestAuthorization = { _ in false }
+//      $0.mainRunLoop = .immediate
+//    }
+//
+//    await store.send(.notificationButtonTapped) {
+//      $0.destination = .notificationsAuthAlert(NotificationsAuthAlert.State())
+//    }
+//    await store.send(
+//      .destination(.presented(.notificationsAuthAlert(.turnOnNotificationsButtonTapped)))
+//    )
+//    await store.receive(
+//      \.destination.notificationsAuthAlert.delegate.didChooseNotificationSettings
+//    ) {
+//      $0.userNotificationSettings = .init(authorizationStatus: .denied)
+//    }
+//    await store.receive(\.destination.dismiss) {
+//      $0.destination = nil
+//    }
+//  }
+//}
diff --git a/Tests/DailyChallengeFeatureTests/DailyChallengeViewTests.swift b/Tests/DailyChallengeFeatureTests/DailyChallengeViewTests.swift
index 17dc1906..650a774c 100644
--- a/Tests/DailyChallengeFeatureTests/DailyChallengeViewTests.swift
+++ b/Tests/DailyChallengeFeatureTests/DailyChallengeViewTests.swift
@@ -1,74 +1,74 @@
-import ComposableArchitecture
-import DailyChallengeFeature
-import SharedModels
-import SnapshotTesting
-import Styleguide
-import XCTest
-
-class DailyChallengeViewTests: XCTestCase {
-  override class func setUp() {
-    super.setUp()
-    Styleguide.registerFonts()
-    SnapshotTesting.diffTool = "ksdiff"
-  }
-
-  override func setUpWithError() throws {
-    try super.setUpWithError()
-    try XCTSkipIf(!Styleguide.registerFonts())
-//    isRecording = true
-  }
-
-  func testDefault() {
-    assertSnapshot(
-      matching: DailyChallengeView(
-        store: .init(initialState: .init()) {
-        }
-      )
-      .environment(\.date) { .mock },
-      as: .image(perceptualPrecision: 0.98, layout: .device(config: .iPhoneXsMax))
-    )
-  }
-
-  func testTimedGamePlayed_UnlimitedGameResumable() {
-    assertSnapshot(
-      matching: DailyChallengeView(
-        store: Store(
-          initialState: DailyChallengeReducer.State(
-            dailyChallenges: [
-              .init(
-                dailyChallenge: .init(
-                  endsAt: .mock,
-                  gameMode: .timed,
-                  id: .init(rawValue: .dailyChallengeId),
-                  language: .en
-                ),
-                yourResult: .init(outOf: 3_000, rank: 20, score: 2_000, started: true)
-              ),
-              .init(
-                dailyChallenge: .init(
-                  endsAt: .mock,
-                  gameMode: .unlimited,
-                  id: .init(rawValue: .dailyChallengeId),
-                  language: .en
-                ),
-                yourResult: .init(outOf: 5_000, rank: nil, score: nil)
-              ),
-            ],
-            inProgressDailyChallengeUnlimited: .init(
-              cubes: .mock,
-              gameContext: .dailyChallenge(.init(rawValue: .dailyChallengeId)),
-              gameMode: .unlimited,
-              gameStartTime: .mock,
-              moves: [.mock],
-              secondsPlayed: 0
-            ),
-            userNotificationSettings: .init(authorizationStatus: .notDetermined)
-          )
-        ) {
-        }
-      )
-      .environment(\.date) { .mock },
-      as: .image(perceptualPrecision: 0.98, layout: .device(config: .iPhoneXsMax))
-    )
-  }
-}
+//import ComposableArchitecture
+//import DailyChallengeFeature
+//import SharedModels
+//import SnapshotTesting
+//import Styleguide
+//import XCTest
+//
+//class DailyChallengeViewTests: XCTestCase {
+//  override class func setUp() {
+//    super.setUp()
+//    Styleguide.registerFonts()
+//    SnapshotTesting.diffTool = "ksdiff"
+//  }
+//
+//  override func setUpWithError() throws {
+//    try super.setUpWithError()
+//    try XCTSkipIf(!Styleguide.registerFonts())
+////    isRecording = true
+//  }
+//
+//  func testDefault() {
+//    assertSnapshot(
+//      matching: DailyChallengeView(
+//        store: .init(initialState: .init()) {
+//        }
+//      )
+//      .environment(\.date) { .mock },
+//      as: .image(perceptualPrecision: 0.98, layout: .device(config: .iPhoneXsMax))
+//    )
+//  }
+//
+//  func testTimedGamePlayed_UnlimitedGameResumable() {
+//    assertSnapshot(
+//      matching: DailyChallengeView(
+//        store: Store(
+//          initialState: DailyChallengeReducer.State(
+//            dailyChallenges: [
+//              .init(
+//                dailyChallenge: .init(
+//                  endsAt: .mock,
+//                  gameMode: .timed,
+//                  id: .init(rawValue: .dailyChallengeId),
+//                  language: .en
+//                ),
+//                yourResult: .init(outOf: 3_000, rank: 20, score: 2_000, started: true)
+//              ),
+//              .init(
+//                dailyChallenge: .init(
+//                  endsAt: .mock,
+//                  gameMode: .unlimited,
+//                  id: .init(rawValue: .dailyChallengeId),
+//                  language: .en
+//                ),
+//                yourResult: .init(outOf: 5_000, rank: nil, score: nil)
+//              ),
+//            ],
+//            inProgressDailyChallengeUnlimited: .init(
+//              cubes: .mock,
+//              gameContext: .dailyChallenge(.init(rawValue: .dailyChallengeId)),
+//              gameMode: .unlimited,
+//              gameStartTime: .mock,
+//              moves: [.mock],
+//              secondsPlayed: 0
+//            ),
+//            userNotificationSettings: .init(authorizationStatus: .notDetermined)
+//          )
+//        ) {
+//        }
+//      )
+//      .environment(\.date) { .mock },
+//      as: .image(perceptualPrecision: 0.98, layout: .device(config: .iPhoneXsMax))
+//    )
+//  }
+//}
diff --git a/Tests/GameFeatureTests/DailyChallengeTests.swift b/Tests/GameFeatureTests/DailyChallengeTests.swift
index c1dc8ea8..ba236ca9 100644
--- a/Tests/GameFeatureTests/DailyChallengeTests.swift
+++ b/Tests/GameFeatureTests/DailyChallengeTests.swift
@@ -48,7 +48,6 @@ class DailyChallengeTests: XCTestCase {
     } withDependencies: {
       $0.audioPlayer.stop = { _ in }
       $0.database.saveGame = { _ in await didSave.setValue(true) }
-      $0.fileClient.load = { @Sendable _ in try await Task.never() }
       $0.gameCenter.localPlayer.localPlayer = { .authenticated }
       $0.mainQueue = .immediate
     }
@@ -103,7 +102,6 @@ class DailyChallengeTests: XCTestCase {
     } withDependencies: {
       $0.audioPlayer.stop = { _ in }
       $0.database.saveGame = { _ in await didSave.setValue(true) }
-      $0.fileClient.load = { @Sendable _ in try await Task.never() }
       $0.gameCenter.localPlayer.localPlayer = { .authenticated }
       $0.mainQueue = .immediate
     }
diff --git a/Tests/GameFeatureTests/GameFeatureTests.swift b/Tests/GameFeatureTests/GameFeatureTests.swift
index f97082e5..58f2fcf3 100644
--- a/Tests/GameFeatureTests/GameFeatureTests.swift
+++ b/Tests/GameFeatureTests/GameFeatureTests.swift
@@ -45,7 +45,6 @@ class GameFeatureTests: XCTestCase {
       GameFeature()
     } withDependencies: {
       $0.audioPlayer.play = { _ in }
-      $0.fileClient.load = { @Sendable _ in try await Task.never() }
       $0.gameCenter.localPlayer.localPlayer = { .authenticated }
       $0.mainRunLoop = self.mainRunLoop.eraseToAnyScheduler()
     }
@@ -87,7 +86,6 @@ class GameFeatureTests: XCTestCase {
     ) {
       GameFeature()
     } withDependencies: {
-      $0.fileClient.load = { @Sendable _ in try await Task.never() }
       $0.gameCenter.localPlayer.localPlayer = { .authenticated }
       $0.mainRunLoop = self.mainRunLoop.eraseToAnyScheduler()
     }
diff --git a/Tests/GameOverFeatureTests/GameOverFeatureTests.swift b/Tests/GameOverFeatureTests/GameOverFeatureTests.swift
index 3b843628..4fd0eda8 100644
--- a/Tests/GameOverFeatureTests/GameOverFeatureTests.swift
+++ b/Tests/GameOverFeatureTests/GameOverFeatureTests.swift
@@ -10,7 +10,6 @@ import UpgradeInterstitialFeature
 import XCTest
 
 @testable import LocalDatabaseClient
-@testable import UserDefaultsClient
 
 class GameOverFeatureTests: XCTestCase {
   @MainActor
diff --git a/Tests/HomeFeatureTests/HomeViewTests.swift b/Tests/HomeFeatureTests/HomeViewTests.swift
index db636539..c9d6faf3 100644
--- a/Tests/HomeFeatureTests/HomeViewTests.swift
+++ b/Tests/HomeFeatureTests/HomeViewTests.swift
@@ -64,13 +64,7 @@ class HomeFeatureTests: XCTestCase {
       matching: HomeView(
         store: Store(
           initialState: Home.State(
-            dailyChallenges: [],
-            savedGames: .init(
-              dailyChallengeUnlimited: .mock,
-              unlimited: update(.mock) {
-                $0?.moves = [.mock]
-              }
-            )
+            dailyChallenges: []
           )
         ) {
         }
diff --git a/Tests/LeaderboardFeatureTests/LeaderboardFeatureTests.swift b/Tests/LeaderboardFeatureTests/LeaderboardFeatureTests.swift
index 72dd966a..3e81ca1c 100644
--- a/Tests/LeaderboardFeatureTests/LeaderboardFeatureTests.swift
+++ b/Tests/LeaderboardFeatureTests/LeaderboardFeatureTests.swift
@@ -119,7 +119,6 @@ class LeaderboardFeatureTests: XCTestCase {
       $0.destination = .cubePreview(
         .init(
           cubes: .mock,
-          isOnLowPowerMode: false,
           moveIndex: 0,
           moves: []
         )
diff --git a/Tests/SettingsFeatureTests/SettingsFeatureTests.swift b/Tests/SettingsFeatureTests/SettingsFeatureTests.swift
index 2a14e3f3..c48991ba 100644
--- a/Tests/SettingsFeatureTests/SettingsFeatureTests.swift
+++ b/Tests/SettingsFeatureTests/SettingsFeatureTests.swift
@@ -6,9 +6,8 @@ import ComposableUserNotifications
 import Overture
 import SharedModels
 import TestHelpers
-import UserDefaultsClient
 import UserNotifications
-import UserSettingsClient
+import UserSettings
 import XCTest
 
 @testable import SettingsFeature
@@ -19,12 +18,10 @@ extension DependencyValues {
     self.apiClient.currentPlayer = { .some(.init(appleReceipt: .mock, player: .blob)) }
     self.build.number = { 42 }
     self.mainQueue = .immediate
-    self.fileClient.save = { @Sendable _, _ in }
     self.storeKit.fetchProducts = { _ in
       .init(invalidProductIdentifiers: [], products: [])
     }
     self.storeKit.observer = { .finished }
-    self.userSettings = .mock()
   }
 }
 
@@ -72,7 +69,6 @@ class SettingsFeatureTests: XCTestCase {
     } withDependencies: {
       $0.setUpDefaults()
       $0.applicationClient.alternateIconName = { nil }
-      $0.fileClient.save = { @Sendable _, _ in }
       $0.mainQueue = .immediate
       $0.serverConfig.config = { .init() }
       $0.userDefaults.boolForKey = { _ in false }
@@ -117,7 +113,6 @@ class SettingsFeatureTests: XCTestCase {
     } withDependencies: {
       $0.setUpDefaults()
       $0.applicationClient.alternateIconName = { nil }
-      $0.fileClient.save = { @Sendable _, _ in }
       $0.mainQueue = .immediate
       $0.serverConfig.config = { .init() }
       $0.userDefaults.boolForKey = { _ in false }
@@ -159,7 +154,6 @@ class SettingsFeatureTests: XCTestCase {
     } withDependencies: {
       $0.setUpDefaults()
       $0.applicationClient.alternateIconName = { nil }
-      $0.fileClient.save = { @Sendable _, _ in }
       $0.mainQueue = .immediate
       $0.serverConfig.config = { .init() }
       $0.userDefaults.boolForKey = { _ in false }
@@ -205,7 +199,6 @@ class SettingsFeatureTests: XCTestCase {
         await openedUrl.setValue(url)
         return true
       }
-      $0.fileClient.save = { @Sendable _, _ in }
       $0.mainQueue = .immediate
       $0.serverConfig.config = { .init() }
       $0.userDefaults.boolForKey = { _ in false }
@@ -269,14 +262,12 @@ class SettingsFeatureTests: XCTestCase {
           }
         )
         $0.applicationClient.alternateIconName = { nil }
-        $0.fileClient.save = { @Sendable _, _ in }
         $0.mainQueue = .immediate
         $0.serverConfig.config = { .init() }
         $0.userDefaults.boolForKey = { _ in false }
         $0.userNotifications.getNotificationSettings = {
           .init(authorizationStatus: .authorized)
         }
-        $0.userSettings = .mock(initialUserSettings: userSettings)
       }
 
       let task = await store.send(.task) {
@@ -462,49 +453,4 @@ class SettingsFeatureTests: XCTestCase {
     await setBaseUrl.withValue { XCTAssertNoDifference($0, URL(string: "http://localhost:9876")!) }
     await didLogout.withValue { XCTAssert($0) }
   }
-
-  @MainActor
-  func testToggleEnableGyroMotion() async {
-    let store = TestStore(
-      initialState: Settings.State()
-    ) {
-      Settings()
-    } withDependencies: {
-      $0.setUpDefaults()
-      $0.userSettings = .mock(initialUserSettings: UserSettings(enableGyroMotion: true))
-    }
-
-    var userSettings = store.state.userSettings
-    userSettings.enableGyroMotion = false
-    await store.send(.set(\.userSettings, userSettings)) {
-      $0.userSettings.enableGyroMotion = false
-    }
-    userSettings.enableGyroMotion = true
-    await store.send(.set(\.userSettings, userSettings)) {
-      $0.userSettings.enableGyroMotion = true
-    }
-  }
-
-  @MainActor
-  func testToggleEnableHaptics() async {
-    let store = TestStore(
-      initialState: Settings.State()
-    ) {
-      Settings()
-    } withDependencies: {
-      $0.setUpDefaults()
-      $0.userSettings = .mock(initialUserSettings: UserSettings(enableHaptics: true))
-    }
-
-
-    var userSettings = store.state.userSettings
-    userSettings.enableHaptics = false
-    await store.send(.set(\.userSettings, userSettings)) {
-      $0.userSettings.enableHaptics = false
-    }
-    userSettings.enableHaptics = true
-    await store.send(.set(\.userSettings, userSettings)) {
-      $0.userSettings.enableHaptics = true
-    }
-  }
 }
diff --git a/Tests/SettingsFeatureTests/SettingsPurchaseTests.swift b/Tests/SettingsFeatureTests/SettingsPurchaseTests.swift
index fd31f30a..bc25b1e8 100644
--- a/Tests/SettingsFeatureTests/SettingsPurchaseTests.swift
+++ b/Tests/SettingsFeatureTests/SettingsPurchaseTests.swift
@@ -1,7 +1,6 @@
 import Combine
 import ComposableArchitecture
 import ComposableStoreKit
-import FileClient
 import SharedModels
 import XCTest
 
@@ -14,11 +13,9 @@ fileprivate extension DependencyValues {
     self.applicationClient.alternateIconName = { nil }
     self.build.number = { 42 }
     self.mainQueue = .immediate
-    self.fileClient.save = { @Sendable _, _ in }
     self.userNotifications.getNotificationSettings = {
       (try? await Task.never()) ?? .init(authorizationStatus: .notDetermined)
     }
-    self.userSettings = .mock()
   }
 }
 
diff --git a/Tests/SettingsFeatureTests/SettingsViewTests.swift b/Tests/SettingsFeatureTests/SettingsViewTests.swift
index 7cacc724..ee806154 100644
--- a/Tests/SettingsFeatureTests/SettingsViewTests.swift
+++ b/Tests/SettingsFeatureTests/SettingsViewTests.swift
@@ -2,7 +2,7 @@ import ComposableArchitecture
 @testable import SettingsFeature
 import SnapshotTesting
 import Styleguide
-import UserSettingsClient
+import UserSettings
 import XCTest
 
 class SettingsViewTests: XCTestCase {
@@ -59,13 +59,14 @@ class SettingsViewTests: XCTestCase {
       as: .image(perceptualPrecision: 0.98, layout: .device(config: .iPhoneXsMax))
     )
 
+    @Shared(.userSettings) var userSettings = UserSettings()
+    userSettings = UserSettings(enableNotifications: true)
+
     assertSnapshot(
       matching: NotificationsSettingsView(
         store: .init(
           initialState: .init()
         ) {
-        } withDependencies: {
-          $0.userSettings = .mock(initialUserSettings: UserSettings(enableNotifications: true))
         }
       ),
       as: .image(perceptualPrecision: 0.98, layout: .device(config: .iPhoneXsMax))
@@ -83,15 +84,14 @@ class SettingsViewTests: XCTestCase {
       as: .image(perceptualPrecision: 0.98, layout: .device(config: .iPhoneXsMax))
     )
 
+    @Shared(.userSettings) var userSettings = UserSettings()
+    userSettings = UserSettings(musicVolume: 0, soundEffectsVolume: 0)
+
     assertSnapshot(
       matching: SoundsSettingsView(
         store: Store(
           initialState: Settings.State()
         ) {
-        } withDependencies: {
-          $0.userSettings = .mock(
-            initialUserSettings: UserSettings(musicVolume: 0, soundEffectsVolume: 0)
-          )
         }
       ),
       as: .image(perceptualPrecision: 0.98, layout: .device(config: .iPhoneXsMax))
diff --git a/Tests/SettingsFeatureTests/__Snapshots__/SettingsViewTests/testBasics.3.png b/Tests/SettingsFeatureTests/__Snapshots__/SettingsViewTests/testBasics.3.png
index 6c65577d..9124fda7 100644
--- a/Tests/SettingsFeatureTests/__Snapshots__/SettingsViewTests/testBasics.3.png
+++ b/Tests/SettingsFeatureTests/__Snapshots__/SettingsViewTests/testBasics.3.png
@@ -1,3 +1,3 @@
 version https://git-lfs.github.com/spec/v1
-oid sha256:7bcf8aaf60ac9b9137c802c74015b94433a50557ffa023894ded85711bf539ac
-size 163450
+oid sha256:d518f3d2ec8dfe58bcb1cbd80454fa235ac22e146b048c202772c54e8652a6c8
+size 163451
diff --git a/Tests/UpgradeInterstitialFeatureTests/UpgradeInterstitialFeatureTests.swift b/Tests/UpgradeInterstitialFeatureTests/UpgradeInterstitialFeatureTests.swift
index 63a83f9a..ff521c67 100644
--- a/Tests/UpgradeInterstitialFeatureTests/UpgradeInterstitialFeatureTests.swift
+++ b/Tests/UpgradeInterstitialFeatureTests/UpgradeInterstitialFeatureTests.swift
@@ -8,7 +8,7 @@ import StoreKit
 import UpgradeInterstitialFeature
 import XCTest
 
-@testable import ServerConfigClient
+@testable import ServerConfigPersistenceKey
 
 class UpgradeInterstitialFeatureTests: XCTestCase {
   let scheduler = RunLoop.test
```
