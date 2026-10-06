"""Tests for configuration loading, validation, and secret protection."""

import os
import pytest
from link2media.config import ConfigError, load_settings


def test_missing_token_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(ConfigError) as exc_info:
        load_settings(require_token=True)
    assert "BOT_TOKEN is missing" in str(exc_info.value)


def test_invalid_token_format(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "bad_token_format")
    with pytest.raises(ConfigError) as exc_info:
        load_settings(require_token=True)
    assert "BOT_TOKEN does not look like a Telegram bot token" in str(exc_info.value)


def test_valid_token_and_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    test_token = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789"
    monkeypatch.setenv("BOT_TOKEN", test_token)
    monkeypatch.setenv("ALLOWED_USER_IDS", "111, 222; 333")
    monkeypatch.setenv("MAX_DURATION_SECONDS", "600")

    settings = load_settings(require_token=True)
    assert settings.bot_token == test_token
    assert 111 in settings.allowed_user_ids
    assert 222 in settings.allowed_user_ids
    assert 333 in settings.allowed_user_ids
    assert settings.max_duration_seconds == 600
    assert settings.max_upload_bytes == 48_000_000

    # Ensure token is excluded from repr for safety
    assert test_token not in repr(settings)


def test_max_upload_clamped_to_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789")
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "999999999")  # Exceeds 50MB
    with pytest.raises(ConfigError) as exc:
        load_settings(require_token=True)
    assert "MAX_UPLOAD_BYTES must be at most 50000000" in str(exc.value)
