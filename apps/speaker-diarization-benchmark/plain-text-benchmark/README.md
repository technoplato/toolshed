# Plain Text Benchmark

This directory contains the "text in, text out" benchmark for speaker diarization and segmentation.

## Goal
To benchmark different segmentation, diarization, and transcription workflows by outputting a standardized text file containing:
- Workflow metadata (commit, model, arguments)
- Full transcription
- Segmentation details (start/end times, speaker ID, text)

## Usage
Run the benchmark script (to be created) with a target audio clip.

## Output Format
The output will be a plain text file prefixed with `plain_text_transcription_`.
