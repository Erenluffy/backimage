FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3.11-dev \
    imagemagick \
    libmagic-dev \
    libmagickwand-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    fonts-dejavu-core \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python and pip are already in PATH, no need to create symlinks
# Ubuntu already has python3 and pip3 commands

# Create a non-root user
RUN useradd -m -u 1000 imagelab

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads logs

# Copy ImageMagick security policy
COPY config/imagick-policy.xml /etc/ImageMagick-6/policy.xml

# Set permissions
RUN chown -R imagelab:imagelab /app

# Switch to non-root user
USER imagelab

# Use gunicorn with proper port handling
CMD gunicorn --bind 0.0.0.0:$PORT app:app
