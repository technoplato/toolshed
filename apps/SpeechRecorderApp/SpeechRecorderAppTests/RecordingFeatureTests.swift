/**
 HOW:
   Run tests with: `xcodebuild test -scheme SpeechRecorderApp -destination 'platform=iOS Simulator,name=iPhone 16'`
   Or use SweetPad: `sweetpad.build.test`
   
   [Inputs]
   - None (unit tests)
   
   [Outputs]
   - Test results
   
   [Side Effects]
   - None (uses mocked dependencies)

 WHO:
   AI Agent, Developer
   (Context: TDD for RecordingFeature reducer)

 WHAT:
   Unit tests for the RecordingFeature reducer.
   Tests recording flow, permission handling, and state transitions.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/RecordingFeatureTests.swift

 WHY:
   TDD approach - write tests first to define expected behavior.
   These tests verify the RecordingFeature reducer handles all
   recording states and actions correctly.
 */

import ComposableArchitecture
import Foundation
import Testing
@testable import SpeechRecorderApp

@Suite("RecordingFeature Tests")
struct RecordingFeatureTests {
    
    @Test("Record button tapped starts recording when permission granted")
    func recordButtonTappedStartsRecording() async {
        let testDate = Date(timeIntervalSince1970: 0)
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000000")!
        
        let store = await TestStore(initialState: RecordingFeature.State()) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.requestRecordPermission = { true }
            $0.audioRecorder.startRecording = { _ in }
            $0.audioRecorder.currentTime = { nil }
            $0.date.now = testDate
            $0.uuid = .constant(testUUID)
            $0.continuousClock = ImmediateClock()
        }
        
        /// Mark as non-exhaustive since we're just testing the immediate state change
        /// The recording and timer effects will run in the background
        store.exhaustivity = .off
        
        await store.send(.recordButtonTapped) {
            $0.isRecording = true
            $0.recordingStartTime = testDate
            $0.mode = .recording
            $0.recordingURL = URL(fileURLWithPath: NSTemporaryDirectory())
                .appendingPathComponent(testUUID.uuidString)
                .appendingPathExtension("m4a")
        }
        
        await store.receive(\.permissionResponse) {
            $0.hasPermission = true
        }
    }
    
    @Test("Record button tapped shows alert when permission denied")
    func recordButtonTappedShowsAlertWhenDenied() async {
        let testDate = Date(timeIntervalSince1970: 0)
        
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000000")!
        
        let store = await TestStore(initialState: RecordingFeature.State()) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.requestRecordPermission = { false }
            $0.date.now = testDate
            $0.uuid = .constant(testUUID)
            $0.continuousClock = ImmediateClock()
        }
        
        await store.send(.recordButtonTapped) {
            $0.isRecording = true
            $0.recordingStartTime = testDate
            $0.mode = .recording
            $0.recordingURL = URL(fileURLWithPath: NSTemporaryDirectory())
                .appendingPathComponent(testUUID.uuidString)
                .appendingPathExtension("m4a")
        }
        
        await store.receive(\.permissionResponse) {
            $0.isRecording = false
            $0.recordingStartTime = nil
            $0.mode = .idle
            $0.hasPermission = false
            $0.alert = AlertState {
                TextState("Permission Required")
            } message: {
                TextState("Microphone access is required to record audio.")
            }
        }
    }
    
    @Test("Stop button tapped stops recording")
    func stopButtonTappedStopsRecording() async {
        let testDate = Date(timeIntervalSince1970: 0)
        let testDuration: TimeInterval = 5.0
        let testUUID = UUID(uuidString: "00000000-0000-0000-0000-000000000000")!
        let testURL = URL(fileURLWithPath: "/tmp/test.m4a")
        
        var state = RecordingFeature.State()
        state.isRecording = true
        state.recordingStartTime = testDate
        state.hasPermission = true
        state.recordingURL = testURL
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.stopRecording = { }
            $0.audioRecorder.currentTime = { testDuration }
            $0.uuid = .constant(testUUID)
        }
        
        await store.send(.stopButtonTapped) {
            $0.mode = .encoding
        }
        
        await store.receive(\.finalRecordingTime) {
            $0.duration = testDuration
        }
        
        await store.receive(\.recordingStopped) {
            $0.isRecording = false
            $0.mode = .idle
        }
        
        await store.receive(\.delegate)
    }
    
    @Test("Timer updates duration while recording")
    func timerUpdatesDuration() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        await store.send(.timerTicked) {
            $0.duration += 1
        }
        
        await store.send(.timerTicked) {
            $0.duration += 1
        }
    }
    
    @Test("Cancel button resets state")
    func cancelButtonResetsState() async {
        var state = RecordingFeature.State()
        state.isRecording = true
        state.duration = 5.0
        state.hasPermission = true
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        } withDependencies: {
            $0.audioRecorder.stopRecording = { }
        }
        
        await store.send(.cancelButtonTapped) {
            $0.isRecording = false
            $0.duration = 0
            $0.mode = .idle
        }
    }
    
    @Test("Alert dismissed clears alert state")
    func alertDismissedClearsState() async {
        var state = RecordingFeature.State()
        state.alert = AlertState {
            TextState("Test Alert")
        }
        
        let store = await TestStore(initialState: state) {
            RecordingFeature()
        }
        
        await store.send(.alert(.dismiss)) {
            $0.alert = nil
        }
    }
}