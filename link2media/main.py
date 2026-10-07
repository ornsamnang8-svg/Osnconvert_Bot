"""Main entrypoint for Link2Media Telegram bot."""

from __future__ import annotations

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import ConfigError, load_settings
from .db import init_db
from .handlers import main_router
from .queue_manager import QueueManager

logger = logging.getLogger("link2media")


def setup_logging(log_level: str) -> None:
    """Configure secure and readable logging format."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # Suppress verbose HTTP logs from aiogram/aiohttp
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)


async def main() -> None:
    try:
        settings = load_settings(require_token=True)
    except ConfigError as exc:
        print(f"\n[ERROR] {exc}\n", file=sys.stderr)
        sys.exit(1)

    setup_logging(settings.log_level)
    logger.info("Starting Link2Media bot...")

    # Initialize SQLite database
    await init_db(settings.db_path)
    logger.info("Database initialized at %s", settings.db_path)

    # Initialize queue manager and clean up old temp files
    queue_mgr = QueueManager(settings)
    queue_mgr.cleanup_stale_directories()

    # Create Bot and Dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Pass dependencies via dispatcher workflow data
    dp["settings"] = settings
    dp["queue_mgr"] = queue_mgr

    # Include main handlers router
    dp.include_router(main_router)

    # Verify bot credentials and get info
    try:
        bot_user = await bot.get_me()
        logger.info("Bot authenticated as @%s (id: %s)", bot_user.username, bot_user.id)
    except Exception as exc:
        logger.error("Failed to connect to Telegram Bot API with BOT_TOKEN: %s", exc)
        print("\n[ERROR] Could not authenticate with Telegram. Check your BOT_TOKEN in .env.\n", file=sys.stderr)
        await bot.session.close()
        sys.exit(1)

    logger.info("Bot is ready. Starting polling...")
    try:
        # Delete pending webhook if any to prevent conflicts with polling
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("Bot polling cancelled.")
    finally:
        logger.info("Shutting down bot...")
        queue_mgr.cleanup_stale_directories()
        await bot.session.close()
        logger.info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
