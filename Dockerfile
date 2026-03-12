FROM python:3.11-slim

# Install system dependencies including OpenCV requirements
RUN apt-get update && apt-get install -y \
    # OpenCV dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Image processing dependencies
    imagemagick \
    libmagic-dev \
    libmagickwand-dev \
    # Build tools
    gcc \
    g++ \
    # Other utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 imagelab && \
    mkdir -p /app && \
    chown -R imagelab:imagelab /app

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=imagelab:imagelab . .

# Create necessary directories
RUN mkdir -p /app/static/uploads /app/logs && \
    chown -R imagelab:imagelab /app/static /app/logs

# Copy ImageMagick security policy
COPY config/imagick-policy.xml /etc/ImageMagick-6/policy.xml

# Switch to non-root user
USER imagelab

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120", "app:app"]
