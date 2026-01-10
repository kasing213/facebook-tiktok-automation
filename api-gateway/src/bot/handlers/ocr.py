# api-gateway/src/bot/handlers/ocr.py
"""OCR payment verification command handlers."""

import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.ocr_service import ocr_service
from src.services.invoice_service import invoice_service
from src.bot.services.linking import get_user_by_telegram_id

logger = logging.getLogger(__name__)
router = Router()


class OCRStates(StatesGroup):
    """States for OCR verification flow."""
    waiting_for_screenshot = State()
    waiting_for_invoice_screenshot = State()
    waiting_for_invoice_selection = State()


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

    is_mock = health.get("mode") == "mock"

    await state.set_state(OCRStates.waiting_for_screenshot)

    if is_mock:
        await message.answer(
            "<b>OCR Payment Verification (Mock Mode)</b>\n\n"
            "Please send me a screenshot of the payment receipt.\n\n"
            "<i>Note: OCR is in mock mode for testing.\n"
            "For actual invoice verification, use:</i>\n"
            "<code>/verify_invoice INV-XXXXX</code>\n\n"
            "Send /cancel to cancel."
        )
    else:
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
    elif status.get("mode") == "mock":
        await message.answer(
            f"<b>OCR Service Status</b>\n\n"
            f"Status: Active (Mock Mode)\n"
            f"Mode: Testing/Development\n\n"
            f"<i>Mock mode simulates OCR verification.\n"
            f"Use /verify_invoice to test payment verification.</i>"
        )
    else:
        await message.answer(
            f"<b>OCR Service Status</b>\n\n"
            f"Status: {status.get('status', 'Unknown')}\n"
            f"Mode: External API\n"
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

        # Check if in mock mode
        is_mock = result.get("mock_mode", False)

        # Format the result
        extracted = result.get("extracted_data", {})
        confidence = result.get("confidence", 0)

        amount = extracted.get("amount", "N/A")
        currency = extracted.get("currency", "")
        date = extracted.get("date", "N/A")
        reference = extracted.get("reference", "N/A")

        confidence_bar = get_confidence_bar(confidence)

        if is_mock:
            await message.answer(
                f"<b>OCR Result (Mock Mode)</b>\n\n"
                f"Screenshot received ({len(image_data):,} bytes)\n\n"
                f"<i>Note: OCR is in mock mode for testing.\n"
                f"For actual verification, use:</i>\n"
                f"<code>/verify_invoice INV-XXXXX</code>\n\n"
                f"<i>This will match your screenshot against the invoice amount.</i>\n\n"
                f"Record ID: <code>{result.get('record_id', 'N/A')}</code>"
            )
        else:
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


# ============================================================================
# Invoice-linked verification commands
# ============================================================================

@router.message(Command("verify_invoice"))
async def cmd_verify_invoice(message: types.Message, command: CommandObject, state: FSMContext):
    """Handle /verify_invoice command - verify payment for a specific invoice."""
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
            "<b>Invoice Verification</b>\n\n"
            "OCR service not configured.\n"
            "Please set OCR_API_URL and OCR_API_KEY environment variables."
        )
        return

    # Check for invoice ID/number argument
    invoice_ref = command.args.strip() if command.args else None

    if invoice_ref:
        # Try to find invoice by ID or number
        invoice = await invoice_service.get_invoice_by_id(invoice_ref)
        if not invoice:
            invoice = await invoice_service.get_invoice_by_number(invoice_ref)

        if not invoice:
            await message.answer(
                f"<b>Invoice Not Found</b>\n\n"
                f"Could not find invoice: <code>{invoice_ref}</code>\n\n"
                f"Please check the invoice ID or number and try again."
            )
            return

        # Store invoice in state and ask for screenshot
        await state.update_data(invoice=invoice)
        await state.set_state(OCRStates.waiting_for_invoice_screenshot)

        # Format invoice details
        currency = invoice.get("currency", "KHR")
        amount = invoice.get("amount", 0)
        if currency == "KHR":
            amount_str = f"{amount:,.0f} KHR"
        else:
            amount_str = f"${amount:.2f}"

        # Format due date
        due_date = invoice.get('due_date')
        due_date_str = due_date[:10] if due_date else "Not specified"

        await message.answer(
            f"<b>Invoice Payment Verification</b>\n\n"
            f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
            f"Customer: {invoice.get('customer_name', 'N/A')}\n"
            f"Amount: <b>{amount_str}</b>\n"
            f"Bank: {invoice.get('bank') or 'Not specified'}\n"
            f"Account: <code>{invoice.get('expected_account') or 'Not specified'}</code>\n"
            f"Recipient: {invoice.get('recipient_name') or 'Not specified'}\n"
            f"Due Date: {due_date_str}\n\n"
            f"Please send a screenshot of the payment receipt.\n"
            f"Send /cancel to cancel."
        )
    else:
        # No invoice specified, show list of pending invoices
        invoices = await invoice_service.get_invoices(limit=10)

        # Filter to pending verification
        pending = [inv for inv in invoices if inv.get("verification_status") == "pending"]

        if not pending:
            await message.answer(
                "<b>No Pending Invoices</b>\n\n"
                "You don't have any invoices pending verification.\n\n"
                "Usage: <code>/verify_invoice INV-XXXXX</code>"
            )
            return

        # Build invoice list
        invoice_list = []
        for inv in pending[:5]:
            currency = inv.get("currency", "KHR")
            amount = inv.get("amount", 0)
            if currency == "KHR":
                amount_str = f"{amount:,.0f} KHR"
            else:
                amount_str = f"${amount:.2f}"
            invoice_list.append(
                f"- <code>{inv.get('invoice_number')}</code> - {amount_str}"
            )

        await message.answer(
            "<b>Pending Invoices</b>\n\n"
            f"{chr(10).join(invoice_list)}\n\n"
            f"To verify payment, use:\n"
            f"<code>/verify_invoice INV-XXXXX</code>\n\n"
            f"Or reply with an invoice number:"
        )
        await state.set_state(OCRStates.waiting_for_invoice_selection)


@router.message(OCRStates.waiting_for_invoice_selection)
async def handle_invoice_selection(message: types.Message, state: FSMContext):
    """Handle invoice number/ID input for verification."""
    if message.text and message.text.startswith("/"):
        # User sent a command, let it pass through
        await state.clear()
        return

    invoice_ref = message.text.strip() if message.text else ""

    if not invoice_ref:
        await message.answer("Please enter an invoice number or use /cancel to cancel.")
        return

    # Try to find invoice
    invoice = await invoice_service.get_invoice_by_id(invoice_ref)
    if not invoice:
        invoice = await invoice_service.get_invoice_by_number(invoice_ref)

    if not invoice:
        await message.answer(
            f"Could not find invoice: <code>{invoice_ref}</code>\n"
            f"Please try again or use /cancel to cancel."
        )
        return

    # Store invoice and transition to screenshot state
    await state.update_data(invoice=invoice)
    await state.set_state(OCRStates.waiting_for_invoice_screenshot)

    currency = invoice.get("currency", "KHR")
    amount = invoice.get("amount", 0)
    if currency == "KHR":
        amount_str = f"{amount:,.0f} KHR"
    else:
        amount_str = f"${amount:.2f}"

    # Format due date
    due_date = invoice.get('due_date')
    due_date_str = due_date[:10] if due_date else "Not specified"

    await message.answer(
        f"<b>Invoice Found</b>\n\n"
        f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
        f"Amount: <b>{amount_str}</b>\n"
        f"Bank: {invoice.get('bank') or 'Not specified'}\n"
        f"Account: <code>{invoice.get('expected_account') or 'Not specified'}</code>\n"
        f"Recipient: {invoice.get('recipient_name') or 'Not specified'}\n"
        f"Due Date: {due_date_str}\n\n"
        f"Now send me the payment screenshot."
    )


@router.message(Command("cancel"), OCRStates.waiting_for_invoice_screenshot)
@router.message(Command("cancel"), OCRStates.waiting_for_invoice_selection)
async def cmd_cancel_invoice_verify(message: types.Message, state: FSMContext):
    """Cancel the invoice verification operation."""
    await state.clear()
    await message.answer("Invoice verification cancelled.")


@router.message(OCRStates.waiting_for_invoice_screenshot, F.photo)
async def handle_invoice_screenshot(message: types.Message, state: FSMContext):
    """Handle screenshot upload for invoice verification."""
    await message.answer("Verifying payment... Please wait.")

    try:
        # Get stored invoice from state
        data = await state.get_data()
        invoice = data.get("invoice")

        if not invoice:
            await state.clear()
            await message.answer("Session expired. Please start again with /verify_invoice")
            return

        # Get the highest resolution photo
        photo = message.photo[-1]

        # Download the photo
        file = await message.bot.get_file(photo.file_id)
        photo_bytes = await message.bot.download_file(file.file_path)
        image_data = photo_bytes.read()

        # Build expected payment from invoice
        # Note: OCR service expects recipientNames as an ARRAY (plural)
        recipient_name = invoice.get("recipient_name")
        recipient_names = [recipient_name] if recipient_name else []

        expected_payment = {
            "amount": invoice.get("amount"),
            "currency": invoice.get("currency", "KHR"),
            "toAccount": invoice.get("expected_account"),
            "bank": invoice.get("bank"),
            "recipientNames": recipient_names,  # Array format for OCR service
            "dueDate": invoice.get("due_date"),
            "tolerancePercent": 5
        }

        # Debug logging - show what data we're sending to OCR
        logger.info(f"OCR Verification - Invoice ID: {invoice.get('id')}")
        logger.info(f"OCR Verification - Invoice Number: {invoice.get('invoice_number')}")
        logger.info(f"OCR Verification - expected_account: '{invoice.get('expected_account')}'")
        logger.info(f"OCR Verification - recipient_names: {recipient_names}")
        logger.info(f"OCR Verification - Expected Payment: {expected_payment}")

        # Check for missing verification fields and build warnings
        verification_warnings = []
        if not invoice.get("expected_account"):
            verification_warnings.append("Expected Account not set - account verification skipped")
        if not invoice.get("recipient_name"):
            verification_warnings.append("Recipient Name not set - recipient verification skipped")

        # Send to OCR service
        result = await ocr_service.verify_screenshot(
            image_data=image_data,
            filename=f"telegram_{photo.file_id}.jpg",
            invoice_id=invoice.get("id"),
            expected_payment=expected_payment,
            customer_id=invoice.get("customer_id")
        )

        await state.clear()

        if result.get("success") is False:
            await message.answer(
                f"<b>Verification Failed</b>\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Error: {result.get('message', 'Unknown error')}"
            )
            return

        # Extract verification result
        extracted = result.get("extracted_data", {})
        verification = result.get("verification", {})
        confidence = result.get("confidence", 0)

        # Determine verification status
        verification_status = verification.get("status", "pending")
        status_emoji = {
            "verified": "[OK]",
            "rejected": "[X]",
            "pending": "[?]"
        }.get(verification_status, "[?]")

        # Format extracted data
        ext_amount = extracted.get("amount", "N/A")
        ext_currency = extracted.get("currency", "")

        confidence_bar = get_confidence_bar(confidence)

        # Update invoice verification status in database
        if verification_status in ["verified", "rejected"]:
            note = f"OCR Record: {result.get('record_id', 'N/A')}"
            if verification.get("rejectionReason"):
                note += f". Reason: {verification.get('rejectionReason')}"

            await invoice_service.update_invoice_verification(
                invoice_id=invoice.get("id"),
                verification_status=verification_status,
                verified_by="telegram-ocr-bot",
                verification_note=note
            )

        # Check if mock mode
        is_mock = result.get("mock_mode", False)
        mock_note = "\n<i>(Mock Mode - Testing)</i>" if is_mock else ""

        # Build warnings text
        warnings_text = ""
        if verification_warnings:
            warnings_text = "\n<b>Warnings:</b>\n" + "\n".join(f"- {w}" for w in verification_warnings) + "\n"

        # Build response message
        if verification_status == "verified":
            await message.answer(
                f"<b>{status_emoji} Payment Verified</b>{mock_note}\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Expected: {invoice.get('currency', 'KHR')} {invoice.get('amount'):,.0f}\n"
                f"Detected: {ext_currency} {ext_amount}\n\n"
                f"Confidence: {confidence_bar} {confidence:.0%}\n"
                f"{warnings_text}\n"
                f"Invoice marked as <b>PAID</b>"
            )
        elif verification_status == "rejected":
            reason = verification.get("rejectionReason", "Amount or account mismatch")
            await message.answer(
                f"<b>{status_emoji} Payment Rejected</b>{mock_note}\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Expected: {invoice.get('currency', 'KHR')} {invoice.get('amount'):,.0f}\n"
                f"Detected: {ext_currency} {ext_amount}\n\n"
                f"Reason: {reason}\n"
                f"Confidence: {confidence_bar} {confidence:.0%}"
                f"{warnings_text}"
            )
        else:
            await message.answer(
                f"<b>{status_emoji} Manual Review Required</b>{mock_note}\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Detected: {ext_currency} {ext_amount}\n\n"
                f"Confidence: {confidence_bar} {confidence:.0%}\n"
                f"{warnings_text}\n"
                f"The payment could not be automatically verified.\n"
                f"Please review manually in the dashboard."
            )

    except Exception as e:
        logger.error(f"Invoice OCR verification error: {e}")
        await state.clear()
        await message.answer(
            f"<b>Error Processing Screenshot</b>\n\n"
            f"An error occurred while verifying the payment.\n"
            f"Please try again or contact support."
        )


@router.message(OCRStates.waiting_for_invoice_screenshot)
async def handle_invoice_invalid_input(message: types.Message):
    """Handle non-photo messages while waiting for invoice screenshot."""
    await message.answer(
        "Please send a payment screenshot image, or use /cancel to cancel."
    )


def get_confidence_bar(confidence: float) -> str:
    """Generate a visual confidence bar."""
    filled = int(confidence * 10)
    empty = 10 - filled
    return "[" + "#" * filled + "-" * empty + "]"
