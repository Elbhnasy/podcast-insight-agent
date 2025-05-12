# Use official Python image with Python 3.11 for better performance
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.5.1

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies with cleanup in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory and ensure it's owned by appuser
WORKDIR /app

# Install Poetry for dependency management
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy only requirements first to leverage Docker caching
COPY requirements.txt poetry.lock* pyproject.toml* /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app/

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the API port
EXPOSE 8000

# Create volume for persistent data
VOLUME ["/app/data"]

# Set healthcheck to verify the app is running properly
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run the application with proper startup
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "src.api:create_app()"]