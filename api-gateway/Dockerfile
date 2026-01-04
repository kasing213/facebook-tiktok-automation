FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Copy and setup start script
COPY start.sh .
RUN chmod +x start.sh

# Set Python path
ENV PYTHONPATH=/app

# Default port (Railway will override with PORT env var)
ENV PORT=8001

# Expose port
EXPOSE 8001

# Run the application using start script
CMD ["./start.sh"]
