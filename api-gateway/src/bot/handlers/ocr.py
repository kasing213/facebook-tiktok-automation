# api-gateway/src/bot/handlers/ocr.py
"""OCR payment verification command handlers."""

import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.ocr_service import ocr_service
from src.bot.services.linking import get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


class OCRStates(StatesGroup):
    """States for OCR verification flow."""
    waiting_for_screenshot = State()


@router.message(Command("ocr"))
async def cmd_ocr(message: types.Message, state: FSMContext):
    """Handle /ocr command - initiate payment screenshot verification."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard -> Integrations -> Telegram to connect."
        )
        return

    # Check if OCR service is configured
    if not ocr_service.is_configured():
        await message.answer(
            "<b>OCR Verification</b>\n\n"
            "Service not configured.\n"
            "Please set OCR_API_URL and OCR_API_KEY environment variables."
        )
        return

    # Check service health
    health = await ocr_service.health_check()
    if health.get("status") != "healthy":
        await message.answer(
            "<b>OCR Verification</b>\n\n"
            f"Service unavailable: {health.get('message', 'Unknown error')}"
        )
        return

    await state.set_state(OCRStates.waiting_for_screenshot)
    await message.answer(
        "<b>OCR Payment Verification</b>\n\n"
        "Please send me a screenshot of the payment receipt.\n\n"
        "The OCR system will extract:\n"
        "- Transaction amount\n"
        "- Currency\n"
        "- Date/time\n"
        "- Reference numbers\n\n"
        "Send /cancel to cancel."
    )


@router.message(Command("ocr_status"))
async def cmd_ocr_status(message: types.Message):
    """Handle /ocr_status command - check OCR service status."""
    telegram_id = str(message.from_user.id)

    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer("Please link your account first.")
        return

    if not ocr_service.is_configured():
        await message.answer(
            "<b>OCR Service Status</b>\n\n"
            "Status: Not Configured\n"
            "Missing: OCR_API_URL and/or OCR_API_KEY"
        )
        return

    status = await ocr_service.get_status()

    if status.get("status") == "error":
        await message.answer(
            f"<b>OCR Service Status</b>\n\n"
            f"Status: Error\n"
            f"Message: {status.get('message', 'Unknown')}"
        )
    else:
        await message.answer(
            f"<b>OCR Service Status</b>\n\n"
            f"Status: {status.get('status', 'Unknown')}\n"
            f"Service: Connected"
        )


@router.message(Command("cancel"), OCRStates.waiting_for_screenshot)
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Cancel the current OCR operation."""
    await state.clear()
    await message.answer("OCR verification cancelled.")


@router.message(OCRStates.waiting_for_screenshot, F.photo)
async def handle_screenshot(message: types.Message, state: FSMContext):
    """Handle screenshot upload for OCR verification."""
    await message.answer("Processing screenshot... Please wait.")

    try:
        # Get the highest resolution photo
        photo = message.photo[-1]

        # Download the photo
        file = await message.bot.get_file(photo.file_id)
        photo_bytes = await message.bot.download_file(file.file_path)

        # Read bytes from BytesIO
        image_data = photo_bytes.read()

        # Send to OCR service
        result = await ocr_service.verify_screenshot(
            image_data=image_data,
            filename=f"telegram_{photo.file_id}.jpg"
        )

        await state.clear()

        if result.get("success") is False:
            await message.answer(
                f"<b>Verification Failed</b>\n\n"
                f"Error: {result.get('message', 'Unknown error')}"
            )
            return

        # Format the result
        extracted = result.get("extracted_data", {})
        confidence = result.get("confidence", 0)

        amount = extracted.get("amount", "N/A")
        currency = extracted.get("currency", "")
        date = extracted.get("date", "N/A")
        reference = extracted.get("reference", "N/A")

        confidence_bar = get_confidence_bar(confidence)

        await message.answer(
            f"<b>OCR Verification Result</b>\n\n"
            f"Amount: <code>{currency} {amount}</code>\n"
            f"Date: {date}\n"
            f"Reference: <code>{reference}</code>\n\n"
            f"Confidence: {confidence_bar} {confidence:.0%}\n\n"
            f"Record ID: <code>{result.get('record_id', 'N/A')}</code>"
        )

    except Exception as e:
        logger.error(f"OCR processing error: {e}")
        await state.clear()
        await message.answer(
            f"<b>Error Processing Screenshot</b>\n\n"
            f"An error occurred while processing your screenshot.\n"
            f"Please try again or contact support."
        )


@router.message(OCRStates.waiting_for_screenshot)
async def handle_invalid_input(message: types.Message):
    """Handle non-photo messages while waiting for screenshot."""
    await message.answer(
        "Please send a screenshot image, or use /cancel to cancel."
    )


def get_confidence_bar(confidence: float) -> str:
    """Generate a visual confidence bar."""
    filled = int(confidence * 10)
    empty = 10 - filled
    return "[" + "#" * filled + "-" * empty + "]"
