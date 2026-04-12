# Use an official Python runtime as a parent image (3.13-slim for balanced size/speed)
FROM python:3.13-slim

# Set the working directory to the standardised /app path
WORKDIR /app

# Copy the project files into the container, ensuring .dockerignore prevents cache bloating
COPY . /app

# Install standard dependencies using --no-cache-dir to minimise image footprint
RUN pip install --no-cache-dir -r requirements.txt

# Register the project entry points (tasks/graders) via an editable-mode installation
RUN pip install --no-cache-dir .

# Expose the standard Hugging Face Spaces API port
EXPOSE 7860

# Ensure Python outputs are synchronised to stdout for real-time judge monitoring
ENV PYTHONUNBUFFERED=1

# Launch the FastAPI application using the uvicorn production server
# We bind to 0.0.0.0 to enable external traffic routing from the HF Spaces reverse proxy
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
