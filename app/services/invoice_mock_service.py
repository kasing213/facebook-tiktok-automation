# app/services/invoice_mock_service.py
"""
Mock Invoice API service for testing.

Provides in-memory CRUD operations that simulate the external Invoice API.
Data is stored in memory and lost on restart - suitable for development/testing.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4


# In-memory data stores (module-level singletons)
_customers: Dict[str, Dict[str, Any]] = {}
_invoices: Dict[str, Dict[str, Any]] = {}
_invoice_counter: int = 1000


def _generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid4())


def _now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


# ============================================================================
# Customer Operations
# ============================================================================

def list_customers(
    limit: int = 50,
    skip: int = 0,
    search: Optional[str] = None
) -> List[Dict]:
    """List customers with optional search and pagination."""
    customers = list(_customers.values())

    if search:
        search_lower = search.lower()
        customers = [
            c for c in customers
            if search_lower in c["name"].lower()
            or (c.get("email") and search_lower in c["email"].lower())
            or (c.get("company") and search_lower in c["company"].lower())
        ]

    # Sort by created_at descending
    customers.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return customers[skip:skip + limit]


def get_customer(customer_id: str) -> Optional[Dict]:
    """Get a single customer by ID."""
    return _customers.get(customer_id)


def create_customer(data: Dict) -> Dict:
    """Create a new customer."""
    customer_id = _generate_id()
    customer = {
        "id": customer_id,
        "name": data["name"],
        "email": data.get("email"),
        "phone": data.get("phone"),
        "address": data.get("address"),
        "company": data.get("company"),
        "notes": data.get("notes"),
        "created_at": _now_iso(),
        "updated_at": _now_iso()
    }
    _customers[customer_id] = customer
    return customer


def update_customer(customer_id: str, data: Dict) -> Optional[Dict]:
    """Update an existing customer."""
    if customer_id not in _customers:
        return None

    customer = _customers[customer_id]
    for key, value in data.items():
        if value is not None:
            customer[key] = value
    customer["updated_at"] = _now_iso()

    return customer


def delete_customer(customer_id: str) -> bool:
    """Delete a customer."""
    if customer_id in _customers:
        del _customers[customer_id]
        return True
    return False


# ============================================================================
# Invoice Operations
# ============================================================================

def list_invoices(
    limit: int = 50,
    skip: int = 0,
    customer_id: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict]:
    """List invoices with optional filtering and pagination."""
    invoices = list(_invoices.values())

    if customer_id:
        invoices = [i for i in invoices if i["customer_id"] == customer_id]
    if status:
        invoices = [i for i in invoices if i["status"] == status]

    # Add customer info to each invoice
    for inv in invoices:
        inv["customer"] = _customers.get(inv["customer_id"])

    # Sort by created_at descending
    invoices.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return invoices[skip:skip + limit]


def get_invoice(invoice_id: str) -> Optional[Dict]:
    """Get a single invoice by ID with customer info."""
    invoice = _invoices.get(invoice_id)
    if invoice:
        # Return a copy with customer info
        invoice = invoice.copy()
        invoice["customer"] = _customers.get(invoice["customer_id"])
    return invoice


def create_invoice(data: Dict) -> Dict:
    """Create a new invoice with auto-calculated totals."""
    global _invoice_counter

    invoice_id = _generate_id()
    _invoice_counter += 1

    # Process items
    items = data.get("items", [])
    processed_items = []

    for item in items:
        quantity = float(item.get("quantity", 1))
        unit_price = float(item.get("unit_price", 0))
        tax_rate = float(item.get("tax_rate", 0))
        item_total = quantity * unit_price

        processed_items.append({
            "id": _generate_id(),
            "description": item.get("description", ""),
            "quantity": quantity,
            "unit_price": unit_price,
            "tax_rate": tax_rate,
            "total": round(item_total, 2)
        })

    # Calculate totals
    subtotal = sum(item["total"] for item in processed_items)
    tax_amount = sum(
        item["total"] * (item.get("tax_rate", 0) / 100)
        for item in processed_items
    )
    discount = float(data.get("discount", 0))
    discount_amount = subtotal * (discount / 100) if discount > 0 else 0
    total = subtotal + tax_amount - discount_amount

    invoice = {
        "id": invoice_id,
        "invoice_number": f"INV-{_invoice_counter:05d}",
        "customer_id": data["customer_id"],
        "items": processed_items,
        "subtotal": round(subtotal, 2),
        "tax_rate": sum(item.get("tax_rate", 0) for item in processed_items) / max(len(processed_items), 1),
        "tax_amount": round(tax_amount, 2),
        "discount": discount,
        "discount_amount": round(discount_amount, 2),
        "total": round(total, 2),
        "status": "draft",
        "due_date": data.get("due_date"),
        "notes": data.get("notes"),
        # Payment verification fields
        "bank": data.get("bank"),
        "expected_account": data.get("expected_account") or data.get("expectedAccount"),
        "currency": data.get("currency", "KHR"),
        "verification_status": "pending",
        "verified_at": None,
        "verified_by": None,
        "verification_note": None,
        "created_at": _now_iso(),
        "updated_at": _now_iso()
    }

    _invoices[invoice_id] = invoice

    # Return with customer info
    invoice = invoice.copy()
    invoice["customer"] = _customers.get(invoice["customer_id"])
    return invoice


def update_invoice(invoice_id: str, data: Dict) -> Optional[Dict]:
    """Update an existing invoice with recalculated totals if items changed."""
    if invoice_id not in _invoices:
        return None

    invoice = _invoices[invoice_id]

    # Update fields
    for key, value in data.items():
        if value is not None and key != "items":
            invoice[key] = value

    # Recalculate totals if items changed
    if "items" in data and data["items"] is not None:
        items = data["items"]
        processed_items = []

        for item in items:
            quantity = float(item.get("quantity", 1))
            unit_price = float(item.get("unit_price", 0))
            tax_rate = float(item.get("tax_rate", 0))
            item_total = quantity * unit_price

            processed_items.append({
                "id": item.get("id", _generate_id()),
                "description": item.get("description", ""),
                "quantity": quantity,
                "unit_price": unit_price,
                "tax_rate": tax_rate,
                "total": round(item_total, 2)
            })

        invoice["items"] = processed_items

        subtotal = sum(item["total"] for item in processed_items)
        tax_amount = sum(
            item["total"] * (item.get("tax_rate", 0) / 100)
            for item in processed_items
        )
        discount = float(invoice.get("discount", 0))
        discount_amount = subtotal * (discount / 100) if discount > 0 else 0

        invoice["subtotal"] = round(subtotal, 2)
        invoice["tax_amount"] = round(tax_amount, 2)
        invoice["discount_amount"] = round(discount_amount, 2)
        invoice["total"] = round(subtotal + tax_amount - discount_amount, 2)

    invoice["updated_at"] = _now_iso()

    # Return with customer info
    result = invoice.copy()
    result["customer"] = _customers.get(invoice["customer_id"])
    return result


def delete_invoice(invoice_id: str) -> bool:
    """Delete an invoice."""
    if invoice_id in _invoices:
        del _invoices[invoice_id]
        return True
    return False


def verify_invoice(invoice_id: str, data: Dict) -> Optional[Dict]:
    """
    Update verification status of an invoice.

    Args:
        invoice_id: The invoice ID
        data: Dict with verificationStatus, verifiedBy, verificationNote

    Returns:
        Updated invoice or None if not found
    """
    if invoice_id not in _invoices:
        return None

    invoice = _invoices[invoice_id]

    # Update verification fields
    verification_status = data.get("verificationStatus") or data.get("verification_status")
    if verification_status:
        invoice["verification_status"] = verification_status

    verified_by = data.get("verifiedBy") or data.get("verified_by")
    if verified_by:
        invoice["verified_by"] = verified_by

    verification_note = data.get("verificationNote") or data.get("verification_note")
    if verification_note is not None:
        invoice["verification_note"] = verification_note

    # Set verified_at timestamp if status is verified
    if verification_status == "verified":
        invoice["verified_at"] = _now_iso()
        # Also update invoice status to paid when verified
        invoice["status"] = "paid"

    invoice["updated_at"] = _now_iso()

    # Return with customer info
    result = invoice.copy()
    result["customer"] = _customers.get(invoice["customer_id"])
    return result


# ============================================================================
# Statistics
# ============================================================================

def get_stats() -> Dict:
    """Get invoice statistics."""
    invoices = list(_invoices.values())

    total_revenue = sum(i["total"] for i in invoices if i["status"] == "paid")
    pending_amount = sum(i["total"] for i in invoices if i["status"] in ["pending", "draft"])
    paid_amount = total_revenue
    overdue_count = len([i for i in invoices if i["status"] == "overdue"])

    return {
        "total_invoices": len(invoices),
        "total_revenue": round(total_revenue, 2),
        "pending_amount": round(pending_amount, 2),
        "paid_amount": round(paid_amount, 2),
        "overdue_count": overdue_count,
        "customers_count": len(_customers)
    }


# ============================================================================
# PDF Generation (Mock)
# ============================================================================

def generate_pdf(invoice_id: str) -> Optional[bytes]:
    """
    Generate a mock PDF for testing.

    Returns a minimal valid PDF that can be opened by PDF readers.
    In production, this would connect to a real PDF generation service.
    """
    invoice = get_invoice(invoice_id)
    if not invoice:
        return None

    # Create a simple but valid PDF
    invoice_num = invoice["invoice_number"]
    customer_name = invoice.get("customer", {}).get("name", "Unknown")
    total = invoice["total"]
    currency = invoice.get("currency", "KHR")
    bank = invoice.get("bank") or "N/A"
    expected_account = invoice.get("expected_account") or "N/A"
    verification_status = invoice.get("verification_status", "pending").upper()

    # Format amount with currency
    if currency == "KHR":
        amount_str = f"{total:,.0f} KHR"
    else:
        amount_str = f"${total:.2f} {currency}"

    # Verification badge
    if verification_status == "VERIFIED":
        badge = "[VERIFIED]"
    elif verification_status == "REJECTED":
        badge = "[REJECTED]"
    else:
        badge = "[PENDING]"

    # Build PDF content with payment info
    content = f"""Invoice: {invoice_num}
Customer: {customer_name}
Total: {amount_str}
Status: {invoice["status"]}
Verification: {badge}

Payment Information:
Bank: {bank}
Account: {expected_account}
Amount: {amount_str}

This is a mock PDF generated for testing purposes."""

    # Minimal valid PDF structure
    pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(content) + 200} >>
stream
BT
/F1 14 Tf
450 750 Td
({badge}) Tj
/F1 12 Tf
50 700 Td
({invoice_num}) Tj
0 -20 Td
(Customer: {customer_name}) Tj
0 -20 Td
(Total: {amount_str}) Tj
0 -20 Td
(Status: {invoice["status"]}) Tj
0 -40 Td
(--- Payment Information ---) Tj
0 -20 Td
(Bank: {bank}) Tj
0 -20 Td
(Account: {expected_account}) Tj
0 -20 Td
(Amount: {amount_str}) Tj
0 -40 Td
(Mock PDF for testing) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000{450 + len(content):03d} 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
{550 + len(content)}
%%EOF"""

    return pdf_content.encode('latin-1')


# ============================================================================
# Export (Mock)
# ============================================================================

def export_invoices(
    format: str = "csv",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> bytes:
    """
    Export invoices to CSV or Excel format.

    For testing, returns properly formatted CSV or a placeholder for XLSX.
    """
    invoices = list(_invoices.values())

    # Filter by date if provided
    if start_date:
        invoices = [i for i in invoices if i.get("created_at", "") >= start_date]
    if end_date:
        invoices = [i for i in invoices if i.get("created_at", "") <= end_date]

    if format == "csv":
        lines = ["Invoice Number,Customer,Status,Subtotal,Tax,Discount,Total,Due Date,Created"]
        for inv in invoices:
            customer = _customers.get(inv["customer_id"], {})
            customer_name = customer.get("name", "Unknown").replace(",", " ")
            lines.append(
                f'{inv["invoice_number"]},'
                f'{customer_name},'
                f'{inv["status"]},'
                f'{inv["subtotal"]},'
                f'{inv["tax_amount"]},'
                f'{inv["discount_amount"]},'
                f'{inv["total"]},'
                f'{inv.get("due_date", "")},'
                f'{inv["created_at"]}'
            )
        return "\n".join(lines).encode("utf-8")
    else:
        # For xlsx, return a placeholder
        # In production, use openpyxl or xlsxwriter
        return b"PK\x03\x04XLSX_MOCK_CONTENT"


# ============================================================================
# Sample Data Seeding
# ============================================================================

def seed_sample_data():
    """
    Populate with sample data for testing.

    Only seeds if the data stores are empty.
    """
    global _invoice_counter

    # Only seed if empty
    if _customers or _invoices:
        return {"seeded": False, "message": "Data already exists"}

    # Sample customers
    sample_customers = [
        {
            "name": "Acme Corporation",
            "email": "billing@acme.com",
            "phone": "+1-555-0100",
            "company": "Acme Corp",
            "address": "123 Business St, New York, NY 10001"
        },
        {
            "name": "TechStart Inc",
            "email": "invoices@techstart.io",
            "phone": "+1-555-0101",
            "company": "TechStart",
            "address": "456 Innovation Blvd, San Francisco, CA 94105"
        },
        {
            "name": "Global Services LLC",
            "email": "accounts@globalservices.com",
            "phone": "+1-555-0102",
            "address": "789 Commerce Ave, Chicago, IL 60601"
        },
        {
            "name": "Local Business Shop",
            "email": "owner@localbiz.com",
            "phone": "+1-555-0103",
            "address": "321 Main St, Austin, TX 78701"
        },
        {
            "name": "Enterprise Solutions Ltd",
            "email": "procurement@enterprise.com",
            "company": "Enterprise Solutions Ltd",
            "address": "555 Corporate Dr, Seattle, WA 98101"
        },
    ]

    created_customers = []
    for cust_data in sample_customers:
        customer = create_customer(cust_data)
        created_customers.append(customer)

    # Sample invoices with varied statuses
    statuses = ["draft", "pending", "paid", "paid", "overdue"]

    for i, customer in enumerate(created_customers):
        invoice_data = {
            "customer_id": customer["id"],
            "items": [
                {
                    "description": "Consulting Services",
                    "quantity": 10 + i * 2,
                    "unit_price": 150.00,
                    "tax_rate": 10
                },
                {
                    "description": "Software License",
                    "quantity": 1,
                    "unit_price": 500.00 + i * 100,
                    "tax_rate": 10
                },
            ],
            "due_date": (datetime.utcnow() + timedelta(days=30 - i * 7)).strftime("%Y-%m-%d"),
            "notes": f"Sample invoice #{i + 1} for testing purposes."
        }

        invoice = create_invoice(invoice_data)

        # Update status
        update_invoice(invoice["id"], {"status": statuses[i % len(statuses)]})

    return {
        "seeded": True,
        "customers": len(created_customers),
        "invoices": len(_invoices)
    }


def clear_all_data():
    """Clear all mock data (for testing reset)."""
    global _customers, _invoices, _invoice_counter
    _customers = {}
    _invoices = {}
    _invoice_counter = 1000
    return {"cleared": True}


def get_data_counts() -> Dict:
    """Get current data counts."""
    return {
        "customers": len(_customers),
        "invoices": len(_invoices)
    }
