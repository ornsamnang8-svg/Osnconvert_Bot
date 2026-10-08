"""AI Translation and Summarization service using Google Gemini."""

from __future__ import annotations

import logging
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

API_KEY_HINT_KM = (
    "⚠️ <b>មិនទាន់បានកំណត់ GEMINI_API_KEY</b>\n\n"
    "ដើម្បីដំណើរការមុខងារ <b>បកប្រែ</b> និង <b>សង្ខេបខ្លឹមសារ</b> ដោយ AI សូម៖\n"
    "1. ចូលទៅកាន់ <a href=\"https://aistudio.google.com/app/apikey\">Google AI Studio</a> (Free 100%)\n"
    "2. ចុច <b>Create API key</b>\n"
    "3. បើកឯកសារ <code>.env</code> ហើយបន្ថែម៖\n"
    "   <code>GEMINI_API_KEY=your_key_here</code>\n"
    "4. រួច Restart Bot ឡើងវិញ។"
)

API_KEY_HINT_EN = (
    "⚠️ <b>GEMINI_API_KEY not configured</b>\n\n"
    "To enable AI <b>Translation</b> and <b>Summarization</b>:\n"
    "1. Visit <a href=\"https://aistudio.google.com/app/apikey\">Google AI Studio</a> (Free 100%)\n"
    "2. Click <b>Create API key</b>\n"
    "3. Add to your <code>.env</code> file:\n"
    "   <code>GEMINI_API_KEY=your_key_here</code>\n"
    "4. Restart the bot."
)


MODELS_TO_TRY = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
]



async def _call_gemini_generate(prompt: str, api_key: str, timeout_seconds: int = 45) -> str:
    """Call Google Gemini generateContent endpoint with automatic model failover."""
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048,
        }
    }

    last_error: Exception | None = None
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for model in MODELS_TO_TRY:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates") or []
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "").strip()
                    elif resp.status in (429, 503):
                        logger.warning("Gemini model %s busy (%s), trying fallback...", model, resp.status)
                        continue
                    else:
                        err_text = await resp.text()
                        logger.warning("Gemini model %s returned %s: %s", model, resp.status, err_text)
            except Exception as exc:
                last_error = exc
                logger.warning("Error with Gemini model %s: %s", model, exc)
                continue

    if last_error:
        raise last_error
    raise RuntimeError("All Gemini models were temporarily busy. Please retry.")



async def translate_to_khmer(
    text: str,
    api_key: Optional[str] = None,
    lang: str = "km",
) -> str:
    """Translate text to Khmer. Uses Gemini if API key is provided."""
    cleaned_text = text.strip()
    if not cleaned_text:
        return "❌ មិនមានអត្ថបទសម្រាប់បកប្រែទេ (Empty text)"

    if not api_key:
        return API_KEY_HINT_KM if lang == "km" else API_KEY_HINT_EN

    prompt = (
        "You are an expert bilingual translator specialized in English and Khmer. "
        "Translate the following text into fluent, natural Khmer (ភាសាខ្មែរ).\n"
        "Guidelines:\n"
        "- Maintain exact meaning, tone, and appropriate Khmer vocabulary.\n"
        "- Keep emojis, mentions, links, or technical identifiers unchanged.\n"
        "- Output ONLY the translated Khmer text, without intro or outro.\n\n"
        f"Original text:\n{cleaned_text}"
    )

    try:
        return await _call_gemini_generate(prompt, api_key)
    except Exception as exc:
        logger.exception("Failed to translate via Gemini: %s", exc)
        err_msg = "❌ ការបកប្រែមានបញ្ហា សូមព្យាយាមម្តងទៀត" if lang == "km" else "❌ Translation error, please try again"
        return f"{err_msg}\n<code>{exc}</code>"


async def summarize_in_khmer(
    text: str,
    api_key: Optional[str] = None,
    lang: str = "km",
) -> str:
    """Summarize text in Khmer. Uses Gemini if API key is provided."""
    cleaned_text = text.strip()
    if not cleaned_text:
        return "❌ មិនមានអត្ថបទសម្រាប់សង្ខេបទេ (Empty text)"

    if not api_key:
        return API_KEY_HINT_KM if lang == "km" else API_KEY_HINT_EN

    prompt = (
        "You are an expert content analyzer. "
        "Summarize the following content clearly and concisely in natural Khmer (ភាសាខ្មែរ).\n"
        "Guidelines:\n"
        "- Structure with key takeaway points (bullet points using • or 🔹).\n"
        "- Highlight core ideas, context, and conclusion.\n"
        "- Write naturally in fluent Khmer.\n"
        "- Output ONLY the summary in Khmer.\n\n"
        f"Content to summarize:\n{cleaned_text}"
    )

    try:
        return await _call_gemini_generate(prompt, api_key)
    except Exception as exc:
        logger.exception("Failed to summarize via Gemini: %s", exc)
        err_msg = "❌ ការសង្ខេបមានបញ្ហា សូមព្យាយាមម្តងទៀត" if lang == "km" else "❌ Summarization error, please try again"
        return f"{err_msg}\n<code>{exc}</code>"
