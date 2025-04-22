# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size, --upgrade ensures latest pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download and cache the Orpheus TTS model
# Replace model_name if you want to use a different one
RUN python -c "from orpheus_tts import OrpheusModel; print('Downloading model...'); model = OrpheusModel(model_name='canopylabs/orpheus-tts-0.1-finetune-prod'); print('Model download complete.')"

# Copy the handler file into the container at /app
COPY handler.py .

# Run handler.py when the container launches
# -u ensures that Python output is sent straight to terminal without being buffered
CMD [ "python", "-u", "handler.py" ] 