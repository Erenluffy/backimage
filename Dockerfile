# -----------------------------
# Base Image
# -----------------------------
FROM python:3.11-slim

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# -----------------------------
# Install system dependencies
# -----------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV runtime
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    \
    # Image processing
    imagemagick \
    libmagic-dev \
    libmagickwand-dev \
    \
    # Build tools
    gcc \
    g++ \
    \
    # Utilities
    curl \
    \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Create non-root user
# -----------------------------
RUN useradd -m -u 1000 imagelab

# -----------------------------
# Set working directory
# -----------------------------
WORKDIR /app

# -----------------------------
# Install Python dependencies
# -----------------------------
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Copy application
# -----------------------------
COPY . .

# -----------------------------
# Create necessary folders
# -----------------------------
RUN mkdir -p \
    /app/static/uploads \
    /app/logs

# -----------------------------
# ImageMagick Security Policy
# -----------------------------
COPY config/imagick-policy.xml /etc/ImageMagick-6/policy.xml

# -----------------------------
# Set ownership
# -----------------------------
RUN chown -R imagelab:imagelab /app

# -----------------------------
# Switch to non-root user
# -----------------------------
USER imagelab

# -----------------------------
# Healthcheck
# -----------------------------
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
CMD curl -f http://localhost:5000/api/health || exit 1

# -----------------------------
# Expose port
# -----------------------------
EXPOSE 5000

# -----------------------------
# Start Gunicorn
# -----------------------------
CMD ["gunicorn", \
"--bind", "0.0.0.0:5000", \
"--workers", "4", \
"--threads", "2", \
"--timeout", "120", \
"app:app"]
