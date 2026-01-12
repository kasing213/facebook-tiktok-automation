# api-gateway/src/bot/handlers/client.py
"""Client registration and payment verification handlers."""

import logging
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.services.linking import get_user_by_telegram_id
from src.services.client_linking_service import client_linking_service
from src.services.ocr_service import ocr_service
from src.services.invoice_service import invoice_service

logger = logging.getLogger(__name__)
router = Router()


class ClientStates(StatesGroup):
    """States for client payment verification flow."""
    waiting_for_invoice_selection = State()
    waiting_for_payment_screenshot = State()


# ============================================================================
# Merchant Commands: Client Registration
# ============================================================================

@router.message(Command("register_client"))
async def cmd_register_client(message: types.Message, command: CommandObject):
    """Handle /register_client command - merchant registers a new client."""
    telegram_id = str(message.from_user.id)

    # Check if user is a linked merchant
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard -> Integrations -> Telegram to connect."
        )
        return

    # Get client name from command args
    client_name = command.args.strip() if command.args else None

    if not client_name:
        await message.answer(
            "<b>Register Client</b>\n\n"
            "Usage: <code>/register_client Client Name</code>\n\n"
            "Example: <code>/register_client John Doe</code>\n\n"
            "This will create a registration link for your client."
        )
        return

    tenant_id = user.get("tenant_id")
    merchant_id = user.get("user_id")

    if not tenant_id or not merchant_id:
        await message.answer("Error: Could not determine your account details.")
        return

    # Create customer record
    customer = await client_linking_service.create_customer(
        tenant_id=tenant_id,
        merchant_id=merchant_id,
        name=client_name
    )

    if not customer:
        await message.answer(
            "<b>Error</b>\n\n"
            "Failed to create client record. Please try again."
        )
        return

    # Generate link code
    link_data = await client_linking_service.generate_link_code(
        tenant_id=tenant_id,
        merchant_id=merchant_id,
        customer_id=customer["id"]
    )

    if not link_data:
        await message.answer(
            "<b>Error</b>\n\n"
            "Client created but failed to generate registration link. Please try again."
        )
        return

    await message.answer(
        f"<b>Client Registered Successfully!</b>\n\n"
        f"Name: <b>{client_name}</b>\n"
        f"Status: Pending (waiting for client to connect)\n\n"
        f"<b>Share this link with your client:</b>\n"
        f"<code>{link_data['link']}</code>\n\n"
        f"Once they click it, they'll be able to receive invoices "
        f"and send payment screenshots for verification.\n\n"
        f"<i>Link expires: {link_data.get('expires_at', 'in 7 days')}</i>"
    )


@router.message(Command("my_clients"))
async def cmd_my_clients(message: types.Message):
    """Handle /my_clients command - list merchant's registered clients."""
    telegram_id = str(message.from_user.id)

    # Check if user is a linked merchant
    user = await get_user_by_telegram_id(telegram_id)
    if not user:
        await message.answer(
            "You need to link your Telegram account first.\n"
            "Go to the dashboard -> Integrations -> Telegram to connect."
        )
        return

    tenant_id = user.get("tenant_id")
    merchant_id = user.get("user_id")

    if not tenant_id or not merchant_id:
        await message.answer("Error: Could not determine your account details.")
        return

    clients = await client_linking_service.get_merchant_clients(
        tenant_id=tenant_id,
        merchant_id=merchant_id
    )

    if not clients:
        await message.answer(
            "<b>My Clients</b>\n\n"
            "You haven't registered any clients yet.\n\n"
            "Use <code>/register_client Client Name</code> to register a new client."
        )
        return

    # Build client list
    client_list = []
    for client in clients[:10]:
        status_icon = "[OK]" if client["telegram_linked"] else "[?]"
        client_list.append(
            f"{status_icon} <b>{client['name']}</b>\n"
            f"    Telegram: {'Connected' if client['telegram_linked'] else 'Pending'}"
        )

    await message.answer(
        f"<b>My Clients</b> ({len(clients)} total)\n\n"
        f"{chr(10).join(client_list)}\n\n"
        f"<i>[OK] = Telegram connected, [?] = Pending</i>\n\n"
        f"Use <code>/register_client Name</code> to add more clients."
    )


# ============================================================================
# Client Registration Handler (via deep link)
# ============================================================================

async def handle_client_registration(
    message: types.Message,
    code: str
) -> bool:
    """
    Handle client registration via deep link.

    Args:
        message: Telegram message
        code: The link code (without 'client_' prefix)

    Returns:
        True if handled, False if code not found
    """
    telegram_id = str(message.from_user.id)
    telegram_username = message.from_user.username

    # First resolve the code to show merchant info
    link_data = await client_linking_service.resolve_link_code(code)

    if not link_data:
        return False

    # Consume the code (registers the client)
    result = await client_linking_service.consume_link_code(
        code=code,
        telegram_chat_id=telegram_id,
        telegram_username=telegram_username
    )

    if result.get("success"):
        await message.answer(
            f"<b>Welcome!</b>\n\n"
            f"You've been registered as a client of <b>{result.get('merchant_name', 'your merchant')}</b>.\n\n"
            f"<b>What happens next:</b>\n"
            f"- You'll receive invoice notifications here\n"
            f"- To pay, simply send a screenshot of your payment\n"
            f"- We'll verify it and notify your merchant\n\n"
            f"<i>Client ID: {result.get('customer_name', 'N/A')}</i>"
        )
    else:
        error = result.get("error", "unknown")
        if error == "already_registered":
            await message.answer(
                f"<b>Already Registered</b>\n\n"
                f"{result.get('message', 'This Telegram account is already registered.')}"
            )
        else:
            await message.answer(
                f"<b>Registration Failed</b>\n\n"
                f"{result.get('message', 'Invalid or expired link.')}\n\n"
                f"Please contact your merchant for a new registration link."
            )

    return True


# ============================================================================
# Client Payment Verification Flow
# ============================================================================

@router.message(F.photo)
async def handle_client_photo(message: types.Message, state: FSMContext):
    """Handle photo from any user - check if it's a client sending payment screenshot."""
    telegram_id = str(message.from_user.id)

    # Check if this is a merchant (linked user)
    user = await get_user_by_telegram_id(telegram_id)
    if user:
        # This is a merchant - let other handlers deal with it
        # Check if they're in an OCR state
        current_state = await state.get_state()
        if current_state:
            return  # Let the appropriate state handler deal with it
        return  # Ignore photos from merchants outside of OCR flows

    # Check if this is a registered client
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        # Not a merchant, not a client - ignore
        return

    # This is a registered client - check if they're in payment mode
    current_state = await state.get_state()
    state_data = await state.get_data()

    if current_state == ClientStates.waiting_for_payment_screenshot:
        # They're in payment mode - process the screenshot
        await process_client_payment_screenshot(message, state, customer, state_data)
    else:
        # They sent a photo but not in payment mode - show pending invoices
        await show_pending_invoices_for_payment(message, state, customer)


@router.message()
async def handle_client_message(message: types.Message, state: FSMContext):
    """Handle any message from a client - show pending invoices."""
    telegram_id = str(message.from_user.id)

    # Skip commands
    if message.text and message.text.startswith("/"):
        return

    # Check if this is a merchant
    user = await get_user_by_telegram_id(telegram_id)
    if user:
        return  # Let other handlers deal with merchants

    # Check if this is a registered client
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        return  # Not a registered client

    # Show pending invoices
    await show_pending_invoices_for_payment(message, state, customer)


async def show_pending_invoices_for_payment(
    message: types.Message,
    state: FSMContext,
    customer: dict
):
    """Show pending invoices with inline buttons for selection."""
    invoices = await client_linking_service.get_pending_invoices_for_customer(
        customer_id=customer["id"]
    )

    if not invoices:
        await message.answer(
            f"<b>No Pending Invoices</b>\n\n"
            f"Hi {customer['name']}, you don't have any pending invoices at the moment.\n\n"
            f"You'll receive a notification when a new invoice is created for you."
        )
        return

    if len(invoices) == 1:
        # Only one invoice - auto-select and ask for screenshot
        invoice = invoices[0]
        await state.update_data(selected_invoice=invoice)
        await state.set_state(ClientStates.waiting_for_payment_screenshot)

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
            f"<b>Invoice Payment</b>\n\n"
            f"Invoice: <code>{invoice['invoice_number']}</code>\n"
            f"Amount: <b>{amount_str}</b>\n"
            f"Bank: {invoice.get('bank') or 'Not specified'}\n"
            f"Account: <code>{invoice.get('expected_account') or 'Not specified'}</code>\n"
            f"Recipient: {invoice.get('recipient_name') or 'Not specified'}\n"
            f"Due Date: {due_date_str}\n\n"
            f"Please send a screenshot of your payment.\n\n"
            f"Send /cancel to cancel."
        )
    else:
        # Multiple invoices - show selection
        buttons = []
        for inv in invoices[:5]:  # Limit to 5
            currency = inv.get("currency", "KHR")
            amount = inv.get("amount", 0)
            if currency == "KHR":
                amount_str = f"{amount:,.0f} KHR"
            else:
                amount_str = f"${amount:.2f}"

            buttons.append([
                InlineKeyboardButton(
                    text=f"{inv['invoice_number']} - {amount_str}",
                    callback_data=f"pay_invoice:{inv['id']}"
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await state.set_state(ClientStates.waiting_for_invoice_selection)
        await message.answer(
            f"<b>Select Invoice to Pay</b>\n\n"
            f"Hi {customer['name']}, you have {len(invoices)} pending invoice(s).\n"
            f"Select which one you want to pay:",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("pay_invoice:"))
async def handle_invoice_selection(callback: types.CallbackQuery, state: FSMContext):
    """Handle invoice selection from inline keyboard."""
    await callback.answer()

    invoice_id = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)

    # Get customer
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        await callback.message.edit_text("Session expired. Please try again.")
        return

    # Get invoice details
    invoice = await invoice_service.get_invoice_by_id(invoice_id)
    if not invoice:
        await callback.message.edit_text("Invoice not found. Please try again.")
        return

    # Store invoice in state
    await state.update_data(selected_invoice=invoice)
    await state.set_state(ClientStates.waiting_for_payment_screenshot)

    currency = invoice.get("currency", "KHR")
    amount = invoice.get("amount", 0)
    if currency == "KHR":
        amount_str = f"{amount:,.0f} KHR"
    else:
        amount_str = f"${amount:.2f}"

    # Format due date
    due_date = invoice.get('due_date')
    due_date_str = due_date[:10] if due_date else "Not specified"

    await callback.message.edit_text(
        f"<b>Invoice Payment</b>\n\n"
        f"Invoice: <code>{invoice['invoice_number']}</code>\n"
        f"Amount: <b>{amount_str}</b>\n"
        f"Bank: {invoice.get('bank') or 'Not specified'}\n"
        f"Account: <code>{invoice.get('expected_account') or 'Not specified'}</code>\n"
        f"Recipient: {invoice.get('recipient_name') or 'Not specified'}\n"
        f"Due Date: {due_date_str}\n\n"
        f"Please send a screenshot of your payment.\n\n"
        f"Send /cancel to cancel."
    )


@router.callback_query(F.data.startswith("verify_invoice:"))
async def handle_verify_invoice_button(callback: types.CallbackQuery, state: FSMContext):
    """Handle verify invoice button click from PDF message - prompt for payment screenshot."""
    await callback.answer()

    invoice_id = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)

    # Check if registered client
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        await callback.message.answer(
            "You need to link your account first.\n"
            "Please contact the merchant for a registration link."
        )
        return

    # Get invoice details
    invoice = await invoice_service.get_invoice_by_id(invoice_id)
    if not invoice:
        await callback.message.answer("Invoice not found. Please try again.")
        return

    # Store invoice in state for payment verification
    await state.update_data(selected_invoice=invoice)
    await state.set_state(ClientStates.waiting_for_payment_screenshot)

    # Format amount
    currency = invoice.get("currency", "KHR")
    total = invoice.get("amount", 0)
    if currency == "KHR":
        amount_str = f"{total:,.0f} KHR"
    else:
        amount_str = f"${total:.2f}"

    # Format due date
    due_date = invoice.get('due_date')
    due_date_str = due_date[:10] if due_date else "Not specified"

    # Prompt for screenshot (new message, don't edit the PDF)
    await callback.message.answer(
        f"<b>Payment Verification</b>\n\n"
        f"Invoice: <code>{invoice['invoice_number']}</code>\n"
        f"Amount: <b>{amount_str}</b>\n"
        f"Bank: {invoice.get('bank') or 'Not specified'}\n"
        f"Account: <code>{invoice.get('expected_account') or 'Not specified'}</code>\n"
        f"Recipient: {invoice.get('recipient_name') or 'Not specified'}\n"
        f"Due Date: {due_date_str}\n\n"
        f"Please send a screenshot of your payment receipt.\n\n"
        f"<i>Use /cancel to cancel verification.</i>"
    )


@router.callback_query(F.data.startswith("view_other_invoices:"))
async def handle_view_other_invoices_button(callback: types.CallbackQuery, state: FSMContext):
    """Handle view other invoices button click - show other pending invoices."""
    await callback.answer()

    current_invoice_id = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)

    # Check if registered client
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        await callback.message.answer(
            "You need to link your account first.\n"
            "Please contact the merchant for a registration link."
        )
        return

    # Get all pending invoices
    all_invoices = await client_linking_service.get_pending_invoices_for_customer(
        customer_id=customer["id"]
    )

    # Filter out current invoice
    other_invoices = [inv for inv in all_invoices if str(inv.get("id")) != current_invoice_id]

    # Sort by issue date (oldest first)
    # Use created_at or invoice_date field with fallback
    other_invoices.sort(key=lambda x: x.get("created_at") or x.get("invoice_date") or "")

    if not other_invoices:
        await callback.message.answer(
            "✅ <b>No Other Pending Invoices</b>\n\n"
            "You don't have any other pending invoices at the moment.\n"
            "You're all caught up!",
            parse_mode="HTML"
        )
        return

    if len(other_invoices) == 1:
        # Auto-select single invoice
        invoice = other_invoices[0]
        await state.update_data(selected_invoice=invoice)
        await state.set_state(ClientStates.waiting_for_payment_screenshot)

        currency = invoice.get("currency", "KHR")
        amount = invoice.get("amount", 0)
        if currency == "KHR":
            amount_str = f"{amount:,.0f} KHR"
        else:
            amount_str = f"${amount:.2f}"

        due_date = invoice.get('due_date')
        due_date_str = due_date[:10] if due_date else "Not specified"

        await callback.message.answer(
            f"<b>Payment Verification</b>\n\n"
            f"Invoice: <code>{invoice['invoice_number']}</code>\n"
            f"Amount: <b>{amount_str}</b>\n"
            f"Bank: {invoice.get('bank') or 'Not specified'}\n"
            f"Account: <code>{invoice.get('expected_account') or 'Not specified'}</code>\n"
            f"Recipient: {invoice.get('recipient_name') or 'Not specified'}\n"
            f"Due Date: {due_date_str}\n\n"
            f"Please send a screenshot of your payment receipt.\n\n"
            f"<i>Use /cancel to cancel verification.</i>",
            parse_mode="HTML"
        )
        return

    # Multiple invoices - show selection
    buttons = []
    for inv in other_invoices[:10]:  # Limit to 10
        currency = inv.get("currency", "KHR")
        amount = inv.get("amount", 0)
        if currency == "KHR":
            amount_str = f"{amount:,.0f} KHR"
        else:
            amount_str = f"${amount:.2f}"

        due_date = inv.get('due_date')
        due_date_str = f" - Due: {due_date[:10]}" if due_date else ""

        buttons.append([
            InlineKeyboardButton(
                text=f"{inv['invoice_number']} - {amount_str}{due_date_str}",
                callback_data=f"pay_invoice:{inv['id']}"
            )
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await state.set_state(ClientStates.waiting_for_invoice_selection)
    await callback.message.answer(
        f"<b>Select Invoice to Verify</b>\n\n"
        f"You have {len(other_invoices)} other pending invoice(s).\n"
        f"Select which one you want to verify:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("cancel"), ClientStates.waiting_for_payment_screenshot)
@router.message(Command("cancel"), ClientStates.waiting_for_invoice_selection)
async def cmd_cancel_client_payment(message: types.Message, state: FSMContext):
    """Cancel the client payment flow."""
    await state.clear()
    await message.answer("Payment verification cancelled.")


async def process_client_payment_screenshot(
    message: types.Message,
    state: FSMContext,
    customer: dict,
    state_data: dict
):
    """Process payment screenshot from client."""
    invoice = state_data.get("selected_invoice")

    if not invoice:
        await state.clear()
        await message.answer(
            "Session expired. Please tap on an invoice to start again."
        )
        return

    await message.answer("Processing your payment screenshot... Please wait.")

    try:
        # Get the highest resolution photo
        photo = message.photo[-1]

        # Download the photo
        file = await message.bot.get_file(photo.file_id)
        photo_bytes = await message.bot.download_file(file.file_path)
        image_data = photo_bytes.read()

        # Build expected payment from invoice
        # Transform recipient_name to array format (per CLAUDE.md OCR fix)
        recipient_name = invoice.get("recipient_name")
        recipient_names = [recipient_name] if recipient_name else []

        expected_payment = {
            "amount": invoice.get("amount"),
            "currency": invoice.get("currency", "KHR"),
            "toAccount": invoice.get("expected_account"),
            "bank": invoice.get("bank"),
            "recipientNames": recipient_names,
            "dueDate": invoice.get("due_date"),
            "tolerancePercent": 5
        }

        # Send to OCR service
        result = await ocr_service.verify_screenshot(
            image_data=image_data,
            filename=f"client_{photo.file_id}.jpg",
            invoice_id=invoice.get("id"),
            expected_payment=expected_payment,
            customer_id=customer.get("id")
        )

        await state.clear()

        if result.get("success") is False:
            await message.answer(
                f"<b>Verification Failed</b>\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Error: {result.get('message', 'Unknown error')}\n\n"
                f"Please try again or contact your merchant."
            )
            return

        # Extract verification result
        verification = result.get("verification", {})
        verification_status = verification.get("status", "pending")
        confidence = result.get("confidence", 0)

        # Update invoice status
        if verification_status in ["verified", "rejected"]:
            note = f"OCR Record: {result.get('record_id', 'N/A')}"
            if verification.get("rejectionReason"):
                note += f". Reason: {verification.get('rejectionReason')}"

            await invoice_service.update_invoice_verification(
                invoice_id=invoice.get("id"),
                verification_status=verification_status,
                verified_by="telegram-client-ocr",
                verification_note=note
            )

        # Send response to client
        currency = invoice.get("currency", "KHR")
        amount = invoice.get("amount", 0)
        if currency == "KHR":
            amount_str = f"{amount:,.0f} KHR"
        else:
            amount_str = f"${amount:.2f}"

        confidence_bar = get_confidence_bar(confidence)

        # Check if mock mode
        is_mock = result.get("mock_mode", False)
        mock_note = "\n<i>(Mock Mode - Testing)</i>" if is_mock else ""

        if verification_status == "verified":
            await message.answer(
                f"<b>[OK] Payment Verified!</b>{mock_note}\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Amount: {amount_str}\n"
                f"Status: <b>PAID</b>\n\n"
                f"Confidence: {confidence_bar} {confidence:.0%}\n\n"
                f"Your merchant has been notified. Thank you!"
            )
            # Notify merchant
            await notify_merchant_payment(customer, invoice, "verified")

        elif verification_status == "rejected":
            reason = verification.get("rejectionReason", "Amount or account mismatch")
            await message.answer(
                f"<b>[X] Payment Rejected</b>{mock_note}\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Expected: {amount_str}\n\n"
                f"Reason: {reason}\n"
                f"Confidence: {confidence_bar} {confidence:.0%}\n\n"
                f"Please check your payment and try again."
            )
            # Notify merchant
            await notify_merchant_payment(customer, invoice, "rejected", reason)

        else:  # pending
            await message.answer(
                f"<b>[?] Manual Review Required</b>{mock_note}\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Amount: {amount_str}\n\n"
                f"Confidence: {confidence_bar} {confidence:.0%}\n\n"
                f"Your payment screenshot needs manual review.\n"
                f"Your merchant will verify it shortly."
            )
            # Notify merchant
            await notify_merchant_payment(customer, invoice, "pending")

    except Exception as e:
        logger.error(f"Client payment verification error: {e}")
        await state.clear()
        await message.answer(
            "<b>Error Processing Screenshot</b>\n\n"
            "An error occurred while verifying your payment.\n"
            "Please try again or contact your merchant."
        )


async def notify_merchant_payment(
    customer: dict,
    invoice: dict,
    status: str,
    reason: str = None
):
    """Notify merchant about client payment verification."""
    try:
        # Get merchant's telegram info
        merchant_id = customer.get("merchant_id")
        if not merchant_id:
            return

        # Look up merchant's telegram chat ID
        from src.db.postgres import get_db_session
        from sqlalchemy import text

        with get_db_session() as db:
            result = db.execute(
                text("""
                    SELECT telegram_user_id FROM public.user
                    WHERE id = :merchant_id AND telegram_user_id IS NOT NULL
                """),
                {"merchant_id": merchant_id}
            )
            row = result.fetchone()

            if not row or not row.telegram_user_id:
                return

            merchant_chat_id = row.telegram_user_id

        # Import bot to send message
        from src.bot import create_bot
        bot, _ = create_bot()

        if not bot:
            return

        currency = invoice.get("currency", "KHR")
        amount = invoice.get("amount", 0)
        if currency == "KHR":
            amount_str = f"{amount:,.0f} KHR"
        else:
            amount_str = f"${amount:.2f}"

        if status == "verified":
            status_text = "[OK] VERIFIED"
        elif status == "rejected":
            status_text = "[X] REJECTED"
        else:
            status_text = "[?] PENDING REVIEW"

        message_text = (
            f"<b>[Payment Notification]</b>\n\n"
            f"Client: <b>{customer.get('name', 'Unknown')}</b>\n"
            f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
            f"Amount: {amount_str}\n\n"
            f"Status: <b>{status_text}</b>"
        )

        if reason:
            message_text += f"\nReason: {reason}"

        await bot.send_message(chat_id=merchant_chat_id, text=message_text)

    except Exception as e:
        logger.error(f"Error notifying merchant: {e}")


def get_confidence_bar(confidence: float) -> str:
    """Generate a visual confidence bar."""
    filled = int(confidence * 10)
    empty = 10 - filled
    return "[" + "#" * filled + "-" * empty + "]"
