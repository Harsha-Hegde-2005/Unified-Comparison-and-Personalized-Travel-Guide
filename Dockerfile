FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and database assets
COPY backend/ ./backend/
COPY database/ ./database/
COPY unified_transit.db ./unified_transit.db
COPY main.py ./main.py

# Configure environment
ENV PORT=8000 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Launch FastAPI using Uvicorn bound to dynamic $PORT
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
