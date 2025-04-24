# CSM Streaming TTS RunPod Endpoint

This repository contains a RunPod serverless endpoint for the CSM (Conditional Speech Model) streaming TTS model.

## Setup

1. Clone this repository
2. Build and deploy the Docker container to RunPod
3. Configure the endpoint with appropriate GPU settings (recommended: A100 or similar)

## Usage

The endpoint accepts POST requests with the following JSON structure:

```json
{
  "input": {
    "text": "The text to convert to speech",
    "speaker": 0, // Optional: speaker ID (default: 0)
    "context": [] // Optional: context segments
  }
}
```

The response will be a JSON object containing:

```json
{
  "audio": "base64_encoded_audio_data",
  "sample_rate": 24000
}
```

## Example Python Client

```python
import runpod
import base64
import io
import torchaudio
import sounddevice as sd
import numpy as np

# Initialize RunPod client
runpod.api_key = "YOUR_RUNPOD_API_KEY"
endpoint = runpod.Endpoint("YOUR_ENDPOINT_ID")

# Prepare input
input_data = {
    "text": "Hello, this is a test of the CSM streaming TTS model.",
    "speaker": 0
}

# Call the endpoint
result = endpoint.run_sync(input_data)

if "error" in result:
    print(f"Error: {result['error']}")
else:
    # Decode the audio
    audio_bytes = base64.b64decode(result["audio"])
    audio_buffer = io.BytesIO(audio_bytes)
    audio_tensor, sample_rate = torchaudio.load(audio_buffer)

    # Play the audio
    audio_np = audio_tensor.numpy().squeeze()
    sd.play(audio_np, sample_rate)
    sd.wait()
```

## Notes

- The model requires a GPU with CUDA support
- The endpoint uses the CSM-1B model from the original repository
- Audio is returned as base64-encoded WAV data
- The sample rate is 24000 Hz
