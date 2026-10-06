"""Message handler for receiving and validating video URLs."""

from __future__ import annotations

import logging
import time
import uuid
from aiogram import Bot, Router
from aiogram.types import Message

from ..config import Settings
from ..db import get_user_language
from ..extract import extract_media_info
from ..i18n import t
from ..models import UserSession
from ..queue_manager import QueueManager
from ..security import extract_urls, validate_url
from .commands import is_allowed_user
from .keyboards import make_action_keyboard
from .ui_helpers import format_media_card

logger = logging.getLogger(__name__)
router = Router(name="messages")


@router.message()
async def handle_incoming_text(
    message: Message,
    bot: Bot,
    settings: Settings,
    queue_mgr: QueueManager,
) -> None:
    """Process incoming chat messages containing media URLs."""
    if message.chat.type != "private":
        await message.reply(t("en", "private_chat_only"))
        return

    if not is_allowed_user(message, settings):
        await message.reply(t("km", "not_allowed"))
        return

    text = (message.text or message.caption or "").strip()
    user_id = message.from_user.id if message.from_user else 0
    lang = await get_user_language(settings.db_path, user_id)

    urls = extract_urls(text)
    if not urls:
        await message.reply(t(lang, "send_link_hint"))
        return

    if len(urls) > 1:
        await message.reply(t(lang, "one_link_only"), parse_mode="HTML")
        return

    target_url = urls[0]

    # Validate URL and platform
    is_valid, platform, err_key = validate_url(target_url)
    if not is_valid:
        error_msg = t(lang, err_key or "invalid_url")
        await message.reply(error_msg, parse_mode="HTML")
        return

    assert platform is not None

    # Check if user already has an active downloading job
    can_run, busy_err = await queue_mgr.can_enqueue(user_id)
    if not can_run:
        await message.reply(t(lang, busy_err or "busy_user"))
        return

    # Send initial status message
    status_msg = await message.reply(t(lang, "status_checking"))

    # Extract metadata
    media_info, extract_err_key, extract_detail = await extract_media_info(
        url=target_url,
        platform=platform,
        settings=settings,
    )

    if not media_info or extract_err_key:
        fail_text = t(lang, extract_err_key or "err_unsupported")
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            text=f"{t(lang, 'status_failed')}\n\n{fail_text}",
            parse_mode="HTML",
        )
        return

    # Create session
    session_id = uuid.uuid4().hex[:8]
    session = UserSession(
        session_id=session_id,
        user_id=user_id,
        chat_id=message.chat.id,
        media_info=media_info,
        created_at=time.time(),
        status_message_id=status_msg.message_id,
    )
    queue_mgr.store_session(session)

    # Format card
    card_text = format_media_card(media_info, lang, settings)
    card_text += f"\n\n{t(lang, 'choose_action')}"

    keyboard = make_action_keyboard(session_id, lang, media_info)

    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        text=card_text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )
