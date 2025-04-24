import runpod
import torch
import torchaudio
from csm_streaming.generator import load_csm_1b
import io
import base64
import json
import sys

# Initialize the model
generator = None

def init():
    global generator
    if generator is None:
        generator = load_csm_1b("cuda")

def text_to_speech_generator(text, speaker=0, context=None):
    """
    Generator function that yields audio chunks as they're generated
    """
    init()
    
    # Process audio chunks as they're generated
    for audio_chunk in generator.generate_stream(
        text=text,
        speaker=speaker,
        context=context or []
    ):
        # Convert chunk to bytes
        buffer = io.BytesIO()
        torchaudio.save(buffer, audio_chunk.unsqueeze(0), generator.sample_rate, format="wav")
        audio_bytes = buffer.getvalue()
        
        # Convert to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        yield {
            "status": "processing",
            "audio": audio_base64,
            "sample_rate": generator.sample_rate
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
    speaker = job_input.get('speaker', 0)
    context = job_input.get('context', [])
    
    if not text:
        yield {
            "status": "error",
            "error": "No text provided"
        }
        return
    
    print(f"TTS Generator | Starting job {job['id']}")
    print(f"Processing text: {text}")
    
    for result in text_to_speech_generator(text, speaker, context):
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
        runpod.serverless.start({"handler": generator_handler}) 