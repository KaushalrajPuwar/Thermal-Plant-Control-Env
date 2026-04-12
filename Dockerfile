# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Install the project itself so entry points (tasks/graders) are registered
RUN pip install --no-cache-dir .

# Make port 7860 available to the world outside this container
EXPOSE 7860

# Define environment variable to ensure Python outputs are sent straight to the terminal
ENV PYTHONUNBUFFERED=1

# Run app.py when the container launches
# Use uvicorn to run the FastAPI application, making it accessible on all network interfaces
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
