import requests
import base64
import os
import subprocess
import tempfile
import platform  # Import platform to check OS

def main():
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    endpoint_url = 'https://api.runpod.ai/v2/4nugpnfk98lqfb/runsync'
    data = {
        'input': {
            "text": "This is a test of the text-to-speech endpoint.", # Changed from 'prompt' to 'text'
            "lang_code": "a",      # Added lang_code (using default from handler)
            "voice": "af_heart",   # Changed key and used default from handler
            "speed": 1.0           # Added speed (using default from handler)
            # "output_format": "mp3" # Removed - not used by this handler
         }
    }

    print("Making API request to RunPod TTS endpoint...")
    try:
        response = requests.post(endpoint_url, headers=headers, json=data, timeout=60) # Added timeout
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        print("API request successful.")
        result = response.json()
        # print("Full API response:", result) # Removed debug print

        # Check for errors in the RunPod response structure
        if result.get('status') == 'FAILED':
            print(f"RunPod job failed: {result.get('error', 'Unknown error')}")
            return
        elif result.get('status') != 'COMPLETED':
             print(f"RunPod job status: {result.get('status')}")
             # Potentially handle IN_PROGRESS or IN_QUEUE if using /run instead of /runsync
             return


        # Extract audio from the expected output structure
        output_data = result.get('output') # Get the output field

        audio_output = None
        if isinstance(output_data, dict):
            # If output is a dictionary, get 'audio_output' directly
            audio_output = output_data.get('audio_output')
        elif isinstance(output_data, list) and len(output_data) > 0:
            # If output is a non-empty list, assume the first item might contain the audio
            # This might need adjustment based on the actual structure within the list
            first_item = output_data[0]
            if isinstance(first_item, dict):
                 audio_output = first_item.get('audio_output')
            # Handle if the first item is just the base64 string directly (less likely)
            # elif isinstance(first_item, str):
            #      audio_output = first_item

        if not audio_output:
             print("Error: Could not find 'audio_output' in the response output.")
             print("Full response:", result) # Print response again if audio not found
             return

        print("Decoding base64 audio...")
        audio_bytes = base64.b64decode(audio_output)

        # Save to a temporary file and play
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio_file:
            temp_audio_file.write(audio_bytes)
            temp_file_path = temp_audio_file.name

        print(f"Audio saved temporarily to: {temp_file_path}")

        try:
            print("Playing audio...")
            system = platform.system()
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", temp_file_path], check=True)
            elif system == "Linux":
                # Try paplay first, then aplay
                try:
                    subprocess.run(["paplay", temp_file_path], check=True)
                except FileNotFoundError:
                    try:
                        subprocess.run(["aplay", temp_file_path], check=True)
                    except FileNotFoundError:
                        print("Error: Neither paplay nor aplay found. Cannot play audio on Linux.")
            else:
                 print(f"Warning: Unsupported OS '{system}'. Cannot automatically play audio.")

            print("Playback finished.")
        except subprocess.CalledProcessError as e:
            print(f"Error playing audio: {e}")
        except FileNotFoundError:
             if system == "Darwin":
                 print("Error: 'afplay' command not found. Please ensure it's installed or in your PATH.")
             # We already handled Linux file not found above
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print(f"Temporary file {temp_file_path} removed.")

    except requests.exceptions.RequestException as e:
        print(f"Error during API request: {e}")
    except KeyError as e:
        print(f"Error parsing response JSON: Missing key {e}")
        print("Full response:", response.text) # Print raw text if JSON parsing fails early
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
