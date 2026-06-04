FROM python:3.12-slim AS builder

# Update system packages and delete garbage
RUN apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Set up workdir
WORKDIR /app

# Copy requirements file tp workdir
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# Runtime
FROM python:3.12-slim AS runtime

# Update system packages and delete garbage
RUN apt-get update && apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Copy already built dependencies from builder
COPY --from=builder /install /usr/local

# Copy codebase
COPY . /app

# Set up workdir
WORKDIR /app

# Creating non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app

# Starting container as non-root user
USER appuser

# Set up entrypoint
CMD ["python", "main.py"]
