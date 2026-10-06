"""Tests for queue concurrency, per-user limits, cancellation, and cleanup."""

import asyncio
import time
from pathlib import Path
import pytest

from link2media.config import Settings
from link2media.models import MediaInfo, UserSession
from link2media.queue_manager import ActiveJob, QueueManager


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        bot_token="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789",
        data_dir=tmp_path / "data",
        temp_dir=tmp_path / "tmp",
        db_path=tmp_path / "test.db",
        cache_dir=tmp_path / "cache",
        max_concurrent_jobs=2,
        max_queue_size=2,
        session_ttl=2,  # 2 seconds for test
    )


@pytest.mark.asyncio
async def test_session_ownership_and_ttl(test_settings: Settings) -> None:
    queue_mgr = QueueManager(test_settings)

    media_info = MediaInfo(
        url="https://youtube.com/watch?v=123",
        platform="YouTube",
        title="Test Video",
    )

    session = UserSession(
        session_id="sess_123",
        user_id=1001,
        chat_id=1001,
        media_info=media_info,
        created_at=time.time(),
    )

    queue_mgr.store_session(session)
    retrieved = queue_mgr.get_session("sess_123")
    assert retrieved is not None
    assert retrieved.user_id == 1001

    # Ownership check simulation
    caller_legit = 1001
    caller_intruder = 9999
    assert retrieved.user_id == caller_legit
    assert retrieved.user_id != caller_intruder

    # Wait for TTL to expire
    await asyncio.sleep(2.5)
    assert queue_mgr.get_session("sess_123") is None


@pytest.mark.asyncio
async def test_single_active_job_per_user(test_settings: Settings) -> None:
    queue_mgr = QueueManager(test_settings)
    user_id = 5001

    can_enqueue, err = await queue_mgr.can_enqueue(user_id)
    assert can_enqueue is True
    assert err is None

    job = ActiveJob(job_id="job_1", user_id=user_id, chat_id=user_id)
    reg_ok = await queue_mgr.register_job(job)
    assert reg_ok is True

    # User attempts to submit another job while first is active
    can_enqueue_second, err_second = await queue_mgr.can_enqueue(user_id)
    assert can_enqueue_second is False
    assert err_second == "busy_user"

    # Finish job
    await queue_mgr.unregister_job("job_1")

    # Now allowed again
    can_enqueue_after, _ = await queue_mgr.can_enqueue(user_id)
    assert can_enqueue_after is True


@pytest.mark.asyncio
async def test_cancellation(test_settings: Settings) -> None:
    queue_mgr = QueueManager(test_settings)
    user_id = 7001

    job = ActiveJob(job_id="job_cancel_test", user_id=user_id, chat_id=user_id)
    await queue_mgr.register_job(job)
    assert not job.cancel_event.is_set()

    # User sends /cancel
    cancelled = await queue_mgr.cancel_user_job(user_id)
    assert cancelled is True
    assert job.cancel_event.is_set()

    # Cancel when nothing active
    cancelled_again = await queue_mgr.cancel_user_job(user_id)
    # The job is marked cancelled
    await queue_mgr.unregister_job("job_cancel_test")
    assert await queue_mgr.cancel_user_job(user_id) is False


def test_stale_directory_cleanup(test_settings: Settings) -> None:
    queue_mgr = QueueManager(test_settings)
    test_settings.temp_dir.mkdir(parents=True, exist_ok=True)

    stale_dir_1 = test_settings.temp_dir / "job_stale_1"
    stale_dir_2 = test_settings.temp_dir / "job_stale_2"
    keep_file = test_settings.temp_dir / "keep_this.txt"

    stale_dir_1.mkdir()
    stale_dir_2.mkdir()
    keep_file.write_text("keep")

    queue_mgr.cleanup_stale_directories()

    assert not stale_dir_1.exists()
    assert not stale_dir_2.exists()
    assert keep_file.exists()
