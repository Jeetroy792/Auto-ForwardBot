FROM python:3.12-slim

# Install required system dependencies
RUN apt update && apt install -y \
    git gcc python3-dev libffi-dev build-essential \
    && apt upgrade -y

# Set the working directory
WORKDIR /fwdbot

# Copy all repository files into the container
# This step was missing in your previous file
COPY . .

# Install Python dependencies
RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

# Grant execution permission to the start script
RUN chmod +x start.sh

# Start the application
CMD ["/bin/bash", "start.sh"]
