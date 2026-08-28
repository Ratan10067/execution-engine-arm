"""
Native Process Sandboxing & Resource Limit Enforcement Engine.
Enforces CPU time, memory limits (up to 10 GB), stack limits, process counts,
and maps OS signals to Judge0 status codes.
"""
import os
import sys
import time
import signal
import platform
import subprocess
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

try:
    import resource
except ImportError:
    resource = None  # type: ignore

from src.statuses import (
    STATUS_ACCEPTED,
    STATUS_TIME_LIMIT_EXCEEDED,
    STATUS_RUNTIME_ERROR_SIGSEGV,
    STATUS_RUNTIME_ERROR_SIGXFSZ,
    STATUS_RUNTIME_ERROR_SIGFPE,
    STATUS_RUNTIME_ERROR_SIGABRT,
    STATUS_RUNTIME_ERROR_NZEC,
    STATUS_RUNTIME_ERROR_OTHER,
    STATUS_INTERNAL_ERROR,
)


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: Optional[int]
    exit_signal: Optional[int]
    status_id: int
    cpu_time: float
    wall_time: float
    memory_kb: int
    message: Optional[str] = None


def _set_limits(
    cpu_time_limit: float,
    cpu_extra_time: float,
    memory_limit_kb: Optional[int],
    stack_limit_kb: Optional[int],
    max_processes: Optional[int],
    max_file_size_kb: Optional[int],
):
    """Pre-exec hook to set process resource limits inside the sandbox child process."""
    # Create a new session/process group so we can cleanly kill all children
    try:
        os.setsid()
    except Exception:
        pass

    if resource is None:
        return

    # 1. CPU Time Limit (seconds)
    try:
        total_cpu_seconds = int(cpu_time_limit + cpu_extra_time) + 1
        resource.setrlimit(resource.RLIMIT_CPU, (total_cpu_seconds, total_cpu_seconds + 1))
    except Exception:
        pass

    # 2. Memory Limit (KB -> Bytes)
    if memory_limit_kb and memory_limit_kb > 0:
        mem_bytes = memory_limit_kb * 1024
        # On Linux, RLIMIT_AS restricts total virtual memory
        if hasattr(resource, "RLIMIT_AS") and platform.system() != "Darwin":
            try:
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
            except Exception:
                pass
        if hasattr(resource, "RLIMIT_DATA"):
            try:
                resource.setrlimit(resource.RLIMIT_DATA, (mem_bytes, mem_bytes))
            except Exception:
                pass

    # 3. Stack Limit (KB -> Bytes)
    if stack_limit_kb and stack_limit_kb > 0:
        stack_bytes = stack_limit_kb * 1024
        if hasattr(resource, "RLIMIT_STACK"):
            try:
                resource.setrlimit(resource.RLIMIT_STACK, (stack_bytes, stack_bytes))
            except Exception:
                pass

    # 4. Max Processes / Threads (Only on Linux)
    if max_processes and max_processes > 0 and platform.system() != "Darwin":
        if hasattr(resource, "RLIMIT_NPROC"):
            try:
                resource.setrlimit(resource.RLIMIT_NPROC, (max_processes, max_processes))
            except Exception:
                pass

    # 5. Max File Size (KB -> Bytes)
    if max_file_size_kb and max_file_size_kb > 0:
        file_bytes = max_file_size_kb * 1024
        if hasattr(resource, "RLIMIT_FSIZE"):
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes, file_bytes))
            except Exception:
                pass


def map_signal_to_status(sig: int) -> int:
    """Map POSIX signals to Judge0 status codes."""
    sig = abs(sig)
    if sig == signal.SIGSEGV:
        return STATUS_RUNTIME_ERROR_SIGSEGV
    elif hasattr(signal, "SIGXFSZ") and sig == signal.SIGXFSZ:
        return STATUS_RUNTIME_ERROR_SIGXFSZ
    elif sig == signal.SIGFPE:
        return STATUS_RUNTIME_ERROR_SIGFPE
    elif sig == signal.SIGABRT:
        return STATUS_RUNTIME_ERROR_SIGABRT
    elif hasattr(signal, "SIGXCPU") and sig == signal.SIGXCPU:
        return STATUS_TIME_LIMIT_EXCEEDED
    elif sig in (signal.SIGKILL, signal.SIGTERM):
        return STATUS_TIME_LIMIT_EXCEEDED
    return STATUS_RUNTIME_ERROR_OTHER


def run_sandboxed_command(
    cmd: str,
    cwd: str,
    stdin_data: Optional[str] = None,
    cpu_time_limit: float = 2.0,
    cpu_extra_time: float = 0.5,
    wall_time_limit: float = 5.0,
    memory_limit_kb: Optional[int] = 524288,
    stack_limit_kb: Optional[int] = 64000,
    max_processes: Optional[int] = 60,
    max_file_size_kb: Optional[int] = 10240,
    env: Optional[Dict[str, str]] = None,
    redirect_stderr_to_stdout: bool = False,
) -> ExecutionResult:
    """
    Execute a command with strict sandboxing and resource limits.
    Returns ExecutionResult with status, timings, and outputs.
    """
    exec_env = os.environ.copy()
    exec_env["PATH"] = f"/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:{exec_env.get('PATH', '')}"
    if env:
        exec_env.update(env)

    # Initial rusage before child execution
    rusage_before = None
    if resource:
        try:
            rusage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
        except Exception:
            rusage_before = None

    stdin_bytes = stdin_data.encode("utf-8") if stdin_data else None
    start_wall_time = time.perf_counter()

    preexec = lambda: _set_limits(
        cpu_time_limit=cpu_time_limit,
        cpu_extra_time=cpu_extra_time,
        memory_limit_kb=memory_limit_kb,
        stack_limit_kb=stack_limit_kb,
        max_processes=max_processes,
        max_file_size_kb=max_file_size_kb,
    )

    stderr_dest = subprocess.STDOUT if redirect_stderr_to_stdout else subprocess.PIPE

    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,
            stdin=subprocess.PIPE if stdin_bytes else None,
            stdout=subprocess.PIPE,
            stderr=stderr_dest,
            env=exec_env,
            preexec_fn=preexec if os.name != "nt" else None,
        )

        try:
            out_bytes, err_bytes = proc.communicate(
                input=stdin_bytes,
                timeout=wall_time_limit + cpu_extra_time,
            )
            end_wall_time = time.perf_counter()
            wall_time = max(0.001, end_wall_time - start_wall_time)
            is_timeout = False
        except subprocess.TimeoutExpired:
            is_timeout = True
            end_wall_time = time.perf_counter()
            wall_time = end_wall_time - start_wall_time

            # Kill entire process group
            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                else:
                    proc.kill()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

            out_bytes, err_bytes = proc.communicate()

    except Exception as e:
        return ExecutionResult(
            stdout="",
            stderr=str(e),
            exit_code=1,
            exit_signal=None,
            status_id=STATUS_INTERNAL_ERROR,
            cpu_time=0.0,
            wall_time=0.0,
            memory_kb=0,
            message=f"Sandbox execution failed: {str(e)}",
        )

    # Compute CPU time and memory delta
    cpu_time = 0.0
    memory_kb = 0
    if resource:
        try:
            rusage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
            if rusage_before:
                user_cpu = max(0.0, rusage_after.ru_utime - rusage_before.ru_utime)
                sys_cpu = max(0.0, rusage_after.ru_stime - rusage_before.ru_stime)
                cpu_time = round(user_cpu + sys_cpu, 4)
            else:
                cpu_time = round(rusage_after.ru_utime + rusage_after.ru_stime, 4)

            maxrss = rusage_after.ru_maxrss
            if platform.system() == "Darwin":
                memory_kb = int(maxrss / 1024)
            else:
                memory_kb = int(maxrss)
        except Exception:
            cpu_time = round(wall_time, 4)

    if cpu_time <= 0.0:
        cpu_time = round(min(wall_time, cpu_time_limit), 4)

    stdout_str = out_bytes.decode("utf-8", errors="replace") if out_bytes else ""
    stderr_str = err_bytes.decode("utf-8", errors="replace") if err_bytes else ""

    # Truncate output if larger than max_file_size
    max_bytes = (max_file_size_kb or 10240) * 1024
    if len(stdout_str.encode("utf-8")) > max_bytes:
        stdout_str = stdout_str[:max_bytes]
    if len(stderr_str.encode("utf-8")) > max_bytes:
        stderr_str = stderr_str[:max_bytes]

    returncode = proc.returncode

    # Evaluate Status
    if is_timeout or cpu_time > (cpu_time_limit + cpu_extra_time):
        return ExecutionResult(
            stdout=stdout_str,
            stderr=stderr_str,
            exit_code=None,
            exit_signal=signal.SIGKILL if is_timeout else signal.SIGXCPU,
            status_id=STATUS_TIME_LIMIT_EXCEEDED,
            cpu_time=cpu_time,
            wall_time=wall_time,
            memory_kb=memory_kb,
            message="Time Limit Exceeded",
        )

    if returncode < 0:
        # Terminated by signal
        sig = -returncode
        status_id = map_signal_to_status(sig)
        msg = f"Process terminated with signal {sig}"
        return ExecutionResult(
            stdout=stdout_str,
            stderr=stderr_str,
            exit_code=None,
            exit_signal=sig,
            status_id=status_id,
            cpu_time=cpu_time,
            wall_time=wall_time,
            memory_kb=memory_kb,
            message=msg,
        )
    elif returncode > 0:
        # Non-zero exit code (NZEC)
        return ExecutionResult(
            stdout=stdout_str,
            stderr=stderr_str,
            exit_code=returncode,
            exit_signal=None,
            status_id=STATUS_RUNTIME_ERROR_NZEC,
            cpu_time=cpu_time,
            wall_time=wall_time,
            memory_kb=memory_kb,
            message=f"Exited with error status {returncode}",
        )

    # Clean exit code 0
    return ExecutionResult(
        stdout=stdout_str,
        stderr=stderr_str,
        exit_code=0,
        exit_signal=None,
        status_id=STATUS_ACCEPTED,
        cpu_time=cpu_time,
        wall_time=wall_time,
        memory_kb=memory_kb,
        message=None,
    )
