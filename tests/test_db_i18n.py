"""Tests for SQLite language preference persistence and i18n messages."""

from pathlib import Path
import pytest
from link2media.db import get_user_language, init_db, set_user_language
from link2media.i18n import DEFAULT_LANG, t


@pytest.mark.asyncio
async def test_db_language_persistence(tmp_path: Path) -> None:
    db_file = tmp_path / "test_prefs.sqlite3"
    await init_db(db_file)

    user_id = 987654

    # Default is Khmer
    lang_initial = await get_user_language(db_file, user_id)
    assert lang_initial == DEFAULT_LANG
    assert lang_initial == "km"

    # Set to English
    await set_user_language(db_file, user_id, "en")
    lang_en = await get_user_language(db_file, user_id)
    assert lang_en == "en"

    # Set back to Khmer
    await set_user_language(db_file, user_id, "km")
    lang_km = await get_user_language(db_file, user_id)
    assert lang_km == "km"


def test_i18n_messages() -> None:
    # Test Khmer default messages
    km_start = t("km", "start")
    assert "សូមស្វាគមន៍មកកាន់ Link2Media" in km_start

    # Test English messages
    en_start = t("en", "start")
    assert "Welcome to Link2Media" in en_start

    # Formatting with parameters
    help_en = t("en", "help", max_minutes=20, max_mb=48)
    assert "20 minutes" in help_en
    assert "48 MB" in help_en

    # Fallback to English/default when invalid key or language
    assert t("invalid_lang", "start") == km_start
    assert t("en", "non_existent_key") == "non_existent_key"
