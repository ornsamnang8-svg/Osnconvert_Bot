"""Download executor and orchestrator with progress tracking and size guards."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yt_dlp

from .config import Settings
from .convert import (
    check_free_space,
    convert_to_mp3,
    convert_to_mp4,
    extract_thumbnail_jpg,
    probe_file,
)
from .extract import _build_ydl_opts, classify_yt_dlp_error
from .models import DownloadResult, JobProgress
from .security import sanitize_filename

logger = logging.getLogger(__name__)


class DownloadAborted(Exception):
    """Raised when download was aborted due to size limit or cancellation."""


def run_download_sync(
    url: str,
    format_selector: str,
    output_template: str,
    temp_dir: Path,
    settings: Settings,
    progress_callback: Optional[Callable[[float], None]] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Path:
    """
    Run yt-dlp download synchronously with progress hook and size limiter.
    Returns path of downloaded file.
    """
    downloaded_file: Optional[Path] = None

    def _hook(d: Dict[str, Any]) -> None:
        if cancel_check and cancel_check():
            raise DownloadAborted("Cancelled by user")

        # Disk space check
        if not check_free_space(temp_dir, settings.min_free_disk_bytes):
            raise DownloadAborted("Server disk space low")

        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes") or 0

            # Guard against exceeding max download bytes
            if downloaded > settings.max_download_bytes:
                raise DownloadAborted(
                    f"Download exceeded size budget ({downloaded} > {settings.max_download_bytes})"
                )

            if total > 0 and progress_callback:
                pct = round((downloaded / total) * 100, 1)
                progress_callback(pct)

        elif status == "finished":
            fn = d.get("filename")
            if fn:
                nonlocal downloaded_file
                downloaded_file = Path(fn)
                if progress_callback:
                    progress_callback(100.0)

    ydl_opts = _build_ydl_opts(
        settings,
        {
            "format": format_selector,
            "outtmpl": output_template,
            "progress_hooks": [_hook],
            "overwrites": True,
            "updatetime": False,
        },
    )

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if not downloaded_file or not downloaded_file.exists():
        # Search temp_dir for any downloaded media file if filename wasn't captured in hook
        files = [p for p in temp_dir.iterdir() if p.is_file() and not p.name.endswith(".part")]
        if files:
            # Sort by newest / largest
            files.sort(key=lambda p: p.stat().st_size, reverse=True)
            downloaded_file = files[0]
        else:
            raise FileNotFoundError("Downloaded file could not be located in temp directory.")

    return downloaded_file


async def execute_download_job(
    url: str,
    target_type: str,  # "video" or "audio"
    target_option: Any,  # VideoQualityOption or AudioOption
    title: str,
    uploader: Optional[str],
    settings: Settings,
    job_id: str,
    progress_queue: asyncio.Queue[JobProgress],
    cancel_event: asyncio.Event,
) -> DownloadResult:
    """
    Execute full download, conversion, and validation pipeline.
    """
    job_dir = settings.temp_dir / f"job_{job_id}"
    job_dir.mkdir(parents=True, exist_ok=True)

    clean_title = sanitize_filename(title)
    output_tmpl = str(job_dir / f"{clean_title}.%(ext)s")

    last_pct = 0.0

    def _on_progress(pct: float) -> None:
        nonlocal last_pct
        if abs(pct - last_pct) >= 5.0 or pct >= 100.0:
            last_pct = pct
            try:
                progress_queue.put_nowait(
                    JobProgress(stage="downloading", percent=pct)
                )
            except Exception:
                pass

    try:
        # Pre-check disk space
        if not check_free_space(job_dir, settings.min_free_disk_bytes):
            return DownloadResult(
                success=False,
                error_key="err_disk_full",
                temp_dir=job_dir,
            )

        await progress_queue.put(JobProgress(stage="downloading", percent=0.0))

        if target_type == "video":
            selector = getattr(target_option, "format_selector", "bestvideo+bestaudio/best")
        else:
            selector = "bestaudio/best"

        # Run yt-dlp in thread
        raw_downloaded = await asyncio.to_thread(
            run_download_sync,
            url=url,
            format_selector=selector,
            output_template=output_tmpl,
            temp_dir=job_dir,
            settings=settings,
            progress_callback=_on_progress,
            cancel_check=cancel_event.is_set,
        )

        if cancel_event.is_set():
            return DownloadResult(
                success=False,
                error_key="cancelled",
                temp_dir=job_dir,
            )

        # Stage: Converting
        await progress_queue.put(JobProgress(stage="converting"))

        final_path: Path
        duration: Optional[int] = None
        width: Optional[int] = None
        height: Optional[int] = None
        thumb_path: Optional[Path] = None

        if target_type == "video":
            final_path = job_dir / f"{clean_title}_final.mp4"
            conv_ok, conv_err = await convert_to_mp4(
                ffmpeg_bin=settings.ffmpeg_path,
                ffprobe_bin=settings.ffprobe_path,
                input_file=raw_downloaded,
                output_file=final_path,
                timeout_seconds=settings.convert_timeout,
                cancel_event=cancel_event,
            )
            if not conv_ok:
                logger.error("FFmpeg mp4 conversion error: %s", conv_err)
                return DownloadResult(
                    success=False,
                    error_key="err_internal",
                    error_detail=conv_err,
                    temp_dir=job_dir,
                )

            # Inspect dimensions & duration
            probe_info = await probe_file(settings.ffprobe_path, final_path)
            streams = probe_info.get("streams", [])
            v_s = next((s for s in streams if s.get("codec_type") == "video"), {})
            width = v_s.get("width")
            height = v_s.get("height")
            fmt = probe_info.get("format", {})
            try:
                duration = int(float(fmt.get("duration", 0)))
            except (ValueError, TypeError):
                duration = None

            # Generate thumbnail
            cand_thumb = job_dir / "thumb.jpg"
            if await extract_thumbnail_jpg(settings.ffmpeg_path, final_path, cand_thumb):
                thumb_path = cand_thumb

        else:
            # Audio (MP3)
            final_path = job_dir / f"{clean_title}.mp3"
            bitrate = getattr(target_option, "bitrate_kbps", 128)
            conv_ok, conv_err = await convert_to_mp3(
                ffmpeg_bin=settings.ffmpeg_path,
                input_file=raw_downloaded,
                output_file=final_path,
                bitrate_kbps=bitrate,
                title=clean_title,
                artist=uploader,
                timeout_seconds=settings.convert_timeout,
                cancel_event=cancel_event,
            )
            if not conv_ok:
                logger.error("FFmpeg mp3 conversion error: %s", conv_err)
                return DownloadResult(
                    success=False,
                    error_key="err_internal",
                    error_detail=conv_err,
                    temp_dir=job_dir,
                )

            probe_info = await probe_file(settings.ffprobe_path, final_path)
            fmt = probe_info.get("format", {})
            try:
                duration = int(float(fmt.get("duration", 0)))
            except (ValueError, TypeError):
                duration = None

        # Verify final file exists and check file size
        if not final_path.exists():
            return DownloadResult(
                success=False,
                error_key="err_internal",
                temp_dir=job_dir,
            )

        file_size = final_path.stat().st_size
        if file_size > settings.max_upload_bytes:
            mb = file_size / 1_000_000
            max_mb = settings.max_upload_bytes / 1_000_000
            return DownloadResult(
                success=False,
                error_key="err_too_large",
                error_detail=f"File is {mb:.1f} MB (limit is {max_mb:.0f} MB)",
                file_size_bytes=file_size,
                temp_dir=job_dir,
            )

        return DownloadResult(
            success=True,
            file_path=final_path,
            file_type=target_type,
            title=title,
            duration_seconds=duration,
            width=width,
            height=height,
            thumbnail_path=thumb_path,
            file_size_bytes=file_size,
            temp_dir=job_dir,
        )

    except DownloadAborted as exc:
        msg = str(exc)
        if "Cancelled" in msg:
            return DownloadResult(success=False, error_key="cancelled", temp_dir=job_dir)
        if "size budget" in msg:
            return DownloadResult(success=False, error_key="err_too_large", temp_dir=job_dir)
        if "disk space" in msg:
            return DownloadResult(success=False, error_key="err_disk_full", temp_dir=job_dir)
        return DownloadResult(success=False, error_key="err_internal", error_detail=msg, temp_dir=job_dir)

    except yt_dlp.utils.DownloadError as exc:
        key = classify_yt_dlp_error(str(exc))
        return DownloadResult(success=False, error_key=key, error_detail=str(exc), temp_dir=job_dir)

    except Exception as exc:
        logger.exception("Unexpected error in download job: %s", exc)
        return DownloadResult(success=False, error_key="err_internal", error_detail=str(exc), temp_dir=job_dir)
