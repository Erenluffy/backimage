# =============================
# Base Image
# =============================
FROM python:3.11-slim

# =============================
# Environment
# =============================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# =============================
# Install system dependencies
# =============================
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

# =============================
# Create non-root user
# =============================
RUN useradd -m -u 1000 imagelab

# =============================
# Working directory
# =============================
WORKDIR /app

# =============================
# Install Python dependencies
# =============================
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================
# Copy application files
# =============================
COPY . .

# =============================
# Create runtime folders
# =============================
RUN mkdir -p \
    /app/static/uploads \
    /app/logs

# =============================
# ImageMagick policy
# =============================
COPY config/imagick-policy.xml /etc/ImageMagick-6/policy.xml

# =============================
# Set permissions
# =============================
RUN chown -R imagelab:imagelab /app

# =============================
# Switch to non-root user
# =============================
USER imagelab

# =============================
# Expose port
# =============================
EXPOSE 5000

# =============================
# Healthcheck
# =============================
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
CMD curl -f http://localhost:$PORT/api/health || exit 1

# =============================
# Start server (Render compatible)
# =============================
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 app:app
