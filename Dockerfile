# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency definition files
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv sync for speed and consistency
# Using --strict ensures only locked dependencies are installed
RUN uv pip sync --strict uv.lock

# Copy the rest of the application code into the container at /app
COPY . .

# Define environment variables (if any)
# ENV NAME=value

# Make port 8000 available to the world outside this container (if needed for web apps)
# EXPOSE 8000

# Run main.py when the container launches (adjust as necessary)
# You might need to change "main.py" to your actual entry point script
CMD ["python", "main.py"] 