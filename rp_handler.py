import runpod
import time
import re
import json
import sys
import numpy as np
import base64
from kokoro import KPipeline

# --- Configuration ---
KOKORO_SAMPLE_RATE = 24000
DEFAULT_KOKORO_LANG = 'a'
DEFAULT_KOKORO_VOICE = 'af_heart'

# --- Initialize global pipeline ---
print(f"Initializing Kokoro Pipeline globally (lang_code='{DEFAULT_KOKORO_LANG}')...")
try:
    kokoro_pipeline = KPipeline(lang_code=DEFAULT_KOKORO_LANG)
    print("Global pipeline initialized successfully.")
except Exception as e:
    print(f"FATAL: Failed to initialize global Kokoro Pipeline: {e}")
    kokoro_pipeline = None

# --- RunPod Handler ---
def generator_handler(job):
    """
    RunPod serverless handler.
    Streams Kokoro TTS audio chunks (base64 encoded) using a global pipeline.
    """
    global kokoro_pipeline

    if kokoro_pipeline is None:
        yield {"error": "Kokoro pipeline is not available (global init failed)."}
        return

    # Extract inputs
    job_input = job.get('input', {})
    text = job_input.get('text', "Hello from Kokoro TTS on RunPod!")
    lang_code = job_input.get('lang_code', DEFAULT_KOKORO_LANG)
    voice = job_input.get('voice', DEFAULT_KOKORO_VOICE)
    speed = job_input.get('speed', 1.0)

    print(f"Job {job.get('id','N/A')}: Processing text '{text[:50]}...' ")
    print(f"Using lang: {lang_code}, voice: {voice}, speed: {speed}")

    start_time = time.monotonic()

    # Reinitialize pipeline if language changed
    current_lang = getattr(getattr(kokoro_pipeline, 'hps', None), 'lang_code', None)
    if current_lang != lang_code:
        print(f"Language change detected ('{current_lang}' -> '{lang_code}'), reinitializing pipeline...")
        try:
            kokoro_pipeline = KPipeline(lang_code=lang_code)
            print("Pipeline reinitialized successfully.")
        except Exception as e:
            print(f"ERROR: Failed to reinit for lang '{lang_code}': {e}")
            yield {"error": f"Failed to switch language: {e}"}
            return

    # Generate and stream audio chunks
    chunk_count = 0
    total_duration = 0.0

    try:
        for i, (gs, ps, audio_array) in enumerate(kokoro_pipeline(text, voice=voice, speed=speed)):
            if audio_array is None or (hasattr(audio_array, 'size') and len(audio_array) == 0):
                continue

            # Time to first chunk log
            if chunk_count == 0:
                print(f"Time to first audio chunk: {time.monotonic() - start_time:.2f}s")

            # Convert to numpy array, handling both torch.Tensor and numpy.ndarray
            if hasattr(audio_array, 'cpu'):
                audio_np = audio_array.cpu().numpy().astype(np.float32) # type: ignore[attr-defined]
            else:
                audio_np = np.array(audio_array, dtype=np.float32)

            # Scale float32 [-1,1] to int16
            audio_int16 = (audio_np * 32767).astype(np.int16)
            encoded = base64.b64encode(audio_int16.tobytes()).decode('utf-8')

            yield {"audio_chunk_base64": encoded}

            duration = len(audio_np) / KOKORO_SAMPLE_RATE
            total_duration += duration
            chunk_count += 1

        print(f"Finished job {job.get('id','N/A')}: {chunk_count} chunks, ~{total_duration:.2f}s audio in {time.monotonic()-start_time:.2f}s.")
        yield {"status": "completed"}

    except Exception as e:
        print(f"Error during job {job.get('id','N/A')}: {e}")
        yield {"error": str(e)}


if __name__ == "__main__":
    # Local test harness
    if "--test_input" in sys.argv:
        idx = sys.argv.index("--test_input")
        if idx + 1 < len(sys.argv):
            try:
                job = json.loads(sys.argv[idx+1])
                print(f"Local test input: {job}")
                for out in generator_handler(job):
                    print(json.dumps(out))
            except json.JSONDecodeError:
                print("Error: Invalid JSON for --test_input")
        else:
            print("Error: --test_input requires a JSON argument.")
    else:
        print("Starting RunPod Serverless Worker for Kokoro TTS...")
        runpod.serverless.start({"handler": generator_handler})