"""
Pydantic Models matching Judge0 REST API v1.13.0 specifications.
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class StatusModel(BaseModel):
    id: int
    description: str


class LanguageModel(BaseModel):
    id: int
    name: str
    is_archived: bool = False
    source_file: Optional[str] = None
    compile_cmd: Optional[str] = None
    run_cmd: Optional[str] = None


class SubmissionRequest(BaseModel):
    source_code: str
    language_id: int
    stdin: Optional[str] = None
    expected_output: Optional[str] = None
    cpu_time_limit: Optional[float] = None
    cpu_extra_time: Optional[float] = None
    wall_time_limit: Optional[float] = None
    memory_limit: Optional[int] = None  # In KB
    stack_limit: Optional[int] = None   # In KB
    max_processes_and_or_threads: Optional[int] = None
    enable_per_process_and_thread_time_limit: Optional[bool] = None
    enable_per_process_and_thread_memory_limit: Optional[bool] = None
    max_file_size: Optional[int] = None
    enable_network: Optional[bool] = False
    number_of_runs: Optional[int] = 1
    additional_files: Optional[str] = None  # Base64 encoded zip
    callback_url: Optional[str] = None
    compiler_options: Optional[str] = None
    command_line_arguments: Optional[str] = None
    redirect_stderr_to_stdout: Optional[bool] = False


class SubmissionResponse(BaseModel):
    token: str
    source_code: Optional[str] = None
    language_id: Optional[int] = None
    stdin: Optional[str] = None
    expected_output: Optional[str] = None
    stdout: Optional[str] = None
    status_id: Optional[int] = None
    created_at: Optional[str] = None
    finished_at: Optional[str] = None
    time: Optional[str] = None
    wall_time: Optional[str] = None
    memory: Optional[int] = None
    stderr: Optional[str] = None
    token: str
    number_of_runs: Optional[int] = None
    cpu_time_limit: Optional[str] = None
    cpu_extra_time: Optional[str] = None
    wall_time_limit: Optional[str] = None
    memory_limit: Optional[int] = None
    stack_limit: Optional[int] = None
    max_processes_and_or_threads: Optional[int] = None
    enable_per_process_and_thread_time_limit: Optional[bool] = None
    enable_per_process_and_thread_memory_limit: Optional[bool] = None
    max_file_size: Optional[int] = None
    compile_output: Optional[str] = None
    exit_code: Optional[int] = None
    exit_signal: Optional[int] = None
    message: Optional[str] = None
    compiler_options: Optional[str] = None
    command_line_arguments: Optional[str] = None
    redirect_stderr_to_stdout: Optional[bool] = None
    callback_url: Optional[str] = None
    additional_files: Optional[str] = None
    status: Optional[StatusModel] = None

    model_config = {"extra": "allow"}


class BatchSubmissionRequest(BaseModel):
    submissions: List[SubmissionRequest]


class TokenResponse(BaseModel):
    token: str


class SystemInfo(BaseModel):
    version: str
    architecture: str
    os: str
    cpu_count: int
    total_memory_kb: int
    free_memory_kb: int
    engine: str = "Native ARM64 / x86_64 High-Performance Engine"


class WorkerInfo(BaseModel):
    available_workers: int
    active_workers: int
    queued_jobs: int
    status: str = "healthy"
