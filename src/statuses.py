"""
Judge0 Standard Status Codes and Descriptions.
Matches official Judge0 specifications.
"""
from typing import Dict, List, Any

STATUS_IN_QUEUE = 1
STATUS_PROCESSING = 2
STATUS_ACCEPTED = 3
STATUS_WRONG_ANSWER = 4
STATUS_TIME_LIMIT_EXCEEDED = 5
STATUS_COMPILATION_ERROR = 6
STATUS_RUNTIME_ERROR_SIGSEGV = 7
STATUS_RUNTIME_ERROR_SIGXFSZ = 8
STATUS_RUNTIME_ERROR_SIGFPE = 9
STATUS_RUNTIME_ERROR_SIGABRT = 10
STATUS_RUNTIME_ERROR_NZEC = 11
STATUS_RUNTIME_ERROR_OTHER = 12
STATUS_INTERNAL_ERROR = 13
STATUS_EXEC_FORMAT_ERROR = 14

STATUS_DESCRIPTIONS: Dict[int, str] = {
    STATUS_IN_QUEUE: "In Queue",
    STATUS_PROCESSING: "Processing",
    STATUS_ACCEPTED: "Accepted",
    STATUS_WRONG_ANSWER: "Wrong Answer",
    STATUS_TIME_LIMIT_EXCEEDED: "Time Limit Exceeded",
    STATUS_COMPILATION_ERROR: "Compilation Error",
    STATUS_RUNTIME_ERROR_SIGSEGV: "Runtime Error (SIGSEGV)",
    STATUS_RUNTIME_ERROR_SIGXFSZ: "Runtime Error (SIGXFSZ)",
    STATUS_RUNTIME_ERROR_SIGFPE: "Runtime Error (SIGFPE)",
    STATUS_RUNTIME_ERROR_SIGABRT: "Runtime Error (SIGABRT)",
    STATUS_RUNTIME_ERROR_NZEC: "Runtime Error (NZEC)",
    STATUS_RUNTIME_ERROR_OTHER: "Runtime Error (Other)",
    STATUS_INTERNAL_ERROR: "Internal Error",
    STATUS_EXEC_FORMAT_ERROR: "Exec Format Error",
}


def get_status_dict(status_id: int) -> Dict[str, Any]:
    """Get status representation as dict."""
    return {
        "id": status_id,
        "description": STATUS_DESCRIPTIONS.get(status_id, "Unknown Status"),
    }


def get_all_statuses() -> List[Dict[str, Any]]:
    """Return all standard statuses as a list of dicts."""
    return [
        {"id": sid, "description": desc}
        for sid, desc in sorted(STATUS_DESCRIPTIONS.items())
    ]
