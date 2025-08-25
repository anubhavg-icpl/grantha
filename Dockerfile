# Multi-stage Dockerfile for Grantha
# Similar to deepwiki-open setup

# Frontend Build Stage
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package.json frontend/pnpm-lock.yaml* ./

# Install pnpm and dependencies
RUN npm install -g pnpm@9.0.0
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY frontend/ .

# Copy unified .env to frontend directory for build
COPY .env ../.env

# Build frontend
RUN pnpm run build

# Backend Runtime Stage
FROM python:3.12-slim AS backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt requirements-dev.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Copy Python source code
COPY src/ ./src/
COPY configs/ ./configs/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create non-root user for security
RUN groupadd -r grantha && useradd -r -g grantha grantha
RUN chown -R grantha:grantha /app
USER grantha

# Create logs directory
RUN mkdir -p logs

# Copy unified environment file
COPY .env ./

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "src.grantha.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]