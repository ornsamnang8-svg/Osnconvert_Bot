"""UI card formatting and throttled Telegram status message editing."""

from __future__ import annotations

import asyncio
import html
import logging
import time
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup

from ..config import Settings
from ..i18n import t
from ..models import MediaInfo

logger = logging.getLogger(__name__)


def format_media_card(media_info: MediaInfo, lang: str, settings: Settings) -> str:
    """Format safe HTML media preview card."""
    title_escaped = html.escape(media_info.title)
    details: list[str] = []

    if media_info.uploader:
        details.append(t(lang, "card_uploader", uploader=html.escape(media_info.uploader)))
    if media_info.duration_seconds:
        details.append(t(lang, "card_duration", duration=media_info.formatted_duration))
    details.append(t(lang, "card_platform", platform=html.escape(media_info.platform)))

    details_str = "\n".join(details)
    return t(lang, "card", title=title_escaped, details=details_str)


class StatusUpdater:
    """Safely updates a single status message while throttling edits."""

    def __init__(self, bot: Bot, chat_id: int, message_id: int, min_interval: float = 2.5) -> None:
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id
        self.min_interval = min_interval
        self.last_edit_time = 0.0
        self.last_text = ""
        self._lock = asyncio.Lock()

    async def update(
        self,
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
        force: bool = False,
    ) -> bool:
        """Edit the status message if throttled interval passed or forced."""
        now = time.time()
        if not force and (now - self.last_edit_time < self.min_interval):
            return False

        if text == self.last_text and reply_markup is None:
            return False

        async with self._lock:
            try:
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
                self.last_edit_time = time.time()
                self.last_text = text
                return True
            except TelegramRetryAfter as retry:
                logger.warning("Telegram flood wait: sleeping %ss", retry.retry_after)
                await asyncio.sleep(retry.retry_after)
                return False
            except TelegramBadRequest as exc:
                if "message is not modified" in str(exc).lower():
                    return True
                logger.warning("Failed to edit status message %s: %s", self.message_id, exc)
                return False
            except Exception as exc:
                logger.warning("Unexpected error editing status message: %s", exc)
                return False
