"""Configuration loading.

All settings come from environment variables (optionally loaded from a local
``.env`` file).  The bot token is never printed: it is excluded from ``repr``
and error messages only mention the variable name.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# The public Bot API server accepts uploads of "up to 50 MB" for non-photo
# files (https://core.telegram.org/bots/api#sending-files).  We interpret MB
# conservatively as 1,000,000 bytes so the configured budget can never exceed
# the real limit.
TELEGRAM_UPLOAD_HARD_LIMIT = 50_000_000

_TOKEN_RE = re.compile(r"^\d{5,16}:[A-Za-z0-9_-]{30,}$")


class ConfigError(Exception):
    """Raised for missing or invalid settings (message is safe to print)."""


def _get_int(name: str, default: int, *, minimum: int | None = None,
             maximum: int | None = None) -> int:
    raw = os.getenv(name, "").strip().replace("_", "")
    if not raw:
        value = default
    else:
        try:
            value = int(raw)
        except ValueError as exc:
            raise ConfigError(f"{name} must be a whole number (got {raw!r}).") from exc
    if minimum is not None and value < minimum:
        raise ConfigError(f"{name} must be at least {minimum} (got {value}).")
    if maximum is not None and value > maximum:
        raise ConfigError(f"{name} must be at most {maximum} (got {value}).")
    return value


def _get_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number (got {raw!r}).") from exc
    if value < minimum:
        raise ConfigError(f"{name} must be at least {minimum}.")
    return value


def _parse_user_ids(raw: str) -> frozenset[int]:
    ids: set[int] = set()
    for part in re.split(r"[,\s;]+", raw.strip()):
        if not part:
            continue
        if not part.isdigit():
            raise ConfigError(
                f"ALLOWED_USER_IDS must contain numeric Telegram user IDs (got {part!r})."
            )
        ids.add(int(part))
    return frozenset(ids)


def find_binary(name: str, override: str | None) -> str | None:
    """Return a usable path for an executable, or ``None`` if not found."""
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file():
            return str(candidate)
        found = shutil.which(override)
        return found
    found = shutil.which(name)
    if found:
        return found
    # pip-installed executables (e.g. ``deno`` from PyPI) live next to the
    # virtualenv's python, which is not on PATH if the venv is not activated.
    exe = name + (".exe" if os.name == "nt" else "")
    local = Path(sys.executable).parent / exe
    if local.is_file():
        return str(local)
    return None


@dataclass(frozen=True)
class Settings:
    bot_token: str = field(repr=False)
    allowed_user_ids: frozenset[int] = frozenset()

    data_dir: Path = PROJECT_ROOT / "data"
    temp_dir: Path = PROJECT_ROOT / "data" / "tmp"
    db_path: Path = PROJECT_ROOT / "data" / "link2media.sqlite3"
    cache_dir: Path = PROJECT_ROOT / "data" / "cache"

    max_duration_seconds: int = 20 * 60
    max_upload_bytes: int = 48_000_000
    max_download_bytes: int = 200_000_000
    max_job_disk_bytes: int = 600_000_000
    min_free_disk_bytes: int = 500_000_000

    max_concurrent_jobs: int = 2
    max_queue_size: int = 10
    max_concurrent_checks: int = 4

    extract_timeout: int = 90
    download_timeout: int = 600
    convert_timeout: int = 600
    job_timeout: int = 1200
    upload_timeout: int = 600
    session_ttl: int = 900
    status_interval: float = 3.0

    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"
    deno_path: str | None = None
    log_level: str = "INFO"

    def worker_limits(self) -> dict:
        """Plain-data limits passed to worker processes (no secrets)."""
        return {
            "max_duration": self.max_duration_seconds,
            "max_upload": self.max_upload_bytes,
            "max_download": self.max_download_bytes,
            "max_disk": self.max_job_disk_bytes,
            "min_free_disk": self.min_free_disk_bytes,
            "download_timeout": self.download_timeout,
            "convert_timeout": self.convert_timeout,
            "ffmpeg": self.ffmpeg_path,
            "ffprobe": self.ffprobe_path,
            "deno": self.deno_path,
            "cache_dir": str(self.cache_dir),
        }


def load_settings(env_file: str | os.PathLike | None = None, *,
                  require_token: bool = True) -> Settings:
    """Load settings from ``.env`` (if present) and the environment."""
    env_path = Path(env_file) if env_file else PROJECT_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)

    token = os.getenv("BOT_TOKEN", "").strip()
    if require_token:
        if not token or "PASTE" in token.upper() or token.lower().startswith("your"):
            raise ConfigError(
                "BOT_TOKEN is missing. Copy .env.example to .env and put the token "
                "from @BotFather after BOT_TOKEN=."
            )
        if not _TOKEN_RE.match(token):
            raise ConfigError(
                "BOT_TOKEN does not look like a Telegram bot token "
                "(expected digits, a colon, then letters). Check your .env file."
            )

    data_dir = Path(os.getenv("DATA_DIR", "").strip() or PROJECT_ROOT / "data")
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir

    max_upload = _get_int("MAX_UPLOAD_BYTES", 48_000_000, minimum=1_000_000,
                          maximum=TELEGRAM_UPLOAD_HARD_LIMIT)
    max_download = _get_int("MAX_DOWNLOAD_BYTES", 200_000_000, minimum=max_upload)
    max_disk = _get_int("MAX_JOB_DISK_BYTES", 600_000_000, minimum=max_download)

    ffmpeg = find_binary("ffmpeg", os.getenv("FFMPEG_PATH", "").strip() or None)
    ffprobe = find_binary("ffprobe", os.getenv("FFPROBE_PATH", "").strip() or None)
    deno = find_binary("deno", os.getenv("DENO_PATH", "").strip() or None)

    log_level = (os.getenv("LOG_LEVEL", "INFO").strip() or "INFO").upper()
    if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
        raise ConfigError("LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR.")

    max_concurrent = _get_int("MAX_CONCURRENT_JOBS", 2, minimum=1, maximum=16)

    return Settings(
        bot_token=token,
        allowed_user_ids=_parse_user_ids(os.getenv("ALLOWED_USER_IDS", "")),
        data_dir=data_dir,
        temp_dir=data_dir / "tmp",
        db_path=data_dir / "link2media.sqlite3",
        cache_dir=data_dir / "cache",
        max_duration_seconds=_get_int("MAX_DURATION_SECONDS", 20 * 60, minimum=10,
                                      maximum=6 * 3600),
        max_upload_bytes=max_upload,
        max_download_bytes=max_download,
        max_job_disk_bytes=max_disk,
        min_free_disk_bytes=_get_int("MIN_FREE_DISK_BYTES", 500_000_000, minimum=0),
        max_concurrent_jobs=max_concurrent,
        max_queue_size=_get_int("MAX_QUEUE_SIZE", 10, minimum=0, maximum=1000),
        max_concurrent_checks=_get_int("MAX_CONCURRENT_CHECKS", max(2, max_concurrent * 2),
                                       minimum=1, maximum=32),
        extract_timeout=_get_int("EXTRACT_TIMEOUT_SECONDS", 90, minimum=10),
        download_timeout=_get_int("DOWNLOAD_TIMEOUT_SECONDS", 600, minimum=30),
        convert_timeout=_get_int("CONVERT_TIMEOUT_SECONDS", 600, minimum=30),
        job_timeout=_get_int("JOB_TIMEOUT_SECONDS", 1200, minimum=60),
        upload_timeout=_get_int("UPLOAD_TIMEOUT_SECONDS", 600, minimum=30),
        session_ttl=_get_int("SESSION_TTL_SECONDS", 900, minimum=60),
        status_interval=_get_float("STATUS_UPDATE_INTERVAL", 3.0, minimum=1.0),
        ffmpeg_path=ffmpeg or "",
        ffprobe_path=ffprobe or "",
        deno_path=deno,
        log_level=log_level,
    )
