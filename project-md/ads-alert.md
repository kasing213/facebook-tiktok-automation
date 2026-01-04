# Ads Alert (Daily Promotion Bot)

Path: /mnt/d/ads-alert

Purpose: Registration bot collects chat IDs in MongoDB; sender bot sends daily promos to registered chats.

Stack: Node.js (ESM), MongoDB.

Entry points:
- src/registerChat.js (registration bot)
- src/sendPromo.js (send daily promos)

Scripts (package.json):
- npm start
- npm run register
- npm run send
- npm run send:test

Start scripts:
- ./start-register.sh
- ./start-sender.sh
- ./start-bot.sh (legacy flexible starter)

Promo content folder layout (default):
- /promo/today (one image + message.txt)
- /promo/sent/YYYY-MM-DD (archive)

Observed promo folder on this machine:
- /mnt/d/promo

Env (from README):
- TELEGRAM_BOT_TOKEN
- MONGO_DB_URI
- MONGO_DB_NAME
- MONGO_CHAT_COLLECTION
- MONGO_CHAT_FIELD
- PROMO_FOLDER
- ADMIN_USER_IDS
- RETRY_MAX_ATTEMPTS
- RETRY_INITIAL_DELAY_MS
- RETRY_MAX_DELAY_MS
- RETRY_BACKOFF_MULTIPLIER
- RETRY_JITTER
- TELEGRAM_CHAT_ID / TELEGRAM_CHAT_IDS / TELEGRAM_CHAT_IDS_FILE (legacy)

Notes:
- Sender is intended to run via cron; registration bot is long-running.
