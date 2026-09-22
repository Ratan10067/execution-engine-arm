"""
Main FastAPI Application for Judge0 ARM64 / x86_64 Execution Engine.
Fully compatible with official Judge0 REST API v1.13.0.
"""
import asyncio
import os
import platform
import psutil
from contextlib import asynccontextmanager
from typing import Optional, List, Union, Dict, Any

from fastapi import FastAPI, Depends, Query, HTTPException, status, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from src.config import settings
from src.models import (
    SubmissionRequest,
    SubmissionResponse,
    BatchSubmissionRequest,
    TokenResponse,
    SystemInfo,
    WorkerInfo,
)
from src.statuses import get_all_statuses, STATUS_IN_QUEUE
from src.languages import get_all_languages, get_language
from src.storage import storage
from src.queue_manager import queue_manager
from src.auth import verify_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan."""
    # Ensure sandbox dir exists
    os.makedirs(settings.SANDBOX_BASE_DIR, exist_ok=True)
    # Start background execution workers
    await queue_manager.start()
    yield
    # Stop background workers on shutdown
    await queue_manager.stop()


app = FastAPI(
    title="Judge0 ARM64 Execution Engine",
    description="High-performance, 100% Judge0-API-compatible online code execution engine optimized for ARM64 & x86_64 architectures (12 GB RAM System Profile).",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Enable CORS for contest platforms and frontend editors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 1. SUBMISSION ENDPOINTS
# ==========================================

@app.post(
    "/submissions",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_auth)],
)
async def create_submission(
    submission: SubmissionRequest,
    wait: bool = Query(False, description="Wait for submission to finish before responding"),
    base64_encoded: bool = Query(False, description="Whether source_code/stdin are base64 encoded"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to return"),
):
    """
    Create a new code execution submission.
    Supports asynchronous processing or immediate synchronous wait (?wait=true).
    """
    token = storage.generate_token()
    sub_data = submission.model_dump()

    event = await queue_manager.submit_job(token, sub_data, is_base64=base64_encoded)

    if wait:
        # Wait for worker to finish execution or timeout
        timeout = float(submission.wall_time_limit or settings.WALL_TIME_LIMIT) + 5.0
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass

        record = storage.get(token) or sub_data
        formatted = storage.format_output(record, fields=fields, base64_encoded=base64_encoded)
        return JSONResponse(content=formatted, status_code=status.HTTP_201_CREATED)

    # Asynchronous return token
    if fields:
        res_data = {"token": token}
        formatted = storage.format_output(res_data, fields=fields, base64_encoded=base64_encoded)
        return JSONResponse(content=formatted, status_code=status.HTTP_201_CREATED)

    return JSONResponse(content={"token": token}, status_code=status.HTTP_201_CREATED)


@app.post(
    "/submissions/batch",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_auth)],
)
async def create_batch_submissions(
    request: Union[BatchSubmissionRequest, List[SubmissionRequest]],
    base64_encoded: bool = Query(False, description="Whether input code is base64 encoded"),
):
    """Create batch submissions."""
    submissions_list = request.submissions if isinstance(request, BatchSubmissionRequest) else request
    tokens_response = []

    for sub in submissions_list:
        token = storage.generate_token()
        sub_data = sub.model_dump()
        await queue_manager.submit_job(token, sub_data, is_base64=base64_encoded)
        tokens_response.append({"token": token})

    return JSONResponse(content=tokens_response, status_code=status.HTTP_201_CREATED)


@app.get(
    "/submissions/batch",
    dependencies=[Depends(verify_auth)],
)
async def get_batch_submissions(
    tokens: str = Query(..., description="Comma-separated list of submission tokens"),
    base64_encoded: bool = Query(False, description="Whether output fields should be base64 encoded"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to return"),
):
    """Retrieve multiple submissions in batch by tokens."""
    token_list = [t.strip() for t in tokens.split(",") if t.strip()]
    results = storage.get_batch(token_list, fields=fields, base64_encoded=base64_encoded)
    # Filter out None results
    valid_results = [r for r in results if r is not None]
    return JSONResponse(content={"submissions": valid_results})


@app.get(
    "/submissions/{token}",
    dependencies=[Depends(verify_auth)],
)
async def get_submission(
    token: str,
    base64_encoded: bool = Query(False, description="Whether output fields should be base64 encoded"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to return"),
):
    """Get the status and result of a submission by token."""
    record = storage.get(token)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    formatted = storage.format_output(record, fields=fields, base64_encoded=base64_encoded)
    return JSONResponse(content=formatted)


@app.delete(
    "/submissions/{token}",
    dependencies=[Depends(verify_auth)],
)
async def delete_submission(token: str):
    """Delete a submission by token."""
    deleted = storage.delete(token)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )
    return JSONResponse(content={"message": "Submission deleted successfully"})



# ==========================================
# 2. LANGUAGES ENDPOINTS
# ==========================================

@app.get("/languages")
async def list_languages():
    """List supported programming languages."""
    return get_all_languages()


@app.get("/languages/all")
async def list_all_languages():
    """List all supported programming languages with full configuration details."""
    return get_all_languages()


@app.get("/languages/{language_id}")
async def get_language_by_id(language_id: int):
    """Get details for a specific language ID."""
    lang = get_language(language_id)
    if not lang:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Language ID {language_id} not found",
        )
    return {
        "id": lang.id,
        "name": lang.name,
        "is_archived": lang.is_archived,
        "source_file": lang.source_file,
        "compile_cmd": lang.compile_cmd,
        "run_cmd": lang.run_cmd,
    }


# ==========================================
# 3. STATUSES ENDPOINTS
# ==========================================

@app.get("/statuses")
async def list_statuses():
    """List all 14 official Judge0 execution status codes."""
    return get_all_statuses()


# ==========================================
# 4. SYSTEM, WORKERS, & CONFIG INFO
# ==========================================

@app.get("/system_info")
async def system_info():
    """Get system and hardware runtime information."""
    mem = psutil.virtual_memory()
    return {
        "version": settings.VERSION,
        "architecture": platform.machine(),
        "os": platform.system(),
        "platform_release": platform.release(),
        "cpu_count": os.cpu_count() or 1,
        "total_memory_kb": int(mem.total / 1024),
        "free_memory_kb": int(mem.available / 1024),
        "engine": "Native ARM64 / x86_64 High-Performance Engine",
    }


@app.get("/config_info")
async def config_info():
    """Get Judge0 runtime configuration."""
    return {
        "version": settings.VERSION,
        "maintainer": settings.MAINTAINER,
        "homepage": settings.HOMEPAGE,
        "cpu_time_limit": settings.CPU_TIME_LIMIT,
        "max_cpu_time_limit": settings.MAX_CPU_TIME_LIMIT,
        "cpu_extra_time": settings.CPU_EXTRA_TIME,
        "max_cpu_extra_time": settings.MAX_CPU_EXTRA_TIME,
        "wall_time_limit": settings.WALL_TIME_LIMIT,
        "max_wall_time_limit": settings.MAX_WALL_TIME_LIMIT,
        "memory_limit": settings.MEMORY_LIMIT,
        "max_memory_limit": settings.MAX_MEMORY_LIMIT,
        "stack_limit": settings.STACK_LIMIT,
        "max_stack_limit": settings.MAX_STACK_LIMIT,
        "max_processes_and_or_threads": settings.MAX_PROCESSES_AND_OR_THREADS,
        "max_max_processes_and_or_threads": settings.MAX_MAX_PROCESSES_AND_OR_THREADS,
        "enable_per_process_and_thread_time_limit": settings.ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT,
        "enable_per_process_and_thread_memory_limit": settings.ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT,
        "max_file_size": settings.MAX_FILE_SIZE,
        "max_max_file_size": settings.MAX_MAX_FILE_SIZE,
        "number_of_runs": settings.NUMBER_OF_RUNS,
        "max_number_of_runs": settings.MAX_NUMBER_OF_RUNS,
        "count": settings.COUNT,
        "max_queue_size": settings.MAX_QUEUE_SIZE,
        "submission_cache_duration": settings.SUBMISSION_CACHE_DURATION,
        "enable_callbacks": settings.ENABLE_CALLBACKS,
        "callback_timeout": settings.CALLBACK_TIMEOUT,
    }


@app.get("/workers")
async def list_workers():
    """Get worker pool status."""
    return [queue_manager.get_stats()]


@app.get("/statistics")
async def statistics():
    """Get execution statistics."""
    return {
        "total_cached_submissions": storage.count(),
        "workers": queue_manager.get_stats(),
    }


@app.get("/about")
async def about():
    """About Judge0 Engine."""
    return {
        "version": settings.VERSION,
        "homepage": settings.HOMEPAGE,
        "maintainer": settings.MAINTAINER,
        "architecture": platform.machine(),
    }


@app.get("/version", response_class=PlainTextResponse)
async def version():
    """Get plain version string."""
    return settings.VERSION


@app.get("/license", response_class=PlainTextResponse)
async def license_info():
    """Get license information."""
    return "GPL-3.0 License. Compatible with Judge0 API specifications."


@app.post("/authenticate")
async def authenticate(request: Request):
    """Verify authentication credentials."""
    verify_auth(request)
    return {"message": "Authenticated"}


@app.post("/authorize")
async def authorize(request: Request):
    """Verify authorization credentials."""
    verify_auth(request)
    return {"message": "Authorized"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "arch": platform.machine(),
        "workers": queue_manager.get_stats(),
    }
