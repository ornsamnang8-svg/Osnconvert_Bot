"""Callback query handlers for buttons and job execution."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from aiogram import Bot, Router
from aiogram.types import CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup

from ..ai_service import summarize_in_khmer, translate_to_khmer
from ..config import Settings
from ..db import get_user_language, set_user_language
from ..download import execute_download_job
from ..i18n import t
from ..models import DownloadResult, JobProgress, UserSession
from ..queue_manager import ActiveJob, QueueManager
from .keyboards import (
    make_action_keyboard,
    make_audio_bitrates_keyboard,
    make_video_qualities_keyboard,
)
from .ui_helpers import StatusUpdater, format_media_card

logger = logging.getLogger(__name__)
router = Router(name="callbacks")


async def run_job_pipeline(
    bot: Bot,
    settings: Settings,
    queue_mgr: QueueManager,
    job: ActiveJob,
    session: UserSession,
    target_type: str,
    target_option: object,
    lang: str,
) -> None:
    """Background task executing the queued download and upload pipeline."""
    updater = StatusUpdater(
        bot=bot,
        chat_id=job.chat_id,
        message_id=session.status_message_id or 0,
        min_interval=settings.status_interval,
    )

    # Status: Queued
    pos = queue_mgr.get_queue_position(job.job_id)
    if pos > 1:
        await updater.update(t(lang, "status_queued_pos", position=pos), force=True)
    else:
        await updater.update(t(lang, "status_queued"), force=True)

    try:
        # Wait for concurrency slot
        async with queue_mgr.semaphore:
            if job.cancel_event.is_set():
                await updater.update(t(lang, "cancelled"), force=True)
                return

            await updater.update(t(lang, "status_downloading"), force=True)

            # Monitor progress queue asynchronously
            async def _monitor_progress() -> None:
                while not job.cancel_event.is_set():
                    try:
                        progress = await asyncio.wait_for(job.progress_queue.get(), timeout=1.0)
                        if progress.stage == "downloading":
                            if progress.percent is not None:
                                text = t(lang, "status_downloading_pct", percent=int(progress.percent))
                            else:
                                text = t(lang, "status_downloading")
                            await updater.update(text)
                        elif progress.stage == "converting":
                            await updater.update(t(lang, "status_converting"))
                        job.progress_queue.task_done()
                    except asyncio.TimeoutError:
                        continue
                    except asyncio.CancelledError:
                        break

            progress_task = asyncio.create_task(_monitor_progress())

            try:
                res: DownloadResult = await execute_download_job(
                    url=session.media_info.url,
                    target_type=target_type,
                    target_option=target_option,
                    title=session.media_info.title,
                    uploader=session.media_info.uploader,
                    settings=settings,
                    job_id=job.job_id,
                    progress_queue=job.progress_queue,
                    cancel_event=job.cancel_event,
                )
            finally:
                progress_task.cancel()

            if job.cancel_event.is_set() or not res.success:
                err_k = res.error_key or "err_internal"
                err_text = t(lang, err_k)
                if res.error_key == "err_too_large" and res.file_size_bytes:
                    mb = res.file_size_bytes / 1_000_000
                    max_mb = settings.max_upload_bytes / 1_000_000
                    err_text = t(lang, "err_too_large", size_mb=f"{mb:.1f}", max_mb=int(max_mb))

                await updater.update(f"{t(lang, 'status_failed')}\n\n{err_text}", force=True)
                return

            # Stage: Uploading to Telegram
            await updater.update(t(lang, "status_uploading"), force=True)

            bot_info = await bot.get_me()
            bot_username = bot_info.username or "Link2MediaBot"
            caption = t(lang, "file_caption", bot_username=bot_username)

            if target_type == "video" and not session.media_info.has_audio:
                caption = f"{t(lang, 'video_no_audio_note')}\n\n{caption}"

            assert res.file_path is not None
            logger.info("Uploading %s (%s bytes) to chat %s...", target_type, res.file_size_bytes, job.chat_id)
            if target_type == "video":
                v_file = FSInputFile(str(res.file_path))
                th_file = FSInputFile(str(res.thumbnail_path)) if res.thumbnail_path else None
                await bot.send_video(
                    chat_id=job.chat_id,
                    video=v_file,
                    duration=res.duration_seconds,
                    width=res.width,
                    height=res.height,
                    thumbnail=th_file,
                    caption=caption,
                    supports_streaming=True,
                    request_timeout=300,
                )
            else:
                a_file = FSInputFile(str(res.file_path))
                await bot.send_audio(
                    chat_id=job.chat_id,
                    audio=a_file,
                    duration=res.duration_seconds,
                    title=res.title,
                    performer=session.media_info.uploader,
                    caption=caption,
                    request_timeout=300,
                )

            logger.info("Successfully uploaded %s to chat %s", target_type, job.chat_id)

            # Stage: Done
            await updater.update(t(lang, "status_done"), force=True)

    except asyncio.CancelledError:
        await updater.update(t(lang, "cancelled"), force=True)
    except Exception as exc:
        logger.exception("Error during job execution: %s", exc)
        await updater.update(f"{t(lang, 'status_failed')}\n\n{t(lang, 'err_internal')}", force=True)
    finally:
        await queue_mgr.unregister_job(job.job_id)
        queue_mgr.remove_session(session.session_id)


@router.callback_query()
async def handle_callback_query(
    query: CallbackQuery,
    bot: Bot,
    settings: Settings,
    queue_mgr: QueueManager,
) -> None:
    data = query.data or ""
    user_id = query.from_user.id
    lang = await get_user_language(settings.db_path, user_id)

    # 1. Language change
    if data.startswith("lang:"):
        new_lang = data.split(":", 1)[1]
        await set_user_language(settings.db_path, user_id, new_lang)
        await query.answer()
        if query.message:
            await query.message.edit_text(t(new_lang, "language_set"))
        return

    # Check for session-based callbacks: act:*, vq:*, aq:*, ai:*, txt:*
    parts = data.split(":")
    if len(parts) < 3:
        await query.answer(t(lang, "expired_button"), show_alert=True)
        return

    prefix, action_val, session_id = parts[0], parts[1], parts[2]

    # Handle text session callbacks: txt:*
    if prefix == "txt":
        txt_session = queue_mgr.get_text_session(session_id)
        if not txt_session:
            await query.answer(t(lang, "expired_button"), show_alert=True)
            return
        if txt_session.user_id != user_id:
            await query.answer(t(lang, "not_your_button"), show_alert=True)
            return

        if action_val == "c":
            await query.answer()
            queue_mgr.remove_text_session(session_id)
            if query.message:
                await query.message.edit_text(t(lang, "cancelled"))
            return

        await query.answer()
        if action_val == "tr":
            if query.message:
                await query.message.edit_text(t(lang, "status_translating"))
            result = await translate_to_khmer(txt_session.text, settings.gemini_api_key, lang)
            header = t(lang, "translate_result_title")
        else:
            if query.message:
                await query.message.edit_text(t(lang, "status_summarizing"))
            result = await summarize_in_khmer(txt_session.text, settings.gemini_api_key, lang)
            header = t(lang, "summarize_result_title")

        output_text = f"{header}\n\n{result}"
        if len(output_text) > 4000:
            output_text = output_text[:3990] + "…"
        if query.message:
            await query.message.edit_text(output_text, parse_mode="HTML")
        return

    session = queue_mgr.get_session(session_id)
    if not session:
        await query.answer(t(lang, "expired_button"), show_alert=True)
        return

    # Button ownership check
    if session.user_id != user_id:
        await query.answer(t(lang, "not_your_button"), show_alert=True)
        return

    # AI translation / summarization for media session
    if prefix == "ai":
        await query.answer()
        title = session.media_info.title
        desc = (session.media_info.description or "").strip()
        media_text = f"{title}\n\n{desc}".strip() if desc else title

        back_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"act:b:{session_id}"),
                    InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data=f"act:c:{session_id}"),
                ]
            ]
        )

        if action_val == "tr":
            if query.message:
                await query.message.edit_text(t(lang, "status_translating"))
            result = await translate_to_khmer(media_text, settings.gemini_api_key, lang)
            header = t(lang, "translate_result_title")
        else:
            if query.message:
                await query.message.edit_text(t(lang, "status_summarizing"))
            result = await summarize_in_khmer(media_text, settings.gemini_api_key, lang)
            header = t(lang, "summarize_result_title")

        output_text = f"{header}\n\n{result}"
        if len(output_text) > 4000:
            output_text = output_text[:3990] + "…"
        if query.message:
            await query.message.edit_text(output_text, reply_markup=back_kb, parse_mode="HTML")
        return

    # 2. Main menu choices
    if prefix == "act":
        if action_val == "c":
            # Cancel
            await query.answer()
            queue_mgr.remove_session(session_id)
            await queue_mgr.cancel_user_job(user_id)
            if query.message:
                await query.message.edit_text(t(lang, "cancelled"))
            return

        elif action_val == "b":
            # Back to main menu
            await query.answer()
            card_text = format_media_card(session.media_info, lang, settings)
            card_text += f"\n\n{t(lang, 'choose_action')}"
            kb = make_action_keyboard(session_id, lang, session.media_info)
            if query.message:
                await query.message.edit_text(card_text, reply_markup=kb, parse_mode="HTML")
            return

        elif action_val == "v":
            # Show video qualities
            await query.answer()
            card_text = format_media_card(session.media_info, lang, settings)
            card_text += f"\n\n{t(lang, 'choose_quality')}"

            max_mb = int(settings.max_upload_bytes / 1_000_000)
            has_oversized = any(o.is_oversized for o in session.media_info.video_qualities)
            if has_oversized:
                card_text += f"\n\n{t(lang, 'some_too_large', max_mb=max_mb)}"

            all_oversized = all(o.is_oversized for o in session.media_info.video_qualities)
            if all_oversized:
                card_text += f"\n\n{t(lang, 'no_video_fits', max_mb=max_mb)}"

            kb = make_video_qualities_keyboard(session_id, lang, session.media_info.video_qualities)
            if query.message:
                await query.message.edit_text(card_text, reply_markup=kb, parse_mode="HTML")
            return

        elif action_val == "a":
            # Show audio bitrates
            await query.answer()
            card_text = format_media_card(session.media_info, lang, settings)
            card_text += f"\n\n{t(lang, 'choose_bitrate')}"

            if session.media_info.source_audio_bitrate_kbps:
                card_text += f"\n\n{t(lang, 'source_audio', kbps=session.media_info.source_audio_bitrate_kbps)}"

            kb = make_audio_bitrates_keyboard(session_id, lang, session.media_info)
            if query.message:
                await query.message.edit_text(card_text, reply_markup=kb, parse_mode="HTML")
            return

    # 3. Start download job (Video Quality or Audio Quality)
    target_type = "video" if prefix == "vq" else "audio"
    target_option = None

    if prefix == "vq":
        target_height = int(action_val)
        target_option = next(
            (o for o in session.media_info.video_qualities if o.height == target_height),
            None,
        )
        if not target_option:
            await query.answer(t(lang, "expired_button"), show_alert=True)
            return

    elif prefix == "aq":
        target_bitrate = int(action_val)
        target_option = next(
            (o for o in session.media_info.audio_options if o.bitrate_kbps == target_bitrate),
            None,
        )
        if not target_option:
            await query.answer(t(lang, "expired_button"), show_alert=True)
            return

    # Check enqueue permission
    can_run, enqueue_err = await queue_mgr.can_enqueue(user_id)
    if not can_run:
        await query.answer(t(lang, enqueue_err or "busy_user"), show_alert=True)
        return

    await query.answer()

    # Create job
    job_id = uuid.uuid4().hex[:8]
    job_dir = settings.temp_dir / f"job_{job_id}"
    job = ActiveJob(
        job_id=job_id,
        user_id=user_id,
        chat_id=query.message.chat.id if query.message else user_id,
        temp_dir=job_dir,
    )
    registered = await queue_mgr.register_job(job)
    if not registered:
        await query.answer(t(lang, "busy_user"), show_alert=True)
        return

    # Remove inline keyboard
    if query.message:
        try:
            await query.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass

    # Launch background job
    job_task = asyncio.create_task(
        run_job_pipeline(
            bot=bot,
            settings=settings,
            queue_mgr=queue_mgr,
            job=job,
            session=session,
            target_type=target_type,
            target_option=target_option,
            lang=lang,
        )
    )
    job.task = job_task
