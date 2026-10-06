"""Data models for media extraction, options, and download jobs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional


@dataclass
class VideoQualityOption:
    """A selectable video quality tier."""

    height: int  # e.g. 360, 480, 720, 1080
    label: str  # e.g. "360p", "720p HD", "1080p FHD"
    format_selector: str
    estimated_size_bytes: Optional[int] = None
    has_audio: bool = True
    is_oversized: bool = False

    @property
    def display_size(self) -> str:
        if not self.estimated_size_bytes:
            return ""
        mb = self.estimated_size_bytes / 1_000_000
        return f" (~{mb:.1f} MB)"


@dataclass
class AudioOption:
    """A selectable audio bitrate tier."""

    bitrate_kbps: int  # 128 or 192
    estimated_size_bytes: Optional[int] = None

    @property
    def display_size(self) -> str:
        if not self.estimated_size_bytes:
            return ""
        mb = self.estimated_size_bytes / 1_000_000
        return f" (~{mb:.1f} MB)"


@dataclass
class MediaInfo:
    """Extracted metadata for a validated media URL."""

    url: str
    platform: str
    title: str
    uploader: Optional[str] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    has_audio: bool = True
    is_live: bool = False
    is_playlist: bool = False
    source_audio_bitrate_kbps: Optional[int] = None
    video_qualities: List[VideoQualityOption] = field(default_factory=list)
    audio_options: List[AudioOption] = field(default_factory=list)
    webpage_url: Optional[str] = None

    @property
    def formatted_duration(self) -> str:
        if not self.duration_seconds or self.duration_seconds <= 0:
            return ""
        mins, secs = divmod(self.duration_seconds, 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            return f"{hours}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"


@dataclass
class UserSession:
    """Temporary state storing media info awaiting user button click."""

    session_id: str
    user_id: int
    chat_id: int
    media_info: MediaInfo
    created_at: float
    status_message_id: Optional[int] = None


@dataclass
class JobProgress:
    """Progress snapshot reported back to Telegram status updater."""

    stage: str  # checking, queued, downloading, converting, uploading, done, failed, cancelled
    percent: Optional[float] = None
    queue_pos: Optional[int] = None
    extra_text: Optional[str] = None


@dataclass
class DownloadResult:
    """Final output of download & conversion process."""

    success: bool
    file_path: Optional[Path] = None
    file_type: str = "video"  # "video" or "audio"
    title: str = ""
    duration_seconds: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail_path: Optional[Path] = None
    file_size_bytes: int = 0
    error_key: Optional[str] = None
    error_detail: Optional[str] = None
    temp_dir: Optional[Path] = None
