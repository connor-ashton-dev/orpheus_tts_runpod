import requests
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import base64
import io
import queue
import threading
from pynput import keyboard

# Global state for recording control
recording_active = False
stop_recording_event = threading.Event()
audio_queue = queue.Queue()

# --- Keyboard Listener ---

def on_press(key):
    """Handles key presses for starting/stopping recording."""
    global recording_active, stop_recording_event
    try:
        if key == keyboard.Key.enter:
            if not recording_active:
                print("\nStarting recording...")
                recording_active = True
                stop_recording_event.clear() # Ensure event is clear before starting
            else:
                print("\nStopping recording...")
                stop_recording_event.set() # Signal the recording thread to stop
                recording_active = False
                # Returning False stops the listener
                return False
    except AttributeError:
        pass # Ignore other keys

# --- Audio Recording ---

def _record_audio_interactive(fs=16000):
    """Internal function to record audio interactively."""
    global recording_active, stop_recording_event, audio_queue

    # Reset state
    recording_active = False
    stop_recording_event.clear()
    while not audio_queue.empty(): audio_queue.get() # Clear queue

    print("Press Enter to start recording...")
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # Wait for Enter to start
    while not recording_active and listener.is_alive():
         if stop_recording_event.wait(0.1): # Check if stopped early
              break

    if not recording_active: # Stopped before starting or listener died
        if listener.is_alive():
            listener.stop()
        listener.join()
        print("Recording cancelled or failed to start.")
        return None, fs

    frames = []
    def callback(indata, frame_count, time_info, status):
        if status: print(status, flush=True)
        if recording_active and not stop_recording_event.is_set():
            audio_queue.put(indata.copy())
        else:
            audio_queue.put(None) # Sentinel value to stop processing

    stream = sd.InputStream(samplerate=fs, channels=1, dtype='int16', callback=callback)
    try:
        stream.start()
        # Process audio data from the queue
        while True:
            try:
                data = audio_queue.get(timeout=0.5) # Add timeout to prevent indefinite block if something goes wrong
                if data is None: break
                frames.append(data)
            except queue.Empty:
                if not recording_active and stop_recording_event.is_set():
                     break # Exit if recording stopped externally
                continue
    finally:
        if stream.active: stream.stop()
        stream.close()
        if listener.is_alive(): listener.stop() # Ensure listener stops if recording ends unexpectedly
        listener.join()

    if not frames:
        print("No audio recorded.")
        return None, fs

    print("Recording finished.")
    recording = np.concatenate(frames, axis=0)
    return recording, fs

# --- Encoding ---

def _encode_audio_base64(audio_data, sample_rate):
    """Encodes NumPy audio data to Base64 string."""
    if audio_data is None: return None
    buffer = io.BytesIO()
    wav.write(buffer, sample_rate, audio_data)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')

# --- API Interaction ---

def _send_to_runpod(audio_base64, api_key, endpoint_id, model="base"):
    """Sends the audio data to the Runpod API and gets the transcription."""
    if not audio_base64: return None

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        'input': {
            "audio_base64": audio_base64,
            "model": model
        }
    }
    api_url = f'https://api.runpod.ai/v2/{endpoint_id}/runsync'

    print("Sending request to Runpod API...")
    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=120) # Add timeout
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        print("Response received:")
        result = response.json()

        if result.get('status') == 'COMPLETED':
            transcription = result.get('output', {}).get('transcription')
            if transcription:
                return transcription
            else:
                print("Transcription not found in the successful response output.")
                print(f"Full response: {result}")
                return None
        else:
            print(f"API Status not COMPLETED: {result.get('status')}")
            print(f"Full response: {result}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error during Runpod API request: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response Status Code: {e.response.status_code}")
            print(f"Response Text: {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during API interaction: {e}")
        return None


# --- Public Function ---

def get_transcription(api_key, endpoint_id, sample_rate=16000, model="base"):
    """
    Records audio interactively, sends it to Runpod API for transcription,
    and returns the resulting text.

    Args:
        api_key (str): Your Runpod API key.
        endpoint_id (str): Your specific Runpod endpoint ID.
        sample_rate (int): The sample rate for audio recording (default 16000).
        model (str): The Whisper model to use (default "base").

    Returns:
        str or None: The transcription text, or None if an error occurs.
    """
    audio_data, fs = _record_audio_interactive(sample_rate)
    if audio_data is None:
        print("Audio recording failed or was cancelled.")
        return None

    audio_base64 = _encode_audio_base64(audio_data, fs)
    if audio_base64 is None:
        print("Audio encoding failed.")
        return None

    transcription = _send_to_runpod(audio_base64, api_key, endpoint_id, model)

    return transcription

# Example usage if the script is run directly
if __name__ == '__main__':
    # Replace with your actual credentials - consider using environment variables!
    RUNPOD_API_KEY = "YOUR_RUNPOD_API_KEY"
    RUNPOD_ENDPOINT_ID = "YOUR_RUNPOD_ENDPOINT_ID"

    if RUNPOD_API_KEY == "YOUR_RUNPOD_API_KEY" or RUNPOD_ENDPOINT_ID == "YOUR_RUNPOD_ENDPOINT_ID":
         print("Please replace 'YOUR_RUNPOD_API_KEY' and 'YOUR_RUNPOD_ENDPOINT_ID' in transcription.py before running.")
    else:
        transcribed_text = get_transcription(RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID)
        if transcribed_text:
            print("\n--- Transcription Result ---")
            print(transcribed_text)
        else:
            print("\nFailed to get transcription.") 