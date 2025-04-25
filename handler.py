import audioop
import base64
import json
import sys

import runpod
from orpheus_tts import OrpheusModel

# Initialize the model
generator = None

ORIG_SR = 24_000
TARGET_SR = 8_000
SAMPLE_W = 2
FRAME_BYTES = 160  # 20 ms @ 8 kHz μ-law


def init():
    global generator
    if generator is None:
        generator = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")


def text_to_speech_generator(text: str, voice: str = "tara"):
    init()
    rate_state = None
    pending = b""

    print(f"[DEBUG] Starting TTS for: {text}")

    for idx, pcm24 in enumerate(generator.generate_speech(prompt=text, voice=voice)):
        print(f"[DEBUG] Chunk #{idx}: {len(pcm24)} bytes raw PCM24")
        pcm8, rate_state = audioop.ratecv(
            pcm24, SAMPLE_W, 1, ORIG_SR, TARGET_SR, rate_state
        )
        print(f"[DEBUG] → {len(pcm8)} bytes resampled PCM8")

        ulaw = audioop.lin2ulaw(pcm8, SAMPLE_W)
        print(f"[DEBUG] → {len(ulaw)} bytes μ-law")

        # accumulate
        pending += ulaw
        print(f"[DEBUG] pending buffer: {len(pending)} bytes")

        # emit only full 160-byte frames
        frame_count = 0
        while len(pending) >= FRAME_BYTES:
            frame, pending = pending[:FRAME_BYTES], pending[FRAME_BYTES:]
            frame_count += 1
            print(
                f"[DEBUG] yielding frame #{frame_count} (160 bytes), pending now {len(pending)} bytes"
            )
            yield {
                "status": "processing",
                "audio": base64.b64encode(frame).decode("utf-8"),
            }

    # flush leftover (pad with µ-law silence 0xFF)
    if pending:
        print(
            f"[DEBUG] flushing leftover tail of {len(pending)} bytes, padding to {FRAME_BYTES}"
        )
        pending += b"\xff" * (FRAME_BYTES - len(pending))
        yield {
            "status": "processing",
            "audio": base64.b64encode(pending).decode("utf-8"),
        }
    else:
        print("[DEBUG] no leftover tail to flush")

    print("[DEBUG] generator completed")
    yield {"status": "completed", "message": "Text-to-speech conversion completed"}


def generator_handler(job):
    job_input = job["input"]
    text = job_input.get("text", "")
    speaker = job_input.get("speaker", "tara")

    if not text:
        yield {"status": "error", "error": "No text provided"}
        return

    print(f"TTS Generator | Starting job {job['id']}")
    print(f"Processing text: {text}")

    for result in text_to_speech_generator(text, speaker):
        # echo the status in logs
        print(f"[DEBUG] emit status: {result['status']}")
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
        runpod.serverless.start(
            {
                "handler": generator_handler,
                "return_aggregate_stream": True,  # This ensures the stream results are returned in /run and /runsync
            }
        )
