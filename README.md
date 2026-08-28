# Native ARM64 / x86_64 High-Performance Judge0 Execution Engine

A high-performance, 100% Judge0-API-compatible online code execution engine optimized for **ARM64 (Oracle Cloud Ampere A1)** and **x86_64** architectures with direct support for up to **10 GB RAM** sandboxed code submissions.

---

## Key Features

- **100% Judge0 REST API Compatibility**: Seamless drop-in replacement for all Judge0 client libraries, contest platforms, frontend code runners, and `nexus-brain`.
- **Native ARM64 Execution**: Zero QEMU emulation overhead. Runs natively at full CPU clock speeds on Oracle Cloud Ampere A1.
- **10 GB RAM Sandboxing**: Full memory scaling supporting data science, high-memory algorithms, and multi-gigabyte memory allocations.
- **Asynchronous Worker Pipeline**: FastAPI + non-blocking async priority queue with configurable worker pools (4–16 concurrent workers).
- **All 14 Official Status Codes**: In Queue (1), Processing (2), Accepted (3), Wrong Answer (4), Time Limit Exceeded (5), Compilation Error (6), Runtime Errors (7–12), Internal Error (13), Exec Format Error (14).
- **Multi-Language Support**: Python 3, Python 2, C++ (GCC/Clang), C (GCC/Clang), Java (OpenJDK), JavaScript (Node.js), TypeScript, Go, Rust, Ruby, PHP, Bash, Swift, Kotlin, SQLite, and Multi-file programs.
- **Base64 Encoding Protocol**: Complete support for `?base64_encoded=true` query parameters and encoded source code/stdin/stdout.
- **Synchronous Wait (`?wait=true`)**: Instantaneous event-driven response upon task completion without polling delays.
- **Webhooks & Callbacks**: Asynchronous HTTP PUT/POST dispatch to `callback_url` on execution completion.
- **Field Filtering**: Efficient response projection with `?fields=stdout,time,memory,status`.

---

## API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/submissions?wait=true&base64_encoded=true` | Submit single code execution |
| `GET` | `/submissions/:token?fields=stdout,time,memory` | Retrieve submission status/results |
| `DELETE` | `/submissions/:token` | Delete submission record |
| `POST` | `/submissions/batch` | Submit multiple execution tasks |
| `GET` | `/submissions/batch?tokens=t1,t2` | Retrieve multiple submission results |
| `GET` | `/languages` | List supported programming languages |
| `GET` | `/languages/:id` | Get configuration for language ID |
| `GET` | `/languages/all` | Get full language compiler/run definitions |
| `GET` | `/statuses` | List all 14 execution status codes |
| `GET` | `/system_info` | System architecture, CPU count, and RAM |
| `GET` | `/config_info` | Engine limits and configuration values |
| `GET` | `/workers` | Health check & active/idle worker counts |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/about`, `/version`, `/license` | Engine metadata and version info |

---

## Quick Start (Native Local / Server)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Engine
```bash
bash start.sh
# Server starts on port 2358: http://localhost:2358
```

### 3. Run Test Suite
```bash
pytest -v tests/
```

---

## Docker Deployment (ARM64 & x86_64)

### Using Docker Compose
```bash
# Build and start in background
docker compose up -d

# Check logs
docker compose logs -f

# Verify status
curl http://localhost:2358/health
```

---

## Configuration (`judge0.conf`)

Tune parameters in `judge0.conf` or pass environment variables:

```ini
# Memory Limits (in KB) - 10 GB Max
MEMORY_LIMIT=524288          # Default: 512 MB
MAX_MEMORY_LIMIT=10485760    # Max: 10 GB

# CPU Time Limits (in seconds)
CPU_TIME_LIMIT=2.0
MAX_CPU_TIME_LIMIT=15.0

# Concurrency
COUNT=8                      # 8 worker threads

# Webhooks & Callbacks
ENABLE_CALLBACKS=true
CALLBACK_TIMEOUT=5.0
```

---

## Example Usage

### Execute Python 3 Code (Synchronous Wait)
```bash
curl -X POST "http://localhost:2358/submissions?wait=true" \
  -H "Content-Type: application/json" \
  -d '{
    "language_id": 71,
    "source_code": "print(sum(range(1, 101)))"
  }'
```

**Response:**
```json
{
  "token": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status_id": 3,
  "status": {
    "id": 3,
    "description": "Accepted"
  },
  "stdout": "5050\n",
  "stderr": null,
  "compile_output": null,
  "time": "0.018",
  "memory": 8420
}
```
