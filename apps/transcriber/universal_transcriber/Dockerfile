FROM python:3.12-slim

# Install system dependencies
# ffmpeg is required for yt-dlp audio extraction
# build-essential and git might be needed for some python packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
# pywhispercpp requires a C++ compiler, hence build-essential above
RUN pip install --no-cache-dir \
    pywhispercpp>=1.4.0 \
    yt-dlp>=2025.11.12 \
    fastapi \
    uvicorn \
    python-multipart

# Copy source code
COPY . .

# Create directories for persistence
RUN mkdir -p transcriptions downloads

# Expose port
EXPOSE 8000

# Run the server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
