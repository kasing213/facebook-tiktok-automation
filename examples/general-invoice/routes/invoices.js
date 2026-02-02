// examples/general-invoice/routes/invoices.js
/**
 * Invoice API routes with JWT authentication and tenant isolation
 *
 * Provides CRUD operations for invoices with proper tenant-based security
 */

const express = require('express');
const router = express.Router();
const { createTenantQuery } = require('../auth');

// Mock database helper (replace with your actual database implementation)
const db = require('../db'); // Your database connection

/**
 * List invoices with tenant isolation
 * GET /api/invoices
 */
router.get('/', async (req, res) => {
    try {
        const tenantId = req.tenant.id;
        const { limit = 50, skip = 0, customer_id, status } = req.query;

        let query = `
            SELECT
                i.*,
                c.name as customer_name,
                c.email as customer_email
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.tenant_id = $1
        `;
        const params = [tenantId];
        let paramCount = 1;

        // Add filters
        if (customer_id) {
            paramCount++;
            query += ` AND i.customer_id = $${paramCount}`;
            params.push(customer_id);
        }

        if (status) {
            paramCount++;
            query += ` AND i.status = $${paramCount}`;
            params.push(status);
        }

        query += ` ORDER BY i.created_at DESC LIMIT $${++paramCount} OFFSET $${++paramCount}`;
        params.push(parseInt(limit), parseInt(skip));

        const result = await db.query(query, params);

        res.json({
            invoices: result.rows,
            limit: parseInt(limit),
            skip: parseInt(skip),
            total: result.rows.length
        });

    } catch (error) {
        console.error('Error listing invoices:', error);
        res.status(500).json({
            error: 'Failed to list invoices',
            details: error.message
        });
    }
});

/**
 * Get single invoice by ID
 * GET /api/invoices/:id
 */
router.get('/:id', async (req, res) => {
    try {
        const tenantId = req.tenant.id;
        const invoiceId = req.params.id;

        const query = `
            SELECT
                i.*,
                c.name as customer_name,
                c.email as customer_email,
                c.phone as customer_phone,
                c.address as customer_address
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.id = $1 AND i.tenant_id = $2
        `;

        const result = await db.query(query, [invoiceId, tenantId]);

        if (result.rows.length === 0) {
            return res.status(404).json({
                error: 'Invoice not found'
            });
        }

        const invoice = result.rows[0];

        // Parse items JSON if stored as string
        if (typeof invoice.items === 'string') {
            try {
                invoice.items = JSON.parse(invoice.items);
            } catch (e) {
                invoice.items = [];
            }
        }

        res.json(invoice);

    } catch (error) {
        console.error('Error getting invoice:', error);
        res.status(500).json({
            error: 'Failed to get invoice',
            details: error.message
        });
    }
});

/**
 * Create new invoice
 * POST /api/invoices
 */
router.post('/', async (req, res) => {
    try {
        const tenantId = req.tenant.id;
        const userId = req.tenant.userId;
        const {
            customer_id,
            items = [],
            notes,
            due_date,
            bank,
            expected_account,
            recipient_name,
            currency = 'KHR'
        } = req.body;

        if (!customer_id) {
            return res.status(400).json({
                error: 'customer_id is required'
            });
        }

        // Calculate totals
        let subtotal = 0;
        let tax_amount = 0;

        const processedItems = items.map(item => {
            const quantity = parseFloat(item.quantity || 1);
            const unit_price = parseFloat(item.unit_price || 0);
            const tax_rate = parseFloat(item.tax_rate || 0);
            const item_total = quantity * unit_price;

            subtotal += item_total;
            tax_amount += item_total * (tax_rate / 100);

            return {
                ...item,
                quantity,
                unit_price,
                tax_rate,
                total: item_total
            };
        });

        const total = subtotal + tax_amount;

        // Generate invoice number
        const countQuery = 'SELECT COUNT(*) FROM invoices WHERE tenant_id = $1';
        const countResult = await db.query(countQuery, [tenantId]);
        const invoiceNumber = `INV-${String(parseInt(countResult.rows[0].count) + 1).padStart(5, '0')}`;

        const insertQuery = `
            INSERT INTO invoices (
                tenant_id, customer_id, invoice_number, items, subtotal,
                tax_amount, total, currency, status, notes, due_date,
                bank, expected_account, recipient_name, created_by, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, 'draft', $9, $10, $11, $12, $13, $14, NOW()
            ) RETURNING *
        `;

        const result = await db.query(insertQuery, [
            tenantId, customer_id, invoiceNumber, JSON.stringify(processedItems),
            subtotal, tax_amount, total, currency, notes, due_date,
            bank, expected_account, recipient_name, userId
        ]);

        res.status(201).json(result.rows[0]);

    } catch (error) {
        console.error('Error creating invoice:', error);
        res.status(500).json({
            error: 'Failed to create invoice',
            details: error.message
        });
    }
});

/**
 * Update invoice
 * PUT /api/invoices/:id
 */
router.put('/:id', async (req, res) => {
    try {
        const tenantId = req.tenant.id;
        const invoiceId = req.params.id;
        const updates = req.body;

        // Verify invoice exists and belongs to tenant
        const checkQuery = 'SELECT id FROM invoices WHERE id = $1 AND tenant_id = $2';
        const checkResult = await db.query(checkQuery, [invoiceId, tenantId]);

        if (checkResult.rows.length === 0) {
            return res.status(404).json({
                error: 'Invoice not found'
            });
        }

        // Build dynamic update query
        const allowedFields = [
            'customer_id', 'items', 'status', 'notes', 'due_date',
            'bank', 'expected_account', 'recipient_name', 'currency'
        ];

        const updateFields = [];
        const params = [];
        let paramCount = 0;

        Object.keys(updates).forEach(key => {
            if (allowedFields.includes(key) && updates[key] !== undefined) {
                paramCount++;
                updateFields.push(`${key} = $${paramCount}`);

                if (key === 'items' && typeof updates[key] === 'object') {
                    params.push(JSON.stringify(updates[key]));
                } else {
                    params.push(updates[key]);
                }
            }
        });

        if (updateFields.length === 0) {
            return res.status(400).json({
                error: 'No valid fields to update'
            });
        }

        updateFields.push(`updated_at = NOW()`);
        params.push(invoiceId, tenantId);

        const updateQuery = `
            UPDATE invoices
            SET ${updateFields.join(', ')}
            WHERE id = $${paramCount + 1} AND tenant_id = $${paramCount + 2}
            RETURNING *
        `;

        const result = await db.query(updateQuery, params);
        res.json(result.rows[0]);

    } catch (error) {
        console.error('Error updating invoice:', error);
        res.status(500).json({
            error: 'Failed to update invoice',
            details: error.message
        });
    }
});

/**
 * Delete invoice
 * DELETE /api/invoices/:id
 */
router.delete('/:id', async (req, res) => {
    try {
        const tenantId = req.tenant.id;
        const invoiceId = req.params.id;

        const deleteQuery = 'DELETE FROM invoices WHERE id = $1 AND tenant_id = $2 RETURNING id';
        const result = await db.query(deleteQuery, [invoiceId, tenantId]);

        if (result.rows.length === 0) {
            return res.status(404).json({
                error: 'Invoice not found'
            });
        }

        res.json({
            message: 'Invoice deleted successfully',
            id: invoiceId
        });

    } catch (error) {
        console.error('Error deleting invoice:', error);
        res.status(500).json({
            error: 'Failed to delete invoice',
            details: error.message
        });
    }
});

/**
 * Verify invoice payment
 * POST /api/invoices/:id/verify
 */
router.post('/:id/verify', async (req, res) => {
    try {
        const tenantId = req.tenant.id;
        const invoiceId = req.params.id;
        const { verification_status, verified_by, verification_note } = req.body;

        const updateQuery = `
            UPDATE invoices
            SET verification_status = $1, verified_by = $2, verification_note = $3,
                verified_at = CASE WHEN $1 = 'verified' THEN NOW() ELSE verified_at END,
                status = CASE WHEN $1 = 'verified' THEN 'paid' ELSE status END,
                updated_at = NOW()
            WHERE id = $4 AND tenant_id = $5
            RETURNING *
        `;

        const result = await db.query(updateQuery, [
            verification_status, verified_by, verification_note, invoiceId, tenantId
        ]);

        if (result.rows.length === 0) {
            return res.status(404).json({
                error: 'Invoice not found'
            });
        }

        res.json(result.rows[0]);

    } catch (error) {
        console.error('Error verifying invoice:', error);
        res.status(500).json({
            error: 'Failed to verify invoice',
            details: error.message
        });
    }
});

/**
 * Generate PDF for invoice
 * GET /api/invoices/:id/pdf
 */
router.get('/:id/pdf', async (req, res) => {
    try {
        const tenantId = req.tenant.id;
        const invoiceId = req.params.id;

        // Get invoice data
        const query = `
            SELECT i.*, c.name as customer_name, c.email as customer_email
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.id = $1 AND i.tenant_id = $2
        `;

        const result = await db.query(query, [invoiceId, tenantId]);

        if (result.rows.length === 0) {
            return res.status(404).json({
                error: 'Invoice not found'
            });
        }

        // Generate PDF (implement your PDF generation logic)
        const pdfBuffer = await generateInvoicePDF(result.rows[0]);

        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', `attachment; filename="invoice-${result.rows[0].invoice_number}.pdf"`);
        res.send(pdfBuffer);

    } catch (error) {
        console.error('Error generating PDF:', error);
        res.status(500).json({
            error: 'Failed to generate PDF',
            details: error.message
        });
    }
});

/**
 * Placeholder PDF generation function
 * Replace with your actual PDF generation implementation
 */
async function generateInvoicePDF(invoice) {
    // This is a placeholder - implement with your preferred PDF library
    // Examples: puppeteer, jsPDF, PDFKit, etc.
    return Buffer.from(`PDF content for invoice ${invoice.invoice_number}`);
}

module.exports = router;