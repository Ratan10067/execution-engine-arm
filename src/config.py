"""
Configuration loader for Judge0 ARM64 Execution Engine.
Supports judge0.conf key-value file and environment variables.
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any


def parse_conf_file(file_path: str) -> Dict[str, str]:
    """Parse judge0.conf key=value configuration file."""
    config: Dict[str, str] = {}
    path = Path(file_path)
    if not path.exists():
        return config

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                config[key] = val
    return config


class Settings:
    """Judge0 Configuration Settings."""

    def __init__(self, conf_file: Optional[str] = None):
        if not conf_file:
            conf_file = os.getenv("JUDGE0_CONF", "judge0.conf")

        file_conf = parse_conf_file(conf_file)

        def get_val(key: str, default: Any, val_type=str):
            env_val = os.getenv(key)
            if env_val is not None:
                raw = env_val
            elif key in file_conf:
                raw = file_conf[key]
            else:
                return default

            if val_type == bool:
                return str(raw).lower() in ("true", "1", "yes", "on")
            elif val_type == int:
                try:
                    return int(raw)
                except ValueError:
                    return default
            elif val_type == float:
                try:
                    return float(raw)
                except ValueError:
                    return default
            elif val_type == list:
                if isinstance(raw, list):
                    return raw
                return [x.strip() for x in str(raw).split(",") if x.strip()]
            return str(raw)

        # Server info
        self.PORT: int = get_val("PORT", 2358, int)
        self.HOST: str = get_val("HOST", "0.0.0.0", str)
        self.VERSION: str = get_val("VERSION", "1.13.0", str)
        self.HOMEPAGE: str = get_val("HOMEPAGE", "https://judge0.com", str)
        self.MAINTAINER: str = get_val("MAINTAINER", "Judge0 ARM64 Engine", str)

        # Authentication / Authorization
        self.AUTHN_TOKEN: Optional[str] = get_val("AUTHN_TOKEN", None, str)
        self.AUTHN_HEADER: str = get_val("AUTHN_HEADER", "X-Auth-Token", str)
        self.AUTHZ_TOKEN: Optional[str] = get_val("AUTHZ_TOKEN", None, str)
        self.AUTHZ_HEADER: str = get_val("AUTHZ_HEADER", "X-Auth-User", str)
        self.RAPIDAPI_KEY: Optional[str] = get_val("RAPIDAPI_KEY", None, str)
        self.RAPIDAPI_HOST: Optional[str] = get_val("RAPIDAPI_HOST", None, str)

        # Memory limits (in KB) - default 512MB, max 10GB for ARM64 10GB RAM
        self.MEMORY_LIMIT: int = get_val("MEMORY_LIMIT", 524288, int)  # 512 MB
        self.MAX_MEMORY_LIMIT: int = get_val("MAX_MEMORY_LIMIT", 10485760, int)  # 10 GB

        # CPU Time limits (in seconds)
        self.CPU_TIME_LIMIT: float = get_val("CPU_TIME_LIMIT", 2.0, float)
        self.MAX_CPU_TIME_LIMIT: float = get_val("MAX_CPU_TIME_LIMIT", 15.0, float)
        self.CPU_EXTRA_TIME: float = get_val("CPU_EXTRA_TIME", 0.5, float)
        self.MAX_CPU_EXTRA_TIME: float = get_val("MAX_CPU_EXTRA_TIME", 2.0, float)

        # Wall Time limits (in seconds)
        self.WALL_TIME_LIMIT: float = get_val("WALL_TIME_LIMIT", 5.0, float)
        self.MAX_WALL_TIME_LIMIT: float = get_val("MAX_WALL_TIME_LIMIT", 20.0, float)

        # Stack limit (in KB)
        self.STACK_LIMIT: int = get_val("STACK_LIMIT", 64000, int)
        self.MAX_STACK_LIMIT: int = get_val("MAX_STACK_LIMIT", 256000, int)

        # Process limit
        self.MAX_PROCESSES_AND_OR_THREADS: int = get_val("MAX_PROCESSES_AND_OR_THREADS", 60, int)
        self.MAX_MAX_PROCESSES_AND_OR_THREADS: int = get_val("MAX_MAX_PROCESSES_AND_OR_THREADS", 120, int)

        # Flags
        self.ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT: bool = get_val("ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT", False, bool)
        self.ALLOW_ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT: bool = get_val("ALLOW_ENABLE_PER_PROCESS_AND_THREAD_TIME_LIMIT", True, bool)
        self.ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT: bool = get_val("ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT", False, bool)
        self.ALLOW_ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT: bool = get_val("ALLOW_ENABLE_PER_PROCESS_AND_THREAD_MEMORY_LIMIT", True, bool)

        # File size limit (in KB)
        self.MAX_FILE_SIZE: int = get_val("MAX_FILE_SIZE", 10240, int)
        self.MAX_MAX_FILE_SIZE: int = get_val("MAX_MAX_FILE_SIZE", 51200, int)

        # Runs
        self.NUMBER_OF_RUNS: int = get_val("NUMBER_OF_RUNS", 1, int)
        self.MAX_NUMBER_OF_RUNS: int = get_val("MAX_NUMBER_OF_RUNS", 10, int)

        # Worker count & Queue
        self.COUNT: int = get_val("COUNT", 8, int)  # 8 worker threads for high concurrency
        self.MAX_QUEUE_SIZE: int = get_val("MAX_QUEUE_SIZE", 1000, int)
        self.SUBMISSION_CACHE_DURATION: int = get_val("SUBMISSION_CACHE_DURATION", 3600, int)

        # Webhook / Callbacks
        self.ENABLE_CALLBACKS: bool = get_val("ENABLE_CALLBACKS", True, bool)
        self.CALLBACK_TIMEOUT: float = get_val("CALLBACK_TIMEOUT", 5.0, float)

        # Compiler options allowed languages (empty = all allowed)
        self.ALLOWED_LANGUAGES_FOR_COMPILER_OPTIONS: List[str] = get_val("ALLOWED_LANGUAGES_FOR_COMPILER_OPTIONS", [], list)

        # Sandbox directory
        self.SANDBOX_BASE_DIR: str = get_val("SANDBOX_BASE_DIR", "/tmp/judge0_sandbox", str)


settings = Settings()
