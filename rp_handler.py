import runpod
import time
import numpy as np
from kokoro import KPipeline
import base64
# import io # Not needed for direct numpy to base64
# import wave # Not needed for direct numpy to base64

# --- Configuration ---
KOKORO_SAMPLE_RATE = 24000
DEFAULT_KOKORO_LANG = 'a'
DEFAULT_KOKORO_VOICE = 'af_heart'

# --- Load model at startup, outside the handler ---
print(f"Initializing Kokoro Pipeline globally (lang_code='{DEFAULT_KOKORO_LANG}')...")
try:
    # Initialize the pipeline in the global scope
    kokoro_pipeline = KPipeline(lang_code=DEFAULT_KOKORO_LANG)
    print("Global pipeline initialized successfully.")
except Exception as e:
    print(f"FATAL: Failed to initialize global Kokoro Pipeline: {e}")
    # If the pipeline fails globally, the worker might be unhealthy.
    # You might want to exit or handle this state appropriately.
    kokoro_pipeline = None 
    # exit(1) # Optionally exit if global init fails

# --- RunPod Handler ---
def handler(job):
    """
    RunPod serverless handler function.
    Takes text input and streams Kokoro TTS audio chunks (base64 encoded).
    Uses the globally initialized pipeline, re-initializes only if lang_code changes.
    """
    global kokoro_pipeline

    # Check if global initialization failed
    if kokoro_pipeline is None:
        yield {"error": "Kokoro pipeline is not available (failed global initialization)."}
        return

    job_input = job.get('input', {})
    text = job_input.get('text', "Hello from Kokoro TTS on RunPod!")
    lang_code = job_input.get('lang_code', DEFAULT_KOKORO_LANG)
    voice = job_input.get('voice', DEFAULT_KOKORO_VOICE)
    speed = job_input.get('speed', 1.0)

    print(f"Job {job.get('id', 'N/A')}: Processing text '{text[:50]}...'")
    print(f"Using lang: {lang_code}, voice: {voice}, speed: {speed}")

    start_time = time.monotonic()

    try:
        # Re-initialize pipeline *only if* the requested language code is different
        # and the global pipeline is currently valid
        current_pipeline_lang = getattr(getattr(kokoro_pipeline, 'hps', None), 'lang_code', None)
        if current_pipeline_lang != lang_code:
            print(f"Language changed ('{current_pipeline_lang}' -> '{lang_code}'). Reinitializing Kokoro Pipeline...")
            try:
                kokoro_pipeline = KPipeline(lang_code=lang_code) # Re-assign the global variable
                print("Pipeline reinitialized successfully.")
            except Exception as e:
                 print(f"ERROR: Failed to reinitialize pipeline for lang '{lang_code}': {e}")
                 yield {"error": f"Failed to switch language to {lang_code}: {e}"}
                 return # Stop processing if re-init fails

        # Generate audio chunks using the (potentially re-initialized) global pipeline
        generator = kokoro_pipeline(
            text,
            voice=voice,
            speed=speed
        )

        total_duration_yielded = 0.0
        chunk_count = 0
        first_chunk_yielded = False

        for i, (gs, ps, audio_array) in enumerate(generator):
            if audio_array is not None and len(audio_array) > 0:
                # Convert torch.Tensor to numpy array
                audio_np_array = audio_array.cpu().numpy() # type: ignore

                if not first_chunk_yielded:
                    time_to_first_chunk = time.monotonic() - start_time
                    print(f"Time to first audio chunk: {time_to_first_chunk:.2f}s")
                    first_chunk_yielded = True

                # Convert numpy array (float32) to bytes (int16)
                audio_int16 = (audio_np_array * 32767).astype(np.int16) # type: ignore

                # Encode bytes to base64
                encoded_chunk = base64.b64encode(audio_int16.tobytes()).decode('utf-8')

                # Yield the chunk
                yield {"audio_chunk_base64": encoded_chunk}

                chunk_duration = len(audio_np_array) / KOKORO_SAMPLE_RATE
                total_duration_yielded += chunk_duration
                chunk_count += 1

        end_time = time.monotonic()
        print(f"Finished processing job {job.get('id', 'N/A')}.")
        print(f"Yielded {chunk_count} chunks, total duration ~{total_duration_yielded:.2f}s in {end_time - start_time:.2f}s.")

        # Yield final status (optional)
        yield {"status": "completed"}

    except Exception as e:
        print(f"Error during processing job {job.get('id', 'N/A')}: {e}")
        yield {"error": str(e)}


if __name__ == "__main__":
    # This block now only starts the server or handles local testing
    # Pipeline initialization happens above, when the script is loaded.
    import sys
    import json

    if "--test_input" in sys.argv:
        # ... (local testing code remains the same) ...
        test_input_index = sys.argv.index("--test_input")
        if test_input_index + 1 < len(sys.argv):
            test_input_json = sys.argv[test_input_index + 1]
            print(f"Local testing with input: {test_input_json}")
            try:
                job = json.loads(test_input_json)
                generator_output = handler(job)
                print("--- Handler Output --- ")
                for item in generator_output:
                    print(json.dumps(item))
                print("--- End Handler Output --- ")
            except json.JSONDecodeError:
                print("Error: Invalid JSON provided for --test_input")
            except Exception as e:
                print(f"Error during local handler execution: {e}")
        else:
            print("Error: --test_input requires a JSON string argument")
    else:
        print("Starting RunPod Serverless Worker for Kokoro TTS (Pipeline initialized globally)...")
        runpod.serverless.start({"handler": handler})