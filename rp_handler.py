import runpod
import time
from orpheus_tts import OrpheusModel
import wave
import base64


model = OrpheusModel(model_name ="canopylabs/orpheus-tts-0.1-finetune-prod")

def handler(event):
    print('worker start')
    input = event['input']

    prompt = input.get('prompt')
    print(f"Received prompt: {prompt}")

    start_time = time.monotonic()

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

    return encoded_audio

if __name__ == '__main__':
    runpod.serverless.start({"handler": handler, "return_aggregate_stream": True,  })