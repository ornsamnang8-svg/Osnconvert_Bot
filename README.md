# 🎬 Link2Media — Telegram Media Downloader Bot

A reliable, privacy-respecting Telegram bot that lets users send public video links from **YouTube, TikTok, Facebook, Instagram, and X/Twitter**, select their preferred video quality or MP3 bitrate, and receive the downloadable file directly inside Telegram.

Built with **Python 3.13**, **aiogram 3**, **yt-dlp**, and **FFmpeg**. Features full **Khmer (default) and English** support with per-user preference persistence in SQLite.

---

## 🌟 Key Features

- **Target Platforms**: Public videos from YouTube & Shorts, TikTok, Facebook (videos & Reels), Instagram (videos & Reels), and X/Twitter.
- **Video & Audio Downloads**:
  - 🎬 **Video**: Selectable quality tiers up to **1080p FHD** (never upscales beyond original source resolution).
  - 🎵 **MP3**: Genuine audio conversion with `libmp3lame` at **128 kbps** or **192 kbps** with ID3 tags (never just renames extensions).
- **Smooth User Experience**:
  - Single status message dynamically updated: `Checking → Queued → Downloading → Converting → Uploading → Done`.
  - Preview card with video title, duration, uploader, and platform.
  - Video streaming support (`+faststart` MP4) and proper audio tags.
- **Bilingual Interface**:
  - 🇰🇭 Khmer (default) and 🇬🇧 English.
  - Switch anytime via `/language` or interactive buttons.
- **Safety & Production Reliability**:
  - **SSRF Protection**: Strict host resolution checks block loopback, RFC 1918 private IPs, link-local, and cloud metadata addresses (e.g. AWS/GCP 169.254.169.254).
  - **Single Active Job per User**: Prevents abuse and queue starvation.
  - **Queue Concurrency Control**: Configurable global worker pool with bounded queue.
  - **Upload Limit Guards**: Enforces Telegram's 50 MB limit with a safe 48 MB default budget. Aborts streaming downloads immediately if size exceeds budget.
  - **Child Process Management**: Subprocesses are tracked and terminated cleanly on timeout or `/cancel` via `psutil`.
  - **Temporary Isolation & Cleanup**: Each job runs in its own isolated folder and cleans up automatically on success, failure, cancellation, or restart.

---

## 📋 Prerequisites

Before running the bot, ensure you have:

1. **Python 3.10+** (Python 3.13 recommended)
2. **FFmpeg & FFprobe** installed and accessible on your system PATH
3. A **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)

---

## 🚀 Quick Start Guide

### Step 1: Create a Bot with @BotFather

1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Start the chat and send `/newbot`.
3. Choose a display name (e.g., `Link2Media Downloader`).
4. Choose a username ending in `bot` (e.g., `MyLink2Media_bot`).
5. Copy the generated **HTTP API Token** (format: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789`).

> [!CAUTION]
> Never share your Bot Token publicly or commit it to GitHub. Anyone with your token can control your bot.

---

### Step 2: Configure Environment Variables

1. In the project folder, make a copy of `.env.example` named `.env`:
   - **Windows (PowerShell)**:
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```
2. Open `.env` in a text editor and paste your token:
   ```env
   BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ123456789
   ```
3. *(Optional)* Restrict access to your personal Telegram user ID:
   ```env
   ALLOWED_USER_IDS=123456789
   ```

---

### Step 3: Installation & Running on Windows

1. **Install Python & FFmpeg (if not already installed)**:
   Open PowerShell and run:
   ```powershell
   winget install Python.Python.3.13
   winget install Gyan.FFmpeg
   ```
   *(Close and reopen PowerShell after installation to refresh PATH).*

2. **Create and Activate Virtual Environment**:
   ```powershell
   cd Link2Media
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run the Bot**:
   ```powershell
   python -m link2media.main
   ```

5. **Stop the Bot**:
   Press `Ctrl + C` in PowerShell to stop the bot gracefully.

---

### Step 4: Running on a Linux Server with Docker (Recommended for 24/7 Hosting)

Docker Compose provides container isolation, automatic restart on system reboot, and bundles FFmpeg and Python dependencies.

1. **Install Docker and Docker Compose**:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose-v2
   ```

2. **Clone / Upload Project to Server**:
   ```bash
   cd /opt/Link2Media
   cp .env.example .env
   nano .env # Paste your BOT_TOKEN
   ```

3. **Build and Start in Background**:
   ```bash
   docker compose up -d --build
   ```

4. **View Logs**:
   ```bash
   docker compose logs -f
   ```

5. **Stop the Container**:
   ```bash
   docker compose down
   ```

---

### Step 5: Running Continuously on Linux without Docker (systemd)

If you run directly on a Linux VPS without Docker:

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/link2media.service
   ```
2. Paste the configuration:
   ```ini
   [Unit]
   Description=Link2Media Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/opt/Link2Media
   ExecStart=/opt/Link2Media/.venv/bin/python -m link2media.main
   Restart=always
   RestartSec=5
   EnvironmentFile=/opt/Link2Media/.env

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now link2media.service
   sudo systemctl status link2media.service
   ```

---

## 🔄 Keeping yt-dlp Updated

Social media platforms (especially YouTube, Instagram, and TikTok) frequently change their internal video extraction signatures and challenge scripts. When links stop downloading:

### In Local Virtual Environment:
```powershell
.\.venv\Scripts\Activate.ps1
pip install --upgrade yt-dlp yt-dlp-ejs deno
```

### In Docker:
Rebuild the container image with the latest dependencies:
```bash
docker compose build --no-cache
docker compose up -d
```

---

## 🛠 Troubleshooting Guide

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **"This content requires login or is private"** | The video is set to private, friends-only, or age-restricted. | The bot only downloads public content. Do not attempt to bypass login or private walls. |
| **"This video is unavailable, deleted, or private"** | The URL is broken or the creator removed the post. | Verify the link opens in a private/incognito browser window. |
| **"The file is X MB, which is over the 48 MB limit"** | Telegram Bot API enforces a strict 50 MB limit for standard bot uploads. | Select a lower resolution (e.g. 480p or 360p) or download as MP3. |
| **"YouTube JS challenge solver error"** | YouTube updated challenge scripts. | Ensure `deno` and `yt-dlp-ejs` are installed. Run `pip install --upgrade yt-dlp yt-dlp-ejs`. |
| **"This link isn't a single video"** | User sent a playlist, channel, user profile, or story. | The bot only processes single video URLs. Send direct video link. |
| **"You already have a request in progress"** | User sent another link while previous download is still working. | Wait for the active download to finish, or send `/cancel`. |

---

## 🧪 Running Automated Tests

A comprehensive test suite verifies security defenses, format selection, size limits, and actual FFmpeg conversions on local media fixtures:

```powershell
.\.venv\Scripts\Activate.ps1
pytest -v
```

All 22 unit & integration tests run locally without needing external network access or Telegram credentials.

---

## 📁 Project Structure

```
Link2Media/
├── link2media/
│   ├── __init__.py
│   ├── config.py         # Validated settings, safe defaults, secrets hiding
│   ├── convert.py        # FFmpeg transcode (H.264/AAC faststart & libmp3lame MP3)
│   ├── db.py             # SQLite database for user preferences
│   ├── download.py       # yt-dlp download pipeline with real-time size limiters
│   ├── extract.py        # yt-dlp metadata extractor & format tier builder
│   ├── i18n.py           # Khmer (default) and English translations
│   ├── main.py           # Bot entrypoint, polling loop, shutdown hooks
│   ├── models.py         # Dataclasses for MediaInfo, QualityOption, Jobs
│   ├── queue_manager.py  # Bounded concurrency queue, single-job per user
│   ├── security.py       # SSRF protection, URL validation, filename sanitizer
│   └── handlers/
│       ├── __init__.py   # Router aggregator
│       ├── callbacks.py  # Button interactions & job pipeline runner
│       ├── commands.py   # /start, /help, /language, /cancel handlers
│       ├── keyboards.py  # Inline keyboard builders
│       ├── messages.py   # URL receiver & media card previewer
│       └── ui_helpers.py # HTML card formatter & throttled status updater
├── tests/
│   ├── test_config.py
│   ├── test_conversion_fixture.py  # Real FFmpeg MP4 & MP3 conversion tests
│   ├── test_db_i18n.py
│   ├── test_format_selection.py
│   ├── test_queue_and_sessions.py
│   └── test_security.py
├── .dockerignore
├── .env.example
├── .gitignore
├── compose.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ⚖️ License & Fair Use

This tool is designed strictly for downloading public media that you own or have explicit authorization to download. It contains no DRM circumvention or paywall bypasses.
