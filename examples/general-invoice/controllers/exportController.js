// examples/general-invoice/controllers/exportController.js
/**
 * Export controller with unified endpoint and parameter compatibility
 *
 * Supports both CSV and Excel export with date filtering and tenant isolation
 */

const { createTenantQuery } = require('../auth');

// Database connection (replace with your actual database implementation)
const db = require('../db');

/**
 * Export invoices to CSV or Excel format
 * GET /api/invoices/export?format=csv&start_date=2023-01-01&end_date=2023-12-31
 */
async function exportInvoices(req, res) {
    try {
        const tenantId = req.tenant.id;
        const {
            format = 'csv',
            start_date,
            end_date,
            // Support both parameter formats for compatibility
            startDate = start_date,
            endDate = end_date
        } = req.query;

        // Validate format
        if (!['csv', 'xlsx'].includes(format)) {
            return res.status(400).json({
                error: 'Invalid format. Supported formats: csv, xlsx'
            });
        }

        console.log(`📊 Exporting invoices for tenant ${tenantId}, format: ${format}`);

        // Build query with tenant isolation and date filters
        let query = `
            SELECT
                i.invoice_number,
                c.name as customer_name,
                i.status,
                i.currency,
                i.subtotal,
                i.tax_amount,
                i.total,
                i.due_date,
                i.created_at,
                i.verification_status
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            WHERE i.tenant_id = $1
        `;

        const params = [tenantId];
        let paramCount = 1;

        // Add date filters if provided
        if (startDate) {
            paramCount++;
            query += ` AND i.created_at >= $${paramCount}`;
            params.push(startDate);
        }

        if (endDate) {
            paramCount++;
            query += ` AND i.created_at <= $${paramCount}`;
            params.push(endDate + ' 23:59:59'); // Include full end date
        }

        query += ` ORDER BY i.created_at DESC`;

        // Execute query
        const result = await db.query(query, params);
        const invoices = result.rows;

        console.log(`📊 Found ${invoices.length} invoices to export`);

        if (format === 'csv') {
            return exportToCSV(res, invoices);
        } else {
            return exportToExcel(res, invoices);
        }

    } catch (error) {
        console.error('Export error:', error);
        res.status(500).json({
            error: 'Export failed',
            details: error.message
        });
    }
}

/**
 * Export to CSV format
 */
function exportToCSV(res, invoices) {
    const headers = [
        'Invoice Number',
        'Customer',
        'Status',
        'Currency',
        'Subtotal',
        'Tax',
        'Total',
        'Due Date',
        'Created',
        'Verification Status'
    ];

    let csvContent = headers.join(',') + '\n';

    invoices.forEach(invoice => {
        const row = [
            `"${invoice.invoice_number || ''}"`,
            `"${(invoice.customer_name || 'Unknown').replace(/"/g, '""')}"`,
            `"${invoice.status || ''}"`,
            `"${invoice.currency || 'USD'}"`,
            invoice.subtotal || 0,
            invoice.tax_amount || 0,
            invoice.total || 0,
            `"${invoice.due_date ? formatDate(invoice.due_date) : ''}"`,
            `"${invoice.created_at ? formatDate(invoice.created_at) : ''}"`,
            `"${invoice.verification_status || 'pending'}"`
        ];
        csvContent += row.join(',') + '\n';
    });

    const filename = `invoices_${new Date().toISOString().split('T')[0]}.csv`;

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
    res.send(csvContent);

    console.log(`✅ CSV export completed: ${filename} (${invoices.length} rows)`);
}

/**
 * Export to Excel format
 * Note: This is a simplified example. For production, use a proper Excel library like 'exceljs'
 */
async function exportToExcel(res, invoices) {
    try {
        // For this example, we'll create a simple Excel file
        // In production, use a library like 'exceljs' or 'xlsx'
        const ExcelJS = require('exceljs');

        const workbook = new ExcelJS.Workbook();
        const worksheet = workbook.addWorksheet('Invoices');

        // Define columns
        worksheet.columns = [
            { header: 'Invoice Number', key: 'invoice_number', width: 15 },
            { header: 'Customer', key: 'customer_name', width: 20 },
            { header: 'Status', key: 'status', width: 12 },
            { header: 'Currency', key: 'currency', width: 10 },
            { header: 'Subtotal', key: 'subtotal', width: 12 },
            { header: 'Tax', key: 'tax_amount', width: 12 },
            { header: 'Total', key: 'total', width: 12 },
            { header: 'Due Date', key: 'due_date', width: 12 },
            { header: 'Created', key: 'created_at', width: 15 },
            { header: 'Verification Status', key: 'verification_status', width: 18 }
        ];

        // Style the header row
        worksheet.getRow(1).font = { bold: true, color: { argb: 'FFFFFF' } };
        worksheet.getRow(1).fill = {
            type: 'pattern',
            pattern: 'solid',
            fgColor: { argb: '4A90E2' } // Blue header
        };

        // Add data
        invoices.forEach(invoice => {
            worksheet.addRow({
                invoice_number: invoice.invoice_number || '',
                customer_name: invoice.customer_name || 'Unknown',
                status: invoice.status || '',
                currency: invoice.currency || 'USD',
                subtotal: parseFloat(invoice.subtotal || 0),
                tax_amount: parseFloat(invoice.tax_amount || 0),
                total: parseFloat(invoice.total || 0),
                due_date: invoice.due_date ? formatDate(invoice.due_date) : '',
                created_at: invoice.created_at ? formatDate(invoice.created_at) : '',
                verification_status: invoice.verification_status || 'pending'
            });
        });

        // Auto-fit columns
        worksheet.columns.forEach(column => {
            if (column.eachCell) {
                let maxLength = 0;
                column.eachCell({ includeEmpty: true }, cell => {
                    const columnLength = cell.value ? cell.value.toString().length : 10;
                    if (columnLength > maxLength) {
                        maxLength = columnLength;
                    }
                });
                column.width = Math.min(maxLength + 2, 50);
            }
        });

        const filename = `invoices_${new Date().toISOString().split('T')[0]}.xlsx`;

        res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);

        await workbook.xlsx.write(res);
        res.end();

        console.log(`✅ Excel export completed: ${filename} (${invoices.length} rows)`);

    } catch (error) {
        // Fallback to CSV if Excel library is not available
        console.warn('Excel library not available, falling back to CSV:', error.message);
        return exportToCSV(res, invoices);
    }
}

/**
 * Format date for export
 */
function formatDate(date) {
    if (!date) return '';
    const d = new Date(date);
    return d.toISOString().split('T')[0]; // YYYY-MM-DD format
}

/**
 * Get export statistics
 * GET /api/invoices/export/stats
 */
async function getExportStats(req, res) {
    try {
        const tenantId = req.tenant.id;

        const query = `
            SELECT
                COUNT(*) as total_invoices,
                SUM(total) as total_amount,
                COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_invoices,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_invoices,
                MAX(created_at) as latest_invoice,
                MIN(created_at) as oldest_invoice
            FROM invoices
            WHERE tenant_id = $1
        `;

        const result = await db.query(query, [tenantId]);
        const stats = result.rows[0];

        res.json({
            tenant_id: tenantId,
            statistics: {
                total_invoices: parseInt(stats.total_invoices || 0),
                total_amount: parseFloat(stats.total_amount || 0),
                paid_invoices: parseInt(stats.paid_invoices || 0),
                pending_invoices: parseInt(stats.pending_invoices || 0),
                latest_invoice: stats.latest_invoice,
                oldest_invoice: stats.oldest_invoice
            },
            export_info: {
                supported_formats: ['csv', 'xlsx'],
                date_filters: ['start_date', 'end_date'],
                example_url: '/api/invoices/export?format=xlsx&start_date=2023-01-01&end_date=2023-12-31'
            }
        });

    } catch (error) {
        console.error('Export stats error:', error);
        res.status(500).json({
            error: 'Failed to get export statistics',
            details: error.message
        });
    }
}

module.exports = {
    exportInvoices,
    getExportStats
};