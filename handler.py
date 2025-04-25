import runpod
import base64
from orpheus_tts import OrpheusModel
import json
import sys
import audioop

# Initialize the model
generator = None

ORIG_SR = 24_000
TARGET_SR = 8_000
SAMPLE_W = 2

def init():
    global generator
    if generator is None:
        generator = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")

def text_to_speech_generator(text: str, voice: str = "tara"):
    init()

    rate_state = None
    for pcm24 in generator.generate_speech(prompt=text, voice=voice):
        # 1. resample – preserve rate_state across calls
        pcm8, rate_state = audioop.ratecv(pcm24, SAMPLE_W, 1, ORIG_SR, TARGET_SR, rate_state)

        # 2. PCM -> μ-law conversion
        ulaw = audioop.lin2ulaw(pcm8, SAMPLE_W)

        # 3. split into 20ms / 160-byte frames
        while len(ulaw) >= 160:
            frame, ulaw = ulaw[:160], ulaw[160:]
            yield {
                "status": "processing",
                "audio": base64.b64encode(frame).decode('utf-8'),
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