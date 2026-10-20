"""Tests for AI translation and summarization service and text handlers."""

import pytest
from unittest.mock import patch, AsyncMock
from link2media.ai_service import translate_to_khmer, summarize_in_khmer
from link2media.handlers.keyboards import make_text_action_keyboard


@pytest.mark.asyncio
async def test_translate_empty_text():
    res = await translate_to_khmer("", api_key="test_key", lang="km")
    assert "មិនមានអត្ថបទ" in res


@pytest.mark.asyncio
async def test_summarize_empty_text():
    res = await summarize_in_khmer("   ", api_key="test_key", lang="km")
    assert "មិនមានអត្ថបទ" in res


@pytest.mark.asyncio
async def test_missing_api_key_returns_hint():
    res = await translate_to_khmer("Hello world", api_key=None, lang="km")
    assert "GEMINI_API_KEY" in res


@pytest.mark.asyncio
async def test_successful_gemini_call():
    with patch("link2media.ai_service._call_gemini_generate", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "សួស្តីពិភពលោក"
        result = await translate_to_khmer("Hello world", api_key="dummy_key", lang="km")
        assert result == "សួស្តីពិភពលោក"
        assert mock_call.called


def test_text_action_keyboard():
    kb = make_text_action_keyboard("sess123", "km")
    buttons = [btn for row in kb.inline_keyboard for btn in row]
    callbacks = [btn.callback_data for btn in buttons]
    assert "txt:tr:sess123" in callbacks
    assert "txt:sm:sess123" in callbacks
    assert "txt:c:sess123" in callbacks


@pytest.mark.asyncio
async def test_translate_media_segmented():
    from link2media.ai_service import translate_media_segmented
    with patch("link2media.ai_service._call_gemini_generate", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "1️⃣ ចំណងជើង\n2️⃣ ការពិពណ៌នា\n3️⃣ សំឡេង"
        res = await translate_media_segmented("Title", "Desc", "Transcript", api_key="test_key", lang="km")
        assert "ចំណងជើង" in res
        assert mock_call.called


@pytest.mark.asyncio
async def test_summarize_media_speech():
    from link2media.ai_service import summarize_media_speech
    with patch("link2media.ai_service._call_gemini_generate", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "🔹 ចំណុចសំខាន់"
        res = await summarize_media_speech("Title", "Desc", "Transcript", api_key="test_key", lang="km")
        assert "ចំណុចសំខាន់" in res
        assert mock_call.called


def test_sanitize_pure_khmer():
    from link2media.ai_service import sanitize_pure_khmer, contains_foreign_scripts
    mixed_text = "សួស្តី สวัสดี ពិភពលោក 特斯拉 thế giới ສະບាយດີ"
    assert contains_foreign_scripts(mixed_text) is True
    cleaned = sanitize_pure_khmer(mixed_text)
    assert contains_foreign_scripts(cleaned) is False
    assert "សួស្តី" in cleaned
    assert "ពិភពលោក" in cleaned
    assert "สวัสดี" not in cleaned
    assert "特斯拉" not in cleaned
    assert "thế giới" not in cleaned
    assert "ສະບាយດີ" not in cleaned

