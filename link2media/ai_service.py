"""AI Translation and Summarization service using Google Gemini."""

from __future__ import annotations

import logging
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)

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
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
]

SYSTEM_PROMPT = (
    "You are a native Cambodian professional linguist and translator specialized strictly in the Khmer language (ភាសាខ្មែរ).\n"
    "CRITICAL MANDATORY RULES:\n"
    "1. You must write EXCLUSIVELY in 100% pure Cambodian Khmer language and Khmer script (អក្សរខ្មែរ).\n"
    "2. ABSOLUTELY FORBIDDEN: NEVER use, mix, or output ANY Thai language (ภาษาไทย), Thai script (Unicode range U+0E00 to U+0E7F), Thai vocabulary, or Lao script under any circumstance.\n"
    "3. Use standard Cambodian vocabulary, proper spelling, and natural Khmer phrasing.\n"
    "4. Preserve emojis, numbers, and URLs without modification."
)


def contains_thai_characters(text: str) -> bool:
    """Check if string contains any Thai Unicode characters (U+0E00 to U+0E7F)."""
    return any("\u0e00" <= c <= "\u0e7f" for c in text)


async def _call_gemini_generate(prompt: str, api_key: str, timeout_seconds: int = 45) -> str:
    """Call Google Gemini generateContent endpoint with automatic model failover and strict Khmer enforcement."""
    payload = {
        "systemInstruction": {
            "parts": [
                {"text": SYSTEM_PROMPT}
            ]
        },
        "contents": [
            {"parts": [{"text": prompt}]}
        ],
        "generationConfig": {
            "temperature": 0.1,
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
                                text_result = parts[0].get("text", "").strip()
                                # Guard against any leaked Thai characters
                                if contains_thai_characters(text_result):
                                    logger.warning("Output from %s contained Thai script, cleaning...", model)
                                    # Request immediate pure-Khmer rewrite
                                    rewrite_payload = {
                                        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                                        "contents": [{"parts": [{"text": f"Remove all Thai characters and rewrite entirely in 100% pure Khmer language:\n\n{text_result}"}]}],
                                        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 2048}
                                    }
                                    async with session.post(url, json=rewrite_payload) as fix_resp:
                                        if fix_resp.status == 200:
                                            fix_data = await fix_resp.json()
                                            fix_candidates = fix_data.get("candidates") or []
                                            if fix_candidates:
                                                fix_parts = fix_candidates[0].get("content", {}).get("parts", [])
                                                if fix_parts:
                                                    return fix_parts[0].get("text", "").strip()

                                return text_result
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
    """Translate text strictly into 100% pure Khmer without any Thai language."""
    cleaned_text = text.strip()
    if not cleaned_text:
        return "❌ មិនមានអត្ថបទសម្រាប់បកប្រែទេ (Empty text)"

    if not api_key:
        return API_KEY_HINT_KM if lang == "km" else API_KEY_HINT_EN

    prompt = (
        "Translate the following text into 100% pure Cambodian Khmer language (ភាសាខ្មែរ).\n\n"
        "STRICT MANDATORY REQUIREMENTS:\n"
        "- Write strictly in Cambodian Khmer script (អក្សរខ្មែរ).\n"
        "- DO NOT use, borrow, or mix ANY Thai language (ภาษาไทย) or Thai characters.\n"
        "- Ensure smooth, natural, and accurate Cambodian Khmer phrasing.\n"
        "- Output ONLY the translated Khmer text without intro or outro.\n\n"
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
    """Summarize text strictly into 100% pure Khmer without any Thai language."""
    cleaned_text = text.strip()
    if not cleaned_text:
        return "❌ មិនមានអត្ថបទសម្រាប់សង្ខេបទេ (Empty text)"

    if not api_key:
        return API_KEY_HINT_KM if lang == "km" else API_KEY_HINT_EN

    prompt = (
        "Summarize the following content concisely and clearly in 100% pure Cambodian Khmer language (ភាសាខ្មែរ).\n\n"
        "STRICT MANDATORY REQUIREMENTS:\n"
        "- Write strictly in Cambodian Khmer script (អក្សរខ្មែរ).\n"
        "- DO NOT use, borrow, or mix ANY Thai language (ภาษาไทย) or Thai characters.\n"
        "- Highlight core ideas using clean bullet points (🔹 or •).\n"
        "- Write naturally and elegantly in Cambodian Khmer.\n"
        "- Output ONLY the summary in Khmer.\n\n"
        f"Content to summarize:\n{cleaned_text}"
    )

    try:
        return await _call_gemini_generate(prompt, api_key)
    except Exception as exc:
        logger.exception("Failed to summarize via Gemini: %s", exc)
        err_msg = "❌ ការសង្ខេបមានបញ្ហា សូមព្យាយាមម្តងទៀត" if lang == "km" else "❌ Summarization error, please try again"
        return f"{err_msg}\n<code>{exc}</code>"


async def translate_media_segmented(
    title: str,
    description: Optional[str],
    transcript: Optional[str],
    api_key: Optional[str],
    lang: str = "km",
) -> str:
    """Translate media into 3 distinct sections: Title, Description, and Spoken Speech/Transcript."""
    if not api_key:
        return API_KEY_HINT_KM if lang == "km" else API_KEY_HINT_EN

    desc_clean = (description or "").strip()
    trans_clean = (transcript or "").strip()

    prompt = (
        "You are an expert native Cambodian translator. Translate the following video elements into 100% pure Khmer language (ភាសាខ្មែរ).\n\n"
        "STRICT MANDATORY RULES:\n"
        "1. Write EXCLUSIVELY in pure Cambodian Khmer script (អក្សរខ្មែរ). Absolutely NO Thai language (ภาษาไทย) or Thai characters.\n"
        "2. Translate all available sections accurately.\n"
        "3. Output STRICTLY in the following 3-part format:\n\n"
        "1️⃣ <b>ចំណងជើង (Title)៖</b>\n"
        "[Khmer translation of Title]\n\n"
        "2️⃣ <b>សេចក្តីពិពណ៌នា (Description)៖</b>\n"
        "[Khmer translation of Description, or '(គ្មានសេចក្តីពិពណ៌នា)' if empty]\n\n"
        "3️⃣ <b>បកប្រែចេញពីសំឡេងនិយាយផ្ទាល់ក្នុងវីដេអូ (Speech / Transcript)៖</b>\n"
        "[Khmer translation of the spoken transcript, or '(វីដេអូនេះមិនមានអត្ថបទសំឡេង/Subtitle សម្រាប់ស្រង់ចេញទេ)' if empty]\n\n"
        f"Input Title:\n{title}\n\n"
        f"Input Description:\n{desc_clean if desc_clean else '(None)'}\n\n"
        f"Input Spoken Transcript:\n{trans_clean[:3500] if trans_clean else '(None)'}"
    )

    try:
        return await _call_gemini_generate(prompt, api_key)
    except Exception as exc:
        logger.exception("Failed to translate media segmented: %s", exc)
        err_msg = "❌ ការបកប្រែមានបញ្ហា សូមព្យាយាមម្តងទៀត" if lang == "km" else "❌ Translation error, please try again"
        return f"{err_msg}\n<code>{exc}</code>"


async def summarize_media_speech(
    title: str,
    description: Optional[str],
    transcript: Optional[str],
    api_key: Optional[str],
    lang: str = "km",
) -> str:
    """Summarize video focusing directly on its spoken speech/transcript."""
    if not api_key:
        return API_KEY_HINT_KM if lang == "km" else API_KEY_HINT_EN

    desc_clean = (description or "").strip()
    trans_clean = (transcript or "").strip()

    if trans_clean:
        content_to_summarize = f"Video Title: {title}\nSpoken Speech/Transcript:\n{trans_clean[:4000]}"
        focus_instruction = "Summarize specifically from the video's spoken dialogue and speech (សំឡេងនិយាយផ្ទាល់ក្នុងវីដេអូ)."
        note_prefix = "📝 <b>ការសង្ខេបខ្លឹមសារចេញពីសំឡេងនិយាយផ្ទាល់ក្នុងវីដេអូ៖</b>\n\n"
    else:
        content_to_summarize = f"Video Title: {title}\nDescription:\n{desc_clean}"
        focus_instruction = "Since spoken transcript is unavailable, summarize the video's content and description."
        note_prefix = "📝 <b>ការសង្ខេបខ្លឹមសារវីដេអូ (សង្ខេបពីការពិពណ៌នា ដោយសារគ្មាន Subtitle)៖</b>\n\n"

    prompt = (
        f"You are an expert content analyzer. {focus_instruction}\n"
        "Write strictly in 100% pure Cambodian Khmer language (ភាសាខ្មែរ).\n\n"
        "STRICT MANDATORY RULES:\n"
        "1. Write EXCLUSIVELY in pure Cambodian Khmer script (អក្សរខ្មែរ). Absolutely NO Thai language (ภาษาไทย) or Thai characters.\n"
        "2. Structure with clear, high-value key takeaways using bullet points (🔹 or •).\n"
        "3. Output ONLY the summary points in Khmer without intro or outro.\n\n"
        f"Content to summarize:\n{content_to_summarize}"
    )

    try:
        summary_body = await _call_gemini_generate(prompt, api_key)
        return f"{note_prefix}{summary_body}"
    except Exception as exc:
        logger.exception("Failed to summarize media speech: %s", exc)
        err_msg = "❌ ការសង្ខេបមានបញ្ហា សូមព្យាយាមម្តងទៀត" if lang == "km" else "❌ Summarization error, please try again"
        return f"{err_msg}\n<code>{exc}</code>"

