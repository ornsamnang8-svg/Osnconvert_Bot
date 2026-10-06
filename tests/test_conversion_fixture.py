"""Integration tests verifying real MP4 and MP3 conversions on synthetic media."""

import shutil
import subprocess
from pathlib import Path
import pytest

from link2media.convert import (
    convert_to_mp3,
    convert_to_mp4,
    extract_thumbnail_jpg,
    probe_file,
)

FFMPEG_BIN = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE_BIN = shutil.which("ffprobe") or "ffprobe"


@pytest.fixture(scope="module")
def sample_video_fixture(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a lightweight 2-second test video with video & audio streams using ffmpeg."""
    out_dir = tmp_path_factory.mktemp("fixtures")
    fixture_path = out_dir / "sample_raw.mkv"

    cmd = [
        FFMPEG_BIN,
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=2:size=320x240:rate=15",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=2",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        str(fixture_path),
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert res.returncode == 0, f"FFmpeg fixture generation failed: {res.stderr.decode()}"
    assert fixture_path.exists()
    return fixture_path


@pytest.mark.asyncio
async def test_real_mp4_conversion(sample_video_fixture: Path, tmp_path: Path) -> None:
    output_mp4 = tmp_path / "test_out.mp4"

    success, err = await convert_to_mp4(
        ffmpeg_bin=FFMPEG_BIN,
        ffprobe_bin=FFPROBE_BIN,
        input_file=sample_video_fixture,
        output_file=output_mp4,
    )
    assert success is True
    assert err is None
    assert output_mp4.exists()
    assert output_mp4.stat().st_size > 0

    # Probe resulting MP4
    info = await probe_file(FFPROBE_BIN, output_mp4)
    streams = info.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    assert v_stream is not None
    assert v_stream.get("codec_name") in ("h264", "avc1")
    assert v_stream.get("pix_fmt") == "yuv420p"

    assert a_stream is not None
    assert a_stream.get("codec_name") == "aac"


@pytest.mark.asyncio
async def test_real_mp3_conversion(sample_video_fixture: Path, tmp_path: Path) -> None:
    output_mp3 = tmp_path / "test_audio.mp3"

    success, err = await convert_to_mp3(
        ffmpeg_bin=FFMPEG_BIN,
        input_file=sample_video_fixture,
        output_file=output_mp3,
        bitrate_kbps=192,
        title="Test Song",
        artist="Test Artist",
    )
    assert success is True
    assert err is None
    assert output_mp3.exists()
    assert output_mp3.stat().st_size > 0

    # Probe resulting MP3
    info = await probe_file(FFPROBE_BIN, output_mp3)
    streams = info.get("streams", [])
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    assert a_stream is not None
    assert a_stream.get("codec_name") == "mp3"

    # Verify ID3 metadata tags
    tags = info.get("format", {}).get("tags", {})
    # Case insensitive key search
    tag_map = {k.lower(): v for k, v in tags.items()}
    assert tag_map.get("title") == "Test Song"
    assert tag_map.get("artist") == "Test Artist"


@pytest.mark.asyncio
async def test_real_thumbnail_extraction(sample_video_fixture: Path, tmp_path: Path) -> None:
    output_thumb = tmp_path / "thumb.jpg"

    ok = await extract_thumbnail_jpg(
        ffmpeg_bin=FFMPEG_BIN,
        input_file=sample_video_fixture,
        output_thumb=output_thumb,
    )
    assert ok is True
    assert output_thumb.exists()
    assert output_thumb.stat().st_size > 0
