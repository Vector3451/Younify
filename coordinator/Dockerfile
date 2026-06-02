FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY coordinator/ ./coordinator/
COPY worker/cluster_provider.py ./worker/

EXPOSE 8050

CMD ["uvicorn", "coordinator.coordinator:coordinator_app", "--host", "0.0.0.0", "--port", "8050"]
