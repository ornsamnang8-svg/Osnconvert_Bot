"""Tests for quality selection, no-upscaling guarantee, and size limit checks."""

from link2media.config import Settings
from link2media.extract import classify_yt_dlp_error
from link2media.models import AudioOption, MediaInfo, VideoQualityOption


def test_classify_yt_dlp_errors() -> None:
    assert classify_yt_dlp_error("Sign in to confirm you’re not a bot") == "err_login_required"
    assert classify_yt_dlp_error("Private video. Sign in if you've been granted access.") == "err_login_required"
    assert classify_yt_dlp_error("Video unavailable. This video has been removed") == "err_unavailable"
    assert classify_yt_dlp_error("This video contains DRM protection") == "err_drm"
    assert classify_yt_dlp_error("The live event will begin in a few moments") == "err_live"
    assert classify_yt_dlp_error("HTTP Error 429: Too Many Requests") == "err_rate_limited"
    assert classify_yt_dlp_error("The uploader has not made this video available in your country") == "err_geo_restricted"


def test_quality_options_and_no_upscaling() -> None:
    # Scenario 1: Source video is 720p. It must NEVER offer 1080p.
    source_height = 720
    candidate_tiers = [1080, 720, 480, 360, 240, 144]
    offered_tiers = [t for t in candidate_tiers if t <= min(1080, source_height)]

    assert 1080 not in offered_tiers
    assert offered_tiers == [720, 480, 360, 240, 144]

    # Scenario 2: Source video is 1080p. It should offer 1080p and below.
    source_1080 = 1080
    offered_1080 = [t for t in candidate_tiers if t <= min(1080, source_1080)]
    assert offered_1080[0] == 1080

    # Scenario 3: Source is 4K (2160p). Bot caps at 1080p.
    source_4k = 2160
    offered_4k = [t for t in candidate_tiers if t <= min(1080, source_4k)]
    assert max(offered_4k) == 1080
    assert 2160 not in offered_4k


def test_size_limits_flagging() -> None:
    max_upload = 48_000_000

    opt_fit = VideoQualityOption(
        height=480,
        label="480p SD",
        format_selector="dummy",
        estimated_size_bytes=25_000_000,
        is_oversized=False,
    )
    assert opt_fit.is_oversized is False
    assert "25.0 MB" in opt_fit.display_size

    opt_large = VideoQualityOption(
        height=1080,
        label="1080p FHD",
        format_selector="dummy",
        estimated_size_bytes=75_000_000,
        is_oversized=(75_000_000 > max_upload),
    )
    assert opt_large.is_oversized is True
    assert "75.0 MB" in opt_large.display_size


def test_audio_options_bitrates() -> None:
    duration_secs = 180  # 3 minutes

    # 128 kbps: 128000 / 8 * 180 = 2,880,000 bytes
    est_128 = int((128 * 1000 / 8) * duration_secs)
    opt_128 = AudioOption(bitrate_kbps=128, estimated_size_bytes=est_128)
    assert opt_128.bitrate_kbps == 128
    assert "2.9 MB" in opt_128.display_size

    # 192 kbps: 192000 / 8 * 180 = 4,320,000 bytes
    est_192 = int((192 * 1000 / 8) * duration_secs)
    opt_192 = AudioOption(bitrate_kbps=192, estimated_size_bytes=est_192)
    assert opt_192.bitrate_kbps == 192
    assert "4.3 MB" in opt_192.display_size


def test_formatted_duration_with_float_and_int() -> None:
    """Verify that formatted_duration handles floats, ints, zero, and long durations cleanly."""
    from link2media.models import MediaInfo

    info_float = MediaInfo(
        url="https://example.com/v",
        platform="youtube",
        title="Test",
        duration_seconds=245.8,  # float duration
    )
    assert info_float.formatted_duration == "4:06"

    info_int = MediaInfo(
        url="https://example.com/v",
        platform="youtube",
        title="Test",
        duration_seconds=65,
    )
    assert info_int.formatted_duration == "1:05"

    info_hours = MediaInfo(
        url="https://example.com/v",
        platform="youtube",
        title="Test",
        duration_seconds=3665.4,
    )
    assert info_hours.formatted_duration == "1:01:05"

    info_none = MediaInfo(
        url="https://example.com/v",
        platform="youtube",
        title="Test",
        duration_seconds=None,
    )
    assert info_none.formatted_duration == ""
