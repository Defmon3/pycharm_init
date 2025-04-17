# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
RUN uv export --format requirements-txt --locked > requirements.txt

COPY requirements.txt /app/requirements.txt
# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable to prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/.

# Copy the rest of the application code into the container at /app
COPY /app /app
EXPOSE 8080

# Specify the command to run on container start
CMD ["python", "main.py", "&&", "tail", "-f", "/dev/null"]

