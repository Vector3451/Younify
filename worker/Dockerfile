FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker/worker.py ./worker.py
COPY worker/providers.py ./providers.py
COPY worker/cluster_provider.py ./cluster_provider.py

# Run the worker
CMD ["python", "worker.py"]
