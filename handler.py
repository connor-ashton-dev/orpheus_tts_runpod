import runpod
import base64
from orpheus_tts import OrpheusModel
import json
import sys
import audioop

# Initialize the model
generator = None

def init():
    global generator
    if generator is None:
        generator = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")

def text_to_speech_generator(text, voice="tara"):
    """
    Generator function that yields audio chunks as they're generated
    """
    init()
    
    # Process audio chunks as they're generated
    audio_bytes = generator.generate_speech(
            prompt=text,
            voice=voice,
    )
    for audio_chunk in audio_bytes:
        # Convert PCM chunk to 8-bit μ-law
        mu_law_chunk = audioop.lin2ulaw(audio_chunk, 2)
        audio_base64 = base64.b64encode(mu_law_chunk).decode('utf-8')
        
        yield {
            "status": "processing",
            "audio": audio_base64,
        }
    
    yield {
        "status": "completed",
        "message": "Text-to-speech conversion completed"
    }

def generator_handler(job):
    """
    The main handler function that will be called by RunPod
    """
    job_input = job['input']
    text = job_input.get('text', "")
    speaker = job_input.get('speaker', "tara")
    
    if not text:
        yield {
            "status": "error",
            "error": "No text provided"
        }
        return
    
    print(f"TTS Generator | Starting job {job['id']}")
    print(f"Processing text: {text}")
    
    for result in text_to_speech_generator(text, speaker):
        yield result

if __name__ == "__main__":
    if "--test_input" in sys.argv:
        test_input_index = sys.argv.index("--test_input")
        if test_input_index + 1 < len(sys.argv):
            test_input_json = sys.argv[test_input_index + 1]
            try:
                job = json.loads(test_input_json)
                gen = generator_handler(job)
                for item in gen:
                    print(json.dumps(item))
            except json.JSONDecodeError:
                print("Error: Invalid JSON in test_input")
        else:
            print("Error: --test_input requires a JSON string argument")
    else:
        runpod.serverless.start({
            "handler": generator_handler,
            "return_aggregate_stream": True  # This ensures the stream results are returned in /run and /runsync
        }) 