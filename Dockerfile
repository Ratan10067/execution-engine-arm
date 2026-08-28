# ==============================================================================
# Multi-Arch Dockerfile for Judge0 ARM64 & x86_64 High-Performance Engine
# Optimized for Oracle Cloud Ampere A1 (ARM64) and standard x86_64
# ==============================================================================
FROM ubuntu:22.04

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV TZ=UTC

# Install base system utilities and language compilers/runtimes
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    clang \
    python3 \
    python3-pip \
    python3-dev \
    openjdk-17-jdk-headless \
    nodejs \
    npm \
    golang \
    rustc \
    ruby \
    php-cli \
    sqlite3 \
    bash \
    curl \
    unzip \
    ca-certificates \
    psmisc \
    && npm install -g typescript \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Setup application directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application source code and configuration
COPY src/ /app/src/
COPY judge0.conf /app/judge0.conf

# Create sandbox directory with full access
RUN mkdir -p /tmp/judge0_sandbox && chmod 777 /tmp/judge0_sandbox

# Expose standard Judge0 port
EXPOSE 2358

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:2358/health || exit 1

# Start FastAPI application
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "2358", "--workers", "1"]
