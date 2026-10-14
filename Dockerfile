# Use an official lightweight Python image
FROM python:3.11-slim

# Set environment variables
# Prevents Python from writing .pyc files and buffers stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Set working directory inside container
WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Create a non-privileged system user for cloud security
RUN useradd -u 1001 -m appuser && \
    chown -R appuser:appuser /app
USER appuser

# Document that the container listens on port 8080
EXPOSE 8080

# Run the web service using Gunicorn production WSGI server
# Cloud Run automatically sets the PORT environment variable
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 0 app:app
