"""
Compilation step handler for Judge0 ARM64 Execution Engine.
Handles compiler options, compile-stage limits, and compile diagnostics.
"""
from typing import Optional, Tuple
from src.languages import LanguageConfig
from src.sandbox import run_sandboxed_command
from src.statuses import STATUS_COMPILATION_ERROR, STATUS_ACCEPTED


class CompilerResult:
    def __init__(
        self,
        success: bool,
        compile_output: Optional[str] = None,
        status_id: int = STATUS_ACCEPTED,
        cpu_time: float = 0.0,
        memory_kb: int = 0,
    ):
        self.success = success
        self.compile_output = compile_output
        self.status_id = status_id
        self.cpu_time = cpu_time
        self.memory_kb = memory_kb


def compile_submission(
    lang: LanguageConfig,
    work_dir: str,
    compiler_options: Optional[str] = None,
    compile_time_limit: float = 10.0,
    memory_limit_kb: Optional[int] = 1048576,  # 1 GB compilation memory limit
) -> CompilerResult:
    """
    Compiles source code if the language requires compilation.
    Returns CompilerResult with status and compile diagnostics.
    """
    if not lang.is_compiled or not lang.compile_cmd:
        return CompilerResult(success=True)

    compile_cmd = lang.compile_cmd
    if compiler_options:
        # Append compiler options before target files or flags
        compile_cmd = f"{compile_cmd} {compiler_options}"

    res = run_sandboxed_command(
        cmd=compile_cmd,
        cwd=work_dir,
        cpu_time_limit=compile_time_limit,
        wall_time_limit=compile_time_limit * 1.5,
        memory_limit_kb=memory_limit_kb,
        redirect_stderr_to_stdout=True,
    )

    combined_output = (res.stdout + "\n" + res.stderr).strip()

    if res.exit_code != 0 or res.status_id != STATUS_ACCEPTED:
        return CompilerResult(
            success=False,
            compile_output=combined_output if combined_output else "Compilation Failed",
            status_id=STATUS_COMPILATION_ERROR,
            cpu_time=res.cpu_time,
            memory_kb=res.memory_kb,
        )

    return CompilerResult(
        success=True,
        compile_output=combined_output if combined_output else None,
        status_id=STATUS_ACCEPTED,
        cpu_time=res.cpu_time,
        memory_kb=res.memory_kb,
    )
