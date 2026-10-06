# syntax=docker/dockerfile:1
FROM python:3.13-slim

# Install FFmpeg and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-privileged application user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure deno binary installed by deno wheel is on PATH
ENV PATH="/home/appuser/.local/bin:/usr/local/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

# Prepare data storage directory
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Copy application source code
COPY link2media/ /app/link2media/
RUN chown -R appuser:appuser /app/link2media

USER appuser

CMD ["python", "-m", "link2media.main"]
