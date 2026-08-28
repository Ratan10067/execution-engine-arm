#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting Judge0 ARM64 / x86_64 High-Performance Engine"
echo " Architecture: $(uname -m)"
echo " Memory Limit: 10 GB Supported"
echo "=========================================================="

# Create sandbox temp dir
mkdir -p /tmp/judge0_sandbox

# Run FastAPI app with uvicorn
exec uvicorn src.app:app --host 0.0.0.0 --port 2358 --log-level info
