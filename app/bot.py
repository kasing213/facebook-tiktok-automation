# app/bot.py
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.enums import ParseMode
import asyncio
from typing import Optional

from app.core.config import get_settings
from app.core.db import get_db_session
from app.core.tenant import get_tenant_context
from app.core.models import UserRole
from app.deps import get_logger
from app.services import TenantService

async def on_startup(bot: Bot):
    s = get_settings()
    me = await bot.get_me()
    print(f"🤖 Bot @{me.username} started (env={s.ENV})")

def make_bot_dp():
    s = get_settings()
    bot = Bot(token=s.TELEGRAM_BOT_TOKEN.get_secret_value(), parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    log = get_logger()

    @dp.message(Command("start"))
    async def cmd_start(m: types.Message):
        welcome_msg = """
🤖 <b>Facebook/TikTok Automation Bot</b>

Welcome! This bot helps you manage your social media automation.

Commands:
/connect_here - Link this chat to your tenant
/create_tenant - Create a new tenant
/status - Show your tenant status
/help - Show this help message
        """
        await m.answer(welcome_msg.strip())

    @dp.message(Command("create_tenant"))
    async def cmd_create_tenant(m: types.Message):
        """Create a new tenant and link current chat"""
        try:
            # Extract tenant name from command
            args = m.text.split(maxsplit=1)
            if len(args) < 2:
                await m.answer("Please provide a tenant name: <code>/create_tenant My Company</code>")
                return

            tenant_name = args[1].strip()
            chat_id = str(m.chat.id)
            user_id = str(m.from_user.id) if m.from_user else None

            with get_db_session() as db:
                tenant_service = TenantService(db)

                # Create tenant with admin user
                tenant, admin_user = tenant_service.create_tenant_with_admin(
                    name=tenant_name,
                    admin_telegram_id=user_id,
                    admin_username=m.from_user.username if m.from_user else None
                )
                log.info(f"Created tenant: {tenant.name} ({tenant.id})")

                # Create telegram destination using repository
                from app.repositories import DestinationRepository
                dest_repo = DestinationRepository(db)
                destination = dest_repo.create_telegram_destination(
                    tenant_id=tenant.id,
                    name=f"Chat {chat_id}",
                    chat_id=chat_id
                )
                log.info(f"Created destination: {destination.id}")

                # Commit is handled by the service

                await m.answer(f"""
✅ <b>Tenant Created Successfully!</b>

<b>Tenant:</b> {tenant.name}
<b>ID:</b> <code>{tenant.id}</code>
<b>Slug:</b> <code>{tenant.slug}</code>

This chat is now linked to your tenant. You can start adding social media accounts and setting up automations!

Next steps:
• Visit the web interface to connect Facebook/TikTok accounts
• Configure automation rules
• Set up reports and alerts
                """.strip())

        except ValueError as e:
            await m.answer(f"❌ Error creating tenant: {str(e)}")
            log.error(f"Failed to create tenant: {e}")
        except Exception as e:
            await m.answer("❌ An unexpected error occurred. Please try again.")
            log.error(f"Unexpected error in create_tenant: {e}")

    @dp.message(Command("connect_here"))
    async def cmd_connect_here(m: types.Message):
        """Link current chat to an existing tenant"""
        try:
            # Extract tenant slug from command
            args = m.text.split(maxsplit=1)
            if len(args) < 2:
                await m.answer("Please provide a tenant slug: <code>/connect_here my-tenant-slug</code>")
                return

            tenant_slug = args[1].strip()
            chat_id = str(m.chat.id)

            with get_db_session() as db:
                tenant_service = TenantService(db)

                # Find tenant
                tenant = tenant_service.get_tenant_by_slug(tenant_slug)
                if not tenant:
                    await m.answer(f"❌ Tenant not found: <code>{tenant_slug}</code>")
                    return

                # Create telegram destination using repository
                from app.repositories import DestinationRepository
                dest_repo = DestinationRepository(db)
                destination = dest_repo.create_telegram_destination(
                    tenant_id=tenant.id,
                    name=f"Chat {chat_id}",
                    chat_id=chat_id
                )

                # Commit handled by context manager
                log.info(f"Connected chat {chat_id} to tenant {tenant.id}")

                await m.answer(f"✅ Chat linked to tenant: <b>{tenant.name}</b>")

        except ValueError as e:
            await m.answer(f"❌ Error linking chat: {str(e)}")
            log.error(f"Failed to link chat: {e}")
        except Exception as e:
            await m.answer("❌ An unexpected error occurred. Please try again.")
            log.error(f"Unexpected error in connect_here: {e}")

    @dp.message(Command("status"))
    async def cmd_status(m: types.Message):
        """Show status for connected tenants"""
        try:
            chat_id = str(m.chat.id)

            with get_db_session() as db:
                from app.core.models import Destination

                # Find destinations for this chat
                destinations = db.query(Destination).filter(
                    Destination.type == "telegram_chat",
                    Destination.config.op('->>')('chat_id') == chat_id,
                    Destination.is_active == True
                ).all()

                if not destinations:
                    await m.answer("❌ This chat is not linked to any tenant. Use /create_tenant or /connect_here")
                    return

                # Show status for each connected tenant
                for dest in destinations:
                    context = get_tenant_context(db, str(dest.tenant_id))
                    if context:
                        stats = context['stats']
                        await m.answer(f"""
📊 <b>Tenant Status: {context['name']}</b>

<b>ID:</b> <code>{context['id']}</code>
<b>Slug:</b> <code>{context['slug']}</code>

<b>Resources:</b>
• Users: {stats['users']}
• Destinations: {stats['destinations']}
• Valid Tokens: {stats['valid_tokens']}
• Active Automations: {stats['active_automations']}/{stats['total_automations']}

<b>Connected Platforms:</b>
{' • '.join(f'{platform.title()}: {count}' for platform, count in stats['platforms'].items()) or 'None'}
                        """.strip())

        except Exception as e:
            await m.answer("❌ An unexpected error occurred.")
            log.error(f"Unexpected error in status: {e}")

    @dp.message(Command("help"))
    async def cmd_help(m: types.Message):
        help_text = """
🤖 <b>Facebook/TikTok Automation Bot</b>

<b>Commands:</b>
/create_tenant &lt;name&gt; - Create new tenant and link this chat
/connect_here &lt;slug&gt; - Link this chat to existing tenant
/status - Show tenant status and statistics
/help - Show this help message

<b>Getting Started:</b>
1. Create a tenant: <code>/create_tenant My Company</code>
2. Visit the web interface to connect social accounts
3. Configure automation rules and reports
4. Receive notifications in this chat!

<b>Support:</b>
For technical support, contact your administrator.
        """
        await m.answer(help_text.strip())

    return bot, dp

async def run_bot():
    bot, dp = make_bot_dp()
    await on_startup(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run_bot())
