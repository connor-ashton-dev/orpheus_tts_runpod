import base64
import json
import sys

import numpy as np
import runpod
import torch
import torchaudio
from orpheus_tts import OrpheusModel

# Constants
ORIG_SR = 24_000
TARGET_SR = 8_000
FRAME_BYTES = 160  # 20 ms @ 8 kHz μ-law

# Initialize TTS model & torchaudio transforms once
generator = None
resampler = torchaudio.transforms.Resample(ORIG_SR, TARGET_SR)
mulaw_enc = torchaudio.transforms.MuLawEncoding()


def init():
    global generator
    if generator is None:
        generator = OrpheusModel(model_name="canopylabs/orpheus-tts-0.1-finetune-prod")


def text_to_speech_generator(text: str, voice: str = "tara"):
    init()
    pending = b""

    # Stream raw 24 kHz PCM from Orpheus
    for pcm24 in generator.generate_speech(prompt=text, voice=voice):
        # 1) bytes → int16 Tensor normalized to [-1,1]
        samples = np.frombuffer(pcm24, dtype=np.int16)
        tensor = torch.from_numpy(samples).float().div_(32768.0)

        # 2) resample to 8 kHz
        pcm8 = resampler(tensor.unsqueeze(0)).squeeze(0)  # float32

        # 3) μ-law encode → uint8 [0…255]
        ulaw = mulaw_enc(pcm8).to(torch.uint8)

        # 4) accumulate & chop into 160-byte frames
        pending += ulaw.numpy().tobytes()
        while len(pending) >= FRAME_BYTES:
            frame, pending = pending[:FRAME_BYTES], pending[FRAME_BYTES:]
            yield {
                "status": "processing",
                "audio": base64.b64encode(frame).decode("utf-8"),
            }

    # 5) flush any leftover tail (pad with 0xFF = silence)
    if pending:
        pending += b"\xff" * (FRAME_BYTES - len(pending))
        yield {
            "status": "processing",
            "audio": base64.b64encode(pending).decode("utf-8"),
        }

    # 6) done
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
        yield result


if __name__ == "__main__":
    if "--test_input" in sys.argv:
        idx = sys.argv.index("--test_input") + 1
        if idx < len(sys.argv):
            job = json.loads(sys.argv[idx])
            for item in generator_handler(job):
                print(json.dumps(item))
        else:
            print("Error: --test_input requires JSON")
    else:
        runpod.serverless.start(
            {"handler": generator_handler, "return_aggregate_stream": True}
        )

