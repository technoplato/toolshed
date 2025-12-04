# December 2 voice for forensics segment splitting hypotheses and exploration

## Table of Contents
- [Audio Ingestion CLI Design](#audio-ingestion-cli-design)
- [Segmentation & Diarization Hypotheses](#segmentation--diarization-hypotheses)
- [Manual Correction & Error Analysis](#manual-correction--error-analysis)
- [Agent Instructions & Progress Tracking](#agent-instructions--progress-tracking)
- [Full Text Source](#full-text-source)

## Audio Ingestion CLI Design

### User Requirements & Wonderings
*   **Core Goal**: A unified tool (`audio_ingestion`) to handle the entire audio processing pipeline.
*   **Verb-Based Interface**: The user envisions "verbs" (actions) like `transcribe`, `catalog`, `diarize`.
*   **Configuration**:
    *   Each verb needs specific flags (e.g., `--model` for transcription).
    *   Global flags like `--overwrite` and `--dry-run` are desired.
    *   Needs to handle dependencies (e.g., `catalog` might depend on `transcribe`).
*   **Reporting**:
    *   Must report time, cost, memory usage, and accuracy (if a gold standard exists).
    *   Needs clear error messaging for invalid flag combinations.
*   **Specific Actions**:
    *   **Transcribe**: Convert audio to text using models like `whisper-large-v3-turbo` (MLX) or `parakeet`.
    *   **Catalog**: Use ShazamKit to fingerprint audio and link to external URLs/IDs.
    *   **Diarize/Segment**: Split audio into speaker segments using strategies like `pyannote` or word-level embeddings.
    *   **Analyze**: (Implied) Analyze segments for manual correction.

### Feedback & Critique
*   **Structure**: The "verb" approach is best implemented as **subcommands** (e.g., `audio_ingestion transcribe ...`) rather than just flags. This allows for cleaner argument parsing where each subcommand has its own specific help and valid arguments.
*   **Consistency**: Global flags like `--dry-run` and `--verbose` should apply to all commands, while specific flags like `--model` should be scoped to the relevant subcommand.
*   **Dependencies**: The CLI should intelligently handle dependencies. If `catalog` requires a transcription and one doesn't exist, it should either error out clearly or (optionally) trigger the transcription step if configured to do so.
*   **Output**: Standardizing the output format (e.g., JSON for machine readability vs. rich text for humans) is crucial for the "Reporting" requirement.

### Consolidated API Design

A professional, elegant CLI design using a subcommand structure.

**Global Flags**:
*   `--verbose, -v`: Enable detailed logging.
*   `--dry-run`: Simulate actions without writing to disk or calling paid APIs.
*   `--config, -c`: Path to a configuration file (YAML/JSON) for default settings.

**Commands**:

#### 1. `transcribe`
Converts audio to text.
```bash
audio_ingestion transcribe <input_file> [flags]
```
*   `--model, -m`: Model to use (default: `whisper-large-v3-turbo`).
    *   *Choices*: `whisper-large-v3-turbo`, `parakeet`, `deepgram`.
*   `--overwrite`: Force re-transcription if output exists.
*   `--output-format`: Format of the output (default: `json`).
    *   *Choices*: `json`, `srt`, `vtt`, `txt`.

#### 2. `diarize` (or `segment`)
Splits audio into speaker segments.
```bash
audio_ingestion diarize <input_file> [flags]
```
*   `--strategy, -s`: Diarization strategy (default: `pyannote`).
    *   *Choices*: `pyannote`, `3d-speaker`, `word-level` (experimental).
*   `--min-speakers`: Minimum number of speakers (hint to model).
*   `--max-speakers`: Maximum number of speakers (hint to model).

#### 3. `catalog`
Fingerprints audio and updates the central catalog.
```bash
audio_ingestion catalog <input_file> [flags]
```
*   `--provider`: Catalog provider (default: `shazam`).
*   `--link-url`: External URL to associate with this audio.

#### 4. `report`
Generates a performance and cost report for a processed file.
```bash
audio_ingestion report <input_file> [flags]
```
*   `--gold-standard`: Path to a gold standard file for accuracy comparison.

### Example Usage
```bash
# Transcribe with a specific model
audio_ingestion transcribe interview.wav --model parakeet --overwrite

# Run a full pipeline (hypothetical 'run' command or chained commands)
audio_ingestion transcribe interview.wav && audio_ingestion diarize interview.wav
```

## Segmentation & Diarization Hypotheses

*   **Terminology**: Acknowledging the overlap between segmentation (splitting audio) and diarization (labeling speakers).
*   **Strategies**:
    *   **Word-Level Embedding**: A hypothesis to embed each word individually and compare with neighbors to find boundaries. Acknowledged as likely having poor performance ($O(n^2)$ implications) but worth exploring for precision.
    *   **Model Comparison**: Evaluate `pyannote 3.1`, `3D-Speaker`, and `Wespeaker`.
    *   **Sound Effect Identification**: A stretch goal to identify non-speech audio like laughter, crying, or clapping to auto-generate clips.
*   **Audio Cataloging**:
    *   Use **ShazamKit** to generate unique segment IDs and link them to external URLs.
    *   Maintain a "single speaker per segment" assumption.
    *   Avoid duplicating data; use the catalog to link to the database/graph.

## Manual Correction & Error Analysis

*   **The Problem**: Models often incorrectly identify a segment as having a single speaker when it contains multiple (e.g., `pyannote` failures).
*   **Workflow**:
    1.  **UI-Based Splitting**: Use the custom UI to manually split incorrect segments into multiple "Unknown" speaker segments.
    2.  **Labeling**: Manually assign the correct speaker identities.
    3.  **Tracking**: Keep a record of which segments were split and which model originally failed.
*   **Root Cause Analysis**: Investigate *why* the split failed (overlapping speech, low volume, specific audio characteristics) to improve future models.
*   **Gold Standard**: The ultimate goal is to create a 100% perfect "Gold Standard" dataset to benchmark and score the automated pipeline against.

## Agent Instructions & Progress Tracking

*   **File Documentation Standards**:
    *   **Mandatory Headers**: Agents must ensure all files have comprehensive comments/headers covering **Who, What, Where, Why, and How**.
    *   **Retroactive Documentation**: If a file is uncommented, the agent should add these headers, potentially seeding information from `git history`.
    *   **Maintenance**: Agents must keep these headers up-to-date as code changes (e.g., updating flags, usage instructions).
*   **Workflow Rules**:
    *   **Update `AGENTS.md`**: These instructions should be formalized in `AGENTS.md`.
    *   **Impact Analysis**: When changing flags or features, agents must `grep` to find and update old usages.
*   **Progress Tracking**:
    *   **Routine Updates**: Always run the `update_progress` script before moving to the next feature.
    *   **Global Access**: The `update_progress` script should be made globally accessible (e.g., via PATH) to facilitate easy usage.

## Full Text Source

December 2, voice forensics segment splitting. Hypotheses and exploration. And there's a crying baby. He's a crying baby. He's a crying baby. Baby, baby. He's a crying. There you go, baby. Um, okay, putting the baby to sleep and theorizing about... voice. And now, see... voice. All right. So... All right, so, um, didn't get too much time with our voice transcription, uh, workflow pipeline tonight. As I was busy with work doing work stuff. Um... So, But today was a productive day work, so that's okay. But what I did come up with was, okay, I want to be able to take a segment that has incorrectly been identified as A, a single segment with B. Uh, one speaker when obviously there should be multiple segments, so there should be multiple speakers. So what I want to do here, and this is with the pi and notes P-Y-A-N-N-O-T-E dot A-I, API. As far as I can tell, their best diarization model. And so I want to know why it fails in these sections. And I do need to time box this ultimate effort to a certain amount of time and really kind of move past this with the ability to easily update once I improve and have time to look into this, the different steps, um, of the audio ingestion pipelines. So transcription is more or less solved. Um, even open source models are just phenomenal. Um, I want to try out with uh, parakeet. Um, and see if there's any other top of the line, fast accurate models. Accuracy is most important, and then speed. Um, for me, and they've got to run on a Mac. You don't have to, but I just, I think I want to turn my laptop into a server. Or run a server on my laptop, I guess, I should say. But anyway, that's neither here nor there, but I want to be able to run this ingestion. Um, like just, I guess I should, instead of calling the script benchmark baseline, I should call it, um, uh, audio underscore ingestion, and have it, um, allow you to pass flags for, uh, transcribe, and then, you know, overwrite transcription, which would overwrite a cast transcription for the model that you've passed in, and if you pass transcription, you have to pass. Um, what model you want to transcribe in, and then, um, by default, it'll just print it out to the standard out, and then you have to pass in, um, you know, save transcription. I don't know. probably a better way to do that. Um, but I think just specifying what verb you want and then some config for that verb. Um, seems most straightforward and just throw air messages to the user or just display error messages to the user, saying if you pass in this flag, you need to do this or that and just kind of account for all the different cases there. Um, so there's a transcription. Um, and then you do pass a model, and so you can either pass, you know, uh, whisper. Large turbo V3 and I'm using whispered turbo. MLX, which I think uses Apple Silicon and takes advantage of that. Really not positive, but I think that's what it does. Um, I'll kind of have to do a little bit more research there, but that's my, that's the whisper library I'm using, and then I think you have to get models that are compatible with that thing. Got to kind of test all these different hypotheses and ideas and really solidify them too. But anyway, so you pass in a model, you say parakeet, or whisper large V3 terabao, or whatever. model. And that has to correlate with whatever models we have available to us and we know how to map. Um, so right now, those are gonna be the only two. Um, and then maybe you could do, uh, so that's, that's, uh, transcribed, that turns audio, spoken audio into text. And then you can have, uh, audio fingerprint or audio catalog. Um, and that would add the audio fingerprint to the, uh, uh, growing catalog using Shazam kit under the hood. Um, and so what that would do is, take the transcription, and assuming that already exists, if, um, Yeah, they would have to take some some assumptions. Um, the assumptions, if you pass in audio catalog, is that your fuck, I don't know. Um, update audio catalog. We'll take the words. Um, and or maybe the seconds. Of an audio clip or the words, I don't know. Um, And um, I forget how I was doing it in, uh, what do I, what do I call it? Proof of listening. Project for the Salana Grizzly film. Um, I've got some sample code that works here with the Swift server. Um, and, uh, I think it's called Ketura. It was a Swift Web socket server thing. Anyway. Um, it doesn't have to be that, but, uh, Maybe it's the easiest way to access the Shazam stuff or you'd have to map it over Python. And have the Swift calls the Python bindings. I don't know, whatever. Do what you do. Um, So that would take that and then associate, I guess you just associate the segment ID. I guess the ultimate decision is we want to require We're going to make the trade-off that, uh, using ShazamKit will give you IDs for segments, which then can be, uh, you can ask the database about, but we're not going to duplicate our data across ShazamKit and our database that just doesn't make any sense. So, realistically, Once we have a transcription, then, And yeah, so we're going to assume that a speaker segment is spoken by a single speaker. That's going to be the ultimate goal. And then once you look, you're going to get a speaker segment, ID from ShazamKit. Given, you're gonna get, well, as you as you stream. Um, Um, as you stream audio, you're going to continually get, uh, an updated range of, um, of, uh, speaker segment IDs. Uh, and then you can do whatever you want to with those and you'll, You get a new speaker segment ID and then it'll have the, the link to the external URL to the video. The IDs of the speakers speaking, the external URLs of those speakers. Um, the metadata about them, you know, whatever you want to query from the uh, instant DB graph, you'll be able to query those things. Um, and so that is solved for the audio cataloguing phase, which audio cataloguing is, and then we'll have to have the help there in the art parser. Um, with a nice, long, triple coated string description of what, uh, what that is. Examples of what happens once you pass that flag. how to use the, um, downstream, how to use the audio catalog, what API is to call, what's a recall, and keep that up to date. Um, I also have to tinker with the agent instructions to always add, uh, Um, upon starting any work and investigating any files, if the files aren't commented, um, the files need to be commented with the who it, and where, why, why, why, how? Um, and then we need to provide instructions for the agents to look at those and keep those up to date with changes. Um, and then they can maybe even cede that comment with uh, with a look at the get history. Um, ideally, that's a subagent, but anyway, right now, it'll just all be in the agent.md file. Um, And make sure to keep that up to date, you know, instructions in the comment and things like that as you change, um, important things like flags or add new flags or whatever, always do a, do a grip to see if they're, if the old flag that you change is anywhere. Um, that you need to update or anything. And, um, keep a running log of the, on the where, the where is also always nice that you don't have to, You can just go to the top of the file and see where, you know, where the file is used now. Is that actually gonna work? It's gonna be decent. I need improvement, just like everything else, but it's a good start. Um, So we have transcription, we have cataloguing. Oh, well, we need segmentation then. So that's where, uh, I don't really know the difference. I think they're actually the same thing. segmentation and diarization, because if you can segment something, I guess diarization is a subset of segmentation, where you're labeling a distinct piece of a segment of audio during which an individual was speaking. And there could be multiple individuals speaking. Um, but, uh, Uh, yeah, okay. And that segmentation, or we'll call it diarization phase. We'll say diarize and diarize will need to take a, uh, um, a strategy as well. Um, And so you can say, you know, things are pi in a 3.one community. Buy a note API, latest and greatest, whatever that's called. It's like, Clarity 2 or something, dummy, I mean like that. Um, there's 3D speaker, there's we speaker, there's all kinds of different stuff. Um, I naively thought it would be a good idea to, Just do it word by word. Um, but that didn't work so well. Um, and just embed each word audio section. And then compare that, I guess the comparison there is the rub. Um, you have to be looking out for like oven squared here or, And yeah, I think there's some terrible performance implications here. But there are better ideas. I just don't know what they are, but I thought that, looking at each word, embedding each word, and then looking at the next word and embedding that word, and are those 2 embeddings nearby? If so, include the next word in the segment, and continue doing that. Until you get to a word where, uh, the embeddings are not similar, and then you start a new segment, and then you look, and you see, okay, is this, is this word similar to that word? And you just do that. That's terrible performance and there's probably some optimizations there. But, uh, that's what I was thinking. So anyway, segmentation strategy. Or diarization strategy. Um, and then... speaker identification. I also want a sound effect identification. I think there's some models that do that, so it would be nice to kind of identify clips where there was increased laughter. Um, that could be good for uh, automatically creating clips of new, you know, comedy podcasts or things like that. Um, increased laughter, clapping, crying, screaming, you know, uh, water running. These kinds of things are interesting, but it's not super important and that's a stretch goal. But once you have this pipeline in a way where, you know, you have to be very careful, you have to be very explicit, you want to actually overwrite something, and then, you know, you always kind of get the dry run option as well. You pass dryer on it, overwrites all options to save data to disk and just print it all out to standard out. It doesn't even send to a text file. Or I guess you could say dry run text file as well and save it to a text file and then look at all that. Um, the report will include, um, time for each step in the workflow that you've that you've specified in your flags. Um, Uh, Cost, if you're using an API, time to run each step. Um, so each step is gonna output its, uh, It's information. Um, Uh, memory usage. Cost. Time. And if you have a gold standard, Um, performance against the gold standard. And then have some way of scoring like performance against the gold standard. And that's a pretty good uh, cataloguing, um, I'll just call it audio workflow. And then you have all those different flags. And then so, um, speaker labeling will take an existing, I guess it'll take a strategy, but the only strategy I have right now is a JSON file of speaker embeddings. Or I guess I have a JSON file with, uh, obviously just an arbitrary name. And then that points to a list of embeddings, which is not super efficient, but it's just, uh, workflow code. Um, It's just a kind of work in progress code, well, we learn. Um, eventually be nice to pre-compute and and not dynamically computer, I don't think is the right word, but computer in advance, the, there's something called a centroid, I think, and there's, um, there's something called nearest neighbors that I've learned about so far. I don't know what other strategies there are for speaker embeddings, but they'll be worth investigating. Um, And so we want to, um, We want to, um, have a, uh, identify speakers. Step. I don't know if there's any flags that you can really pass to that. Um, maybe like, Like, do you save the new segment? to the embeddings if it's a match? Is that worth it? Or is that just clutter? Is it like, hey, this is a, this is close. So save it. don't really know. Um, and then does segments need to be linked back out? I think segment segments need to have IDs clearly. Um, And then every word in a segment was spoken by the same user. And so there, it seems like a reasonable, um, workflow, audio workflow, I think. Audio catalogging, audio. Recognition. Audio recognition? Yeah, I'm not going to get cute with names because it'd just be too confusing. But say you have transcribed? And then again, with model. Save the file. Save to database, save to whatever, for whatever reason we have a manifest.js on file with all this stuff in it right now. Um, You have a model. You have a gold standard maybe transcript. And each of these flags need to be suffixed with something like underscore trans- gript, like gold standard transcript for the transcribed stage. Gold standard speaker identification for the speaker identification stage. Gold standard segmentation for the segmentations, et cetera. Um. And then this last little part here is the part that's actually going to come next. And that is, During my analysis and research, I've created a little UI where I can go through and actually, uh, identify, I can, um, Um, open a web page and go through and label this un, the unknown speaker labels with who's actually speaking from that piece of audio content. And I added a feature just now. This is the latest thing I've added. Which that reminds me, I need to add that to the agents.md as well. Always update progress once you move before you move on to the next feature. Call the update progress script, and then I need to make that more global. But anyway, Um, I've created the ability to Split a segment into multiple unknown speakers. But what is really important there is we keep track of the segments I've split. What they were originally, what model originally identified them as one segment. And then I want to do audio analysis on that piece of that segment itself. and see why it was problematic. Because I'm just, I think the tools are going to be powerful enough to create audio analysis. Um, Functions and graphs and things like that. Um, And, uh, yeah. So I want to try that out. and look at those, you know, Um, look at those segments that were originally marked as one, and then I will, by hand, go through and separate those segments out into uh, more than one segment. And then provide the right speaker identity. So that now we have multiple segments from what was originally identified as one segment, with the correct speaker labeled, so that we can look at our embeddings, we could look at our the audio fingerprint itself. And we can say, hey, this was, uh, Here's the reason why. This wasn't identified properly and then how to proceed in the in the future. Was it the transcription? Was it the segmentation phase? Was it the algorithm we used? What exactly was going on with this piece of audio? Is it too quiet? Is the Texas, the Texas overlapping? So it's going to sound different. but is overlapping text getting incorrectly identified as, you know, one person speaking and something's going wrong there. Um, Anyway. And so there's there's only a reasonable amount of time I can I can actually spend on this. Because in general, uh, even my open source solutions are fairly good. They create a lot more segments, so there's some something going on there. Um, Whereas when I sent off to these APIs, both Deep Gram and the Pi a note API, it correctly labeled, I think, 4 speakers. So anyway, it's that analysis of segments that I've needed to mainly manually break break up and break down. And for the gold standards. Um. It'll be good to get these 100% perfect. So, I'm gonna go do some research now and put this baby to sleep, and, uh, gonna copy this into an LLM and have it organize it into different, uh, text documents based on the different topics. No more than three. Good day.