import os
import time
import asyncio
import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from src.config import settings
from src.statuses import (
    STATUS_IN_QUEUE,
    STATUS_PROCESSING,
    get_status_dict,
)
from src.runner import execute_submission_sync, send_callback, safe_rmtree
from src.storage import storage


class QueueManager:
    """Manages worker pool and execution queue."""

    def __init__(self):
        self.queue: Optional[asyncio.Queue] = None
        self.workers: list[asyncio.Task] = []
        self.janitor_task: Optional[asyncio.Task] = None
        self.executor: Optional[ThreadPoolExecutor] = None
        self.events: Dict[str, asyncio.Event] = {}
        self.active_workers_count: int = 0
        self.is_running: bool = False

    async def start(self):
        """Start async background workers and janitor."""
        if self.is_running:
            return
        self.queue = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)
        self.executor = ThreadPoolExecutor(max_workers=max(32, settings.COUNT * 2))
        self.events.clear()
        self.is_running = True
        for i in range(settings.COUNT):
            worker_task = asyncio.create_task(self._worker_loop(i))
            self.workers.append(worker_task)
        # Start background janitor to auto-clean stale sandbox folders
        self.janitor_task = asyncio.create_task(self._janitor_loop())

    async def stop(self):
        """Stop worker tasks, executor, and janitor."""
        self.is_running = False
        if self.janitor_task:
            self.janitor_task.cancel()
        for task in self.workers:
            task.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.executor = None

    async def _janitor_loop(self):
        """Periodic background garbage collector for stale sandbox temp directories and cache."""
        while self.is_running:
            try:
                await asyncio.sleep(60)
                # 1. Clean expired submission results from in-memory cache
                storage._cleanup_expired()

                # 2. Sweep sandbox directory for stale directories older than 3 minutes (180s)
                sandbox_dir = settings.SANDBOX_BASE_DIR
                if os.path.exists(sandbox_dir):
                    now = time.time()
                    try:
                        for entry in os.scandir(sandbox_dir):
                            try:
                                if entry.is_dir() and (now - entry.stat().st_mtime > 180):
                                    safe_rmtree(entry.path)
                            except Exception:
                                pass
                    except Exception:
                        pass
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Janitor error: {e}")


    async def submit_job(
        self,
        token: str,
        submission_data: Dict[str, Any],
        is_base64: bool = False,
    ) -> asyncio.Event:
        """Enqueue a job and return a completion event."""
        now_str = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        initial_record = dict(submission_data)
        initial_record["token"] = token
        initial_record["status_id"] = STATUS_IN_QUEUE
        initial_record["status"] = get_status_dict(STATUS_IN_QUEUE)
        initial_record["created_at"] = now_str
        initial_record["finished_at"] = None

        storage.save(token, initial_record)

        event = asyncio.Event()
        self.events[token] = event

        if self.queue is None:
            self.queue = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)
        await self.queue.put((token, submission_data, is_base64))
        return event

    async def _worker_loop(self, worker_id: int):
        """Individual worker loop processing queued submissions."""
        while self.is_running and self.queue:
            try:
                token, submission_data, is_base64 = await self.queue.get()
                self.active_workers_count += 1

                # Update status to Processing
                current = storage.get(token) or submission_data
                current["status_id"] = STATUS_PROCESSING
                current["status"] = get_status_dict(STATUS_PROCESSING)
                storage.save(token, current)

                # Run submission in executor thread to prevent blocking asyncio loop
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    execute_submission_sync,
                    token,
                    submission_data,
                    is_base64,
                )

                # Update storage with final result
                storage.save(token, result)

                # Trigger webhook callback if configured
                callback_url = submission_data.get("callback_url")
                if callback_url and settings.ENABLE_CALLBACKS:
                    asyncio.create_task(send_callback(callback_url, result))

                # Notify waiting event if any
                event = self.events.pop(token, None)
                if event:
                    event.set()

                if self.queue:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
            finally:
                self.active_workers_count = max(0, self.active_workers_count - 1)

    def get_stats(self) -> Dict[str, Any]:
        """Return worker pool status."""
        return {
            "available_workers": settings.COUNT,
            "active_workers": self.active_workers_count,
            "idle_workers": max(0, settings.COUNT - self.active_workers_count),
            "queued_jobs": self.queue.qsize() if self.queue else 0,
            "status": "healthy" if self.is_running else "stopped",
        }



queue_manager = QueueManager()
