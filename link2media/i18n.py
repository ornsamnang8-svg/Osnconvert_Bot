"""Khmer and English user-facing messages.

Messages use Telegram HTML formatting.  Any value inserted with ``t()`` that
comes from users or media metadata must be escaped by the caller with
``html.escape`` before formatting.
"""

from __future__ import annotations

DEFAULT_LANG = "km"
SUPPORTED_LANGS = ("km", "en")

TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "start": (
            "👋 <b>Welcome to Link2Media!</b>\n\n"
            "Send me <b>one</b> public video link and I will send the file back here.\n\n"
            "1️⃣ Paste a link from YouTube, TikTok, Facebook, Instagram or X/Twitter\n"
            "2️⃣ Choose 🎬 <b>Video</b> or 🎵 <b>MP3</b>\n"
            "3️⃣ Pick a quality and wait a moment\n\n"
            "Commands: /help · /language · /cancel\n\n"
            "<i>Only download content you own or have permission to use.</i>"
        ),
        "help": (
            "ℹ️ <b>Help</b>\n\n"
            "<b>Supported (best effort):</b>\n"
            "• YouTube and YouTube Shorts\n"
            "• TikTok\n"
            "• Facebook videos and Reels\n"
            "• Instagram videos and Reels\n"
            "• X / Twitter\n\n"
            "<b>Limits:</b>\n"
            "• Maximum video length: {max_minutes} minutes\n"
            "• Maximum file size: {max_mb} MB (Telegram bot limit)\n"
            "• Video quality up to 1080p (only qualities the source really has)\n"
            "• MP3 at 128 or 192 kbps\n"
            "• One request at a time per person\n\n"
            "<b>Not supported:</b> private or login-only posts, paywalled or DRM content, "
            "live streams, playlists and channels.\n\n"
            "Platforms change often, so some links may fail even when they look public."
        ),
        "choose_language": "🌐 Choose your language:",
        "language_set": "✅ Language set to English.",
        "send_link_hint": "📎 Please send a video link (for example a YouTube or TikTok URL).",
        "one_link_only": "☝️ Please send only <b>one</b> link at a time.",
        "invalid_url": "❌ That doesn't look like a valid link. Please copy the full link and try again.",
        "unsupported_platform": (
            "❌ This website isn't supported.\n"
            "Supported: YouTube, TikTok, Facebook, Instagram, X/Twitter. See /help."
        ),
        "unsupported_link": (
            "❌ This link isn't a single video. Playlists, channels, profiles and "
            "stories are not supported — please send a link to one video."
        ),
        "blocked_destination": "⛔ This link points to an address that is not allowed.",
        "not_allowed": "🔒 Sorry, this is a private bot.",
        "busy_user": (
            "⏳ You already have a request in progress. Please wait for it to finish "
            "or send /cancel."
        ),
        "queue_full": "🚦 The bot is very busy right now. Please try again in a few minutes.",
        "cancelled": "🛑 Cancelled.",
        "nothing_to_cancel": "There is nothing to cancel.",
        "expired_button": "⌛ This button has expired. Please send the link again.",
        "not_your_button": "🚫 This button belongs to someone else.",
        "duplicate_action": "⏳ Already working on it…",
        "card": "🎬 <b>{title}</b>\n{details}",
        "card_uploader": "👤 {uploader}",
        "card_duration": "⏱ {duration}",
        "card_platform": "🌐 {platform}",
        "unknown_title": "Untitled video",
        "choose_action": "👇 What would you like to download?",
        "choose_quality": "🎬 Choose a video quality:",
        "choose_bitrate": (
            "🎵 Choose an MP3 bitrate.\n"
            "<i>A higher MP3 bitrate makes a bigger file but cannot add quality "
            "that the original recording doesn't have.</i>"
        ),
        "source_audio": "<i>Original audio: about {kbps} kbps.</i>",
        "some_too_large": "<i>Higher qualities are hidden because they would exceed {max_mb} MB.</i>",
        "size_unknown_note": "<i>Size is estimated; the final file is checked before sending.</i>",
        "no_video_fits": (
            "📦 Every video quality would be larger than {max_mb} MB, the Telegram "
            "limit for bots."
        ),
        "no_audio_available": "🔇 This video has no audio track, so MP3 is not available.",
        "btn_video": "🎬 Download Video",
        "btn_mp3": "🎵 Download MP3",
        "btn_cancel": "❌ Cancel",
        "btn_back": "⬅️ Back",
        "btn_quality": "{label}{size}",
        "btn_bitrate_128": "128 kbps · smaller file{size}",
        "btn_bitrate_192": "192 kbps · larger file{size}",
        "status_checking": "🔎 Checking the link…",
        "status_queued": "🕒 Queued…",
        "status_queued_pos": "🕒 Queued (position {position})…",
        "status_downloading": "⬇️ Downloading…",
        "status_downloading_pct": "⬇️ Downloading… {percent}%",
        "status_converting": "⚙️ Converting…",
        "status_uploading": "📤 Uploading to Telegram…",
        "status_done": "✅ Done! Your file is below.",
        "status_failed": "⚠️ Failed.",
        "video_no_audio_note": "🔇 Note: this video has no audio track.",
        "file_caption": "📥 via @{bot_username}",
        "err_login_required": (
            "🔐 This content requires login or is private, so I can't download it. "
            "Only public posts are supported."
        ),
        "err_unavailable": "🚫 This video is unavailable, deleted, or private.",
        "err_geo_restricted": "🌍 This video is not available in the bot's region.",
        "err_drm": "🔒 This video is DRM-protected and can't be downloaded.",
        "err_live": "📡 Live streams (and upcoming or still-processing streams) are not supported.",
        "err_playlist": "📚 Playlists and multi-video posts are not supported. Please send one video.",
        "err_too_long": "⏱ This video is too long. The maximum is {max_minutes} minutes.",
        "err_no_formats": "🎞 No downloadable format was found for this video.",
        "err_no_audio": "🔇 This video has no audio track, so an MP3 can't be created.",
        "err_too_large": (
            "📦 The file is {size_mb} MB, which is over the {max_mb} MB limit for "
            "Telegram bots."
        ),
        "err_too_large_estimate": (
            "📦 This would be larger than the {max_mb} MB limit for Telegram bots."
        ),
        "try_lower": "Please choose a lower quality or MP3 below.",
        "err_network": "🌐 Network problem while contacting the website. Please try again later.",
        "err_timeout": "⏰ This took too long and was stopped. Please try again or choose a lower quality.",
        "err_disk_full": "💾 The server is low on disk space. Please try again later.",
        "err_unsupported": (
            "❌ I couldn't find a video at this link. It may be unsupported, private, "
            "or not a video post."
        ),
        "err_rate_limited": "🚦 The website is limiting requests right now. Please try again later.",
        "err_internal": "⚠️ Something went wrong. Please try again later.",
        "err_upload": "📤 Telegram rejected the upload. Please try again or choose a lower quality.",
        "private_chat_only": "Please message me in a private chat.",
    },
    "km": {
        "start": (
            "👋 <b>សូមស្វាគមន៍មកកាន់ Link2Media!</b>\n\n"
            "សូមផ្ញើតំណវីដេអូសាធារណៈ <b>មួយ</b> មកខ្ញុំ ហើយខ្ញុំនឹងផ្ញើឯកសារត្រឡប់មកទីនេះវិញ។\n\n"
            "1️⃣ បិទភ្ជាប់តំណពី YouTube, TikTok, Facebook, Instagram ឬ X/Twitter\n"
            "2️⃣ ជ្រើសរើស 🎬 <b>វីដេអូ</b> ឬ 🎵 <b>MP3</b>\n"
            "3️⃣ ជ្រើសរើសគុណភាព ហើយរង់ចាំបន្តិច\n\n"
            "ពាក្យបញ្ជា៖ /help · /language · /cancel\n\n"
            "<i>សូមទាញយកតែមាតិកាដែលអ្នកជាម្ចាស់ ឬមានការអនុញ្ញាតប៉ុណ្ណោះ។</i>"
        ),
        "help": (
            "ℹ️ <b>ជំនួយ</b>\n\n"
            "<b>វេទិកាដែលគាំទ្រ (តាមលទ្ធភាព)៖</b>\n"
            "• YouTube និង YouTube Shorts\n"
            "• TikTok\n"
            "• វីដេអូ និង Reels របស់ Facebook\n"
            "• វីដេអូ និង Reels របស់ Instagram\n"
            "• X / Twitter\n\n"
            "<b>ដែនកំណត់៖</b>\n"
            "• ប្រវែងវីដេអូអតិបរមា៖ {max_minutes} នាទី\n"
            "• ទំហំឯកសារអតិបរមា៖ {max_mb} MB (ដែនកំណត់របស់ Telegram bot)\n"
            "• គុណភាពវីដេអូរហូតដល់ 1080p (តែគុណភាពដែលវីដេអូដើមមានពិតប្រាកដ)\n"
            "• MP3 ទំហំ 128 ឬ 192 kbps\n"
            "• ម្នាក់អាចស្នើបានតែម្តងមួយៗ\n\n"
            "<b>មិនគាំទ្រ៖</b> ប្រកាសឯកជន ឬត្រូវចូលគណនី មាតិកាបង់ប្រាក់ ឬមាន DRM "
            "ការផ្សាយផ្ទាល់ បញ្ជីចាក់ (playlist) និងឆានែល។\n\n"
            "វេទិកាទាំងនេះផ្លាស់ប្តូរញឹកញាប់ ដូច្នេះតំណខ្លះអាចបរាជ័យ ទោះបីមើលទៅជាសាធារណៈក៏ដោយ។"
        ),
        "choose_language": "🌐 សូមជ្រើសរើសភាសា៖",
        "language_set": "✅ បានកំណត់ភាសាជាភាសាខ្មែរ។",
        "send_link_hint": "📎 សូមផ្ញើតំណវីដេអូ (ឧទាហរណ៍ តំណ YouTube ឬ TikTok)។",
        "one_link_only": "☝️ សូមផ្ញើតំណតែ <b>មួយ</b> ក្នុងមួយលើក។",
        "invalid_url": "❌ នេះមិនមែនជាតំណត្រឹមត្រូវទេ។ សូមចម្លងតំណពេញ ហើយព្យាយាមម្តងទៀត។",
        "unsupported_platform": (
            "❌ គេហទំព័រនេះមិនត្រូវបានគាំទ្រទេ។\n"
            "គាំទ្រ៖ YouTube, TikTok, Facebook, Instagram, X/Twitter។ មើល /help ។"
        ),
        "unsupported_link": (
            "❌ តំណនេះមិនមែនជាវីដេអូតែមួយទេ។ មិនគាំទ្របញ្ជីចាក់ ឆានែល ប្រូហ្វាល "
            "ឬ story ទេ — សូមផ្ញើតំណទៅកាន់វីដេអូមួយ។"
        ),
        "blocked_destination": "⛔ តំណនេះចង្អុលទៅអាសយដ្ឋានដែលមិនត្រូវបានអនុញ្ញាត។",
        "not_allowed": "🔒 សូមអភ័យទោស នេះជា bot ឯកជន។",
        "busy_user": "⏳ អ្នកមានសំណើមួយកំពុងដំណើរការ។ សូមរង់ចាំឱ្យវាចប់ ឬផ្ញើ /cancel ។",
        "queue_full": "🚦 Bot កំពុងរវល់ខ្លាំង។ សូមព្យាយាមម្តងទៀតក្នុងរយៈពេលប៉ុន្មាននាទីទៀត។",
        "cancelled": "🛑 បានបោះបង់។",
        "nothing_to_cancel": "មិនមានអ្វីត្រូវបោះបង់ទេ។",
        "expired_button": "⌛ ប៊ូតុងនេះផុតកំណត់ហើយ។ សូមផ្ញើតំណម្តងទៀត។",
        "not_your_button": "🚫 ប៊ូតុងនេះជារបស់អ្នកផ្សេង។",
        "duplicate_action": "⏳ កំពុងដំណើរការរួចហើយ…",
        "card": "🎬 <b>{title}</b>\n{details}",
        "card_uploader": "👤 {uploader}",
        "card_duration": "⏱ {duration}",
        "card_platform": "🌐 {platform}",
        "unknown_title": "វីដេអូគ្មានចំណងជើង",
        "choose_action": "👇 តើអ្នកចង់ទាញយកអ្វី?",
        "choose_quality": "🎬 សូមជ្រើសរើសគុណភាពវីដេអូ៖",
        "choose_bitrate": (
            "🎵 សូមជ្រើសរើស bitrate សម្រាប់ MP3។\n"
            "<i>Bitrate ខ្ពស់ធ្វើឱ្យឯកសារធំជាង ប៉ុន្តែមិនអាចបន្ថែមគុណភាពលើសពីសំឡេងដើមបានទេ។</i>"
        ),
        "source_audio": "<i>សំឡេងដើម៖ ប្រហែល {kbps} kbps។</i>",
        "some_too_large": "<i>គុណភាពខ្ពស់ជាងនេះត្រូវបានលាក់ ព្រោះវានឹងលើសពី {max_mb} MB។</i>",
        "size_unknown_note": "<i>ទំហំគ្រាន់តែជាការប៉ាន់ស្មាន។ ឯកសារចុងក្រោយនឹងត្រូវពិនិត្យមុនពេលផ្ញើ។</i>",
        "no_video_fits": "📦 គុណភាពវីដេអូទាំងអស់នឹងធំជាង {max_mb} MB ដែលជាដែនកំណត់របស់ Telegram bot។",
        "no_audio_available": "🔇 វីដេអូនេះគ្មានសំឡេង ដូច្នេះមិនអាចទាញយកជា MP3 បានទេ។",
        "btn_video": "🎬 ទាញយកវីដេអូ",
        "btn_mp3": "🎵 ទាញយក MP3",
        "btn_cancel": "❌ បោះបង់",
        "btn_back": "⬅️ ត្រឡប់ក្រោយ",
        "btn_quality": "{label}{size}",
        "btn_bitrate_128": "128 kbps · ឯកសារតូចជាង{size}",
        "btn_bitrate_192": "192 kbps · ឯកសារធំជាង{size}",
        "status_checking": "🔎 កំពុងពិនិត្យតំណ…",
        "status_queued": "🕒 កំពុងរង់ចាំក្នុងជួរ…",
        "status_queued_pos": "🕒 កំពុងរង់ចាំក្នុងជួរ (លេខ {position})…",
        "status_downloading": "⬇️ កំពុងទាញយក…",
        "status_downloading_pct": "⬇️ កំពុងទាញយក… {percent}%",
        "status_converting": "⚙️ កំពុងបម្លែង…",
        "status_uploading": "📤 កំពុងផ្ញើទៅ Telegram…",
        "status_done": "✅ រួចរាល់! ឯកសាររបស់អ្នកនៅខាងក្រោម។",
        "status_failed": "⚠️ បរាជ័យ។",
        "video_no_audio_note": "🔇 ចំណាំ៖ វីដេអូនេះគ្មានសំឡេងទេ។",
        "file_caption": "📥 តាមរយៈ @{bot_username}",
        "err_login_required": (
            "🔐 មាតិកានេះតម្រូវឱ្យចូលគណនី ឬជាឯកជន ដូច្នេះខ្ញុំមិនអាចទាញយកបានទេ។ "
            "គាំទ្រតែប្រកាសសាធារណៈប៉ុណ្ណោះ។"
        ),
        "err_unavailable": "🚫 វីដេអូនេះមិនមាន ត្រូវបានលុប ឬជាឯកជន។",
        "err_geo_restricted": "🌍 វីដេអូនេះមិនអាចមើលបាននៅក្នុងតំបន់របស់ bot ទេ។",
        "err_drm": "🔒 វីដេអូនេះត្រូវបានការពារដោយ DRM ហើយមិនអាចទាញយកបានទេ។",
        "err_live": "📡 មិនគាំទ្រការផ្សាយផ្ទាល់ (ឬការផ្សាយដែលមិនទាន់ចាប់ផ្តើម ឬកំពុងដំណើរការ) ទេ។",
        "err_playlist": "📚 មិនគាំទ្របញ្ជីចាក់ ឬប្រកាសដែលមានវីដេអូច្រើនទេ។ សូមផ្ញើវីដេអូមួយ។",
        "err_too_long": "⏱ វីដេអូនេះវែងពេក។ អតិបរមាគឺ {max_minutes} នាទី។",
        "err_no_formats": "🎞 រកមិនឃើញទម្រង់ដែលអាចទាញយកបានសម្រាប់វីដេអូនេះទេ។",
        "err_no_audio": "🔇 វីដេអូនេះគ្មានសំឡេង ដូច្នេះមិនអាចបង្កើត MP3 បានទេ។",
        "err_too_large": "📦 ឯកសារមានទំហំ {size_mb} MB ដែលលើសពីដែនកំណត់ {max_mb} MB របស់ Telegram bot។",
        "err_too_large_estimate": "📦 ឯកសារនេះនឹងធំជាងដែនកំណត់ {max_mb} MB របស់ Telegram bot។",
        "try_lower": "សូមជ្រើសរើសគុណភាពទាបជាងនេះ ឬ MP3 ខាងក្រោម។",
        "err_network": "🌐 មានបញ្ហាបណ្តាញពេលភ្ជាប់ទៅគេហទំព័រ។ សូមព្យាយាមម្តងទៀតពេលក្រោយ។",
        "err_timeout": "⏰ ដំណើរការយូរពេក ហើយត្រូវបានបញ្ឈប់។ សូមព្យាយាមម្តងទៀត ឬជ្រើសគុណភាពទាបជាង។",
        "err_disk_full": "💾 ម៉ាស៊ីនមេខ្វះទំហំផ្ទុក។ សូមព្យាយាមម្តងទៀតពេលក្រោយ។",
        "err_unsupported": (
            "❌ ខ្ញុំរកមិនឃើញវីដេអូនៅតំណនេះទេ។ វាអាចមិនត្រូវបានគាំទ្រ ជាឯកជន "
            "ឬមិនមែនជាប្រកាសវីដេអូ។"
        ),
        "err_rate_limited": "🚦 គេហទំព័រកំពុងកំណត់ចំនួនសំណើ។ សូមព្យាយាមម្តងទៀតពេលក្រោយ។",
        "err_internal": "⚠️ មានបញ្ហាអ្វីមួយកើតឡើង។ សូមព្យាយាមម្តងទៀតពេលក្រោយ។",
        "err_upload": "📤 Telegram បដិសេធការផ្ញើឯកសារ។ សូមព្យាយាមម្តងទៀត ឬជ្រើសគុណភាពទាបជាង។",
        "private_chat_only": "សូមផ្ញើសារមកខ្ញុំក្នុងការជជែកឯកជន។",
    },
}

LANGUAGE_NAMES = {"km": "🇰🇭 ភាសាខ្មែរ", "en": "🇬🇧 English"}


def normalize_lang(lang: str | None) -> str:
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def t(lang: str | None, key: str, **kwargs: object) -> str:
    """Return the translated message ``key`` formatted with ``kwargs``."""
    lang = normalize_lang(lang)
    template = TEXTS[lang].get(key) or TEXTS["en"].get(key) or key
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template
    return template
