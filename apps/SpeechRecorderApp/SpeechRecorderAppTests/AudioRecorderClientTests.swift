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
   (Context: TDD for AudioRecorderClient dependency)

 WHAT:
   Unit tests for the AudioRecorderClient dependency.
   Tests the interface contract without touching real audio hardware.

 WHEN:
   Created: 2025-12-10
   Last Modified: 2025-12-10

 WHERE:
   apps/SpeechRecorderApp/SpeechRecorderAppTests/AudioRecorderClientTests.swift

 WHY:
   TDD approach - write tests first to define expected behavior.
   These tests verify the AudioRecorderClient interface works correctly
   when mocked, ensuring features can be tested in isolation.
 */

import ComposableArchitecture
import Foundation
import Testing
@testable import SpeechRecorderApp

@Suite("AudioRecorderClient Tests")
struct AudioRecorderClientTests {
    
    @Test("Request permission returns true when granted")
    func requestPermissionGranted() async {
        let client = AudioRecorderClient(
            currentTime: { nil },
            requestRecordPermission: { true },
            startRecording: { _ in AsyncStream { _ in } },
            pauseRecording: { },
            resumeRecording: { },
            stopRecording: { },
            isPaused: { false },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        let result = await client.requestRecordPermission()
        #expect(result == true)
    }
    
    @Test("Request permission returns false when denied")
    func requestPermissionDenied() async {
        let client = AudioRecorderClient(
            currentTime: { nil },
            requestRecordPermission: { false },
            startRecording: { _ in AsyncStream { _ in } },
            pauseRecording: { },
            resumeRecording: { },
            stopRecording: { },
            isPaused: { false },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        let result = await client.requestRecordPermission()
        #expect(result == false)
    }
    
    @Test("Start recording is called with correct URL")
    func startRecordingWithURL() async throws {
        let expectedURL = URL(fileURLWithPath: "/tmp/test.m4a")
        let receivedURLHolder = LockIsolated<URL?>(nil)
        
        let client = AudioRecorderClient(
            currentTime: { nil },
            requestRecordPermission: { true },
            startRecording: { url in
                receivedURLHolder.setValue(url)
                return AsyncStream { _ in }
            },
            pauseRecording: { },
            resumeRecording: { },
            stopRecording: { },
            isPaused: { false },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        _ = try await client.startRecording(url: expectedURL)
        #expect(receivedURLHolder.value == expectedURL)
    }
    
    @Test("Stop recording is called")
    func stopRecording() async {
        let stopCalledExpectation = LockIsolated(false)
        
        let client = AudioRecorderClient(
            currentTime: { nil },
            requestRecordPermission: { true },
            startRecording: { _ in AsyncStream { _ in } },
            pauseRecording: { },
            resumeRecording: { },
            stopRecording: {
                stopCalledExpectation.setValue(true)
            },
            isPaused: { false },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        await client.stopRecording()
        #expect(stopCalledExpectation.value == true)
    }
    
    @Test("Current time returns recording duration")
    func currentTimeReturnsValue() async {
        let expectedTime: TimeInterval = 5.5
        
        let client = AudioRecorderClient(
            currentTime: { expectedTime },
            requestRecordPermission: { true },
            startRecording: { _ in AsyncStream { _ in } },
            pauseRecording: { },
            resumeRecording: { },
            stopRecording: { },
            isPaused: { false },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        let result = await client.currentTime()
        #expect(result == expectedTime)
    }
    
    @Test("Current time returns nil when not recording")
    func currentTimeReturnsNilWhenNotRecording() async {
        let client = AudioRecorderClient(
            currentTime: { nil },
            requestRecordPermission: { true },
            startRecording: { _ in AsyncStream { _ in } },
            pauseRecording: { },
            resumeRecording: { },
            stopRecording: { },
            isPaused: { false },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        let result = await client.currentTime()
        #expect(result == nil)
    }
    
    @Test("Pause recording is called")
    func pauseRecording() async {
        let pauseCalledExpectation = LockIsolated(false)
        
        let client = AudioRecorderClient(
            currentTime: { nil },
            requestRecordPermission: { true },
            startRecording: { _ in AsyncStream { _ in } },
            pauseRecording: {
                pauseCalledExpectation.setValue(true)
            },
            resumeRecording: { },
            stopRecording: { },
            isPaused: { false },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        await client.pauseRecording()
        #expect(pauseCalledExpectation.value == true)
    }
    
    @Test("Resume recording is called")
    func resumeRecording() async throws {
        let resumeCalledExpectation = LockIsolated(false)
        
        let client = AudioRecorderClient(
            currentTime: { nil },
            requestRecordPermission: { true },
            startRecording: { _ in AsyncStream { _ in } },
            pauseRecording: { },
            resumeRecording: {
                resumeCalledExpectation.setValue(true)
            },
            stopRecording: { },
            isPaused: { false },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        try await client.resumeRecording()
        #expect(resumeCalledExpectation.value == true)
    }
    
    @Test("isPaused returns correct state")
    func isPausedReturnsState() async {
        let isPausedState = LockIsolated(false)
        
        let client = AudioRecorderClient(
            currentTime: { nil },
            requestRecordPermission: { true },
            startRecording: { _ in AsyncStream { _ in } },
            pauseRecording: {
                isPausedState.setValue(true)
            },
            resumeRecording: {
                isPausedState.setValue(false)
            },
            stopRecording: { },
            isPaused: { isPausedState.value },
            audioLevelStream: { AsyncStream { $0.finish() } }
        )
        
        #expect(await client.isPaused() == false)
        await client.pauseRecording()
        #expect(await client.isPaused() == true)
        try? await client.resumeRecording()
        #expect(await client.isPaused() == false)
    }
}