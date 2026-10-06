/**
 * Link2Media Telegram Bot Live Interactive Simulator
 * Provides exact behavioral fidelity with the Python aiogram 3 bot.
 */

// Bilingual message catalog matching link2media/i18n.py
const TEXTS = {
  km: {
    start: `👋 <b>សូមស្វាគមន៍មកកាន់ Link2Media!</b>\n\nសូមផ្ញើតំណវីដេអូសាធារណៈ <b>មួយ</b> មកខ្ញុំ ហើយខ្ញុំនឹងផ្ញើឯកសារត្រឡប់មកទីនេះវិញ។\n\n1️⃣ បិទភ្ជាប់តំណពី YouTube, TikTok, Facebook, Instagram ឬ X/Twitter\n2️⃣ ជ្រើសរើស 🎬 <b>វីដេអូ</b> ឬ 🎵 <b>MP3</b>\n3️⃣ ជ្រើសរើសគុណភាព ហើយរង់ចាំបន្តិច\n\nពាក្យបញ្ជា៖ /help · /language · /cancel\n\n<i>សូមទាញយកតែមាតិកាដែលអ្នកជាម្ចាស់ ឬមានការអនុញ្ញាតប៉ុណ្ណោះ។</i>`,
    help: `ℹ️ <b>ជំនួយ</b>\n\n<b>វេទិកាដែលគាំទ្រ (តាមលទ្ធភាព)៖</b>\n• YouTube និង YouTube Shorts\n• TikTok\n• វីដេអូ និង Reels របស់ Facebook\n• វីដេអូ និង Reels របស់ Instagram\n• X / Twitter\n\n<b>ដែនកំណត់៖</b>\n• ប្រវែងវីដេអូអតិបរមា៖ 20 នាទី\n• ទំហំឯកសារអតិបរមា៖ 48 MB (ដែនកំណត់របស់ Telegram bot)\n• គុណភាពវីដេអូរហូតដល់ 1080p (តែគុណភាពដែលវីដេអូដើមមានពិតប្រាកដ)\n• MP3 ទំហំ 128 ឬ 192 kbps\n• ម្នាក់អាចស្នើបានតែម្តងមួយៗ\n\n<b>មិនគាំទ្រ៖</b> ប្រកាសឯកជន ឬត្រូវចូលគណនី មាតិកាបង់ប្រាក់ ឬមាន DRM ការផ្សាយផ្ទាល់ បញ្ជីចាក់ (playlist) និងឆានែល។`,
    choose_language: "🌐 សូមជ្រើសរើសភាសា៖",
    language_set: "✅ បានកំណត់ភាសាជាភាសាខ្មែរ។",
    send_link_hint: "📎 សូមផ្ញើតំណវីដេអូ (ឧទាហរណ៍ តំណ YouTube ឬ TikTok)។",
    one_link_only: "☝️ សូមផ្ញើតំណតែ <b>មួយ</b> ក្នុងមួយលើក។",
    invalid_url: "❌ នេះមិនមែនជាតំណត្រឹមត្រូវទេ។ សូមចម្លងតំណពេញ ហើយព្យាយាមម្តងទៀត។",
    unsupported_platform: "❌ គេហទំព័រនេះមិនត្រូវបានគាំទ្រទេ។\nគាំទ្រ៖ YouTube, TikTok, Facebook, Instagram, X/Twitter។ មើល /help ។",
    cancelled: "🛑 បានបោះបង់។",
    nothing_to_cancel: "មិនមានអ្វីត្រូវបោះបង់ទេ។",
    choose_action: "👇 តើអ្នកចង់ទាញយកអ្វី?",
    choose_quality: "🎬 សូមជ្រើសរើសគុណភាពវីដេអូ៖",
    choose_bitrate: "🎵 សូមជ្រើសរើស bitrate សម្រាប់ MP3។\n<i>Bitrate ខ្ពស់ធ្វើឱ្យឯកសារធំជាង ប៉ុន្តែមិនអាចបន្ថែមគុណភាពលើសពីសំឡេងដើមបានទេ។</i>",
    source_audio: "<i>សំឡេងដើម៖ ប្រហែល 128 kbps។</i>",
    btn_video: "🎬 ទាញយកវីដេអូ",
    btn_mp3: "🎵 ទាញយក MP3",
    btn_cancel: "❌ បោះបង់",
    btn_back: "⬅️ ត្រឡប់ក្រោយ",
    status_checking: "🔎 កំពុងពិនិត្យតំណ…",
    status_queued: "🕒 កំពុងរង់ចាំក្នុងជួរ…",
    status_downloading: "⬇️ កំពុងទាញយក…",
    status_downloading_pct: "⬇️ កំពុងទាញយក… {percent}%",
    status_converting: "⚙️ កំពុងបម្លែង…",
    status_uploading: "📤 កំពុងផ្ញើទៅ Telegram…",
    status_done: "✅ រួចរាល់! ឯកសាររបស់អ្នកនៅខាងក្រោម។",
    file_caption: "📥 តាមរយៈ @Link2MediaBot"
  },
  en: {
    start: `👋 <b>Welcome to Link2Media!</b>\n\nSend me <b>one</b> public video link and I will send the file back here.\n\n1️⃣ Paste a link from YouTube, TikTok, Facebook, Instagram or X/Twitter\n2️⃣ Choose 🎬 <b>Video</b> or 🎵 <b>MP3</b>\n3️⃣ Pick a quality and wait a moment\n\nCommands: /help · /language · /cancel\n\n<i>Only download content you own or have permission to use.</i>`,
    help: `ℹ️ <b>Help</b>\n\n<b>Supported (best effort):</b>\n• YouTube and YouTube Shorts\n• TikTok\n• Facebook videos and Reels\n• Instagram videos and Reels\n• X / Twitter\n\n<b>Limits:</b>\n• Maximum video length: 20 minutes\n• Maximum file size: 48 MB (Telegram bot limit)\n• Video quality up to 1080p (only qualities the source really has)\n• MP3 at 128 or 192 kbps\n• One request at a time per person\n\n<b>Not supported:</b> private or login-only posts, paywalled or DRM content, live streams, playlists and channels.`,
    choose_language: "🌐 Choose your language:",
    language_set: "✅ Language set to English.",
    send_link_hint: "📎 Please send a video link (for example a YouTube or TikTok URL).",
    one_link_only: "☝️ Please send only <b>one</b> link at a time.",
    invalid_url: "❌ That doesn't look like a valid link. Please copy the full link and try again.",
    unsupported_platform: "❌ This website isn't supported.\nSupported: YouTube, TikTok, Facebook, Instagram, X/Twitter. See /help.",
    cancelled: "🛑 Cancelled.",
    nothing_to_cancel: "There is nothing to cancel.",
    choose_action: "👇 What would you like to download?",
    choose_quality: "🎬 Choose a video quality:",
    choose_bitrate: "🎵 Choose an MP3 bitrate.\n<i>A higher MP3 bitrate makes a bigger file but cannot add quality that the original recording doesn't have.</i>",
    source_audio: "<i>Original audio: about 128 kbps.</i>",
    btn_video: "🎬 Download Video",
    btn_mp3: "🎵 Download MP3",
    btn_cancel: "❌ Cancel",
    btn_back: "⬅️ Back",
    status_checking: "🔎 Checking the link…",
    status_queued: "🕒 Queued…",
    status_downloading: "⬇️ Downloading…",
    status_downloading_pct: "⬇️ Downloading… {percent}%",
    status_converting: "⚙️ Converting…",
    status_uploading: "📤 Uploading to Telegram…",
    status_done: "✅ Done! Your file is below.",
    file_caption: "📥 via @Link2MediaBot"
  }
};

class TelegramSimulator {
  constructor() {
    this.currentLang = 'km'; // Default is Khmer as specified
    this.activeJob = null;
    this.sessionData = null;
    this.chatMessagesEl = document.getElementById('chatMessages');
    this.messageInputEl = document.getElementById('messageInput');
    this.sendBtn = document.getElementById('sendBtn');
    this.langToggleBtn = document.getElementById('langToggleBtn');
    this.langDropdown = document.getElementById('langDropdown');
    this.currentLangFlag = document.getElementById('currentLangFlag');
    this.currentLangName = document.getElementById('currentLangName');
    this.terminalLogsEl = document.getElementById('terminalLogs');

    this.initEvents();
    this.postWelcomeMessage();
  }

  t(key, params = {}) {
    let text = TEXTS[this.currentLang][key] || TEXTS['en'][key] || key;
    for (const [k, v] of Object.entries(params)) {
      text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    }
    return text;
  }

  getCurrentTimeStr() {
    const d = new Date();
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  log(msg, type = 'info') {
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    const time = new Date().toISOString().substring(11, 19);
    line.textContent = `[${time}] [${type.toUpperCase()}] ${msg}`;
    this.terminalLogsEl.appendChild(line);
    this.terminalLogsEl.scrollTop = this.terminalLogsEl.scrollHeight;
  }

  initEvents() {
    // Send message on Enter or click
    this.sendBtn.addEventListener('click', () => this.handleSendMessage());
    this.messageInputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.handleSendMessage();
      }
    });

    // Language dropdown
    this.langToggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      this.langDropdown.classList.toggle('active');
    });

    document.addEventListener('click', () => {
      this.langDropdown.classList.remove('active');
    });

    document.querySelectorAll('.lang-item').forEach(item => {
      item.addEventListener('click', () => {
        const selected = item.dataset.lang;
        this.setLanguage(selected);
      });
    });

    // Shortcuts in header
    document.getElementById('helpShortcutBtn').addEventListener('click', () => {
      this.processCommand('/help');
    });
    document.getElementById('langShortcutBtn').addEventListener('click', () => {
      this.processCommand('/language');
    });
    document.getElementById('resetChatBtn').addEventListener('click', () => {
      this.resetChat();
    });

    // Quick chips
    document.querySelectorAll('.chip').forEach(chip => {
      chip.addEventListener('click', () => {
        const url = chip.dataset.url;
        this.messageInputEl.value = url;
        this.handleSendMessage();
      });
    });

    // Clear logs
    document.getElementById('clearLogsBtn').addEventListener('click', () => {
      this.terminalLogsEl.innerHTML = '';
      this.log('Logs cleared.', 'info');
    });

    // Command trigger button
    document.getElementById('cmdBtn').addEventListener('click', () => {
      this.messageInputEl.value = '/';
      this.messageInputEl.focus();
    });
  }

  setLanguage(lang) {
    this.currentLang = lang;
    if (lang === 'km') {
      this.currentLangFlag.textContent = '🇰🇭';
      this.currentLangName.textContent = 'ភាសាខ្មែរ';
      document.body.style.fontFamily = 'var(--font-khmer)';
    } else {
      this.currentLangFlag.textContent = '🇬🇧';
      this.currentLangName.textContent = 'English';
      document.body.style.fontFamily = 'var(--font-main)';
    }
    this.log(`Language set to ${lang.toUpperCase()}`, 'success');
  }

  resetChat() {
    this.chatMessagesEl.innerHTML = `
      <div class="date-divider">
        <span>Today</span>
      </div>
    `;
    this.activeJob = null;
    this.sessionData = null;
    this.updateInspector('IDLE', 0, 'Ready');
    this.postWelcomeMessage();
    this.log('Session reset.', 'info');
  }

  postWelcomeMessage() {
    this.appendBotMessage(this.t('start'));
  }

  appendUserMessage(text) {
    const wrap = document.createElement('div');
    wrap.className = 'msg-bubble-wrap outgoing';
    wrap.innerHTML = `
      <div class="msg-bubble">
        <div class="msg-text">${this.escapeHtml(text)}</div>
        <span class="msg-time">${this.getCurrentTimeStr()}</span>
      </div>
    `;
    this.chatMessagesEl.appendChild(wrap);
    this.scrollToBottom();
  }

  appendBotMessage(htmlContent, inlineButtons = null) {
    const wrap = document.createElement('div');
    wrap.className = 'msg-bubble-wrap incoming';

    let buttonsHtml = '';
    if (inlineButtons && inlineButtons.length > 0) {
      buttonsHtml = `<div class="inline-keyboard">`;
      for (const row of inlineButtons) {
        buttonsHtml += `<div class="inline-row">`;
        for (const btn of row) {
          const dangerClass = btn.isDanger ? 'btn-danger' : '';
          buttonsHtml += `<button class="tg-btn ${dangerClass}" data-action="${btn.action}" data-val="${btn.val || ''}">${btn.text}</button>`;
        }
        buttonsHtml += `</div>`;
      }
      buttonsHtml += `</div>`;
    }

    wrap.innerHTML = `
      <div class="msg-bubble">
        <div class="msg-text">${htmlContent}</div>
        <span class="msg-time">${this.getCurrentTimeStr()}</span>
      </div>
      ${buttonsHtml}
    `;

    this.chatMessagesEl.appendChild(wrap);
    this.bindInlineButtons(wrap);
    this.scrollToBottom();
    return wrap;
  }

  updateBotMessage(msgWrap, htmlContent, inlineButtons = null) {
    const textEl = msgWrap.querySelector('.msg-text');
    if (textEl) {
      textEl.innerHTML = htmlContent;
    }

    const oldKb = msgWrap.querySelector('.inline-keyboard');
    if (oldKb) oldKb.remove();

    if (inlineButtons && inlineButtons.length > 0) {
      let buttonsHtml = `<div class="inline-keyboard">`;
      for (const row of inlineButtons) {
        buttonsHtml += `<div class="inline-row">`;
        for (const btn of row) {
          const dangerClass = btn.isDanger ? 'btn-danger' : '';
          buttonsHtml += `<button class="tg-btn ${dangerClass}" data-action="${btn.action}" data-val="${btn.val || ''}">${btn.text}</button>`;
        }
        buttonsHtml += `</div>`;
      }
      buttonsHtml += `</div>`;

      msgWrap.insertAdjacentHTML('beforeend', buttonsHtml);
      this.bindInlineButtons(msgWrap);
    }

    this.scrollToBottom();
  }

  bindInlineButtons(wrap) {
    wrap.querySelectorAll('.tg-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        const val = btn.dataset.val;
        this.handleInlineAction(action, val, wrap);
      });
    });
  }

  scrollToBottom() {
    this.chatMessagesEl.scrollTop = this.chatMessagesEl.scrollHeight;
  }

  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  handleSendMessage() {
    const text = this.messageInputEl.value.trim();
    if (!text) return;

    this.messageInputEl.value = '';
    this.appendUserMessage(text);
    this.log(`Incoming message: "${text}"`, 'info');

    if (text.startsWith('/')) {
      this.processCommand(text);
      return;
    }

    this.processUrlInput(text);
  }

  processCommand(cmd) {
    const cleanCmd = cmd.toLowerCase().split(' ')[0];
    if (cleanCmd === '/start') {
      this.postWelcomeMessage();
    } else if (cleanCmd === '/help') {
      this.appendBotMessage(this.t('help'));
    } else if (cleanCmd === '/language') {
      const kb = [
        [
          { text: "🇰🇭 ភាសាខ្មែរ", action: "set_lang", val: "km" },
          { text: "🇬🇧 English", action: "set_lang", val: "en" }
        ]
      ];
      this.appendBotMessage(this.t('choose_language'), kb);
    } else if (cleanCmd === '/cancel') {
      if (this.activeJob) {
        this.activeJob.cancelled = true;
        this.activeJob = null;
        this.appendBotMessage(this.t('cancelled'));
        this.updateInspector('CANCELLED', 0, 'Job cancelled by user');
        this.log('Active job cancelled via /cancel', 'warn');
      } else {
        this.appendBotMessage(this.t('nothing_to_cancel'));
      }
    } else {
      this.appendBotMessage(this.t('send_link_hint'));
    }
  }

  detectPlatform(url) {
    try {
      const u = new URL(url);
      const host = u.hostname.toLowerCase();
      if (host.includes('youtube.com') || host.includes('youtu.be')) return 'YouTube';
      if (host.includes('tiktok.com')) return 'TikTok';
      if (host.includes('facebook.com') || host.includes('fb.watch')) return 'Facebook';
      if (host.includes('instagram.com') || host.includes('instagr.am')) return 'Instagram';
      if (host.includes('twitter.com') || host.includes('x.com') || host.includes('t.co')) return 'X/Twitter';
      return null;
    } catch {
      return null;
    }
  }

  async processUrlInput(text) {
    const urlMatch = text.match(/https?:\/\/[^\s]+/i);
    if (!urlMatch) {
      this.appendBotMessage(this.t('invalid_url'));
      return;
    }

    const url = urlMatch[0];
    const platform = this.detectPlatform(url);

    if (!platform) {
      this.appendBotMessage(this.t('unsupported_platform'));
      this.log(`Rejected unsupported domain: ${url}`, 'warn');
      return;
    }

    this.log(`Validated URL on ${platform}: ${url}`, 'success');

    // Initial status message
    this.updateInspector('CHECKING', 16, `Validating URL on ${platform}...`);
    const statusMsg = this.appendBotMessage(this.t('status_checking'));

    await this.sleep(900);

    // Mock media extraction
    const mediaInfo = {
      title: `${platform} Spotlight Video (4K Sample)`,
      uploader: `@creator_${platform.toLowerCase()}`,
      duration: "0:45",
      platform: platform,
      hasAudio: true,
      qualities: [
        { label: "1080p FHD", height: 1080, size: "24.5 MB" },
        { label: "720p HD", height: 720, size: "14.2 MB" },
        { label: "480p SD", height: 480, size: "8.1 MB" },
        { label: "360p", height: 360, size: "4.5 MB" }
      ],
      bitrates: [
        { label: "128 kbps", kbps: 128, size: "1.8 MB" },
        { label: "192 kbps", kbps: 192, size: "2.7 MB" }
      ]
    };

    this.sessionData = {
      url,
      mediaInfo,
      statusMsgWrap: statusMsg
    };

    this.renderMainMenu(statusMsg);
  }

  renderMainMenu(msgWrap) {
    const info = this.sessionData.mediaInfo;
    const cardHtml = `
      <div class="media-preview-card">
        <img src="assets/sample_thumb.jpg" class="media-thumb-img" alt="Thumbnail">
      </div>
      🎬 <b>${this.escapeHtml(info.title)}</b>\n
      👤 ${this.escapeHtml(info.uploader)}\n
      ⏱ ${info.duration}\n
      🌐 ${info.platform}\n\n
      ${this.t('choose_action')}
    `;

    const kb = [
      [{ text: this.t('btn_video'), action: "show_video_qualities" }],
      [{ text: this.t('btn_mp3'), action: "show_audio_bitrates" }],
      [{ text: this.t('btn_cancel'), action: "cancel_session", isDanger: true }]
    ];

    this.updateBotMessage(msgWrap, cardHtml, kb);
    this.updateInspector('READY', 20, 'Awaiting user quality/bitrate choice');
  }

  renderVideoQualities(msgWrap) {
    const info = this.sessionData.mediaInfo;
    const cardHtml = `
      🎬 <b>${this.escapeHtml(info.title)}</b>\n\n
      ${this.t('choose_quality')}
    `;

    const kb = [];
    for (const q of info.qualities) {
      kb.push([{ text: `${q.label} (~${q.size})`, action: "download_video", val: q.height }]);
    }
    kb.push([
      { text: this.t('btn_back'), action: "back_to_main" },
      { text: this.t('btn_cancel'), action: "cancel_session", isDanger: true }
    ]);

    this.updateBotMessage(msgWrap, cardHtml, kb);
  }

  renderAudioBitrates(msgWrap) {
    const info = this.sessionData.mediaInfo;
    const cardHtml = `
      🎬 <b>${this.escapeHtml(info.title)}</b>\n\n
      ${this.t('choose_bitrate')}\n\n
      ${this.t('source_audio')}
    `;

    const kb = [
      [{ text: `128 kbps · smaller file (~1.8 MB)`, action: "download_audio", val: 128 }],
      [{ text: `192 kbps · larger file (~2.7 MB)`, action: "download_audio", val: 192 }],
      [
        { text: this.t('btn_back'), action: "back_to_main" },
        { text: this.t('btn_cancel'), action: "cancel_session", isDanger: true }
      ]
    ];

    this.updateBotMessage(msgWrap, cardHtml, kb);
  }

  handleInlineAction(action, val, msgWrap) {
    if (action === 'set_lang') {
      this.setLanguage(val);
      this.updateBotMessage(msgWrap, this.t('language_set'));
      return;
    }

    if (!this.sessionData) {
      this.log('Session expired or invalid button click.', 'warn');
      return;
    }

    if (action === 'show_video_qualities') {
      this.renderVideoQualities(msgWrap);
    } else if (action === 'show_audio_bitrates') {
      this.renderAudioBitrates(msgWrap);
    } else if (action === 'back_to_main') {
      this.renderMainMenu(msgWrap);
    } else if (action === 'cancel_session') {
      this.updateBotMessage(msgWrap, this.t('cancelled'));
      this.sessionData = null;
      this.updateInspector('IDLE', 0, 'Cancelled');
      this.log('Session cancelled.', 'info');
    } else if (action === 'download_video') {
      this.startJobPipeline('video', val, msgWrap);
    } else if (action === 'download_audio') {
      this.startJobPipeline('audio', val, msgWrap);
    }
  }

  async startJobPipeline(type, qualityVal, msgWrap) {
    this.activeJob = { type, qualityVal, cancelled: false };

    // Remove buttons from status message
    this.updateBotMessage(msgWrap, this.t('status_queued'));
    this.updateInspector('QUEUED', 20, 'Job queued, waiting for worker slot');
    this.log(`Job queued: type=${type}, quality=${qualityVal}`, 'info');

    await this.sleep(700);
    if (this.activeJob.cancelled) return;

    // Downloading Stage
    this.updateInspector('DOWNLOADING', 40, 'yt-dlp stream downloading...');
    this.log('yt-dlp started streaming download', 'info');

    for (let pct = 20; pct <= 100; pct += 25) {
      if (this.activeJob.cancelled) return;
      this.updateBotMessage(msgWrap, this.t('status_downloading_pct', { percent: pct }));
      this.updateInspector('DOWNLOADING', 40 + (pct * 0.2), `Downloading... ${pct}%`);
      await this.sleep(400);
    }

    if (this.activeJob.cancelled) return;

    // Converting Stage
    this.updateBotMessage(msgWrap, this.t('status_converting'));
    this.updateInspector('CONVERTING', 70, type === 'video' ? 'FFmpeg H.264/AAC transcode +faststart' : 'FFmpeg libmp3lame MP3 audio transcode');
    this.log(type === 'video' ? 'FFmpeg converting to H.264/AAC (+faststart)...' : 'FFmpeg converting to MP3 via libmp3lame...', 'info');
    await this.sleep(900);

    if (this.activeJob.cancelled) return;

    // Uploading Stage
    this.updateBotMessage(msgWrap, this.t('status_uploading'));
    this.updateInspector('UPLOADING', 90, 'Telegram sendVideo/sendAudio multipart upload...');
    this.log('Uploading final file via Telegram Bot API multipart upload...', 'info');
    await this.sleep(800);

    if (this.activeJob.cancelled) return;

    // Done Stage
    this.updateBotMessage(msgWrap, this.t('status_done'));
    this.updateInspector('DONE', 100, 'Completed successfully');
    this.log('Job completed. Sending media file to user chat.', 'success');

    // Send final media bubble
    this.sendFinalMediaMessage(type, qualityVal);
    this.activeJob = null;
  }

  sendFinalMediaMessage(type, qualityVal) {
    const wrap = document.createElement('div');
    wrap.className = 'msg-bubble-wrap incoming';

    let mediaContent = '';
    if (type === 'video') {
      mediaContent = `
        <video class="media-player-video" controls poster="assets/sample_thumb.jpg">
          <source src="assets/sample_video.mp4" type="video/mp4">
          Your browser does not support video playback.
        </video>
        <div style="margin-top: 6px; font-size: 0.82rem; color: #94a3b8;">
          🎬 <b>${this.escapeHtml(this.sessionData.mediaInfo.title)}</b> (${qualityVal}p)\n
          ${this.t('file_caption')}
        </div>
      `;
    } else {
      mediaContent = `
        <div class="media-audio-card">
          <div class="audio-icon-box">🎵</div>
          <div class="audio-info-box">
            <div class="audio-title">${this.escapeHtml(this.sessionData.mediaInfo.title)}</div>
            <div class="audio-artist">Link2Media • ${qualityVal} kbps MP3</div>
          </div>
        </div>
        <audio controls style="width: 100%; margin-top: 8px;">
          <source src="assets/sample_audio.mp3" type="audio/mpeg">
          Your browser does not support audio playback.
        </audio>
        <div style="margin-top: 6px; font-size: 0.82rem; color: #94a3b8;">
          ${this.t('file_caption')}
        </div>
      `;
    }

    wrap.innerHTML = `
      <div class="msg-bubble">
        ${mediaContent}
        <span class="msg-time">${this.getCurrentTimeStr()}</span>
      </div>
    `;

    this.chatMessagesEl.appendChild(wrap);
    this.scrollToBottom();
  }

  updateInspector(stage, progressPct, metaText) {
    const badge = document.getElementById('inspectorStageBadge');
    badge.textContent = stage;
    if (stage === 'IDLE' || stage === 'CANCELLED') {
      badge.className = 'badge';
    } else {
      badge.className = 'badge active';
    }

    document.getElementById('pipelineProgressFill').style.width = `${progressPct}%`;
    document.getElementById('pipelineMetaText').textContent = metaText;

    const stepOrder = ['Checking', 'Queued', 'Downloading', 'Converting', 'Uploading', 'Done'];
    const currentStepIdx = stepOrder.findIndex(s => s.toUpperCase() === stage);

    stepOrder.forEach((stepName, idx) => {
      const el = document.getElementById(`step${stepName}`);
      if (!el) return;

      el.classList.remove('active', 'completed');
      if (idx < currentStepIdx) {
        el.classList.add('completed');
      } else if (idx === currentStepIdx) {
        el.classList.add('active');
      }
    });
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Initialize simulator when DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
  window.sim = new TelegramSimulator();
});
