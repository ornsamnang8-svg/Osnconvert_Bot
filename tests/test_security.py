"""Tests for URL extraction, platform verification, SSRF blocking, and sanitization."""

import ipaddress
import pytest
from link2media.security import (
    extract_urls,
    identify_platform,
    is_ip_blocked,
    sanitize_filename,
    validate_url,
)


def test_extract_urls() -> None:
    text = "Hey check this https://www.youtube.com/watch?v=dQw4w9WgXcQ! and let me know."
    urls = extract_urls(text)
    assert urls == ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]

    # Multiple URLs
    multi = "Link 1: https://youtu.be/abc Link 2: https://tiktok.com/@user/video/123"
    assert len(extract_urls(multi)) == 2

    # Clean trailing punctuation
    dirty = "Watch at https://x.com/status/123, or https://instagram.com/reel/abc?igsh=123)"
    cleaned = extract_urls(dirty)
    assert cleaned == [
        "https://x.com/status/123",
        "https://instagram.com/reel/abc?igsh=123",
    ]


def test_identify_platform() -> None:
    assert identify_platform("youtube.com") == "YouTube"
    assert identify_platform("www.youtube.com") == "YouTube"
    assert identify_platform("youtu.be") == "YouTube"
    assert identify_platform("m.youtube.com") == "YouTube"

    assert identify_platform("tiktok.com") == "TikTok"
    assert identify_platform("vm.tiktok.com") == "TikTok"

    assert identify_platform("facebook.com") == "Facebook"
    assert identify_platform("fb.watch") == "Facebook"

    assert identify_platform("instagram.com") == "Instagram"
    assert identify_platform("instagr.am") == "Instagram"

    assert identify_platform("x.com") == "X/Twitter"
    assert identify_platform("twitter.com") == "X/Twitter"
    assert identify_platform("t.co") == "X/Twitter"

    # Unsupported domains
    assert identify_platform("google.com") is None
    assert identify_platform("attacker.com") is None
    assert identify_platform("localhost") is None


def test_ssrf_ip_blocking() -> None:
    # Loopback
    assert is_ip_blocked(ipaddress.ip_address("127.0.0.1")) is True
    assert is_ip_blocked(ipaddress.ip_address("127.0.0.53")) is True
    assert is_ip_blocked(ipaddress.ip_address("::1")) is True

    # Private RFC 1918
    assert is_ip_blocked(ipaddress.ip_address("10.0.0.1")) is True
    assert is_ip_blocked(ipaddress.ip_address("172.16.0.1")) is True
    assert is_ip_blocked(ipaddress.ip_address("192.168.1.1")) is True

    # Cloud metadata
    assert is_ip_blocked(ipaddress.ip_address("169.254.169.254")) is True
    assert is_ip_blocked(ipaddress.ip_address("169.254.1.1")) is True

    # Public IP should not be blocked
    assert is_ip_blocked(ipaddress.ip_address("8.8.8.8")) is False
    assert is_ip_blocked(ipaddress.ip_address("1.1.1.1")) is False


def test_validate_url_security() -> None:
    # Allowed platform with public domain
    valid, platform, err = validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert valid is True
    assert platform == "YouTube"
    assert err is None

    # Unsupported website
    valid, _, err = validate_url("https://vimeo.com/123456")
    assert valid is False
    assert err == "unsupported_platform"

    # Non-HTTP
    valid, _, err = validate_url("ftp://youtube.com/watch?v=123")
    assert valid is False
    assert err == "invalid_url"

    # Direct playlist link rejected
    valid, platform, err = validate_url("https://www.youtube.com/playlist?list=PL123456789")
    assert valid is False
    assert err == "err_playlist"

    # Channel link rejected
    valid, platform, err = validate_url("https://www.youtube.com/channel/UC123456789")
    assert valid is False
    assert err == "unsupported_link"


def test_sanitize_filename() -> None:
    raw = 'My Cool: "Video" / Test <2026> | New? File.mp4'
    cleaned = sanitize_filename(raw)
    assert "/" not in cleaned
    assert "\\" not in cleaned
    assert ":" not in cleaned
    assert '"' not in cleaned
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "?" not in cleaned
    assert "|" not in cleaned
    assert len(cleaned) <= 80

    # Empty string fallback
    assert sanitize_filename("") == "media"
