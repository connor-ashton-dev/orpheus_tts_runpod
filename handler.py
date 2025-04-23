import runpod
from orpheus_tts import OrpheusModel

engine = None # Initialize lazily

def generator_handler(job):
    global engine # Declare intent to modify global engine
    if engine is None:
        print("Initializing OrpheusModel...")
        engine = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")
        print("OrpheusModel initialized.")

    job_input = job['input']
    text = job_input.get('text', "Welcome to RunPod's text-to-speech simulator!")
    
    print(f"TTS Simulator | Starting job {job['id']}")
    print(f"Processing text: {text}")
    
    syn_tokens = engine.generate_speech(
            prompt=text,
            voice="tara",
            repetition_penalty=1.1,
            stop_token_ids=[128258],
            max_tokens=2000,
            temperature=0.4,
            top_p=0.9
        )
    
    for audio_chunk in syn_tokens:
        yield {"status": "processing", "chunk": audio_chunk}
    
    yield {"status": "completed", "message": "Text-to-speech conversion completed"}

if __name__ == "__main__":
    # Model initialization is now deferred until the handler runs
    runpod.serverless.start({"handler": generator_handler})