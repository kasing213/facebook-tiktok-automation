# Scriptclient

Path: /mnt/d/scriptclient

Purpose: Telegram bot that verifies payment screenshots using OpenAI vision, tracks payments in MongoDB, and organizes screenshots by status.

Stack: Node.js, Express, MongoDB driver, OpenAI, node-telegram-bot-api.

Entry points:
- src/botfetch.js (main bot)
- src/payment-scheduler.js (scheduled checks)
- src/cross-verify-payment.js (verification routine)

Scripts (package.json):
- npm start
- npm run scheduler
- npm run verify

Env (from README):
- TELEGRAM_TOKEN
- MONGO_URL
- DB_NAME
- OPENAI_API_KEY
- USD_TO_KHR_RATE
- PAYMENT_TOLERANCE_PERCENT
- EXPECTED_RECIPIENT_ACCOUNT
- PORT
- SCREENSHOT_DIR
- SCREENSHOT_DOWNLOAD_TOKEN
- MONGO_URL_INVOICE (optional)
- DB_NAME_INVOICE (optional)

Notes:
- Uses separate customer and invoice databases when configured.
- Screenshots are sorted into verified/rejected/pending folders.
