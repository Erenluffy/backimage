FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    imagemagick \
    libmagic-dev \
    libmagickwand-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads logs

# Copy ImageMagick security policy
COPY config/imagick-policy.xml /etc/ImageMagick-6/policy.xml

# Use non-root user
RUN useradd -m -u 1000 imagelab && chown -R imagelab:imagelab /app
USER imagelab

CMD gunicorn --bind 0.0.0.0:$PORT app:app
