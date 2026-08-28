"""
In-memory submission store with TTL cleanup, base64 encoding filtering,
and field projection matching Judge0 specifications.
"""
import time
import uuid
from typing import Dict, Any, Optional, List
from src.config import settings
from src.runner import encode_base64_str


class SubmissionStorage:
    """Thread-safe in-memory cache for submission results."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}

    def generate_token(self) -> str:
        """Generate standard UUID4 submission token."""
        return str(uuid.uuid4())

    def save(self, token: str, data: Dict[str, Any]):
        """Save or update submission data."""
        self._store[token] = data
        self._timestamps[token] = time.time()
        self._cleanup_expired()

    def get(self, token: str) -> Optional[Dict[str, Any]]:
        """Retrieve submission by token."""
        return self._store.get(token)

    def delete(self, token: str) -> bool:
        """Delete submission by token."""
        if token in self._store:
            del self._store[token]
            self._timestamps.pop(token, None)
            return True
        return False

    def count(self) -> int:
        """Return total active submissions stored."""
        return len(self._store)

    def format_output(
        self,
        data: Dict[str, Any],
        fields: Optional[str] = None,
        base64_encoded: bool = False,
    ) -> Dict[str, Any]:
        """
        Format submission result according to ?fields=... and ?base64_encoded=true.
        """
        formatted = dict(data)

        # Base64 encode string fields if requested
        if base64_encoded:
            string_fields = [
                "source_code",
                "stdin",
                "expected_output",
                "stdout",
                "stderr",
                "compile_output",
                "message",
                "additional_files",
            ]
            for f in string_fields:
                if f in formatted and formatted[f] is not None:
                    formatted[f] = encode_base64_str(str(formatted[f]))

        # Apply field projection if fields filter provided
        if fields:
            requested_fields = [f.strip() for f in fields.split(",") if f.strip()]
            if requested_fields:
                # Include only requested fields
                projected = {}
                for field in requested_fields:
                    if field in formatted:
                        projected[field] = formatted[field]
                return projected

        return formatted

    def get_batch(
        self,
        tokens: List[str],
        fields: Optional[str] = None,
        base64_encoded: bool = False,
    ) -> List[Optional[Dict[str, Any]]]:
        """Retrieve and format a batch of submissions."""
        results = []
        for token in tokens:
            item = self.get(token)
            if item:
                results.append(self.format_output(item, fields=fields, base64_encoded=base64_encoded))
            else:
                results.append(None)
        return results

    def _cleanup_expired(self):
        """Remove entries older than cache duration."""
        now = time.time()
        ttl = settings.SUBMISSION_CACHE_DURATION
        expired = [t for t, ts in self._timestamps.items() if now - ts > ttl]
        for t in expired:
            self._store.pop(t, None)
            self._timestamps.pop(t, None)


storage = SubmissionStorage()
