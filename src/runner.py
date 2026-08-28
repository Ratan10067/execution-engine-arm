"""
End-to-end execution runner orchestrating compilation, execution, output evaluation,
and webhook callbacks.
"""
import os
import shutil
import base64
import zipfile
import io
import datetime
import httpx
from typing import Optional, Dict, Any

from src.config import settings
from src.languages import get_language, LanguageConfig
from src.statuses import (
    STATUS_IN_QUEUE,
    STATUS_PROCESSING,
    STATUS_ACCEPTED,
    STATUS_WRONG_ANSWER,
    STATUS_COMPILATION_ERROR,
    STATUS_INTERNAL_ERROR,
    get_status_dict,
)
from src.sandbox import run_sandboxed_command, ExecutionResult
from src.compiler import compile_submission


def decode_base64_str(val: Optional[str]) -> Optional[str]:
    """Decodes a base64 string if non-empty, otherwise returns string as-is or None."""
    if not val:
        return val
    try:
        # Check if valid base64
        decoded_bytes = base64.b64decode(val.encode("utf-8"), validate=True)
        return decoded_bytes.decode("utf-8", errors="replace")
    except Exception:
        # If not valid base64, return original
        return val


def encode_base64_str(val: Optional[str]) -> Optional[str]:
    """Encodes a string to base64."""
    if val is None:
        return None
    return base64.b64encode(val.encode("utf-8")).decode("utf-8")


def normalize_output(text: Optional[str]) -> str:
    """Normalize line endings and trailing whitespace for Judge0 expected output matching."""
    if text is None:
        return ""
    # Standardize newline representations
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing whitespace and newlines for robust comparison
    return normalized.rstrip()


def extract_additional_files(additional_files_b64: str, target_dir: str):
    """Extract base64-encoded zip archive of additional files into the target workspace."""
    try:
        zip_bytes = base64.b64decode(additional_files_b64)
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            z.extractall(target_dir)
    except Exception as e:
        print(f"Error extracting additional files: {e}")


async def send_callback(callback_url: str, payload: Dict[str, Any]):
    """Send asynchronous HTTP PUT or POST callback to webhook URL."""
    try:
        async with httpx.AsyncClient(timeout=settings.CALLBACK_TIMEOUT) as client:
            # Judge0 standard callback method is PUT, with fallback to POST
            try:
                await client.put(callback_url, json=payload)
            except Exception:
                await client.post(callback_url, json=payload)
    except Exception as e:
        print(f"Failed to send webhook callback to {callback_url}: {e}")


def execute_submission_sync(
    token: str,
    submission_data: Dict[str, Any],
    is_base64_input: bool = False,
) -> Dict[str, Any]:
    """
    Synchronous worker execution function for a submission.
    Prepares workspace, compiles, executes, evaluates output, and populates result.
    """
    raw_source = submission_data.get("source_code", "")
    raw_stdin = submission_data.get("stdin")
    raw_expected = submission_data.get("expected_output")
    additional_files = submission_data.get("additional_files")

    # If inputs were explicitly base64 encoded
    if is_base64_input:
        source_code = decode_base64_str(raw_source) or ""
        stdin_data = decode_base64_str(raw_stdin)
        expected_output = decode_base64_str(raw_expected)
    else:
        source_code = raw_source
        stdin_data = raw_stdin
        expected_output = raw_expected

    language_id = int(submission_data.get("language_id", 0))
    lang = get_language(language_id)

    # Defaults & Limit Bounds
    cpu_time_limit = min(
        float(submission_data.get("cpu_time_limit") or settings.CPU_TIME_LIMIT),
        settings.MAX_CPU_TIME_LIMIT,
    )
    cpu_extra_time = min(
        float(submission_data.get("cpu_extra_time") or settings.CPU_EXTRA_TIME),
        settings.MAX_CPU_EXTRA_TIME,
    )
    wall_time_limit = min(
        float(submission_data.get("wall_time_limit") or settings.WALL_TIME_LIMIT),
        settings.MAX_WALL_TIME_LIMIT,
    )
    memory_limit_kb = min(
        int(submission_data.get("memory_limit") or settings.MEMORY_LIMIT),
        settings.MAX_MEMORY_LIMIT,
    )
    stack_limit_kb = min(
        int(submission_data.get("stack_limit") or settings.STACK_LIMIT),
        settings.MAX_STACK_LIMIT,
    )
    max_processes = min(
        int(submission_data.get("max_processes_and_or_threads") or settings.MAX_PROCESSES_AND_OR_THREADS),
        settings.MAX_MAX_PROCESSES_AND_OR_THREADS,
    )
    max_file_size_kb = min(
        int(submission_data.get("max_file_size") or settings.MAX_FILE_SIZE),
        settings.MAX_MAX_FILE_SIZE,
    )
    compiler_options = submission_data.get("compiler_options")
    command_line_args = submission_data.get("command_line_arguments")
    redirect_stderr = bool(submission_data.get("redirect_stderr_to_stdout", False))
    number_of_runs = max(1, min(int(submission_data.get("number_of_runs", 1)), settings.MAX_NUMBER_OF_RUNS))

    work_dir = os.path.join(settings.SANDBOX_BASE_DIR, token)
    os.makedirs(work_dir, exist_ok=True)

    result_data = dict(submission_data)
    result_data["token"] = token

    if not lang:
        result_data["status_id"] = STATUS_INTERNAL_ERROR
        result_data["status"] = get_status_dict(STATUS_INTERNAL_ERROR)
        result_data["message"] = f"Unsupported language ID {language_id}"
        result_data["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        shutil.rmtree(work_dir, ignore_errors=True)
        return result_data

    try:
        # 1. Write source file
        source_path = os.path.join(work_dir, lang.source_file)
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_code)

        # 2. Extract additional files if present
        if additional_files:
            extract_additional_files(additional_files, work_dir)

        # 3. Compilation step
        compile_res = compile_submission(
            lang=lang,
            work_dir=work_dir,
            compiler_options=compiler_options,
            memory_limit_kb=memory_limit_kb,
        )

        result_data["compile_output"] = compile_res.compile_output

        if not compile_res.success:
            result_data["status_id"] = STATUS_COMPILATION_ERROR
            result_data["status"] = get_status_dict(STATUS_COMPILATION_ERROR)
            result_data["stdout"] = None
            result_data["stderr"] = None
            result_data["exit_code"] = 1
            result_data["exit_signal"] = None
            result_data["time"] = f"{compile_res.cpu_time:.3f}"
            result_data["wall_time"] = f"{compile_res.cpu_time:.3f}"
            result_data["memory"] = compile_res.memory_kb
            result_data["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            shutil.rmtree(work_dir, ignore_errors=True)
            return result_data

        # 4. Execution step
        run_cmd = lang.run_cmd
        if command_line_args:
            run_cmd = f"{run_cmd} {command_line_args}"

        total_cpu = 0.0
        total_wall = 0.0
        peak_memory = 0
        last_exec_res: Optional[ExecutionResult] = None

        for _ in range(number_of_runs):
            exec_res = run_sandboxed_command(
                cmd=run_cmd,
                cwd=work_dir,
                stdin_data=stdin_data,
                cpu_time_limit=cpu_time_limit,
                cpu_extra_time=cpu_extra_time,
                wall_time_limit=wall_time_limit,
                memory_limit_kb=memory_limit_kb,
                stack_limit_kb=stack_limit_kb,
                max_processes=max_processes,
                max_file_size_kb=max_file_size_kb,
                redirect_stderr_to_stdout=redirect_stderr,
            )
            last_exec_res = exec_res
            total_cpu += exec_res.cpu_time
            total_wall += exec_res.wall_time
            peak_memory = max(peak_memory, exec_res.memory_kb)

            # If runtime error or TLE occurred, break early
            if exec_res.status_id != STATUS_ACCEPTED:
                break

        assert last_exec_res is not None

        avg_cpu = total_cpu / number_of_runs
        avg_wall = total_wall / number_of_runs

        final_status_id = last_exec_res.status_id
        stdout_output = last_exec_res.stdout
        stderr_output = last_exec_res.stderr

        # 5. Output Evaluation (Accepted vs Wrong Answer)
        if final_status_id == STATUS_ACCEPTED:
            if expected_output is not None:
                norm_actual = normalize_output(stdout_output)
                norm_expected = normalize_output(expected_output)
                if norm_actual == norm_expected:
                    final_status_id = STATUS_ACCEPTED
                else:
                    final_status_id = STATUS_WRONG_ANSWER
            else:
                final_status_id = STATUS_ACCEPTED

        result_data["status_id"] = final_status_id
        result_data["status"] = get_status_dict(final_status_id)
        result_data["stdout"] = stdout_output if stdout_output != "" else None
        result_data["stderr"] = stderr_output if stderr_output != "" else None
        result_data["exit_code"] = last_exec_res.exit_code
        result_data["exit_signal"] = last_exec_res.exit_signal
        result_data["message"] = last_exec_res.message
        result_data["time"] = f"{avg_cpu:.3f}"
        result_data["wall_time"] = f"{avg_wall:.3f}"
        result_data["memory"] = peak_memory
        result_data["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    except Exception as e:
        result_data["status_id"] = STATUS_INTERNAL_ERROR
        result_data["status"] = get_status_dict(STATUS_INTERNAL_ERROR)
        result_data["message"] = f"Internal Engine Error: {str(e)}"
        result_data["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

    return result_data
