# Invoice Generator

Path: /mnt/d/Invoice-generator

Purpose: Telegram bot to create and send PDF invoices; includes customer lookup/history, QR-based registration, and export tools.

Stack: Node.js, MongoDB (Mongoose), Puppeteer, Handlebars, node-telegram-bot-api, qrcode, xlsx.

Entry points:
- src/bot.js (main bot)
- src/generateInvoice.js (PDF generation)
- src/sendtelegram.js (file delivery)
- src/fullAuto.js (batch processing)

Scripts (package.json):
- npm start
- npm run dev
- npm run export:customers
- npm run export:excel
- npm run export:csv
- npm run export:invoices-all
- npm run test:qr
- npm run test:lookup

Key folders:
- templates/, assets/, invoices/, exports/, qr-codes/, scripts/, utils/, models/

Env (from project docs):
- MONGO_URL
- TELEGRAM_BOT_TOKEN
- BOT_USERNAME
- QR_IMAGE_PATH
- CLAUDE_API

Notes:
- Bot enforces rate limiting and duplicate prevention.
- PDF output stored in invoices/ and debug HTML in invoices/.debug/.
