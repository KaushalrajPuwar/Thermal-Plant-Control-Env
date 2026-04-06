#!/bin/bash
#
# Builds the Docker image and runs the container locally.
#

# Set a default image name
IMAGE_NAME="thermal-plant-env"

echo "Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

echo "Running Docker container..."
# Run the container, mapping port 8000 on the host to port 8000 in the container
docker run -p 8000:8000 $IMAGE_NAME