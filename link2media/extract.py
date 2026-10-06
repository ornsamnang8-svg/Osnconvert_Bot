"""Media metadata extraction using yt-dlp."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import yt_dlp

from .config import Settings
from .models import AudioOption, MediaInfo, VideoQualityOption

logger = logging.getLogger(__name__)

STANDARD_HEIGHT_TIERS = [1080, 720, 480, 360, 240, 144]


def classify_yt_dlp_error(error_msg: str) -> str:
    """Map yt-dlp raw error strings to i18n error keys."""
    msg = error_msg.lower()
    if any(k in msg for k in ("login", "sign in", "private video", "requires authentication", "account")):
        return "err_login_required"
    if any(k in msg for k in ("unavailable", "deleted", "not found", "does not exist", "removed")):
        return "err_unavailable"
    if any(k in msg for k in ("geo", "country", "region", "not available in")):
        return "err_geo_restricted"
    if any(k in msg for k in ("drm", "protected", "copyright")):
        return "err_drm"
    if any(k in msg for k in ("live stream", "is a live", "premieres in", "live event")):
        return "err_live"
    if any(k in msg for k in ("playlist",)):
        return "err_playlist"
    if any(k in msg for k in ("rate-limit", "too many requests", "http error 429")):
        return "err_rate_limited"
    if any(k in msg for k in ("connection", "timeout", "network", "remote end closed")):
        return "err_network"
    return "err_unsupported"


def _estimate_video_size(
    fmt: Dict[str, Any],
    duration: Optional[int],
    best_audio_fmt: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """Estimate file size in bytes for a video format."""
    # Direct filesize
    size = fmt.get("filesize") or fmt.get("filesize_approx")
    if size and size > 0:
        if fmt.get("acodec") == "none" and best_audio_fmt:
            a_size = best_audio_fmt.get("filesize") or best_audio_fmt.get("filesize_approx")
            if a_size:
                return size + a_size
            if duration and best_audio_fmt.get("abr"):
                return size + int((best_audio_fmt["abr"] * 1000 / 8) * duration)
        return size

    # Bitrate based calculation
    if duration and duration > 0:
        tbr = fmt.get("tbr")
        if tbr and tbr > 0:
            return int((tbr * 1000 / 8) * duration)
        vbr = fmt.get("vbr") or 0
        abr = fmt.get("abr") or (best_audio_fmt.get("abr") if best_audio_fmt else 128) or 128
        if vbr > 0:
            return int(((vbr + abr) * 1000 / 8) * duration)

    return None


def _build_ydl_opts(settings: Settings, custom_opts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create default safe yt-dlp options dictionary."""
    opts: Dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": False,
        "socket_timeout": 20,
        "cachedir": str(settings.cache_dir),
    }

    if settings.deno_path:
        opts["js_runtimes"] = {"deno": settings.deno_path}

    if settings.ffmpeg_path:
        opts["ffmpeg_location"] = settings.ffmpeg_path

    if custom_opts:
        opts.update(custom_opts)
    return opts


def _extract_sync(url: str, platform: str, settings: Settings) -> Tuple[Optional[MediaInfo], Optional[str], Optional[str]]:
    """Synchronous extraction worker run inside thread pool."""
    ydl_opts = _build_ydl_opts(settings)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        msg = str(exc)
        logger.warning("yt-dlp extraction failed for %s: %s", url, msg)
        key = classify_yt_dlp_error(msg)
        return None, key, msg
    except Exception as exc:
        logger.exception("Unexpected error in yt-dlp extraction: %s", exc)
        return None, "err_internal", str(exc)

    if not info:
        return None, "err_unsupported", "No info returned"

    # Reject playlist/multi-entry
    if info.get("_type") == "playlist" or (info.get("entries") and len(info.get("entries", [])) > 1):
        return None, "err_playlist", "Link contains multiple videos / playlist"

    # In case a single-entry playlist wraps the video
    if info.get("entries") and len(info["entries"]) == 1:
        info = info["entries"][0]

    # Check live streams
    is_live = bool(
        info.get("is_live")
        or info.get("was_live")
        or info.get("live_status") in ("is_live", "is_upcoming", "post_live")
    )
    if is_live:
        return None, "err_live", "Live stream detected"

    # Check duration limit
    duration = info.get("duration")
    if duration and duration > settings.max_duration_seconds:
        return None, "err_too_long", f"Duration {duration}s > {settings.max_duration_seconds}s"

    raw_formats = info.get("formats") or []
    title = (info.get("title") or "video").strip()
    uploader = info.get("uploader") or info.get("channel")
    thumbnail = info.get("thumbnail")

    # Analyze audio availability
    has_audio = False
    best_audio_fmt: Optional[Dict[str, Any]] = None
    best_audio_bitrate: Optional[int] = None

    for f in raw_formats:
        acodec = f.get("acodec")
        if acodec and acodec != "none":
            has_audio = True
            abr = f.get("abr") or 0
            if not best_audio_fmt or abr > (best_audio_fmt.get("abr") or 0):
                best_audio_fmt = f
                if abr > 0:
                    best_audio_bitrate = int(abr)

    # Analyze video formats and tiers up to 1080p
    video_formats = [f for f in raw_formats if f.get("vcodec") and f.get("vcodec") != "none"]
    if not video_formats and not raw_formats:
        return None, "err_no_formats", "No formats found"

    # Collect available heights
    available_heights = set()
    for f in video_formats:
        h = f.get("height")
        if h and isinstance(h, int) and h > 0:
            available_heights.add(h)

    # Filter and construct video options
    video_options: List[VideoQualityOption] = []
    # If no heights reported (e.g. some direct mp4s or specific extractors), offer standard "Best"
    if not available_heights:
        # Single best quality option
        est_size = None
        if raw_formats:
            est_size = _estimate_video_size(raw_formats[-1], duration, best_audio_fmt)
        video_options.append(
            VideoQualityOption(
                height=720,
                label="Normal Quality",
                format_selector="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                estimated_size_bytes=est_size,
                has_audio=has_audio,
                is_oversized=bool(est_size and est_size > settings.max_upload_bytes),
            )
        )
    else:
        # Determine which standard tiers are supported (never upscale beyond source max height)
        max_source_h = max(available_heights)
        # We cap at 1080p as per requirements
        capped_max_h = min(1080, max_source_h)

        matched_tiers = [tier for tier in STANDARD_HEIGHT_TIERS if tier <= capped_max_h]
        # Always include the highest available if not already in standard tiers
        if capped_max_h not in matched_tiers:
            matched_tiers.insert(0, capped_max_h)
            matched_tiers.sort(reverse=True)

        for tier in matched_tiers:
            # Pick format with height <= tier
            # Label
            if tier >= 1080:
                label = "1080p FHD"
            elif tier >= 720:
                label = "720p HD"
            elif tier >= 480:
                label = "480p SD"
            elif tier >= 360:
                label = "360p"
            else:
                label = f"{tier}p"

            selector = (
                f"bestvideo[height<={tier}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={tier}]+bestaudio/"
                f"best[height<={tier}][ext=mp4]/"
                f"best[height<={tier}]/best"
            )

            # Find matching format for size estimation
            candidate_f = None
            for f in sorted(video_formats, key=lambda x: x.get("height") or 0, reverse=True):
                if (f.get("height") or 0) <= tier:
                    candidate_f = f
                    break
            if not candidate_f and video_formats:
                candidate_f = video_formats[0]

            est_size = _estimate_video_size(candidate_f, duration, best_audio_fmt) if candidate_f else None
            is_oversized = bool(est_size and est_size > settings.max_upload_bytes)

            video_options.append(
                VideoQualityOption(
                    height=tier,
                    label=label,
                    format_selector=selector,
                    estimated_size_bytes=est_size,
                    has_audio=has_audio,
                    is_oversized=is_oversized,
                )
            )

    # Audio options: 128 kbps and 192 kbps
    audio_options: List[AudioOption] = []
    if has_audio:
        for bitrate in (128, 192):
            est_audio_size = int((bitrate * 1000 / 8) * duration) if (duration and duration > 0) else None
            audio_options.append(
                AudioOption(
                    bitrate_kbps=bitrate,
                    estimated_size_bytes=est_audio_size,
                )
            )

    media_info = MediaInfo(
        url=url,
        platform=platform,
        title=title,
        uploader=uploader,
        duration_seconds=duration,
        thumbnail_url=thumbnail,
        has_audio=has_audio,
        is_live=False,
        is_playlist=False,
        source_audio_bitrate_kbps=best_audio_bitrate,
        video_qualities=video_options,
        audio_options=audio_options,
        webpage_url=info.get("webpage_url") or url,
    )
    return media_info, None, None


async def extract_media_info(
    url: str,
    platform: str,
    settings: Settings,
) -> Tuple[Optional[MediaInfo], Optional[str], Optional[str]]:
    """
    Extract video metadata with timeout guard.
    Returns: (MediaInfo, error_key, error_detail)
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_extract_sync, url, platform, settings),
            timeout=settings.extract_timeout,
        )
    except asyncio.TimeoutError:
        logger.warning("Metadata extraction timed out for %s", url)
        return None, "err_timeout", f"Timeout after {settings.extract_timeout}s"
    except Exception as exc:
        logger.exception("Error extracting metadata for %s: %s", url, exc)
        return None, "err_internal", str(exc)
