# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        netcat-traditional \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies first (better caching)
# Use custom pip cache directory instead of /tmp to avoid space issues
COPY requirements.txt .
RUN mkdir -p /app/.pip-cache \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --cache-dir /app/.pip-cache -r requirements.txt \
    && pip install --cache-dir /app/.pip-cache grpcio grpcio-tools protobuf==4.24.4

# Copy project files
COPY . .

# Compile protobuf files to Python gRPC stubs
RUN python -m grpc_tools.protoc \
    -I. \
    --python_out=user_service \
    --grpc_python_out=user_service \
    inventory.proto \
    && sed -i 's/^from . import inventory_pb2/import inventory_pb2/' user_service/inventory_pb2_grpc.py

# Create necessary directories
RUN mkdir -p /app/logs

# Expose gRPC port (not HTTP)
EXPOSE 50051

# Health check - gRPC service on port 50051
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import grpc; grpc.aio.insecure_channel('localhost:50051').close()" || exit 1

# Run pure gRPC server
CMD ["python", "user_service/main.py"]
