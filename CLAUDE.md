# Claude Code Project Configuration

## Project Info
- **Name**: Facebook/TikTok Automation Project
- **Type**: FastAPI + Telegram Bot + Social Media Automation
- **Working Directory**: `/mnt/d/Facebook-automation/`

## Development Setup
- **Python Environment**: Use `.venv/` (already created)
- **Activate venv**: `source .venv/bin/activate`
- **Dependencies**: See `app/tests/requirements.txt`
- **Database**: PostgreSQL with SQLAlchemy + Alembic migrations

## Key Commands
```bash
# Start FastAPI server
cd /mnt/d/Facebook-automation
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start Telegram bot
python -m app.bot

# Database migrations
alembic upgrade head
```

## Project Structure
- `app/main.py` - FastAPI application
- `app/bot.py` - Telegram bot
- `app/core/` - Configuration, database, models
- `app/integrations/` - Facebook/TikTok OAuth & APIs
- `migrations/` - Database schema versions

## Current Status
- ✅ Project structure created
- ✅ Virtual environment ready
- ✅ Dependencies defined
- 🔧 Need to set up environment variables
- 🔧 Need to implement Facebook/TikTok integrations
- 🔧 Need to complete database models

## Environment Variables Needed
Create `.env` file with:
- `TELEGRAM_BOT_TOKEN`
- `DATABASE_URL`
- `SECRET_KEY`
- `FACEBOOK_APP_ID`
- `FACEBOOK_APP_SECRET`
- `TIKTOK_CLIENT_ID`
- `TIKTOK_CLIENT_SECRET`
✅ Updated CLAUDE.md with today's progress (2025-10-01):

  Added to Documentation:
  - React frontend added to project type
  - Frontend commands and structure documented
  - Detailed progress log with completed features
  - Next priority tasks for tomorrow

  Key Updates:
  - ✅ React OAuth interface complete with demo mode
  - ✅ Vite/WSL configuration fixed
  - ✅ Frontend-backend proxy working
  - ✅ Both servers running (FastAPI:8000, React:3000)

  Ready for tomorrow's backend OAuth implementation tasks.

  Todos
  ☒ Document today's completed work
  ☐ Set up environment variables (.env file)
  ☐ Implement Facebook OAuth backend integration
  ☐ Implement TikTok OAuth backend integration
  ☐ Complete database models for user and social accounts
  ☐ Connect frontend OAuth buttons to backend endpoints
  ☐ Test OAuth flow end-to-end