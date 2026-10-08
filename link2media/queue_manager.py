"""Job queue manager, concurrency limiter, session registry, and cleanup."""

from __future__ import annotations

import asyncio
import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set

from .config import Settings
from .models import DownloadResult, JobProgress, TextSession, UserSession

logger = logging.getLogger(__name__)


@dataclass
class ActiveJob:
    job_id: str
    user_id: int
    chat_id: int
    cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    progress_queue: asyncio.Queue[JobProgress] = field(default_factory=asyncio.Queue)
    temp_dir: Optional[Path] = None
    task: Optional[asyncio.Task] = None
    created_at: float = field(default_factory=time.time)


class QueueManager:
    """Coordinates concurrent download jobs, per-user limits, and sessions."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_jobs)
        self.active_jobs: Dict[str, ActiveJob] = {}  # job_id -> ActiveJob
        self.user_to_job: Dict[int, str] = {}  # user_id -> job_id
        self.sessions: Dict[str, UserSession] = {}  # session_id -> UserSession
        self.text_sessions: Dict[str, TextSession] = {}  # session_id -> TextSession
        self._waiting_count = 0
        self._lock = asyncio.Lock()

    def cleanup_stale_directories(self) -> None:
        """Clean all lingering job directories on bot startup or restart."""
        temp_dir = self.settings.temp_dir
        if not temp_dir.exists():
            return
        logger.info("Cleaning stale temporary directories in %s...", temp_dir)
        for item in temp_dir.iterdir():
            if item.is_dir() and item.name.startswith("job_"):
                try:
                    shutil.rmtree(item, ignore_errors=True)
                except Exception as exc:
                    logger.warning("Failed to remove stale dir %s: %s", item, exc)

    def clean_job_dir(self, target_dir: Optional[Path]) -> None:
        """Safely delete a job temporary directory."""
        if target_dir and target_dir.exists():
            try:
                shutil.rmtree(target_dir, ignore_errors=True)
            except Exception as exc:
                logger.warning("Error cleaning job dir %s: %s", target_dir, exc)

    # ---------------- Session Handling ----------------

    def store_session(self, session: UserSession) -> None:
        self.expire_stale_sessions()
        self.sessions[session.session_id] = session

    def get_session(self, session_id: str) -> Optional[UserSession]:
        self.expire_stale_sessions()
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def expire_stale_sessions(self) -> None:
        now = time.time()
        ttl = self.settings.session_ttl
        expired = [sid for sid, s in self.sessions.items() if now - s.created_at > ttl]
        for sid in expired:
            self.sessions.pop(sid, None)

    # ---------------- Text Session Handling ----------------

    def store_text_session(self, session: TextSession) -> None:
        self.expire_stale_text_sessions()
        self.text_sessions[session.session_id] = session

    def get_text_session(self, session_id: str) -> Optional[TextSession]:
        self.expire_stale_text_sessions()
        return self.text_sessions.get(session_id)

    def remove_text_session(self, session_id: str) -> None:
        self.text_sessions.pop(session_id, None)

    def expire_stale_text_sessions(self) -> None:
        now = time.time()
        ttl = self.settings.session_ttl
        expired = [sid for sid, s in self.text_sessions.items() if now - s.created_at > ttl]
        for sid in expired:
            self.text_sessions.pop(sid, None)

    # ---------------- Job Handling ----------------

    async def can_enqueue(self, user_id: int) -> tuple[bool, Optional[str]]:
        """Check if user is allowed to submit a new job."""
        async with self._lock:
            if user_id in self.user_to_job:
                return False, "busy_user"
            if self._waiting_count >= self.settings.max_queue_size:
                return False, "queue_full"
            return True, None

    async def register_job(self, job: ActiveJob) -> bool:
        async with self._lock:
            if job.user_id in self.user_to_job:
                return False
            self.active_jobs[job.job_id] = job
            self.user_to_job[job.user_id] = job.job_id
            self._waiting_count += 1
            return True

    async def unregister_job(self, job_id: str) -> None:
        async with self._lock:
            job = self.active_jobs.pop(job_id, None)
            if job:
                self.user_to_job.pop(job.user_id, None)
                if job.temp_dir:
                    self.clean_job_dir(job.temp_dir)

    async def cancel_user_job(self, user_id: int) -> bool:
        """Signal cancellation for user's active job."""
        async with self._lock:
            job_id = self.user_to_job.get(user_id)
            if not job_id:
                return False
            job = self.active_jobs.get(job_id)
            if job:
                job.cancel_event.set()
                if job.task and not job.task.done():
                    job.task.cancel()
                if job.temp_dir:
                    self.clean_job_dir(job.temp_dir)
                return True
            return False

    def get_queue_position(self, job_id: str) -> int:
        """Get approximate queue position for a waiting job."""
        pos = 1
        for jid in self.active_jobs.keys():
            if jid == job_id:
                return pos
            pos += 1
        return pos
