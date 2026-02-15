# api-gateway/src/bot/handlers/client.py
"""Client registration and payment verification handlers."""

import logging
from datetime import datetime, timezone
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.services.linking import get_user_by_telegram_id
from src.services.client_linking_service import client_linking_service
from src.services.ocr_service import ocr_service
from src.services.invoice_service import invoice_service
from src.bot.utils.permissions import require_member_or_owner, require_owner

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
    """Handle /register_client command - merchant registers a new client (OWNER ONLY)."""
    telegram_id = str(message.from_user.id)

    # OWNER ONLY - Only tenant owners can register new clients
    user = await get_user_by_telegram_id(telegram_id)
    if not await require_owner(user, message):
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

    # Check if user is a linked merchant (member or owner)
    user = await get_user_by_telegram_id(telegram_id)
    if not await require_member_or_owner(user, message):
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
# Batch Registration Handler (via deep link - multiple clients can use)
# ============================================================================

async def handle_batch_registration(
    message: types.Message,
    code: str
) -> bool:
    """
    Handle batch registration via deep link.

    This allows multiple clients to register via a single QR code.
    Each client gets an auto-generated ID like "Client-00001".

    Args:
        message: Telegram message
        code: The batch code (without 'batch_' prefix)

    Returns:
        True if handled, False if code not found
    """
    telegram_id = str(message.from_user.id)
    telegram_username = message.from_user.username

    # Consume the batch code (creates new customer with auto-generated ID)
    result = await client_linking_service.consume_batch_code(
        code=code,
        telegram_chat_id=telegram_id,
        telegram_username=telegram_username
    )

    if result.get("success"):
        customer = result.get("customer", {})
        await message.answer(
            f"<b>Welcome!</b>\n\n"
            f"You've been registered as a client of <b>{result.get('merchant_name', 'your merchant')}</b>.\n\n"
            f"<b>Your Client ID:</b> <code>{result.get('customer_name', customer.get('name', 'N/A'))}</code>\n\n"
            f"<b>What happens next:</b>\n"
            f"- You'll receive invoice notifications here\n"
            f"- To pay, simply send a screenshot of your payment\n"
            f"- We'll verify it and notify your merchant\n\n"
            f"<i>Keep this ID for your records!</i>"
        )
        return True

    error = result.get("error", "unknown")

    if error == "already_registered":
        await message.answer(
            f"<b>Already Registered</b>\n\n"
            f"You're already registered as <b>{result.get('customer_name', 'a client')}</b>.\n\n"
            f"You can send a payment screenshot anytime to verify."
        )
        return True

    if error == "max_uses_reached":
        await message.answer(
            "<b>Registration Closed</b>\n\n"
            "This registration link has reached its maximum capacity.\n"
            "Please contact the merchant for a new link."
        )
        return True

    if error == "invalid_code":
        # Return False to let caller show generic error
        return False

    # Other errors
    await message.answer(
        f"<b>Registration Failed</b>\n\n"
        f"{result.get('message', 'An error occurred.')}\n\n"
        f"Please try again or contact the merchant."
    )
    return True


# ============================================================================
# Ads Alert Subscription Commands (for customers)
# ============================================================================

@router.message(Command("subscribe_ads"))
async def cmd_subscribe_ads(message: types.Message):
    """Handle /subscribe_ads command - customer subscribes to promotional broadcasts."""
    telegram_id = str(message.from_user.id)

    # Check if registered customer
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        await message.answer(
            "You need to register first before managing ads preferences.\n"
            "Please contact your merchant for a registration link."
        )
        return

    # Check current subscription status
    status = await client_linking_service.get_ads_alert_subscription_status(telegram_id)

    if not status:
        # Not registered in ads_alert yet - this shouldn't happen with auto-registration
        # but handle it gracefully by trying to register them
        ads_result = await client_linking_service.register_customer_in_ads_alert(
            tenant_id=customer.get("tenant_id"),
            customer_id=customer.get("id"),
            telegram_chat_id=telegram_id,
            customer_name=customer.get("name")
        )
        if ads_result:
            await message.answer(
                "<b>Subscribed!</b>\n\n"
                "You are now subscribed to promotional messages from your merchant.\n"
                "Use /unsubscribe_ads to stop receiving promotions."
            )
        else:
            await message.answer(
                "Sorry, there was an error subscribing. Please try again later."
            )
        return

    if status.get("subscribed"):
        await message.answer(
            "<b>Already Subscribed</b>\n\n"
            "You're already subscribed to promotional messages.\n"
            "Use /unsubscribe_ads if you want to stop receiving promotions."
        )
        return

    # Subscribe the customer
    success = await client_linking_service.update_ads_alert_subscription(telegram_id, subscribed=True)

    if success:
        await message.answer(
            "<b>Subscribed!</b>\n\n"
            "You will now receive promotional messages from your merchant.\n"
            "Use /unsubscribe_ads to stop receiving promotions."
        )
    else:
        await message.answer(
            "Sorry, there was an error subscribing. Please try again later."
        )


@router.message(Command("unsubscribe_ads"))
async def cmd_unsubscribe_ads(message: types.Message):
    """Handle /unsubscribe_ads command - customer unsubscribes from promotional broadcasts."""
    telegram_id = str(message.from_user.id)

    # Check if registered customer
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        await message.answer(
            "You need to register first before managing ads preferences.\n"
            "Please contact your merchant for a registration link."
        )
        return

    # Check current subscription status
    status = await client_linking_service.get_ads_alert_subscription_status(telegram_id)

    if not status:
        await message.answer(
            "You are not registered for promotional messages.\n"
            "There's nothing to unsubscribe from."
        )
        return

    if not status.get("subscribed"):
        await message.answer(
            "<b>Already Unsubscribed</b>\n\n"
            "You're not receiving promotional messages.\n"
            "Use /subscribe_ads if you want to receive promotions again."
        )
        return

    # Unsubscribe the customer
    success = await client_linking_service.update_ads_alert_subscription(telegram_id, subscribed=False)

    if success:
        await message.answer(
            "<b>Unsubscribed</b>\n\n"
            "You will no longer receive promotional messages from your merchant.\n"
            "You will still receive invoice notifications.\n\n"
            "Use /subscribe_ads to start receiving promotions again."
        )
    else:
        await message.answer(
            "Sorry, there was an error unsubscribing. Please try again later."
        )


@router.message(Command("ads_status"))
async def cmd_ads_status(message: types.Message):
    """Handle /ads_status command - check promotional message subscription status."""
    telegram_id = str(message.from_user.id)

    # Check if registered customer
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        await message.answer(
            "You need to register first to check ads status.\n"
            "Please contact your merchant for a registration link."
        )
        return

    # Get subscription status
    status = await client_linking_service.get_ads_alert_subscription_status(telegram_id)

    if not status:
        await message.answer(
            "<b>Ads Subscription Status</b>\n\n"
            "Status: <b>Not Registered</b>\n\n"
            "You are not registered for promotional messages.\n"
            "Use /subscribe_ads to start receiving promotions."
        )
        return

    subscribed = status.get("subscribed", False)
    status_text = "Subscribed" if subscribed else "Unsubscribed"
    status_icon = "[OK]" if subscribed else "[X]"

    await message.answer(
        f"<b>Ads Subscription Status</b>\n\n"
        f"Status: {status_icon} <b>{status_text}</b>\n\n"
        f"{'You will receive promotional messages from your merchant.' if subscribed else 'You will NOT receive promotional messages.'}\n\n"
        f"{'Use /unsubscribe_ads to stop' if subscribed else 'Use /subscribe_ads to start'} receiving promotions."
    )


# ============================================================================
# Client Payment Verification Flow
# ============================================================================

@router.message(F.photo)
async def handle_client_photo(message: types.Message, state: FSMContext):
    """Handle photo from any user - check if it's a client sending payment screenshot."""
    telegram_id = str(message.from_user.id)
    logger.info(f"📸 Photo received from {telegram_id}")

    try:
        # Check FSM state FIRST - most specific indicator of user intent
        current_state = await state.get_state()
        state_data = await state.get_data()

        # CLIENT PAYMENT FLOW - highest priority (state-based)
        if current_state == ClientStates.waiting_for_payment_screenshot:
            logger.info(f"User {telegram_id} in client payment state, checking customer registration...")

            # Verify customer registration (merchant can also be customer)
            customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
            if customer:
                logger.info(f"Processing payment screenshot for customer {customer.get('id')}")
                await process_client_payment_screenshot(message, state, customer, state_data)
                return
            else:
                logger.warning(f"User {telegram_id} in payment state but not registered as customer")
                await state.clear()
                await message.answer(
                    "Session expired or invalid. Please request a new invoice link from your merchant."
                )
                return

        # MERCHANT OCR FLOW - second priority (for other states)
        user = await get_user_by_telegram_id(telegram_id)
        if user:
            logger.info(f"User {telegram_id} is a merchant")
            # If merchant has OTHER states (OCRStates.*), let those handlers process
            if current_state:
                logger.info(f"Merchant {telegram_id} in state {current_state}, delegating to state handler")
                return  # Let OCR handlers deal with it
            logger.info(f"Merchant {telegram_id} not in any state, ignoring photo")
            return  # Ignore photos from merchants outside flows

        # UNREGISTERED CLIENT - show pending invoices
        customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
        if not customer:
            logger.info(f"User {telegram_id} is neither merchant nor customer, ignoring photo")
            return

        logger.info(f"✅ User {telegram_id} is registered customer, showing pending invoices")
        await show_pending_invoices_for_payment(message, state, customer)

    except Exception as e:
        logger.error(f"❌ Error handling photo from {telegram_id}: {e}", exc_info=True)
        await message.answer(
            "Sorry, there was an error processing your photo. Please try again or contact support."
        )


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
    # SECURITY: Pass tenant_id to ensure tenant isolation
    invoices = await client_linking_service.get_pending_invoices_for_customer(
        customer_id=customer["id"],
        tenant_id=customer["tenant_id"]
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

    # SECURITY: Get invoice with tenant validation
    invoice = await invoice_service.get_invoice_by_id(invoice_id, customer.get("tenant_id"))
    if not invoice or str(invoice.get("tenant_id")) != str(customer.get("tenant_id")):
        await callback.message.edit_text("Invoice not found or access denied.")
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

    # SECURITY: Get invoice with tenant validation
    invoice = await invoice_service.get_invoice_by_id(invoice_id, customer.get("tenant_id"))
    if not invoice or str(invoice.get("tenant_id")) != str(customer.get("tenant_id")):
        await callback.message.answer("Invoice not found or access denied.")
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

    # SECURITY: Get all pending invoices with tenant isolation
    all_invoices = await client_linking_service.get_pending_invoices_for_customer(
        customer_id=customer["id"],
        tenant_id=customer["tenant_id"]
    )

    # Filter out current invoice
    other_invoices = [inv for inv in all_invoices if str(inv.get("id")) != current_invoice_id]

    # Sort by issue date (oldest first)
    # Use created_at or invoice_date field with fallback
    other_invoices.sort(key=lambda x: x.get("created_at") or x.get("invoice_date") or "")

    if not other_invoices:
        await callback.answer(
            "✅ No other pending invoices. You're all caught up!",
            show_alert=True
        )
        return

    # Show invoice selection (works for 1 or more invoices)
    # Build selection buttons
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

    # Add a "Back" button to return to original view
    buttons.append([
        InlineKeyboardButton(
            text="⬅️ Back",
            callback_data=f"back_to_invoice:{current_invoice_id}"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await state.set_state(ClientStates.waiting_for_invoice_selection)

    # Edit the existing message's buttons inline (doesn't push content down)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception as e:
        logger.warning(f"Could not edit inline buttons, sending new message: {e}")
        # Fallback: send new message if edit fails
        await callback.message.answer(
            f"<b>Select Invoice to Verify</b>\n\n"
            f"You have {len(other_invoices)} other pending invoice(s).\n"
            f"Select which one you want to verify:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("back_to_invoice:"))
async def handle_back_to_invoice_button(callback: types.CallbackQuery, state: FSMContext):
    """Handle back button - restore original invoice buttons."""
    await callback.answer()

    invoice_id = callback.data.split(":")[1]
    telegram_id = str(callback.from_user.id)

    # SECURITY: Get customer first for tenant context
    customer = await client_linking_service.get_customer_by_chat_id(telegram_id)
    if not customer:
        await callback.answer("Session expired", show_alert=True)
        return

    # SECURITY: Get invoice with tenant validation
    invoice = await invoice_service.get_invoice_by_id(invoice_id, customer.get("tenant_id"))
    if not invoice or str(invoice.get("tenant_id")) != str(customer.get("tenant_id")):
        await callback.answer("Invoice not found", show_alert=True)
        return

    # Restore original buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"✅ Verify {invoice['invoice_number']}",
                callback_data=f"verify_invoice:{invoice_id}"
            ),
            InlineKeyboardButton(
                text="📋 Other Invoices",
                callback_data=f"view_other_invoices:{invoice_id}"
            )
        ]
    ])

    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=keyboard)


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
    logger.info(f"🔄 Starting payment screenshot processing for customer {customer.get('id')}")

    invoice = state_data.get("selected_invoice")

    if not invoice:
        logger.warning(f"❌ No selected_invoice in state for customer {customer.get('id')}")
        await state.clear()
        await message.answer(
            "Session expired. Please tap on an invoice to start again."
        )
        return

    logger.info(f"📄 Processing screenshot for invoice {invoice.get('invoice_number')} ({invoice.get('id')})")
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

        # Save screenshot to MongoDB GridFS (NEW FEATURE)
        logger.info(f"💾 Saving screenshot to GridFS: invoice_id={invoice.get('id')}, customer_id={customer.get('id')}")

        from src.services.payment_screenshot_service import PaymentScreenshotService
        screenshot_service = PaymentScreenshotService()

        try:
            screenshot = await screenshot_service.save_screenshot(
                image_data=image_data,
                invoice_id=invoice.get("id"),
                customer_id=customer.get("id"),
                tenant_id=customer.get("merchant_id"),
                filename=f"payment_{photo.file_id}.jpg"
            )
            logger.info(f"✅ Screenshot saved: {screenshot['id']} -> GridFS: {screenshot['gridfs_file_id']}")
        except Exception as e:
            logger.error(f"❌ Failed to save screenshot: {e}")
            # Continue processing even if screenshot save fails
            screenshot = None

        logger.info(f"📤 Sending to Smart OCR service: invoice_id={invoice.get('id')}, customer_id={customer.get('id')}, amount={expected_payment['amount']}")

        # Import smart OCR service
        from src.services.smart_ocr_service import smart_ocr

        # Send to Smart OCR service (with auto-learning)
        result = await smart_ocr.verify_screenshot_smart(
            image_data=image_data,
            filename=f"client_{photo.file_id}.jpg",
            invoice_id=invoice.get("id"),
            expected_payment=expected_payment,
            customer_id=customer.get("id"),
            tenant_id=customer.get("merchant_id"),  # For merchant-specific learning
            use_learning=True
        )

        logger.info(f"📥 OCR service response: success={result.get('success')}, status={result.get('verification', {}).get('status')}")

        # Update screenshot record with OCR results (if screenshot was saved)
        if screenshot and result.get("success"):
            try:
                verification = result.get("verification", {})
                verification_status = verification.get("status", "pending")
                confidence = result.get("confidence", 0)

                await screenshot_service.update_ocr_results(
                    screenshot_id=screenshot['id'],
                    confidence=confidence,
                    status=verification_status,
                    ocr_data=result.get("extracted_data", {})
                )
                logger.info(f"✅ Updated screenshot OCR results: {screenshot['id']}")
            except Exception as e:
                logger.error(f"❌ Failed to update screenshot OCR results: {e}")

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
                tenant_id=invoice.get("tenant_id"),  # SECURITY: Pass tenant_id for tenant isolation
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
            await notify_merchant_payment(customer, invoice, "verified", screenshot_id=screenshot['id'] if screenshot else None)

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
            await notify_merchant_payment(customer, invoice, "rejected", reason, screenshot_id=screenshot['id'] if screenshot else None)

        else:  # pending
            await message.answer(
                f"<b>[?] Manual Review Required</b>{mock_note}\n\n"
                f"Invoice: <code>{invoice.get('invoice_number')}</code>\n"
                f"Amount: {amount_str}\n\n"
                f"Confidence: {confidence_bar} {confidence:.0%}\n\n"
                f"Your payment screenshot needs manual review.\n"
                f"Your merchant will verify it shortly."
            )
            # Notify merchant (MOST IMPORTANT: Include screenshot for manual review)
            await notify_merchant_payment(customer, invoice, "pending",
                                         screenshot_id=screenshot['id'] if screenshot else None,
                                         confidence=confidence,
                                         ocr_data=result.get("extracted_data", {}))

    except Exception as e:
        logger.error(f"❌ Client payment verification error: {e}", exc_info=True)
        await state.clear()
        await message.answer(
            f"<b>Error Processing Screenshot</b>\n\n"
            f"An error occurred while verifying your payment.\n\n"
            f"Error details: {type(e).__name__}: {str(e)}\n\n"
            f"Please try again or contact your merchant.",
            parse_mode="HTML"
        )


async def notify_merchant_payment(
    customer: dict,
    invoice: dict,
    status: str,
    reason: str = None,
    screenshot_id: str = None,
    confidence: float = None,
    ocr_data: dict = None
):
    """
    Enhanced merchant notification with screenshot viewing and manual verification.

    This function creates rich notifications for merchants including:
    - Screenshot viewing buttons
    - OCR confidence and extracted data
    - Manual verification action buttons (for pending status)
    - Visual confidence indicators
    """
    try:
        # Get merchant's telegram info
        merchant_id = customer.get("merchant_id")
        if not merchant_id:
            logger.warning("No merchant_id found in customer data")
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
                logger.warning(f"No Telegram chat ID found for merchant: {merchant_id}")
                return

            merchant_chat_id = row.telegram_user_id

        # Import bot to send message
        from src.bot import create_bot
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        bot, _ = create_bot()
        if not bot:
            logger.error("Bot not available for merchant notification")
            return

        # Format amount
        currency = invoice.get("currency", "KHR")
        amount = invoice.get("amount", 0)
        if currency == "KHR":
            amount_str = f"{amount:,.0f} KHR"
        else:
            amount_str = f"${amount:.2f}"

        # Build base message
        message_text = (
            f"<b>💳 Payment Notification</b>\n\n"
            f"👤 Client: <b>{customer.get('name', 'Unknown')}</b>\n"
            f"📄 Invoice: <code>{invoice.get('invoice_number')}</code>\n"
            f"💰 Amount: <b>{amount_str}</b>\n\n"
        )

        # Create inline keyboard for actions
        keyboard_buttons = []

        if status == "verified":
            message_text += f"Status: <b>✅ VERIFIED</b>\n"
            if confidence is not None:
                confidence_bar = get_confidence_bar(confidence)
                message_text += f"OCR Confidence: {confidence_bar} {confidence:.0%}\n"

        elif status == "rejected":
            message_text += f"Status: <b>❌ REJECTED</b>\n"
            if reason:
                message_text += f"Reason: {reason}\n"
            if confidence is not None:
                confidence_bar = get_confidence_bar(confidence)
                message_text += f"OCR Confidence: {confidence_bar} {confidence:.0%}\n"

        else:  # pending - MOST IMPORTANT CASE
            message_text += f"Status: <b>⏳ REQUIRES MANUAL REVIEW</b>\n"

            if confidence is not None:
                confidence_bar = get_confidence_bar(confidence)
                message_text += f"OCR Confidence: {confidence_bar} {confidence:.0%}\n\n"

                # Add OCR findings comparison
                if ocr_data and isinstance(ocr_data, dict):
                    message_text += format_ocr_findings(ocr_data, invoice)

                message_text += f"\n<i>Low confidence requires your review.</i>\n"

            # Add action buttons for manual verification
            button_row_1 = []
            button_row_2 = []

            # Screenshot viewing button (if available)
            if screenshot_id:
                button_row_1.append(
                    InlineKeyboardButton(
                        text="👁 View Screenshot",
                        callback_data=f"view_screenshot:{screenshot_id}"
                    )
                )

            # Manual verification buttons
            button_row_2.extend([
                InlineKeyboardButton(
                    text="✅ Verify Payment",
                    callback_data=f"manual_verify:{invoice.get('id')}:{screenshot_id or 'none'}"
                ),
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=f"manual_reject:{invoice.get('id')}:{screenshot_id or 'none'}"
                )
            ])

            # Add buttons to keyboard
            if button_row_1:
                keyboard_buttons.append(button_row_1)
            if button_row_2:
                keyboard_buttons.append(button_row_2)

        # Add screenshot viewing button for all statuses (if available)
        if screenshot_id and status != "pending":
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text="👁 View Screenshot",
                    callback_data=f"view_screenshot:{screenshot_id}"
                )
            ])

        # Send message with or without keyboard
        if keyboard_buttons:
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            await bot.send_message(
                chat_id=merchant_chat_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await bot.send_message(
                chat_id=merchant_chat_id,
                text=message_text,
                parse_mode="HTML"
            )

        logger.info(f"✅ Merchant notification sent: {merchant_chat_id} -> {status} (screenshot: {screenshot_id})")

    except Exception as e:
        logger.error(f"Error notifying merchant: {e}")


def get_confidence_bar(confidence: float) -> str:
    """Generate a visual confidence bar."""
    filled = int(confidence * 10)
    empty = 10 - filled
    return "[" + "#" * filled + "-" * empty + "]"


def format_ocr_findings(ocr_data: dict, expected_invoice: dict) -> str:
    """
    Format OCR findings for merchant review in notification.

    Compares extracted data with expected invoice data and shows:
    - What OCR found vs what was expected
    - Visual indicators for matches/mismatches
    - Sanitized account information (masked for security)
    """
    try:
        findings = "<b>🔍 OCR Analysis:</b>\n"

        # Amount comparison
        expected_amount = expected_invoice.get("amount", 0)
        found_amount = ocr_data.get("amount")

        if found_amount is not None:
            try:
                found_amount_num = float(found_amount)
                tolerance = expected_amount * 0.05  # 5% tolerance
                if abs(found_amount_num - expected_amount) <= tolerance:
                    status = "✅"
                else:
                    status = "⚠️"
                findings += f"• Amount: {found_amount} {status}\n"
            except (ValueError, TypeError):
                findings += f"• Amount: {found_amount} ❓\n"
        else:
            findings += f"• Amount: Not detected ❌\n"

        # Currency
        expected_currency = expected_invoice.get("currency", "KHR")
        found_currency = ocr_data.get("currency")
        if found_currency:
            status = "✅" if found_currency.upper() == expected_currency.upper() else "⚠️"
            findings += f"• Currency: {found_currency} {status}\n"

        # Bank comparison
        expected_bank = expected_invoice.get("bank", "").upper()
        found_bank = ocr_data.get("bank")
        if found_bank:
            found_bank_upper = found_bank.upper()
            if expected_bank and expected_bank in found_bank_upper:
                status = "✅"
            elif found_bank_upper in ["ABA", "ACLEDA", "WING", "CANADIA"]:
                status = "⚠️"
            else:
                status = "❓"
            findings += f"• Bank: {found_bank} {status}\n"

        # Date (if available)
        found_date = ocr_data.get("date")
        if found_date:
            findings += f"• Date: {found_date} 📅\n"

        # Account information (masked for security)
        found_account = ocr_data.get("account") or ocr_data.get("account_masked")
        if found_account:
            # Ensure account is masked
            if len(str(found_account)) > 4 and "***" not in str(found_account):
                masked_account = "***" + str(found_account)[-4:]
            else:
                masked_account = str(found_account)
            findings += f"• Account: {masked_account} 🏦\n"

        # Recipient name check
        expected_recipients = expected_invoice.get("recipientNames", [])
        found_recipient = ocr_data.get("recipient") or ocr_data.get("recipient_name")
        if found_recipient and expected_recipients:
            # Check if any expected recipient is in the found recipient (partial match)
            match_found = any(
                expected.upper() in found_recipient.upper()
                for expected in expected_recipients
                if expected
            )
            status = "✅" if match_found else "⚠️"
            findings += f"• Recipient: {found_recipient} {status}\n"

        findings += f"\n<b>Legend:</b> ✅ Match  ⚠️ Differs  ❓ Unclear  ❌ Missing\n"

        return findings

    except Exception as e:
        logger.error(f"Error formatting OCR findings: {e}")
        return "<b>🔍 OCR Analysis:</b>\nError formatting findings\n"


# ============================================================================
# Screenshot Viewing and Manual Verification Callback Handlers
# ============================================================================

@router.callback_query(F.data.startswith("view_screenshot:"))
async def handle_view_screenshot(callback: types.CallbackQuery):
    """Handle screenshot viewing request from merchant."""
    await callback.answer()

    try:
        screenshot_id = callback.data.split(":")[1]
        merchant_telegram_id = str(callback.from_user.id)

        logger.info(f"📸 Screenshot view request: {screenshot_id} by merchant {merchant_telegram_id}")

        # Get merchant info to validate permission
        from src.bot.services.linking import get_user_by_telegram_id
        merchant_user = await get_user_by_telegram_id(merchant_telegram_id)

        if not merchant_user:
            await callback.message.answer("❌ Access denied - merchant not linked")
            return

        merchant_tenant_id = merchant_user.get("tenant_id")

        # Get screenshot from service
        from src.services.payment_screenshot_service import PaymentScreenshotService
        screenshot_service = PaymentScreenshotService()

        screenshot_data = await screenshot_service.get_screenshot_image_data(
            screenshot_id=screenshot_id,
            tenant_id=merchant_tenant_id
        )

        if not screenshot_data:
            await callback.message.answer("❌ Screenshot not found or access denied")
            return

        image_bytes, content_type, filename = screenshot_data

        # Get screenshot metadata for context
        screenshot_meta = await screenshot_service.get_screenshot_by_id(
            screenshot_id=screenshot_id,
            tenant_id=merchant_tenant_id
        )

        # Build caption with invoice context
        caption = f"📸 <b>Payment Screenshot</b>\n\n"
        if screenshot_meta and screenshot_meta.get('metadata'):
            meta = screenshot_meta['metadata']
            invoice_id = meta.get('invoice_id', 'Unknown')
            customer_id = meta.get('customer_id', 'Unknown')
            ocr_confidence = meta.get('ocr_confidence')

            caption += f"📄 Invoice: {invoice_id[:12]}...\n"
            caption += f"👤 Customer: {customer_id[:12]}...\n"

            if ocr_confidence is not None:
                confidence_bar = get_confidence_bar(ocr_confidence)
                caption += f"🤖 OCR Confidence: {confidence_bar} {ocr_confidence:.0%}\n"

            caption += f"📅 Uploaded: {screenshot_meta.get('created_at', 'Unknown')[:10]}\n"

        caption += f"\n<i>Use buttons below to verify or reject this payment.</i>"

        # Send screenshot as photo with context
        from io import BytesIO
        photo = BytesIO(image_bytes)
        photo.name = filename

        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML"
        )

        logger.info(f"✅ Screenshot sent to merchant: {screenshot_id}")

    except Exception as e:
        logger.error(f"❌ Error viewing screenshot: {e}", exc_info=True)
        await callback.message.answer("❌ Error retrieving screenshot")


@router.callback_query(F.data.startswith("manual_verify:"))
async def handle_manual_verify(callback: types.CallbackQuery):
    """Handle manual payment verification approval by merchant."""
    await callback.answer()

    try:
        parts = callback.data.split(":")
        if len(parts) < 3:
            await callback.answer("❌ Invalid verification request", show_alert=True)
            return

        invoice_id = parts[1]
        screenshot_id = parts[2] if parts[2] != "none" else None
        merchant_telegram_id = str(callback.from_user.id)

        logger.info(f"✅ Manual verify request: invoice={invoice_id}, screenshot={screenshot_id}, merchant={merchant_telegram_id}")

        # Get merchant info
        from src.bot.services.linking import get_user_by_telegram_id
        merchant_user = await get_user_by_telegram_id(merchant_telegram_id)

        if not merchant_user:
            await callback.answer("❌ Access denied", show_alert=True)
            return

        merchant_id = merchant_user.get("user_id")
        merchant_tenant_id = merchant_user.get("tenant_id")

        # Verify merchant has permission for this invoice
        if not await verify_merchant_permission(merchant_telegram_id, invoice_id):
            await callback.answer("❌ Access denied - not your invoice", show_alert=True)
            return

        # Update invoice verification status
        from src.services.invoice_service import invoice_service

        success = await invoice_service.update_invoice_verification(
            invoice_id=invoice_id,
            verification_status="verified",
            tenant_id=merchant_tenant_id,
            verified_by=f"telegram-manual-{merchant_id}",
            verification_note=f"Manually verified via Telegram by merchant. Screenshot: {screenshot_id or 'N/A'}"
        )

        if not success:
            await callback.answer("❌ Failed to update invoice", show_alert=True)
            return

        # Mark screenshot as verified (if available)
        if screenshot_id:
            from src.services.payment_screenshot_service import PaymentScreenshotService
            screenshot_service = PaymentScreenshotService()

            await screenshot_service.mark_as_verified(
                screenshot_id=screenshot_id,
                verified_by=merchant_id,
                verification_method="manual_telegram"
            )

        # Update message to show verification completed
        updated_text = callback.message.text + "\n\n✅ <b>MANUALLY VERIFIED BY MERCHANT</b>"
        await callback.message.edit_text(
            text=updated_text,
            reply_markup=None,  # Remove buttons
            parse_mode="HTML"
        )

        # Notify customer of verification
        await notify_customer_verification_result(
            invoice_id=invoice_id,
            status="verified",
            method="manual",
            tenant_id=merchant_tenant_id
        )

        # Trigger stock deduction if configured
        await handle_stock_deduction(invoice_id, merchant_tenant_id)

        logger.info(f"✅ Manual verification completed: invoice={invoice_id} by merchant={merchant_id}")

    except Exception as e:
        logger.error(f"❌ Error in manual verify: {e}", exc_info=True)
        await callback.answer("❌ Error occurred", show_alert=True)


@router.callback_query(F.data.startswith("manual_reject:"))
async def handle_manual_reject(callback: types.CallbackQuery):
    """Handle manual payment verification rejection by merchant."""
    await callback.answer()

    try:
        parts = callback.data.split(":")
        if len(parts) < 3:
            await callback.answer("❌ Invalid rejection request", show_alert=True)
            return

        invoice_id = parts[1]
        screenshot_id = parts[2] if parts[2] != "none" else None
        merchant_telegram_id = str(callback.from_user.id)

        logger.info(f"❌ Manual reject request: invoice={invoice_id}, screenshot={screenshot_id}, merchant={merchant_telegram_id}")

        # Get merchant info
        from src.bot.services.linking import get_user_by_telegram_id
        merchant_user = await get_user_by_telegram_id(merchant_telegram_id)

        if not merchant_user:
            await callback.answer("❌ Access denied", show_alert=True)
            return

        merchant_id = merchant_user.get("user_id")
        merchant_tenant_id = merchant_user.get("tenant_id")

        # Verify merchant has permission for this invoice
        if not await verify_merchant_permission(merchant_telegram_id, invoice_id):
            await callback.answer("❌ Access denied - not your invoice", show_alert=True)
            return

        # Update invoice verification status
        from src.services.invoice_service import invoice_service

        success = await invoice_service.update_invoice_verification(
            invoice_id=invoice_id,
            verification_status="rejected",
            tenant_id=merchant_tenant_id,
            verified_by=f"telegram-manual-{merchant_id}",
            verification_note=f"Manually rejected via Telegram by merchant. Screenshot: {screenshot_id or 'N/A'}. Reason: Payment verification failed manual review"
        )

        if not success:
            await callback.answer("❌ Failed to update invoice", show_alert=True)
            return

        # Mark screenshot as processed (but not verified)
        if screenshot_id:
            from src.services.payment_screenshot_service import PaymentScreenshotService
            screenshot_service = PaymentScreenshotService()

            # Update metadata but don't mark as verified
            screenshot = await screenshot_service.get_screenshot_by_id(screenshot_id, merchant_tenant_id)
            if screenshot:
                current_meta = screenshot.get('metadata', {})
                current_meta.update({
                    "manually_rejected": True,
                    "rejected_by": merchant_id,
                    "rejected_at": datetime.now(timezone.utc).isoformat(),
                    "rejection_method": "manual_telegram"
                })

        # Update message to show rejection completed
        updated_text = callback.message.text + "\n\n❌ <b>MANUALLY REJECTED BY MERCHANT</b>"
        await callback.message.edit_text(
            text=updated_text,
            reply_markup=None,  # Remove buttons
            parse_mode="HTML"
        )

        # Notify customer of rejection
        await notify_customer_verification_result(
            invoice_id=invoice_id,
            status="rejected",
            method="manual",
            reason="Payment verification failed manual review",
            tenant_id=merchant_tenant_id
        )

        logger.info(f"✅ Manual rejection completed: invoice={invoice_id} by merchant={merchant_id}")

    except Exception as e:
        logger.error(f"❌ Error in manual reject: {e}", exc_info=True)
        await callback.answer("❌ Error occurred", show_alert=True)


# ============================================================================
# Helper Functions for Manual Verification
# ============================================================================

async def verify_merchant_permission(merchant_telegram_id: str, invoice_id: str) -> bool:
    """Verify merchant has permission to verify this invoice."""
    try:
        from src.db.postgres import get_db_session
        from sqlalchemy import text

        with get_db_session() as db:
            result = db.execute(
                text("""
                    SELECT i.id FROM invoice.invoice i
                    JOIN public.user u ON i.merchant_id = u.id
                    WHERE i.id = :invoice_id
                    AND u.telegram_user_id = :telegram_id
                    AND i.tenant_id = u.tenant_id
                """),
                {
                    "invoice_id": invoice_id,
                    "telegram_id": merchant_telegram_id
                }
            ).fetchone()

            return result is not None

    except Exception as e:
        logger.error(f"Error verifying merchant permission: {e}")
        return False


async def notify_customer_verification_result(
    invoice_id: str,
    status: str,
    tenant_id: str,
    method: str = "auto",
    reason: str = None
):
    """Notify customer of verification result."""
    try:
        # Get customer and invoice info
        from src.db.postgres import get_db_session
        from sqlalchemy import text

        with get_db_session() as db:
            result = db.execute(
                text("""
                    SELECT
                        c.name as customer_name,
                        c.telegram_chat_id,
                        i.invoice_number,
                        i.amount,
                        i.currency
                    FROM invoice.invoice i
                    JOIN invoice.customer c ON i.customer_id = c.id
                    WHERE i.id = :invoice_id
                    AND i.tenant_id = :tenant_id
                """),
                {
                    "invoice_id": invoice_id,
                    "tenant_id": tenant_id
                }
            ).fetchone()

            if not result or not result.telegram_chat_id:
                logger.warning(f"Customer not found or no Telegram chat for invoice: {invoice_id}")
                return

            customer_chat_id = result.telegram_chat_id
            invoice_number = result.invoice_number
            amount = result.amount
            currency = result.currency or "KHR"

            # Format amount
            if currency == "KHR":
                amount_str = f"{amount:,.0f} KHR"
            else:
                amount_str = f"${amount:.2f}"

            # Build notification message
            if status == "verified":
                message_text = (
                    f"✅ <b>Payment Verified!</b>\n\n"
                    f"📄 Invoice: <code>{invoice_number}</code>\n"
                    f"💰 Amount: <b>{amount_str}</b>\n\n"
                    f"🎉 Your payment has been confirmed!\n"
                    f"Thank you for your business.\n"
                )
                if method == "manual":
                    message_text += f"\n<i>✅ Verified by merchant review</i>"
            else:
                message_text = (
                    f"❌ <b>Payment Rejected</b>\n\n"
                    f"📄 Invoice: <code>{invoice_number}</code>\n"
                    f"💰 Amount: <b>{amount_str}</b>\n\n"
                    f"❗ Please check your payment and try again.\n"
                )
                if reason:
                    message_text += f"Reason: {reason}\n"
                if method == "manual":
                    message_text += f"\n<i>❌ Reviewed by merchant</i>"

            # Send notification
            from src.bot import create_bot
            bot, _ = create_bot()

            if bot:
                await bot.send_message(
                    chat_id=customer_chat_id,
                    text=message_text,
                    parse_mode="HTML"
                )
                logger.info(f"✅ Customer notified: {customer_chat_id} -> {status}")

    except Exception as e:
        logger.error(f"Error notifying customer: {e}")


async def handle_stock_deduction(invoice_id: str, tenant_id: str):
    """Handle stock deduction after payment verification."""
    try:
        # Import inventory service to handle stock deduction
        # This should integrate with existing stock management system
        logger.info(f"🏪 Processing stock deduction for invoice: {invoice_id}")

        # Implementation would depend on existing inventory system
        # For now, just log the action
        logger.info(f"✅ Stock deduction triggered for invoice: {invoice_id}")

    except Exception as e:
        logger.error(f"Error handling stock deduction: {e}")
