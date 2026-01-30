# api-gateway/src/api/internal.py
"""
Internal API endpoints for service-to-service communication.

These endpoints are used by the main backend (facebook-automation) to
trigger Telegram notifications and other internal operations.
"""

import base64
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

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


class InvoicePDFRequest(BaseModel):
    """Request model for sending invoice PDF to Telegram."""
    chat_id: str
    invoice_id: str
    invoice_number: str
    amount: str
    pdf_data: str  # Base64-encoded PDF
    customer_name: Optional[str] = None


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


@router.post("/telegram/send-invoice-pdf")
async def send_invoice_pdf(data: InvoicePDFRequest):
    """
    Send invoice PDF as document with verify button to Telegram chat.

    Called by the main backend when sending invoice to customer.
    Sends the PDF as a document attachment with an inline "Verify Payment" button.
    """
    bot, _ = create_bot()

    if not bot:
        raise HTTPException(
            status_code=503,
            detail="Telegram bot not configured"
        )

    try:
        # Decode base64 PDF data
        pdf_bytes = base64.b64decode(data.pdf_data)

        # Create PDF file for sending
        pdf_file = BufferedInputFile(
            file=pdf_bytes,
            filename=f"{data.invoice_number}.pdf"
        )

        # Create inline keyboard with two buttons: verify current and view others
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ Verify {data.invoice_number}",
                    callback_data=f"verify_invoice:{data.invoice_id}"
                ),
                InlineKeyboardButton(
                    text="📋 Other Invoices",
                    callback_data=f"view_other_invoices:{data.invoice_id}"
                )
            ]
        ])

        # Build caption
        caption = (
            f"<b>Invoice {data.invoice_number}</b>\n\n"
            f"Amount: <b>{data.amount}</b>\n\n"
            f"After payment, click the button below to verify."
        )

        # Send document with button
        await bot.send_document(
            chat_id=data.chat_id,
            document=pdf_file,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

        logger.info(f"Invoice PDF sent to chat {data.chat_id}: {data.invoice_number}")

        return {
            "success": True,
            "chat_id": data.chat_id,
            "invoice_number": data.invoice_number,
            "type": "pdf"
        }

    except Exception as e:
        logger.error(f"Failed to send invoice PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send Telegram PDF: {str(e)}"
        )


class BroadcastRequest(BaseModel):
    """Request model for broadcasting promotional content to multiple chats."""
    chat_ids: list[str]
    content: str
    media_type: str = "text"  # text, image, video, document, mixed
    media_urls: list[str] = []


class BroadcastResult(BaseModel):
    """Result of broadcasting to a single chat."""
    chat_id: str
    success: bool
    error: Optional[str] = None


@router.post("/telegram/broadcast")
async def broadcast_message(data: BroadcastRequest):
    """
    Broadcast promotional content to multiple Telegram chats.

    Supports different media types:
    - text: Plain text message with HTML formatting
    - image: Single image with caption
    - video: Single video with caption
    - document: Single document with caption
    - mixed: Media group (up to 10 items)

    Called by the main backend's ads-alert system for promotional broadcasts.
    """
    from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument

    # Entry log
    logger.info(
        f"Broadcast request received: chat_count={len(data.chat_ids)}, "
        f"media_type={data.media_type}, media_urls={len(data.media_urls)}, "
        f"content_len={len(data.content) if data.content else 0}"
    )

    bot, _ = create_bot()

    if not bot:
        logger.error("Broadcast failed: Telegram bot not configured")
        raise HTTPException(
            status_code=503,
            detail="Telegram bot not configured"
        )

    # Log media processing details
    if data.media_urls:
        logger.debug(f"Processing media URLs: {data.media_urls}")

    results = []

    for chat_id in data.chat_ids:
        try:
            if data.media_type == "text":
                # Plain text message
                logger.debug(f"Sending text to {chat_id}")
                await bot.send_message(
                    chat_id=chat_id,
                    text=data.content,
                    parse_mode="HTML"
                )
                results.append(BroadcastResult(chat_id=chat_id, success=True))

            elif data.media_type == "image" and data.media_urls:
                # Single image with caption
                logger.debug(f"Sending image to {chat_id}: {data.media_urls[0]}")
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=data.media_urls[0],
                    caption=data.content[:1024] if data.content else None,
                    parse_mode="HTML"
                )
                results.append(BroadcastResult(chat_id=chat_id, success=True))

            elif data.media_type == "video" and data.media_urls:
                # Single video with caption
                logger.debug(f"Sending video to {chat_id}: {data.media_urls[0]}")
                await bot.send_video(
                    chat_id=chat_id,
                    video=data.media_urls[0],
                    caption=data.content[:1024] if data.content else None,
                    parse_mode="HTML"
                )
                results.append(BroadcastResult(chat_id=chat_id, success=True))

            elif data.media_type == "document" and data.media_urls:
                # Single document with caption
                logger.debug(f"Sending document to {chat_id}: {data.media_urls[0]}")
                await bot.send_document(
                    chat_id=chat_id,
                    document=data.media_urls[0],
                    caption=data.content[:1024] if data.content else None,
                    parse_mode="HTML"
                )
                results.append(BroadcastResult(chat_id=chat_id, success=True))

            elif data.media_type == "mixed" and data.media_urls:
                # Media group (up to 10 items)
                logger.debug(f"Sending media group to {chat_id}: {len(data.media_urls)} items")
                media_group = []
                for i, url in enumerate(data.media_urls[:10]):
                    # Determine media type from URL extension
                    url_lower = url.lower()
                    if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        logger.debug(f"Media {i}: {url} -> InputMediaPhoto")
                        media_item = InputMediaPhoto(
                            media=url,
                            caption=data.content[:1024] if i == 0 and data.content else None,
                            parse_mode="HTML" if i == 0 else None
                        )
                    elif any(ext in url_lower for ext in ['.mp4', '.webm', '.mov']):
                        logger.debug(f"Media {i}: {url} -> InputMediaVideo")
                        media_item = InputMediaVideo(
                            media=url,
                            caption=data.content[:1024] if i == 0 and data.content else None,
                            parse_mode="HTML" if i == 0 else None
                        )
                    else:
                        # Default to document for other file types
                        logger.debug(f"Media {i}: {url} -> InputMediaDocument")
                        media_item = InputMediaDocument(
                            media=url,
                            caption=data.content[:1024] if i == 0 and data.content else None,
                            parse_mode="HTML" if i == 0 else None
                        )
                    media_group.append(media_item)

                if media_group:
                    await bot.send_media_group(chat_id=chat_id, media=media_group)
                results.append(BroadcastResult(chat_id=chat_id, success=True))

            else:
                # Fallback to text if media type unknown or no media URLs
                logger.debug(f"Fallback text send to {chat_id}")
                await bot.send_message(
                    chat_id=chat_id,
                    text=data.content or "No content",
                    parse_mode="HTML"
                )
                results.append(BroadcastResult(chat_id=chat_id, success=True))

            logger.info(f"Broadcast sent to chat {chat_id}, type: {data.media_type}")

        except Exception as e:
            logger.error(f"Failed to broadcast to chat {chat_id}: {e}")
            results.append(BroadcastResult(
                chat_id=chat_id,
                success=False,
                error=str(e)
            ))

    # Calculate stats
    sent_count = sum(1 for r in results if r.success)
    failed_count = sum(1 for r in results if not r.success)

    # Summary log
    logger.info(
        f"Broadcast completed: total={len(results)}, sent={sent_count}, "
        f"failed={failed_count}, media_type={data.media_type}"
    )

    return {
        "total": len(results),
        "sent": sent_count,
        "failed": failed_count,
        "results": [r.model_dump() for r in results]
    }


@router.get("/health")
async def internal_health():
    """Health check for internal API."""
    bot, _ = create_bot()
    return {
        "status": "ok",
        "telegram_bot": bot is not None
    }
