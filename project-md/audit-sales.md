# Audit Sales

Path: /mnt/d/audit-sales

Purpose: Audit-only sales case decoder for Telegram messages. Produces structured JSON, plus daily JPG and monthly Excel reports via an API server.

Stack: TypeScript, Telegraf, Express, MongoDB, Puppeteer, ExcelJS, Handlebars.

Entry points:
- src/index.ts (dev)
- dist/index.js (build output)

Scripts (package.json):
- npm run build
- npm start
- npm run dev
- npm run watch
- npm run lint
- npm run typecheck

Start script:
- ./start-bot.sh

API endpoints (from COMMANDS.md):
- GET /reports/daily/jpg?date=YYYY-MM-DD
- GET /reports/monthly/excel?month=YYYY-MM
- GET /health

Env (from COMMANDS.md):
- DATABASE_URL
- TELEGRAM_BOT_TOKEN
- OPENAI_API_KEY
- OPENAI_MODEL
- REPORT_CHAT_ID
- TIMEZONE

Notes:
- Sales entry flow uses a strict header format and reason selection (A-J).
