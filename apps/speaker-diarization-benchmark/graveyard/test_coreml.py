import coremltools as ct
import numpy as np
import os

model_path = os.path.expanduser("~/Library/Application Support/FluidAudio/Models/parakeet-tdt-0.6b-v3-coreml/Melspectrogram_15s.mlmodelc")

print(f"Loading model from {model_path}")
try:
    model = ct.models.MLModel(model_path)
    print("Model loaded successfully")
    
    # Inspect input description
    print("Input description:")
    print(model.input_description)
    
    # Create dummy input
    # Shape [1, 240000] (15s @ 16kHz)
    audio_signal = np.random.rand(1, 240000).astype(np.float32)
    audio_length = np.array([240000], dtype=np.int32)
    
    inputs = {
        "audio_signal": audio_signal,
        "audio_length": audio_length
    }
    
    print("Running prediction...")
    prediction = model.predict(inputs)
    print("Prediction successful!")
    print("Output keys:", prediction.keys())

except Exception as e:
    print(f"Error: {e}")
