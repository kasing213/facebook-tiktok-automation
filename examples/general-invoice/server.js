// examples/general-invoice/server.js
/**
 * General Invoice API Server with JWT Authentication
 *
 * Express.js server that provides invoice management APIs with JWT authentication
 * and proper tenant isolation for integration with Facebook-automation platform.
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { authenticateRequest, requireTenant, getTenantId } = require('./auth');
const invoiceRoutes = require('./routes/invoices');
const customerRoutes = require('./routes/customers');
const exportController = require('./controllers/exportController');

// Load environment variables
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;

// Security middleware
app.use(helmet());
app.use(cors({
    origin: process.env.FRONTEND_URL || 'https://facebooktiktokautomation.vercel.app',
    credentials: true
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 1000, // limit each IP to 1000 requests per windowMs
    message: {
        error: 'Too many requests',
        retry_after: '15 minutes'
    }
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging
app.use((req, res, next) => {
    const timestamp = new Date().toISOString();
    const tenantId = getTenantId(req) || 'anonymous';
    console.log(`[${timestamp}] ${req.method} ${req.path} - Tenant: ${tenantId}`);
    next();
});

// Health check endpoint (no auth required)
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'general-invoice',
        version: process.env.npm_package_version || '1.0.0',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// API status endpoint (no auth required)
app.get('/api/status', (req, res) => {
    res.json({
        service: 'general-invoice-api',
        status: 'operational',
        features: {
            jwt_auth: true,
            tenant_isolation: true,
            export_formats: ['csv', 'xlsx'],
            pdf_generation: true
        },
        endpoints: {
            customers: '/api/customers',
            invoices: '/api/invoices',
            export: '/api/invoices/export',
            auth: '/api/auth'
        }
    });
});

// Authentication middleware for all /api routes
app.use('/api', authenticateRequest);
app.use('/api', requireTenant);

// API Routes
app.use('/api/customers', customerRoutes);
app.use('/api/invoices', invoiceRoutes);

// Export endpoint
app.get('/api/invoices/export', exportController.exportInvoices);

// JWT validation endpoint
app.post('/api/auth/validate', (req, res) => {
    // If we get here, JWT is already validated by middleware
    res.json({
        valid: true,
        tenant_id: req.tenant.id,
        user_id: req.tenant.userId,
        service: req.tenant.service,
        message: 'Token is valid'
    });
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Error:', error);

    if (error.type === 'entity.parse.failed') {
        return res.status(400).json({
            error: 'Invalid JSON in request body'
        });
    }

    if (error.name === 'ValidationError') {
        return res.status(400).json({
            error: 'Validation failed',
            details: error.message
        });
    }

    res.status(500).json({
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'production' ?
            'An unexpected error occurred' :
            error.message
    });
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Endpoint not found',
        available_endpoints: [
            '/health',
            '/api/status',
            '/api/customers',
            '/api/invoices',
            '/api/invoices/export'
        ]
    });
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received. Shutting down gracefully...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('SIGINT received. Shutting down gracefully...');
    process.exit(0);
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
    console.log(`🚀 General Invoice API server running on port ${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
    console.log(`🔐 Authentication: JWT (${process.env.INVOICE_JWT_SECRET ? 'configured' : 'missing'})`);
    console.log(`🏢 Environment: ${process.env.NODE_ENV || 'development'}`);

    // Validate required environment variables
    const required = ['INVOICE_JWT_SECRET', 'DATABASE_URL'];
    const missing = required.filter(env => !process.env[env]);

    if (missing.length > 0) {
        console.warn(`⚠️  Missing environment variables: ${missing.join(', ')}`);
    } else {
        console.log('✅ All required environment variables configured');
    }
});

module.exports = app;