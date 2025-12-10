---
url: "https://developer.apple.com/documentation/speech/speechanalyzer"
title: "SpeechAnalyzer | Apple Developer Documentation"
---

[Skip Navigation](https://developer.apple.com/documentation/speech/speechanalyzer#app-main)

- [Global Nav Open Menu](https://developer.apple.com/documentation/speech/speechanalyzer#ac-gn-menustate) [Global Nav Close Menu](https://developer.apple.com/documentation/speech/speechanalyzer#)
- [Apple Developer](https://developer.apple.com/)

[Search Developer\\
\\
Cancel](https://developer.apple.com/search/)

- [Apple Developer](https://developer.apple.com/)
- [News](https://developer.apple.com/news/)
- [Discover](https://developer.apple.com/discover/)
- [Design](https://developer.apple.com/design/)
- [Develop](https://developer.apple.com/develop/)
- [Distribute](https://developer.apple.com/distribute/)
- [Support](https://developer.apple.com/support/)
- [Account](https://developer.apple.com/account/)
- [Search Developer](https://developer.apple.com/search/)

Cancel

Only search within “Documentation”

### Quick Links

- [Downloads](https://developer.apple.com/download/)
- [Documentation](https://developer.apple.com/documentation/)
- [Sample Code](https://developer.apple.com/documentation/samplecode/)
- [Videos](https://developer.apple.com/videos/)
- [Forums](https://developer.apple.com/forums/)

5 Quick Links

[Documentation](https://developer.apple.com/documentation)

[Open Menu](https://developer.apple.com/documentation/speech/speechanalyzer#)

- SwiftLanguage: Swift


All Technologies

[**Speech**](https://developer.apple.com/documentation/speech)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

1 of 23 symbols inside <root>

### Essentials

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

2 of 23 symbols inside <root> [Bringing advanced speech-to-text capabilities to your app](https://developer.apple.com/documentation/speech/bringing-advanced-speech-to-text-capabilities-to-your-app)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

3 of 23 symbols inside <root> containing 34 symbols [SpeechAnalyzer](https://developer.apple.com/documentation/speech/speechanalyzer)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

1 of 34 symbols inside -1414871264

### Creating an analyzer

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

2 of 34 symbols inside -1414871264 [convenience init(modules: \[any SpeechModule\], options: SpeechAnalyzer.Options?)](https://developer.apple.com/documentation/speech/speechanalyzer/init(modules:options:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

3 of 34 symbols inside -1414871264 [convenience init<InputSequence>(inputSequence: InputSequence, modules: \[any SpeechModule\], options: SpeechAnalyzer.Options?, analysisContext: AnalysisContext, volatileRangeChangedHandler: sending ((CMTimeRange, Bool, Bool) -> Void)?)](https://developer.apple.com/documentation/speech/speechanalyzer/init(inputsequence:modules:options:analysiscontext:volatilerangechangedhandler:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

4 of 34 symbols inside -1414871264 [convenience init(inputAudioFile: AVAudioFile, modules: \[any SpeechModule\], options: SpeechAnalyzer.Options?, analysisContext: AnalysisContext, finishAfterFile: Bool, volatileRangeChangedHandler: sending ((CMTimeRange, Bool, Bool) -> Void)?) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/init(inputaudiofile:modules:options:analysiscontext:finishafterfile:volatilerangechangedhandler:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

S

5 of 34 symbols inside -1414871264 containing 6 symbols [SpeechAnalyzer.Options](https://developer.apple.com/documentation/speech/speechanalyzer/options)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

6 of 34 symbols inside -1414871264

### Managing modules

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

7 of 34 symbols inside -1414871264 [func setModules(\[any SpeechModule\]) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/setmodules(_:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

P

8 of 34 symbols inside -1414871264 [var modules: \[any SpeechModule\]](https://developer.apple.com/documentation/speech/speechanalyzer/modules)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

9 of 34 symbols inside -1414871264

### Performing analysis

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

10 of 34 symbols inside -1414871264 [func analyzeSequence<InputSequence>(InputSequence) async throws -> CMTime?](https://developer.apple.com/documentation/speech/speechanalyzer/analyzesequence(_:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

11 of 34 symbols inside -1414871264 [func analyzeSequence(from: AVAudioFile) async throws -> CMTime?](https://developer.apple.com/documentation/speech/speechanalyzer/analyzesequence(from:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

12 of 34 symbols inside -1414871264

### Performing autonomous analysis

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

13 of 34 symbols inside -1414871264 [func start<InputSequence>(inputSequence: InputSequence) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/start(inputsequence:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

14 of 34 symbols inside -1414871264 [func start(inputAudioFile: AVAudioFile, finishAfterFile: Bool) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/start(inputaudiofile:finishafterfile:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

15 of 34 symbols inside -1414871264

### Finalizing and cancelling results

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

16 of 34 symbols inside -1414871264 [func cancelAnalysis(before: CMTime)](https://developer.apple.com/documentation/speech/speechanalyzer/cancelanalysis(before:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

17 of 34 symbols inside -1414871264 [func finalize(through: CMTime?) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/finalize(through:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

18 of 34 symbols inside -1414871264

### Finishing analysis

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

19 of 34 symbols inside -1414871264 [func cancelAndFinishNow() async](https://developer.apple.com/documentation/speech/speechanalyzer/cancelandfinishnow())

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

20 of 34 symbols inside -1414871264 [func finalizeAndFinishThroughEndOfInput() async throws](https://developer.apple.com/documentation/speech/speechanalyzer/finalizeandfinishthroughendofinput())

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

21 of 34 symbols inside -1414871264 [func finalizeAndFinish(through: CMTime) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/finalizeandfinish(through:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

22 of 34 symbols inside -1414871264 [func finish(after: CMTime) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/finish(after:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

23 of 34 symbols inside -1414871264

### Determining audio formats

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

24 of 34 symbols inside -1414871264 [static func bestAvailableAudioFormat(compatibleWith: \[any SpeechModule\]) async -> AVAudioFormat?](https://developer.apple.com/documentation/speech/speechanalyzer/bestavailableaudioformat(compatiblewith:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

25 of 34 symbols inside -1414871264 [static func bestAvailableAudioFormat(compatibleWith: \[any SpeechModule\], considering: AVAudioFormat?) async -> AVAudioFormat?](https://developer.apple.com/documentation/speech/speechanalyzer/bestavailableaudioformat(compatiblewith:considering:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

26 of 34 symbols inside -1414871264

### Improving responsiveness

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

27 of 34 symbols inside -1414871264 [func prepareToAnalyze(in: AVAudioFormat?) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/preparetoanalyze(in:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

28 of 34 symbols inside -1414871264 [func prepareToAnalyze(in: AVAudioFormat?, withProgressReadyHandler: sending ((Progress) -> Void)?) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/preparetoanalyze(in:withprogressreadyhandler:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

29 of 34 symbols inside -1414871264

### Monitoring analysis

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

30 of 34 symbols inside -1414871264 [func setVolatileRangeChangedHandler(sending ((CMTimeRange, Bool, Bool) -> Void)?)](https://developer.apple.com/documentation/speech/speechanalyzer/setvolatilerangechangedhandler(_:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

P

31 of 34 symbols inside -1414871264 [var volatileRange: CMTimeRange?](https://developer.apple.com/documentation/speech/speechanalyzer/volatilerange)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

32 of 34 symbols inside -1414871264

### Managing contexts

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

M

33 of 34 symbols inside -1414871264 [func setContext(AnalysisContext) async throws](https://developer.apple.com/documentation/speech/speechanalyzer/setcontext(_:))

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

P

34 of 34 symbols inside -1414871264 [var context: AnalysisContext](https://developer.apple.com/documentation/speech/speechanalyzer/context)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

4 of 23 symbols inside <root> containing 11 symbols [AssetInventory](https://developer.apple.com/documentation/speech/assetinventory)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

5 of 23 symbols inside <root>

### Modules

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

6 of 23 symbols inside <root> containing 16 symbols [SpeechTranscriber](https://developer.apple.com/documentation/speech/speechtranscriber)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

7 of 23 symbols inside <root> containing 15 symbols [DictationTranscriber](https://developer.apple.com/documentation/speech/dictationtranscriber)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

8 of 23 symbols inside <root> containing 7 symbols [SpeechDetector](https://developer.apple.com/documentation/speech/speechdetector)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

rP

9 of 23 symbols inside <root> containing 6 symbols [SpeechModule](https://developer.apple.com/documentation/speech/speechmodule)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

rP

10 of 23 symbols inside <root> containing 5 symbols [LocaleDependentSpeechModule](https://developer.apple.com/documentation/speech/localedependentspeechmodule)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

11 of 23 symbols inside <root>

### Input and output

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

S

12 of 23 symbols inside <root> containing 6 symbols [AnalyzerInput](https://developer.apple.com/documentation/speech/analyzerinput)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

rP

13 of 23 symbols inside <root> containing 5 symbols [SpeechModuleResult](https://developer.apple.com/documentation/speech/speechmoduleresult)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

14 of 23 symbols inside <root>

### Custom vocabulary

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

15 of 23 symbols inside <root> containing 8 symbols [AnalysisContext](https://developer.apple.com/documentation/speech/analysiscontext)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

16 of 23 symbols inside <root> containing 7 symbols [SFSpeechLanguageModel](https://developer.apple.com/documentation/speech/sfspeechlanguagemodel)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

17 of 23 symbols inside <root> containing 8 symbols [SFSpeechLanguageModel.Configuration](https://developer.apple.com/documentation/speech/sfspeechlanguagemodel/configuration)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

18 of 23 symbols inside <root> containing 28 symbols [SFCustomLanguageModelData](https://developer.apple.com/documentation/speech/sfcustomlanguagemodeldata)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

19 of 23 symbols inside <root>

### Asset and resource management

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

C

20 of 23 symbols inside <root> containing 2 symbols [AssetInstallationRequest](https://developer.apple.com/documentation/speech/assetinstallationrequest)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

E

21 of 23 symbols inside <root> containing 2 symbols [SpeechModels](https://developer.apple.com/documentation/speech/speechmodels)

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

22 of 23 symbols inside <root>

### Legacy API

To navigate the symbols, press Up Arrow, Down Arrow, Left Arrow or Right Arrow

Collection

23 of 23 symbols inside <root> containing 27 symbols [Speech Recognition in Objective-C](https://developer.apple.com/documentation/speech/speech-recognition-in-objc)

57 items were found. Tab back to navigate through them.

/

Navigator is ready

- [Speech](https://developer.apple.com/documentation/speech)
- SpeechAnalyzer

Class

# SpeechAnalyzer

Analyzes spoken audio content in various ways and manages the analysis session.

iOS 26.0+iPadOS 26.0+Mac Catalyst 26.0+macOS 26.0+visionOS 26.0+

```
final actor SpeechAnalyzer
```

## [Overview](https://developer.apple.com/documentation/speech/speechanalyzer\#overview)

The Speech framework provides several modules that can be added to an analyzer to provide specific types of analysis and transcription. Many use cases only need a [`SpeechTranscriber`](https://developer.apple.com/documentation/speech/speechtranscriber) module, which performs speech-to-text transcriptions.

The `SpeechAnalyzer` class is responsible for:

- Holding associated modules

- Accepting audio speech input

- Controlling the overall analysis


Each module is responsible for:

- Providing guidance on acceptable input

- Providing its analysis or transcription output


Analysis is asynchronous. Input, output, and session control are decoupled and typically occur over several different tasks created by you or by the session. In particular, where an Objective-C API might use a delegate to provide results to you, the Swift API’s modules provides their results via an `AsyncSequence`. Similarly, you provide speech input to this API via an `AsyncSequence` you create and populate.

The analyzer can only analyze one input sequence at a time.

### [Perform analysis](https://developer.apple.com/documentation/speech/speechanalyzer\#Perform-analysis)

To perform analysis on audio files and streams, follow these general steps:

1. Create and configure the necessary modules.

2. Ensure the relevant assets are installed or already present. See [`AssetInventory`](https://developer.apple.com/documentation/speech/assetinventory).

3. Create an input sequence you can use to provide the spoken audio.

4. Create and configure the analyzer with the modules and input sequence.

5. Supply audio.

6. Start analysis.

7. Act on results.

8. Finish analysis when desired.


This example shows how you could perform an analysis that transcribes audio using the `SpeechTranscriber` module:

```
import Speech

// Step 1: Modules
guard let locale = SpeechTranscriber.supportedLocale(equivalentTo: Locale.current) else {
    /* Note unsupported language */
}
let transcriber = SpeechTranscriber(locale: locale, preset: .offlineTranscription)

// Step 2: Assets
if let installationRequest = try await AssetInventory.assetInstallationRequest(supporting: [transcriber]) {
    try await installationRequest.downloadAndInstall()
}

// Step 3: Input sequence
let (inputSequence, inputBuilder) = AsyncStream.makeStream(of: AnalyzerInput.self)

// Step 4: Analyzer
let audioFormat = await SpeechAnalyzer.bestAvailableAudioFormat(compatibleWith: [transcriber])
let analyzer = SpeechAnalyzer(modules: [transcriber])

// Step 5: Supply audio
Task {
    while /* audio remains */ {
        /* Get some audio */
        /* Convert to audioFormat */
        let pcmBuffer = /* an AVAudioPCMBuffer containing some converted audio */
        let input = AnalyzerInput(buffer: pcmBuffer)
        inputBuilder.yield(input)
    }
    inputBuilder.finish()
}

// Step 7: Act on results
Task {
    do {
        for try await result in transcriber.results {
            let bestTranscription = result.text // an AttributedString
            let plainTextBestTranscription = String(bestTranscription.characters) // a String
            print(plainTextBestTranscription)
        }
    } catch {
        /* Handle error */
    }
}

// Step 6: Perform analysis
let lastSampleTime = try await analyzer.analyzeSequence(inputSequence)

// Step 8: Finish analysis
if let lastSampleTime {
    try await analyzer.finalizeAndFinish(through: lastSampleTime)
} else {
    try analyzer.cancelAndFinishNow()
}
```

### [Analyze audio files](https://developer.apple.com/documentation/speech/speechanalyzer\#Analyze-audio-files)

To analyze one or more audio files represented by an `AVAudioFile` object, call methods such as [`analyzeSequence(from:)`](https://developer.apple.com/documentation/speech/speechanalyzer/analyzesequence(from:)) or [`start(inputAudioFile:finishAfterFile:)`](https://developer.apple.com/documentation/speech/speechanalyzer/start(inputaudiofile:finishafterfile:)), or create the analyzer with one of the initializers that has a file parameter. These methods automatically convert the file to a supported audio format and process the file in its entirety.

To end the analysis session after one file, pass `true` for the `finishAfterFile` parameter or call one of the `finish` methods.

Otherwise, by default, the analyzer won’t terminate its result streams and will wait for additional audio files or buffers. The analysis session doesn’t reset the audio timeline after each file; the next audio is assumed to come immediately after the completed file.

### [Analyze audio buffers](https://developer.apple.com/documentation/speech/speechanalyzer\#Analyze-audio-buffers)

To analyze audio buffers directly, convert them to a supported audio format, either on the fly or in advance. You can use [`bestAvailableAudioFormat(compatibleWith:)`](https://developer.apple.com/documentation/speech/speechanalyzer/bestavailableaudioformat(compatiblewith:)) or individual modules’ [`availableCompatibleAudioFormats`](https://developer.apple.com/documentation/speech/speechmodule/availablecompatibleaudioformats) methods to select a format to convert to.

Create an [`AnalyzerInput`](https://developer.apple.com/documentation/speech/analyzerinput) object for each audio buffer and add the object to an input sequence you create. Supply that input sequence to [`analyzeSequence(_:)`](https://developer.apple.com/documentation/speech/speechanalyzer/analyzesequence(_:)), [`start(inputSequence:)`](https://developer.apple.com/documentation/speech/speechanalyzer/start(inputsequence:)), or a similar parameter of the analyzer’s initializer.

To skip past part of an audio stream, omit the buffers you want to skip from the input sequence. When you resume analysis with a later buffer, you can ensure the time-code of each module’s result accounts for the skipped audio. To do this, pass the later buffer’s time-code within the audio stream as the `bufferStartTime` parameter of the later `AnalyzerInput` object.

### [Analyze autonomously](https://developer.apple.com/documentation/speech/speechanalyzer\#Analyze-autonomously)

You can and usually should perform analysis using the [`analyzeSequence(_:)`](https://developer.apple.com/documentation/speech/speechanalyzer/analyzesequence(_:)) or [`analyzeSequence(from:)`](https://developer.apple.com/documentation/speech/speechanalyzer/analyzesequence(from:)) methods; those methods work well with Swift structured concurrency techniques. However, you may prefer that the analyzer proceed independently and perform its analysis autonomously as audio input becomes available in a task managed by the analyzer itself.

To use this capability, create the analyzer with one of the initializers that has an input sequence or file parameter, or call [`start(inputSequence:)`](https://developer.apple.com/documentation/speech/speechanalyzer/start(inputsequence:)) or [`start(inputAudioFile:finishAfterFile:)`](https://developer.apple.com/documentation/speech/speechanalyzer/start(inputaudiofile:finishafterfile:)). To end the analysis when the input ends, call [`finalizeAndFinishThroughEndOfInput()`](https://developer.apple.com/documentation/speech/speechanalyzer/finalizeandfinishthroughendofinput()). To end the analysis of that input and start analysis of different input, call one of the `start` methods again.

### [Control processing and timing of results](https://developer.apple.com/documentation/speech/speechanalyzer\#Control-processing-and-timing-of-results)

Modules deliver results periodically, but you can manually synchronize their processing and delivery to outside cues.

To deliver a result for a particular time-code, call [`finalize(through:)`](https://developer.apple.com/documentation/speech/speechanalyzer/finalize(through:)). To cancel processing of results that are no longer of interest, call [`cancelAnalysis(before:)`](https://developer.apple.com/documentation/speech/speechanalyzer/cancelanalysis(before:)).

### [Improve responsiveness](https://developer.apple.com/documentation/speech/speechanalyzer\#Improve-responsiveness)

By default, the analyzer and modules load the system resources that they require lazily, and unload those resources when they’re deallocated.

To proactively load system resources and “preheat” the analyzer, call [`prepareToAnalyze(in:)`](https://developer.apple.com/documentation/speech/speechanalyzer/preparetoanalyze(in:)) after setting its modules. This may improve how quickly the modules return their first results.

To delay or prevent unloading an analyzer’s resources — caching them for later use by a different analyzer instance — you can select a [`SpeechAnalyzer.Options.ModelRetention`](https://developer.apple.com/documentation/speech/speechanalyzer/options/modelretention-swift.enum) option and create the analyzer with an appropriate [`SpeechAnalyzer.Options`](https://developer.apple.com/documentation/speech/speechanalyzer/options) object.

To set the priority of analysis work, create the analyzer with a [`SpeechAnalyzer.Options`](https://developer.apple.com/documentation/speech/speechanalyzer/options) object given a `priority` value.

Specific modules may also offer options that improve responsiveness.

### [Finish analysis](https://developer.apple.com/documentation/speech/speechanalyzer\#Finish-analysis)

To end an analysis session, you must use one of the analyzer’s `finish` methods or parameters, or deallocate the analyzer.

When the analysis session transitions to the _finished_ state:

- The analyzer won’t take additional input from the input sequence

- Most methods won’t do anything; in particular, the analyzer won’t accept different input sequences or modules

- Module result streams terminate and modules won’t publish additional results, though the app can continue to iterate over already-published results


Note

While you can terminate the input sequence you created with a method such as `AsyncStream.Continuation.finish()`, finishing the input sequence does _not_ cause the analysis session to become finished, and you can continue the session with a different input sequence.

### [Respond to errors](https://developer.apple.com/documentation/speech/speechanalyzer\#Respond-to-errors)

When the analyzer or its modules’ result streams throw an error, the analysis session becomes finished as described above, and the same error (or a `CancellationError`) is thrown from all waiting methods and result streams.

## [Topics](https://developer.apple.com/documentation/speech/speechanalyzer\#topics)

### [Creating an analyzer](https://developer.apple.com/documentation/speech/speechanalyzer\#Creating-an-analyzer)

[`convenience init(modules: [any SpeechModule], options: SpeechAnalyzer.Options?)`](https://developer.apple.com/documentation/speech/speechanalyzer/init(modules:options:))

Creates an analyzer.

[`convenience init<InputSequence>(inputSequence: InputSequence, modules: [any SpeechModule], options: SpeechAnalyzer.Options?, analysisContext: AnalysisContext, volatileRangeChangedHandler: sending ((CMTimeRange, Bool, Bool) -> Void)?)`](https://developer.apple.com/documentation/speech/speechanalyzer/init(inputsequence:modules:options:analysiscontext:volatilerangechangedhandler:))

Creates an analyzer and begins analysis.

[`convenience init(inputAudioFile: AVAudioFile, modules: [any SpeechModule], options: SpeechAnalyzer.Options?, analysisContext: AnalysisContext, finishAfterFile: Bool, volatileRangeChangedHandler: sending ((CMTimeRange, Bool, Bool) -> Void)?) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/init(inputaudiofile:modules:options:analysiscontext:finishafterfile:volatilerangechangedhandler:))

Creates an analyzer and begins analysis on an audio file.

[`struct Options`](https://developer.apple.com/documentation/speech/speechanalyzer/options)

Analysis processing options.

### [Managing modules](https://developer.apple.com/documentation/speech/speechanalyzer\#Managing-modules)

[`func setModules([any SpeechModule]) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/setmodules(_:))

Adds or removes modules.

[`var modules: [any SpeechModule]`](https://developer.apple.com/documentation/speech/speechanalyzer/modules)

The modules performing analysis on the audio input.

### [Performing analysis](https://developer.apple.com/documentation/speech/speechanalyzer\#Performing-analysis)

[`func analyzeSequence<InputSequence>(InputSequence) async throws -> CMTime?`](https://developer.apple.com/documentation/speech/speechanalyzer/analyzesequence(_:))

Analyzes an input sequence, returning when the sequence is consumed.

[`func analyzeSequence(from: AVAudioFile) async throws -> CMTime?`](https://developer.apple.com/documentation/speech/speechanalyzer/analyzesequence(from:))

Analyzes an input sequence created from an audio file, returning when the file has been read.

### [Performing autonomous analysis](https://developer.apple.com/documentation/speech/speechanalyzer\#Performing-autonomous-analysis)

[`func start<InputSequence>(inputSequence: InputSequence) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/start(inputsequence:))

Starts analysis of an input sequence and returns immediately.

[`func start(inputAudioFile: AVAudioFile, finishAfterFile: Bool) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/start(inputaudiofile:finishafterfile:))

Starts analysis of an input sequence created from an audio file and returns immediately.

### [Finalizing and cancelling results](https://developer.apple.com/documentation/speech/speechanalyzer\#Finalizing-and-cancelling-results)

[`func cancelAnalysis(before: CMTime)`](https://developer.apple.com/documentation/speech/speechanalyzer/cancelanalysis(before:))

Stops analyzing audio predating the given time.

[`func finalize(through: CMTime?) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/finalize(through:))

Finalizes the modules’ analyses.

### [Finishing analysis](https://developer.apple.com/documentation/speech/speechanalyzer\#Finishing-analysis)

[`func cancelAndFinishNow() async`](https://developer.apple.com/documentation/speech/speechanalyzer/cancelandfinishnow())

Finishes analysis immediately.

[`func finalizeAndFinishThroughEndOfInput() async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/finalizeandfinishthroughendofinput())

Finishes analysis after an audio input sequence has been fully consumed and its results are finalized.

[`func finalizeAndFinish(through: CMTime) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/finalizeandfinish(through:))

Finishes analysis after finalizing results for a given time-code.

[`func finish(after: CMTime) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/finish(after:))

Finishes analysis once input for a given time is consumed.

### [Determining audio formats](https://developer.apple.com/documentation/speech/speechanalyzer\#Determining-audio-formats)

[`static func bestAvailableAudioFormat(compatibleWith: [any SpeechModule]) async -> AVAudioFormat?`](https://developer.apple.com/documentation/speech/speechanalyzer/bestavailableaudioformat(compatiblewith:))

Retrieves the best-quality audio format that the specified modules can work with, from assets installed on the device.

[`static func bestAvailableAudioFormat(compatibleWith: [any SpeechModule], considering: AVAudioFormat?) async -> AVAudioFormat?`](https://developer.apple.com/documentation/speech/speechanalyzer/bestavailableaudioformat(compatiblewith:considering:))

Retrieves the best-quality audio format that the specified modules can work with, taking into account the natural format of the audio and assets installed on the device.

### [Improving responsiveness](https://developer.apple.com/documentation/speech/speechanalyzer\#Improving-responsiveness)

[`func prepareToAnalyze(in: AVAudioFormat?) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/preparetoanalyze(in:))

Prepares the analyzer to begin work with minimal startup delay.

[`func prepareToAnalyze(in: AVAudioFormat?, withProgressReadyHandler: sending ((Progress) -> Void)?) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/preparetoanalyze(in:withprogressreadyhandler:))

Prepares the analyzer to begin work with minimal startup delay, reporting the progress of that preparation.

### [Monitoring analysis](https://developer.apple.com/documentation/speech/speechanalyzer\#Monitoring-analysis)

[`func setVolatileRangeChangedHandler(sending ((CMTimeRange, Bool, Bool) -> Void)?)`](https://developer.apple.com/documentation/speech/speechanalyzer/setvolatilerangechangedhandler(_:))

A closure that the analyzer calls when the volatile range changes.

[`var volatileRange: CMTimeRange?`](https://developer.apple.com/documentation/speech/speechanalyzer/volatilerange)

The range of results that can change.

### [Managing contexts](https://developer.apple.com/documentation/speech/speechanalyzer\#Managing-contexts)

[`func setContext(AnalysisContext) async throws`](https://developer.apple.com/documentation/speech/speechanalyzer/setcontext(_:))

Sets contextual information to improve or inform the analysis.

[`var context: AnalysisContext`](https://developer.apple.com/documentation/speech/speechanalyzer/context)

An object containing contextual information.

## [Relationships](https://developer.apple.com/documentation/speech/speechanalyzer\#relationships)

### [Conforms To](https://developer.apple.com/documentation/speech/speechanalyzer\#conforms-to)

- [`Actor`](https://developer.apple.com/documentation/Swift/Actor)
- [`Sendable`](https://developer.apple.com/documentation/Swift/Sendable)
- [`SendableMetatype`](https://developer.apple.com/documentation/Swift/SendableMetatype)

## [See Also](https://developer.apple.com/documentation/speech/speechanalyzer\#see-also)

### [Essentials](https://developer.apple.com/documentation/speech/speechanalyzer\#Essentials)

[Bringing advanced speech-to-text capabilities to your app](https://developer.apple.com/documentation/speech/bringing-advanced-speech-to-text-capabilities-to-your-app)

Learn how to incorporate live speech-to-text transcription into your app with SpeechAnalyzer.

[`class AssetInventory`](https://developer.apple.com/documentation/speech/assetinventory)

Manages the assets that are necessary for transcription or other analyses.

Current page is SpeechAnalyzer

[Apple](https://www.apple.com/)

1. [Developer](https://developer.apple.com/)
2. [Documentation](https://developer.apple.com/documentation/)

### Platforms

Toggle Menu

- [iOS](https://developer.apple.com/ios/)
- [iPadOS](https://developer.apple.com/ipados/)
- [macOS](https://developer.apple.com/macos/)
- [tvOS](https://developer.apple.com/tvos/)
- [visionOS](https://developer.apple.com/visionos/)
- [watchOS](https://developer.apple.com/watchos/)

### Tools

Toggle Menu

- [Swift](https://developer.apple.com/swift/)
- [SwiftUI](https://developer.apple.com/swiftui/)
- [Swift Playground](https://developer.apple.com/swift-playground/)
- [TestFlight](https://developer.apple.com/testflight/)
- [Xcode](https://developer.apple.com/xcode/)
- [Xcode Cloud](https://developer.apple.com/xcode-cloud/)
- [SF Symbols](https://developer.apple.com/sf-symbols/)

### Topics & Technologies

Toggle Menu

- [Accessibility](https://developer.apple.com/accessibility/)
- [Accessories](https://developer.apple.com/accessories/)
- [App Extension](https://developer.apple.com/app-extensions/)
- [App Store](https://developer.apple.com/app-store/)
- [Audio & Video](https://developer.apple.com/audio/)
- [Augmented Reality](https://developer.apple.com/augmented-reality/)
- [Design](https://developer.apple.com/design/)
- [Distribution](https://developer.apple.com/distribute/)
- [Education](https://developer.apple.com/education/)
- [Fonts](https://developer.apple.com/fonts/)
- [Games](https://developer.apple.com/games/)
- [Health & Fitness](https://developer.apple.com/health-fitness/)
- [In-App Purchase](https://developer.apple.com/in-app-purchase/)
- [Localization](https://developer.apple.com/localization/)
- [Maps & Location](https://developer.apple.com/maps/)
- [Machine Learning & AI](https://developer.apple.com/machine-learning/)
- [Open Source](https://opensource.apple.com/)
- [Security](https://developer.apple.com/security/)
- [Safari & Web](https://developer.apple.com/safari/)

### Resources

Toggle Menu

- [Documentation](https://developer.apple.com/documentation/)
- [Tutorials](https://developer.apple.com/learn/)
- [Downloads](https://developer.apple.com/download/)
- [Forums](https://developer.apple.com/forums/)
- [Videos](https://developer.apple.com/videos/)

### Support

Toggle Menu

- [Support Articles](https://developer.apple.com/support/articles/)
- [Contact Us](https://developer.apple.com/contact/)
- [Bug Reporting](https://developer.apple.com/bug-reporting/)
- [System Status](https://developer.apple.com/system-status/)

### Account

Toggle Menu

- [Apple Developer](https://developer.apple.com/account/)
- [App Store Connect](https://appstoreconnect.apple.com/)
- [Certificates, IDs, & Profiles](https://developer.apple.com/account/ios/certificate/)
- [Feedback Assistant](https://feedbackassistant.apple.com/)

### Programs

Toggle Menu

- [Apple Developer Program](https://developer.apple.com/programs/)
- [Apple Developer Enterprise Program](https://developer.apple.com/programs/enterprise/)
- [App Store Small Business Program](https://developer.apple.com/app-store/small-business-program/)
- [MFi Program](https://mfi.apple.com/)
- [News Partner Program](https://developer.apple.com/programs/news-partner/)
- [Video Partner Program](https://developer.apple.com/programs/video-partner/)
- [Security Bounty Program](https://developer.apple.com/security-bounty/)
- [Security Research Device Program](https://developer.apple.com/programs/security-research-device/)

### Events

Toggle Menu

- [Meet with Apple](https://developer.apple.com/events/)
- [Apple Developer Centers](https://developer.apple.com/events/developer-centers/)
- [App Store Awards](https://developer.apple.com/app-store/app-store-awards/)
- [Apple Design Awards](https://developer.apple.com/design/awards/)
- [Apple Developer Academies](https://developer.apple.com/academies/)
- [WWDC](https://developer.apple.com/wwdc/)

To submit feedback on documentation, visit [Feedback Assistant](applefeedback://new?form_identifier=developertools.fba&answers%5B%3Aarea%5D=seedADC%3Adevpubs&answers%5B%3Adoc_type_req%5D=Technology%20Documentation&answers%5B%3Adocumentation_link_req%5D=https%3A%2F%2Fdeveloper.apple.com%2Fdocumentation%2Fspeech%2Fspeechanalyzer).

Select a color scheme preference
Light

Dark

Auto

Copyright © 2025 [Apple Inc.](https://www.apple.com/) All rights reserved.

[Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) [Privacy Policy](https://www.apple.com/legal/privacy/) [Agreements and Guidelines](https://developer.apple.com/support/terms/)