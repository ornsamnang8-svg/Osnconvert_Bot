"""FFmpeg conversion and FFprobe media inspection utilities."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil

logger = logging.getLogger(__name__)


def kill_process_tree(pid: int) -> None:
    """Safely terminate a process and all its child processes."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        parent.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass


def check_free_space(target_path: Path, required_bytes: int) -> bool:
    """Verify disk where target_path resides has at least required_bytes free."""
    try:
        usage = shutil.disk_usage(target_path.parent if target_path.parent.exists() else target_path.anchor)
        return usage.free >= required_bytes
    except Exception as exc:
        logger.warning("Could not check disk usage: %s", exc)
        return True


def probe_file_sync(ffprobe_bin: str, file_path: Path) -> Dict[str, Any]:
    """Run ffprobe synchronously on a media file to inspect codecs, dimensions, duration."""
    cmd = [
        ffprobe_bin or "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        return json.loads(res.stdout)
    except Exception as exc:
        logger.warning("ffprobe failed on %s: %s", str(file_path), exc)
        return {}


async def probe_file(ffprobe_bin: str, file_path: Path) -> Dict[str, Any]:
    """Asynchronous ffprobe runner."""
    return await asyncio.to_thread(probe_file_sync, ffprobe_bin, file_path)


async def run_cancellable_command(
    cmd: List[str],
    timeout_seconds: int,
    cancel_event: Optional[asyncio.Event] = None,
) -> Tuple[bool, str]:
    """
    Run subprocess without shell interpolation, supporting cancellation and timeout.
    Returns: (success: bool, stderr_output: str)
    """
    proc: Optional[asyncio.subprocess.Process] = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async def _wait_proc() -> Tuple[bytes, bytes]:
            assert proc is not None
            return await proc.communicate()

        wait_task = asyncio.create_task(_wait_proc())

        if cancel_event is not None:
            cancel_task = asyncio.create_task(cancel_event.wait())
            done, pending = await asyncio.wait(
                [wait_task, cancel_task],
                return_when=asyncio.FIRST_COMPLETED,
                timeout=timeout_seconds,
            )
            for t in pending:
                t.cancel()

            if cancel_event.is_set():
                if proc.pid:
                    kill_process_tree(proc.pid)
                return False, "Cancelled by user"

            if wait_task in done:
                stdout_b, stderr_b = wait_task.result()
                success = proc.returncode == 0
                return success, stderr_b.decode("utf-8", errors="replace")
            else:
                # Timed out
                if proc.pid:
                    kill_process_tree(proc.pid)
                return False, f"Process timed out after {timeout_seconds}s"
        else:
            try:
                stdout_b, stderr_b = await asyncio.wait_for(wait_task, timeout=timeout_seconds)
                success = proc.returncode == 0
                return success, stderr_b.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                if proc and proc.pid:
                    kill_process_tree(proc.pid)
                return False, f"Process timed out after {timeout_seconds}s"

    except Exception as exc:
        if proc and proc.pid:
            kill_process_tree(proc.pid)
        return False, str(exc)


async def convert_to_mp4(
    ffmpeg_bin: str,
    ffprobe_bin: str,
    input_file: Path,
    output_file: Path,
    timeout_seconds: int = 600,
    cancel_event: Optional[asyncio.Event] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Convert or remux input video to a Telegram-playable MP4 container.
    Guarantees:
      - Video: H.264, yuv420p
      - Audio: AAC (if audio present)
      - MOOV atom placed at beginning: +faststart
    """
    if not input_file.exists():
        return False, f"Input file not found: {input_file}"

    # Probe file to see if we can copy streams directly (remux) or need transcode
    probe_data = await probe_file(ffprobe_bin, input_file)
    streams = probe_data.get("streams", [])
    has_video = any(s.get("codec_type") == "video" for s in streams)
    has_audio = any(s.get("codec_type") == "audio" for s in streams)

    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    v_codec = v_stream.get("codec_name", "").lower()
    pix_fmt = v_stream.get("pix_fmt", "").lower()

    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    a_codec = a_stream.get("codec_name", "").lower()

    # Fast copy if already H.264 + yuv420p + (aac or no audio)
    can_copy_video = v_codec in ("h264", "avc1") and pix_fmt == "yuv420p"
    can_copy_audio = (not has_audio) or (a_codec in ("aac",))

    cmd = [
        ffmpeg_bin or "ffmpeg",
        "-y",
        "-i", str(input_file),
    ]

    if can_copy_video and can_copy_audio:
        # Stream copy (super fast)
        cmd.extend(["-c", "copy"])
    else:
        if can_copy_video:
            cmd.extend(["-c:v", "copy"])
        else:
            cmd.extend([
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
            ])

        if has_audio:
            if can_copy_audio:
                cmd.extend(["-c:a", "copy"])
            else:
                cmd.extend(["-c:a", "aac", "-b:a", "128k"])

    cmd.extend([
        "-movflags", "+faststart",
        str(output_file),
    ])

    success, err_out = await run_cancellable_command(cmd, timeout_seconds, cancel_event)
    if not success or not output_file.exists():
        return False, err_out
    return True, None


async def convert_to_mp3(
    ffmpeg_bin: str,
    input_file: Path,
    output_file: Path,
    bitrate_kbps: int = 128,
    title: Optional[str] = None,
    artist: Optional[str] = None,
    timeout_seconds: int = 600,
    cancel_event: Optional[asyncio.Event] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Actually convert audio to genuine MP3 using libmp3lame (never just rename).
    Injects ID3 metadata tags.
    """
    if not input_file.exists():
        return False, f"Input file not found: {input_file}"

    bitrate_str = f"{bitrate_kbps}k"
    cmd = [
        ffmpeg_bin or "ffmpeg",
        "-y",
        "-i", str(input_file),
        "-vn",  # No video
        "-c:a", "libmp3lame",
        "-b:a", bitrate_str,
    ]

    if title:
        cmd.extend(["-metadata", f"title={title}"])
    if artist:
        cmd.extend(["-metadata", f"artist={artist}"])

    cmd.append(str(output_file))

    success, err_out = await run_cancellable_command(cmd, timeout_seconds, cancel_event)
    if not success or not output_file.exists():
        return False, err_out
    return True, None


async def extract_thumbnail_jpg(
    ffmpeg_bin: str,
    input_file: Path,
    output_thumb: Path,
    timeout_seconds: int = 30,
) -> bool:
    """Generate a thumbnail JPG from a video file using ffmpeg."""
    cmd = [
        ffmpeg_bin or "ffmpeg",
        "-y",
        "-ss", "00:00:01",
        "-i", str(input_file),
        "-vframes", "1",
        "-q:v", "3",
        str(output_thumb),
    ]
    success, _ = await run_cancellable_command(cmd, timeout_seconds)
    return success and output_thumb.exists()
