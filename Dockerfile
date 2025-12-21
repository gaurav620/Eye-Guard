# Eyeguard API
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY api/requirements.txt api_requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r api_requirements.txt

# Copy application
COPY src/ src/
COPY api/ api/
COPY data/ data/
COPY models/ models/

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=api/app.py
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "api/app.py"]
