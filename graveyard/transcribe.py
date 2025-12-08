# NOTE: The only combination of transcription we should be using is mlx-community/whisper-large-v3-turbo.
# Do not change this model configuration without explicit approval.

import mlx_whisper
from pydantic import BaseModel, Field
from typing import List, Optional

MODEL_NAME = "mlx-community/whisper-large-v3-turbo"

class Word(BaseModel):
    word: str
    start: float
    end: float
    probability: float

class Segment(BaseModel):
    start: float
    end: float
    text: str
    words: List[Word] = Field(default_factory=list)
    speaker: Optional[str] = "UNKNOWN"

class TranscriptionResult(BaseModel):
    text: str
    segments: List[Segment]
    language: str = "en"

def transcribe(audio_path: str) -> TranscriptionResult:
    """
    Transcribes the given audio file using mlx_whisper with the standardized model.
    Returns a structured TranscriptionResult.
    """
    print(f"Transcribing {audio_path} with {MODEL_NAME}...")
    
    # Run transcription with word timestamps
    result = mlx_whisper.transcribe(
        audio_path, 
        path_or_hf_repo=MODEL_NAME, 
        word_timestamps=True
    )
    
    # Parse into Pydantic models
    segments = []
    for seg in result.get('segments', []):
        words = []
        if 'words' in seg:
            for w in seg['words']:
                words.append(Word(
                    word=w['word'],
                    start=w['start'],
                    end=w['end'],
                    probability=w.get('probability', 0.0)
                ))
        
        segments.append(Segment(
            start=seg['start'],
            end=seg['end'],
            text=seg['text'].strip(),
            words=words
        ))
        
    return TranscriptionResult(
        text=result.get('text', "").strip(),
        segments=segments,
        language=result.get('language', "en")
    )

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file>")
        sys.exit(1)
        
    audio_file = sys.argv[1]
    try:
        transcription = transcribe(audio_file)
        print(json.dumps(transcription.model_dump(), indent=2))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
