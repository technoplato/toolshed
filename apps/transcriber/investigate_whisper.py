from pywhispercpp.model import Model
from pywhispercpp import constants
import sys

def inspect_model():
    print("Loading model...")
    model = Model('base', print_realtime=False, print_progress=False)
    
    print("\nPARAMS_SCHEMA keys:")
    print(constants.PARAMS_SCHEMA.keys())
    
    # We need a small audio file.
    import glob
    wav_files = glob.glob("apps/transcriber/downloads/*.wav")
    if not wav_files:
        print("No wav files found to test.")
        return

    audio_path = wav_files[0]
    print(f"Transcribing {audio_path} with token_timestamps=True...")
    try:
        segments = model.transcribe(audio_path, n_threads=4, token_timestamps=True)
        
        if segments:
            print("Segment object attributes:")
            print(dir(segments[0]))
            print("\nSegment 0 content:")
            print(segments[0])
            
            # Check for tokens or words
            if hasattr(segments[0], 'tokens'):
                 print("\nTokens:")
                 print(segments[0].tokens)
            else:
                print("\nNo 'tokens' attribute found.")
                 
        else:
            print("No segments found.")
    except Exception as e:
        print(f"Error with token_timestamps=True: {e}")


if __name__ == "__main__":
    inspect_model()
