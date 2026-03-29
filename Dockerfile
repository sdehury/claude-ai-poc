FROM python:3.13-slim

LABEL maintainer="FinSight" \
      description="Long-term investment analysis platform for Indian equities and mutual funds"

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required by some Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.yaml .
COPY main.py .
COPY finsight/ finsight/

# Create directories for persistent data
RUN mkdir -p /app/data /app/cache /app/reports_output

# Volumes for data persistence across container runs
VOLUME ["/app/data", "/app/cache", "/app/reports_output"]

ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
