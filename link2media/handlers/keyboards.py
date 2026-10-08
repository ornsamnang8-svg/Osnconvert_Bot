"""Inline keyboards and callback data builders."""

from __future__ import annotations

from typing import List
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..i18n import t
from ..models import MediaInfo, VideoQualityOption


def make_language_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for selecting bot language."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇰🇭 ភាសាខ្មែរ", callback_data="lang:km"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )


def make_action_keyboard(session_id: str, lang: str, media_info: MediaInfo) -> InlineKeyboardMarkup:
    """Main menu keyboard for a media item."""
    rows: List[List[InlineKeyboardButton]] = []

    # Download Video button
    if media_info.video_qualities:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "btn_video"), callback_data=f"act:v:{session_id}")]
        )

    # Download MP3 button (only if audio is present)
    if media_info.has_audio:
        rows.append(
            [InlineKeyboardButton(text=t(lang, "btn_mp3"), callback_data=f"act:a:{session_id}")]
        )

    # AI Translation & Summarization buttons
    rows.append(
        [
            InlineKeyboardButton(text=t(lang, "btn_translate"), callback_data=f"ai:tr:{session_id}"),
            InlineKeyboardButton(text=t(lang, "btn_summarize"), callback_data=f"ai:sm:{session_id}"),
        ]
    )

    # Cancel button
    rows.append(
        [InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data=f"act:c:{session_id}")]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def make_text_action_keyboard(session_id: str, lang: str) -> InlineKeyboardMarkup:
    """Keyboard for incoming plain text messages."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_translate"), callback_data=f"txt:tr:{session_id}"),
                InlineKeyboardButton(text=t(lang, "btn_summarize"), callback_data=f"txt:sm:{session_id}"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data=f"txt:c:{session_id}"),
            ],
        ]
    )


def make_video_qualities_keyboard(
    session_id: str,
    lang: str,
    options: List[VideoQualityOption],
) -> InlineKeyboardMarkup:
    """Keyboard showing available video qualities up to 1080p."""
    rows: List[List[InlineKeyboardButton]] = []

    # Filter out oversized qualities from direct buttons
    for opt in options:
        if opt.is_oversized:
            continue
        btn_text = t(lang, "btn_quality", label=opt.label, size=opt.display_size)
        rows.append(
            [InlineKeyboardButton(text=btn_text, callback_data=f"vq:{opt.height}:{session_id}")]
        )

    # Navigation row
    nav_row = [
        InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"act:b:{session_id}"),
        InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data=f"act:c:{session_id}"),
    ]
    rows.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def make_audio_bitrates_keyboard(
    session_id: str,
    lang: str,
    media_info: MediaInfo,
) -> InlineKeyboardMarkup:
    """Keyboard showing MP3 bitrates (128 kbps and 192 kbps)."""
    rows: List[List[InlineKeyboardButton]] = []

    opt_128 = next((o for o in media_info.audio_options if o.bitrate_kbps == 128), None)
    opt_192 = next((o for o in media_info.audio_options if o.bitrate_kbps == 192), None)

    size_128 = opt_128.display_size if opt_128 else ""
    size_192 = opt_192.display_size if opt_192 else ""

    rows.append(
        [InlineKeyboardButton(
            text=t(lang, "btn_bitrate_128", size=size_128),
            callback_data=f"aq:128:{session_id}",
        )]
    )
    rows.append(
        [InlineKeyboardButton(
            text=t(lang, "btn_bitrate_192", size=size_192),
            callback_data=f"aq:192:{session_id}",
        )]
    )

    # Navigation row
    nav_row = [
        InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"act:b:{session_id}"),
        InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data=f"act:c:{session_id}"),
    ]
    rows.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=rows)
