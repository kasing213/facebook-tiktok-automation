# api-gateway/src/api/internal.py
"""
Internal API endpoints for service-to-service communication.

These endpoints are used by the main backend (facebook-automation) to
trigger Telegram notifications and other internal operations.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot import create_bot

logger = logging.getLogger(__name__)
router = APIRouter()


class InvoiceNotificationRequest(BaseModel):
    """Request model for sending invoice notification to Telegram."""
    chat_id: str
    invoice_number: str
    amount: str
    currency: str = "KHR"
    bank: Optional[str] = None
    expected_account: Optional[str] = None
    due_date: Optional[str] = None
    customer_name: Optional[str] = None
    invoice_id: Optional[str] = None


class MerchantNotificationRequest(BaseModel):
    """Request model for notifying merchant about payment."""
    merchant_telegram_id: str
    customer_name: str
    invoice_number: str
    amount: str
    status: str  # verified, rejected, pending
    reason: Optional[str] = None


@router.post("/telegram/send-invoice")
async def send_invoice_notification(data: InvoiceNotificationRequest):
    """
    Send invoice notification to a client's Telegram chat.

    Called by the main backend when an invoice is created for a
    customer with linked Telegram.
    """
    bot, _ = create_bot()

    if not bot:
        raise HTTPException(
            status_code=503,
            detail="Telegram bot not configured"
        )

    try:
        # Build notification message
        message_parts = [
            "<b>[Invoice]</b> " + data.invoice_number,
            ""
        ]

        if data.customer_name:
            message_parts.append(f"<b>To:</b> {data.customer_name}")

        message_parts.append(f"<b>Amount:</b> {data.amount}")

        if data.due_date:
            message_parts.append(f"<b>Due:</b> {data.due_date}")

        message_parts.append("")

        if data.bank:
            message_parts.append(f"<b>Bank:</b> {data.bank}")
        if data.expected_account:
            message_parts.append(f"<b>Account:</b> <code>{data.expected_account}</code>")

        message_parts.append("")
        message_parts.append("<i>Tap the button below to send payment proof.</i>")

        message = "\n".join(message_parts)

        # Build inline keyboard with "Pay Now" button if invoice_id is provided
        keyboard = None
        if data.invoice_id:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="Send Payment Screenshot",
                    callback_data=f"pay_invoice:{data.invoice_id}"
                )]
            ])

        # Send message with button
        await bot.send_message(
            chat_id=data.chat_id,
            text=message,
            parse_mode="HTML",
            reply_markup=keyboard
        )

        logger.info(f"Invoice notification sent to chat {data.chat_id}: {data.invoice_number}")

        return {
            "success": True,
            "chat_id": data.chat_id,
            "invoice_number": data.invoice_number
        }

    except Exception as e:
        logger.error(f"Failed to send invoice notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send Telegram message: {str(e)}"
        )


@router.post("/telegram/notify-merchant")
async def notify_merchant_payment(data: MerchantNotificationRequest):
    """
    Notify merchant about a payment verification result.

    Called after OCR verification completes to inform the merchant.
    """
    bot, _ = create_bot()

    if not bot:
        raise HTTPException(
            status_code=503,
            detail="Telegram bot not configured"
        )

    try:
        # Build status icon
        if data.status == "verified":
            status_icon = "[OK]"
            status_text = "VERIFIED"
        elif data.status == "rejected":
            status_icon = "[X]"
            status_text = "REJECTED"
        else:
            status_icon = "[?]"
            status_text = "PENDING REVIEW"

        # Build notification message
        message_parts = [
            f"<b>{status_icon} Payment {status_text}</b>",
            "",
            f"<b>Client:</b> {data.customer_name}",
            f"<b>Invoice:</b> <code>{data.invoice_number}</code>",
            f"<b>Amount:</b> {data.amount}",
        ]

        if data.reason and data.status == "rejected":
            message_parts.append(f"<b>Reason:</b> {data.reason}")

        message = "\n".join(message_parts)

        # Send message
        await bot.send_message(
            chat_id=data.merchant_telegram_id,
            text=message
        )

        logger.info(f"Merchant notification sent: {data.invoice_number} -> {data.status}")

        return {
            "success": True,
            "merchant_telegram_id": data.merchant_telegram_id,
            "status": data.status
        }

    except Exception as e:
        logger.error(f"Failed to notify merchant: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send Telegram message: {str(e)}"
        )


@router.get("/health")
async def internal_health():
    """Health check for internal API."""
    bot, _ = create_bot()
    return {
        "status": "ok",
        "telegram_bot": bot is not None
    }
