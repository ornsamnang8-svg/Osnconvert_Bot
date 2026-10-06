"""Bot command handlers: /start, /help, /language, /cancel."""

from __future__ import annotations

import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ..config import Settings
from ..db import get_user_language
from ..i18n import t
from ..queue_manager import QueueManager
from .keyboards import make_language_keyboard

logger = logging.getLogger(__name__)
router = Router(name="commands")


def is_allowed_user(message: Message, settings: Settings) -> bool:
    """Verify private chat and optional user allowlist."""
    if message.chat.type != "private":
        return False
    if not settings.allowed_user_ids:
        return True
    return bool(message.from_user and message.from_user.id in settings.allowed_user_ids)


@router.message(Command("start"))
async def cmd_start(message: Message, settings: Settings, queue_mgr: QueueManager) -> None:
    if message.chat.type != "private":
        await message.reply(t("en", "private_chat_only"))
        return
    if not is_allowed_user(message, settings):
        await message.reply(t("km", "not_allowed"))
        return

    user_id = message.from_user.id if message.from_user else 0
    lang = await get_user_language(settings.db_path, user_id)
    await message.answer(t(lang, "start"), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message, settings: Settings) -> None:
    if message.chat.type != "private":
        await message.reply(t("en", "private_chat_only"))
        return
    if not is_allowed_user(message, settings):
        await message.reply(t("km", "not_allowed"))
        return

    user_id = message.from_user.id if message.from_user else 0
    lang = await get_user_language(settings.db_path, user_id)
    max_minutes = settings.max_duration_seconds // 60
    max_mb = int(settings.max_upload_bytes / 1_000_000)

    await message.answer(
        t(lang, "help", max_minutes=max_minutes, max_mb=max_mb),
        parse_mode="HTML",
    )


@router.message(Command("language"))
async def cmd_language(message: Message, settings: Settings) -> None:
    if message.chat.type != "private":
        await message.reply(t("en", "private_chat_only"))
        return
    if not is_allowed_user(message, settings):
        await message.reply(t("km", "not_allowed"))
        return

    user_id = message.from_user.id if message.from_user else 0
    lang = await get_user_language(settings.db_path, user_id)
    await message.answer(
        t(lang, "choose_language"),
        reply_markup=make_language_keyboard(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, settings: Settings, queue_mgr: QueueManager) -> None:
    if message.chat.type != "private":
        return
    user_id = message.from_user.id if message.from_user else 0
    lang = await get_user_language(settings.db_path, user_id)

    cancelled = await queue_mgr.cancel_user_job(user_id)
    if cancelled:
        await message.answer(t(lang, "cancelled"))
    else:
        await message.answer(t(lang, "nothing_to_cancel"))
