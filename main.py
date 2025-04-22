import os
from dotenv import load_dotenv
from transcription import get_transcription
import sys

# Load environment variables from .env file
load_dotenv()

def main():
    # Get API key and endpoint ID from environment variables
    api_key = os.getenv("RUNPOD_API_KEY")
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")

    if not api_key or not endpoint_id:
        print("Error: RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID must be set in a .env file or environment variables.")
        print("Please create a .env file in the same directory with the following content:")
        print("RUNPOD_API_KEY=your_api_key_here")
        print("RUNPOD_ENDPOINT_ID=your_endpoint_id_here")
        return

    print(f"Using Endpoint ID: {endpoint_id}")
    print("Starting interactive transcription loop. Press Ctrl+C to exit.")

    while True:
        try:
            print("\n--------------------") # Separator for clarity
            # Get transcription using the refactored function
            transcribed_text = get_transcription(api_key, endpoint_id)

            if transcribed_text:
                print("\n--- Transcription Result ---")
                print(transcribed_text)
            else:
                # Avoid printing failure message if recording was simply cancelled before start
                # The get_transcription function already prints messages for failures.
                # Consider adding a specific return value or exception for cancellation if needed.
                pass # Or print a specific message like "Transcription attempt finished." if desired

        except KeyboardInterrupt:
            print("\nExiting program.")
            sys.exit(0)
        except Exception as e:
            print(f"\nAn unexpected error occurred in the main loop: {e}")
            print("Restarting loop...")
            # Optional: add a small delay here
            # time.sleep(1)

if __name__ == "__main__":
    main()
