"""
Inventory management commands for the Telegram bot.

Provides merchants with inventory status, low stock alerts,
and basic stock management functionality via Telegram.
"""

from aiogram import types, Router, F
from aiogram.filters.command import Command
from sqlalchemy import text, and_
from typing import List, Dict, Any

from src.db.postgres import get_db_session

router = Router()


async def get_user_by_telegram_id(telegram_id: str) -> Dict[str, Any] | None:
    """Get user by telegram ID with tenant info"""
    with get_db_session() as db:
        result = db.execute(
            text("""
                SELECT u.id, u.tenant_id, u.role, t.name as tenant_name
                FROM public.user u
                JOIN public.tenant t ON u.tenant_id = t.id
                WHERE u.telegram_user_id = :telegram_id AND u.is_active = true
            """),
            {"telegram_id": telegram_id}
        )
        row = result.fetchone()
        if row:
            return {
                "id": row.id,
                "tenant_id": row.tenant_id,
                "role": row.role,
                "tenant_name": row.tenant_name
            }
    return None


async def get_products_with_stock(tenant_id: str) -> List[Dict[str, Any]]:
    """Get products with current stock levels"""
    with get_db_session() as db:
        result = db.execute(
            text("""
                SELECT id, name, sku, current_stock, low_stock_threshold,
                       unit_price, currency, track_stock
                FROM inventory.products
                WHERE tenant_id = :tenant_id AND is_active = true
                ORDER BY name
            """),
            {"tenant_id": tenant_id}
        )

        products = []
        for row in result.fetchall():
            products.append({
                "id": row.id,
                "name": row.name,
                "sku": row.sku,
                "current_stock": row.current_stock,
                "low_stock_threshold": row.low_stock_threshold,
                "unit_price": row.unit_price,
                "currency": row.currency,
                "track_stock": row.track_stock
            })

        return products


async def get_low_stock_products(tenant_id: str) -> List[Dict[str, Any]]:
    """Get products below low stock threshold"""
    with get_db_session() as db:
        result = db.execute(
            text("""
                SELECT id, name, sku, current_stock, low_stock_threshold,
                       unit_price, currency
                FROM inventory.products
                WHERE tenant_id = :tenant_id
                  AND is_active = true
                  AND track_stock = true
                  AND current_stock <= low_stock_threshold
                ORDER BY current_stock, name
            """),
            {"tenant_id": tenant_id}
        )

        products = []
        for row in result.fetchall():
            products.append({
                "id": row.id,
                "name": row.name,
                "sku": row.sku,
                "current_stock": row.current_stock,
                "low_stock_threshold": row.low_stock_threshold,
                "unit_price": row.unit_price,
                "currency": row.currency
            })

        return products


def format_currency(amount: int, currency: str = "KHR") -> str:
    """Format currency amount (stored in smallest units)"""
    if currency == "KHR":
        return f"{amount:,} KHR"
    else:
        # Assume cents for other currencies
        return f"${amount/100:.2f} {currency}"


@router.message(Command("inventory"))
async def inventory_command(message: types.Message):
    """Show current inventory status"""
    telegram_id = str(message.from_user.id)

    # Get user and verify they're a merchant
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer(
            "❌ You don't appear to be registered. Please link your account first via the dashboard.",
            parse_mode="HTML"
        )
        return

    # Only members and owners can view inventory
    if user["role"] == "viewer":
        await message.answer(
            "❌ You don't have permission to view inventory. Contact your admin.",
            parse_mode="HTML"
        )
        return

    try:
        products = await get_products_with_stock(str(user["tenant_id"]))

        if not products:
            await message.answer(
                "📦 <b>Inventory Status</b>\n\n"
                "No products found. Add products via the dashboard to start tracking inventory.",
                parse_mode="HTML"
            )
            return

        # Calculate summary stats
        total_products = len(products)
        tracked_products = len([p for p in products if p["track_stock"]])
        low_stock_products = len([
            p for p in products
            if p["track_stock"] and p["current_stock"] <= (p["low_stock_threshold"] or 0)
        ])

        # Build response
        response = f"📦 <b>Inventory Status ({user['tenant_name']})</b>\n\n"
        response += f"📊 <b>Summary:</b>\n"
        response += f"• Total Products: {total_products}\n"
        response += f"• Tracked Products: {tracked_products}\n"
        response += f"• Low Stock Items: {low_stock_products}\n\n"

        if low_stock_products > 0:
            response += "⚠️ <b>Low Stock Alert!</b>\n"
            response += f"You have {low_stock_products} item(s) running low.\n"
            response += "Use /lowstock to see details.\n\n"

        # Show first 10 products with stock levels
        response += "📋 <b>Stock Levels:</b>\n"
        for i, product in enumerate(products[:10]):
            if not product["track_stock"]:
                stock_display = "∞ (untracked)"
            else:
                stock = product["current_stock"]
                threshold = product["low_stock_threshold"] or 0
                if stock <= threshold:
                    stock_display = f"⚠️ {stock} (low)"
                else:
                    stock_display = f"✅ {stock}"

            sku_part = f" ({product['sku']})" if product["sku"] else ""
            response += f"• {product['name']}{sku_part}: {stock_display}\n"

        if len(products) > 10:
            response += f"... and {len(products) - 10} more products\n"

        response += "\n💡 <b>Commands:</b>\n"
        response += "• /lowstock - View low stock items\n"
        response += "• Dashboard - Manage products and adjust stock"

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        print(f"Error in inventory command: {e}")
        await message.answer(
            "❌ Error retrieving inventory data. Please try again later.",
            parse_mode="HTML"
        )


@router.message(Command("lowstock"))
async def low_stock_command(message: types.Message):
    """Show products with low stock levels"""
    telegram_id = str(message.from_user.id)

    # Get user and verify they're a merchant
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer(
            "❌ You don't appear to be registered. Please link your account first via the dashboard.",
            parse_mode="HTML"
        )
        return

    # Only members and owners can view inventory
    if user["role"] == "viewer":
        await message.answer(
            "❌ You don't have permission to view inventory. Contact your admin.",
            parse_mode="HTML"
        )
        return

    try:
        low_stock_products = await get_low_stock_products(str(user["tenant_id"]))

        response = f"⚠️ <b>Low Stock Alert ({user['tenant_name']})</b>\n\n"

        if not low_stock_products:
            response += "✅ <b>Great news!</b>\n"
            response += "No products are currently running low on stock.\n\n"
            response += "💡 Use /inventory to view all stock levels."
        else:
            response += f"Found {len(low_stock_products)} item(s) below threshold:\n\n"

            for product in low_stock_products:
                sku_part = f" ({product['sku']})" if product["sku"] else ""
                price_part = format_currency(product["unit_price"], product["currency"])

                response += f"📦 <b>{product['name']}</b>{sku_part}\n"
                response += f"   Stock: {product['current_stock']} / {product['low_stock_threshold']} (threshold)\n"
                response += f"   Price: {price_part}\n\n"

            response += "💡 <b>Next Steps:</b>\n"
            response += "• Use the dashboard to adjust stock levels\n"
            response += "• Update low stock thresholds if needed\n"
            response += "• Reorder inventory to avoid stockouts"

        await message.answer(response, parse_mode="HTML")

    except Exception as e:
        print(f"Error in low stock command: {e}")
        await message.answer(
            "❌ Error retrieving low stock data. Please try again later.",
            parse_mode="HTML"
        )


async def send_low_stock_alert(tenant_id: str, product_name: str, current_stock: int, threshold: int):
    """
    Send low stock alert to all tenant users with Telegram linked.

    This function can be called when stock goes below threshold after a sale.
    """
    try:
        # Get all tenant users with Telegram
        with get_db_session() as db:
            result = db.execute(
                text("""
                    SELECT DISTINCT u.telegram_user_id, t.name as tenant_name
                    FROM public.user u
                    JOIN public.tenant t ON u.tenant_id = t.id
                    WHERE u.tenant_id = :tenant_id
                      AND u.telegram_user_id IS NOT NULL
                      AND u.is_active = true
                      AND u.role IN ('admin', 'user')
                """),
                {"tenant_id": tenant_id}
            )

            users = result.fetchall()

            if users:
                from aiogram import Bot
                from src.config import get_settings

                settings = get_settings()
                bot = Bot(token=settings.TELEGRAM_BOT_TOKEN.get_secret_value())

                alert_message = (
                    f"⚠️ <b>Low Stock Alert</b>\n\n"
                    f"📦 <b>{product_name}</b>\n"
                    f"Current stock: {current_stock}\n"
                    f"Threshold: {threshold}\n\n"
                    f"Consider restocking soon to avoid stockouts.\n\n"
                    f"Use /inventory to check all stock levels."
                )

                for user_row in users:
                    try:
                        await bot.send_message(
                            chat_id=user_row.telegram_user_id,
                            text=alert_message,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        print(f"Failed to send low stock alert to {user_row.telegram_user_id}: {e}")
                        continue

    except Exception as e:
        print(f"Error sending low stock alerts for tenant {tenant_id}: {e}")