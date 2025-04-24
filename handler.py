import os, base64, runpod
from orpheus_tts import OrpheusModel

# ─── one-time model load ────────────────────────────────────────────────────────
model = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")

# ─── streaming handler ─────────────────────────────────────────────────────────
def generator_handler(job):
    """
    Input  -> {"text": "...", "voice": "tara", "hf_token": "⟨optional⟩"}
    Output -> incremental JSON objects with base-64 chunks.
    """
    inp   = job["input"]
    text  = inp["text"]
    voice = inp.get("voice", "tara")

    for audio_chunk in model.generate_speech(prompt=text, voice=voice):
        yield {"status": "processing",
               "audio_chunk": base64.b64encode(audio_chunk).decode()}

    yield {"status": "completed"}

# ─── start the worker ──────────────────────────────────────────────────────────
runpod.serverless.start({"handler": generator_handler})
