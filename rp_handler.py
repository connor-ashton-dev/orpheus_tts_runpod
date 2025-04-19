import runpod
import time
from orpheus_tts import OrpheusModel
import wave
import base64

# Global variable to cache the model within a worker
model = None

def handler(event):
    global model # Use the global model variable
    print('worker start')

    # Initialize model on first call within the worker
    if model is None:
        print("Initializing OrpheusModel...")
        model = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")
        print("Model initialized.")

    input_data = event['input']

    prompt = input_data.get('prompt')
    # seconds = input_data.get('seconds', 0) # Removed as per previous edit

    if not prompt:
        return { "error": "Prompt is required" } # Add basic input validation

    print(f"Received prompt: {prompt}")

    start_time = time.monotonic()

    # Check if model is initialized before using
    if model is None:
        return { "error": "Model not initialized" } # Should not happen with the check above, but good practice

    syn_tokens = model.generate_speech(
        prompt=prompt,
        voice="tara",
    )

    output_filename = "output.wav"
    with wave.open(output_filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)

        total_frames = 0
        chunk_counter = 0
        for audio_chunk in syn_tokens: # output streaming
            chunk_counter += 1
            frame_count = len(audio_chunk) // (wf.getsampwidth() * wf.getnchannels())
            total_frames += frame_count
            wf.writeframes(audio_chunk)
        duration = total_frames / wf.getframerate()

        end_time = time.monotonic()
        print(f"It took {end_time - start_time:.2f} seconds to generate {duration:.2f} seconds of audio")

    # Read the generated wav file and encode it to base64
    with open(output_filename, "rb") as audio_file:
        encoded_audio = base64.b64encode(audio_file.read()).decode('utf-8')

    return encoded_audio # Return base64 string

if __name__ == '__main__':
    # Ensure return_aggregate_stream is False if returning single base64 output
    runpod.serverless.start({"handler": handler, "return_aggregate_stream": False })