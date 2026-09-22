#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting Judge0 ARM64 / x86_64 High-Performance Engine"
echo " Architecture: $(uname -m)"
echo " Profile:      12 GB Host (Co-hosted with 8 GB Backend)"
echo " Engine Cap:   ~3.5 GB Safe Allocation | Workers: 6"
echo "=========================================================="

# Create sandbox temp dir
mkdir -p /tmp/judge0_sandbox

# Run FastAPI app with uvicorn
exec uvicorn src.app:app --host 0.0.0.0 --port 2358 --log-level info
