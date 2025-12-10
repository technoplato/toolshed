Commands
ID	Title	Keyboard Shortcuts	Menu Contexts
sweetpad.build.build

SweetPad: Build (without Run)

commandPalette view/item/context

sweetpad.build.clean

SweetPad: Clean

commandPalette view/item/context

sweetpad.build.diagnoseSetup

SweetPad: Diagnose build setup

commandPalette

sweetpad.build.generateBuildServerConfig

SweetPad: Generate Build Server Config (buildServer.json)

commandPalette view/item/context

sweetpad.build.launch

SweetPad: Build & Run (Launch)

commandPalette view/item/context

sweetpad.build.openXcode

SweetPad: Open Xcode

commandPalette view/title

sweetpad.build.refreshSchemes

SweetPad: Refresh schemes

commandPalette view/title

sweetpad.build.removeBundleDir

SweetPad: Remove bundle directory

commandPalette

sweetpad.build.resolveDependencies

SweetPad: Resolve dependencies

commandPalette view/item/context

sweetpad.build.run

SweetPad: Run (without Build)

commandPalette view/item/context

sweetpad.build.selectConfiguration

SweetPad: Select build configuration

commandPalette

sweetpad.build.selectXcodeWorkspace

SweetPad: Select Xcode workspace

commandPalette

sweetpad.build.setDefaultScheme

SweetPad: Set scheme

commandPalette view/item/context

sweetpad.build.test

SweetPad: Test

commandPalette view/item/context

sweetpad.debugger.debuggingBuild

SweetPad: Build (for debugging)

commandPalette

sweetpad.debugger.debuggingLaunch

SweetPad: Build & Run (for debugging)

commandPalette

sweetpad.debugger.debuggingRun

SweetPad: Run (for debugging)

commandPalette

sweetpad.debugger.getAppPath

SweetPad: Get app path for debugging

commandPalette

sweetpad.destinations.removeRecent

SweetPad: Remove recent destination

commandPalette view/item/context

sweetpad.destinations.select

SweetPad: Select destination

commandPalette view/item/context

sweetpad.destinations.selectForTesting

SweetPad.Testing: Select destination for testing

commandPalette

sweetpad.devices.refresh

SweetPad: Refresh devices list

commandPalette view/item/context

sweetpad.format.run

SweetPad: Format

commandPalette

sweetpad.format.showLogs

SweetPad: Show format logs

commandPalette

sweetpad.simulators.openSimulator

SweetPad: Open simulator

commandPalette view/item/context

sweetpad.simulators.refresh

SweetPad: Refresh simulators list

commandPalette view/item/context

sweetpad.simulators.removeCache

SweetPad: Remove simulator cache

commandPalette view/item/context

sweetpad.simulators.start

SweetPad: Start simulator

commandPalette view/item/context

sweetpad.simulators.stop

SweetPad: Stop simulator

commandPalette view/item/context

sweetpad.system.createIssue.generic

SweetPad: Create Issue on GitHub

commandPalette

sweetpad.system.createIssue.noSchemes

SweetPad: Create Issue on GitHub (No Schemes)

commandPalette

sweetpad.system.openTerminalPanel

SweetPad: Open Terminal Panel

commandPalette

sweetpad.system.resetSweetPadCache

SweetPad: Reset Extension Cache

commandPalette

sweetpad.system.testErrorReporting

SweetPad: Test Error Reporting

commandPalette

sweetpad.testing.buildForTesting

SweetPad.Testing: Build for testing (without running tests)

commandPalette testing/item/context

sweetpad.testing.selectConfiguration

SweetPad.Testing: Select configuration for testing

commandPalette

sweetpad.testing.selectTarget

SweetPad.Testing: Select testing target

commandPalette testing/item/context

sweetpad.testing.setDefaultScheme

SweetPad.Testing: Set scheme for testing

commandPalette

sweetpad.testing.testWithoutBuilding

SweetPad.Testing: Test without building

commandPalette testing/item/context

sweetpad.tools.documentation

SweetPad: Open tool documentation

commandPalette view/item/context

sweetpad.tools.install

SweetPad: Install tool

commandPalette view/item/context

sweetpad.tools.refresh

SweetPad: Refresh tools list

commandPalette view/title

sweetpad.tuist.clean

SweetPad: Clean Tuist project

commandPalette

sweetpad.tuist.edit

SweetPad: Edit Tuist project (Open project in Xcode)

commandPalette

sweetpad.tuist.generate

SweetPad: Generate an Xcode project using Tuist

commandPalette

sweetpad.tuist.install

SweetPad: Install Swift Package using Tuist

commandPalette

sweetpad.tuist.test

SweetPad: Test Generated project using Tuist

commandPalette

sweetpad.xcodegen.generate

SweetPad: Generate an Xcode project using XcodeGen

commandPalette



Settings
ID	Description	Default
sweetpad.build.allowProvisioningUpdates

Allow Xcode to update provisioning profiles.

true
sweetpad.build.arch

Architecture to build for. Can be usefull for building x86_64 simulator builds on M1 Macs. Usually, you don't need to change this setting.

""
sweetpad.build.args

Additional arguments to pass to the build command. You can also override the default arguments

[]
sweetpad.build.autoRefreshSchemes

Automatically refresh schemes when project files change (Package.swift, .xcodeproj, .xcworkspace, etc.)

true
sweetpad.build.autoRefreshSchemesDelay

Delay in milliseconds before auto-refreshing schemes after detecting file changes

500
sweetpad.build.configuration

Configuration to build.

null
sweetpad.build.derivedDataPath

Path to derived data directory. Can be absolute or relative to the workspace root.

null
sweetpad.build.env

Environment variables to pass to the xcodebuild command

{}
sweetpad.build.launchArgs

Arguments to pass to the app on launch

[]
sweetpad.build.launchEnv

Environment variables to pass to the app on launch

{}
sweetpad.build.rosettaDestination

Use Rosetta Destination.

false
sweetpad.build.xcbeautifyEnabled

Enable xcbeautify for build logs.

true
sweetpad.build.xcodeWorkspacePath

Path to Xcode workspace. Can be absolute or relative to the workspace root.

null
sweetpad.format.args

Command or path to formatter executable. Use ${file} as a placeholder for the file path. Placeholder ${file} is supported only as a separate item in the array.

null
sweetpad.format.path

Command or path to formatter executable.

""
sweetpad.format.selectionArgs

Custom arguments to pass to the formatter for selection formatting. Use ${startLine} and ${endLine} as placeholders for the start and end line numbers of the selected code. Use ${startOffset} and ${endOffset} as placeholders for the start and end offset of the selected code. If this is not provided for custom formatters, the entire document will always be reformatted.

null
sweetpad.system.autoRevealTerminal

Automatically reveal the terminal when executing a command or task

true
sweetpad.system.customXcodeWorkspaceParser

Use custom workspace parser instead of the 'xcodebuild' command. This may speed up processing for large projects, but it might not work correctly in all cases.

false
sweetpad.system.enableSentry

Enable Sentry error reporting. NOTE: This config is disable by default, I recommend enabling it when you have issues with SweetPad and want to report about them.

false
sweetpad.system.logLevel

Log level for SweetPad.

"info"
sweetpad.system.showProgressStatusBar

Show progress in the status bar when executing a command or task

true
sweetpad.system.taskExecutor

Use version task executor for build tasks.

"v2"
sweetpad.testing.configuration

Configuration to build for testing.

null
sweetpad.tuist.autogenerate

Watch for new .swift files and regenerate the project using Tuist. Restart VSCode to apply the settings.

false
sweetpad.tuist.generate.env

Environment variables to pass to the Tuist generate command — https://docs.tuist.dev/en/guides/develop/projects/dynamic-configuration

{}
sweetpad.xcodebuildserver.autogenerate

Watch if default scheme is changed and regenerate the build server config

true
sweetpad.xcodebuildserver.path

Path to custom xcodebuildserver executable.

null
sweetpad.xcodegen.autogenerate