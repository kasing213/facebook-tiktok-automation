// examples/general-invoice/auth.js
/**
 * JWT Authentication middleware for general-invoice Node.js service
 *
 * This middleware validates JWT tokens from the Facebook-automation platform
 * and provides tenant isolation for invoice operations.
 */

const jwt = require('jsonwebtoken');

/**
 * JWT validation middleware
 *
 * Validates the Authorization: Bearer token and extracts tenant/user context
 */
function validateJWT(req, res, next) {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({
            error: 'Missing or invalid Authorization header',
            expected: 'Authorization: Bearer <jwt-token>'
        });
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Get JWT secret from environment
    const jwtSecret = process.env.INVOICE_JWT_SECRET || process.env.MASTER_SECRET_KEY;

    if (!jwtSecret) {
        console.error('JWT secret not configured. Set INVOICE_JWT_SECRET or MASTER_SECRET_KEY');
        return res.status(500).json({
            error: 'Server configuration error'
        });
    }

    try {
        // Verify and decode the JWT token
        const payload = jwt.verify(token, jwtSecret, { algorithms: ['HS256'] });

        // Extract required fields
        const tenantId = payload.tenant_id;
        const userId = payload.user_id;
        const service = payload.service;

        if (!tenantId) {
            return res.status(401).json({
                error: 'Invalid token: missing tenant_id'
            });
        }

        // Add tenant context to request for tenant isolation
        req.tenant = {
            id: tenantId,
            userId: userId,
            service: service,
            tokenPayload: payload
        };

        console.log(`✅ JWT validated for tenant ${tenantId}, service: ${service}`);
        next();

    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({
                error: 'Token expired',
                expired_at: error.expiredAt
            });
        }

        if (error.name === 'JsonWebTokenError') {
            return res.status(401).json({
                error: 'Invalid token',
                details: error.message
            });
        }

        console.error('JWT validation error:', error);
        return res.status(500).json({
            error: 'Token validation failed'
        });
    }
}

/**
 * Optional API key validation middleware (for backward compatibility)
 *
 * Can be used alongside JWT or as a fallback authentication method
 */
function validateAPIKey(req, res, next) {
    const apiKey = req.headers['x-api-key'];
    const expectedKey = process.env.INVOICE_API_KEY;

    if (!expectedKey) {
        // No API key configured, skip validation
        return next();
    }

    if (!apiKey) {
        return res.status(401).json({
            error: 'Missing X-API-Key header'
        });
    }

    if (apiKey !== expectedKey) {
        return res.status(401).json({
            error: 'Invalid API key'
        });
    }

    console.log('✅ API key validated');
    next();
}

/**
 * Combined authentication middleware
 *
 * Tries JWT first, falls back to API key for backward compatibility
 */
function authenticateRequest(req, res, next) {
    const authHeader = req.headers.authorization;

    if (authHeader && authHeader.startsWith('Bearer ')) {
        // Use JWT authentication
        return validateJWT(req, res, next);
    } else {
        // Fall back to API key authentication
        return validateAPIKey(req, res, next);
    }
}

/**
 * Tenant isolation helper
 *
 * Ensures all database operations include tenant_id filter
 */
function requireTenant(req, res, next) {
    if (!req.tenant || !req.tenant.id) {
        return res.status(401).json({
            error: 'Tenant context required. Use JWT authentication.'
        });
    }
    next();
}

/**
 * Create tenant-scoped database query helper
 */
function createTenantQuery(baseQuery, tenantId) {
    // Add tenant_id filter to prevent cross-tenant data access
    if (baseQuery.includes('WHERE')) {
        return baseQuery.replace('WHERE', `WHERE tenant_id = $1 AND`);
    } else {
        return `${baseQuery} WHERE tenant_id = $1`;
    }
}

/**
 * Extract tenant ID from request (for logging/routing)
 */
function getTenantId(req) {
    return req.tenant ? req.tenant.id : null;
}

module.exports = {
    validateJWT,
    validateAPIKey,
    authenticateRequest,
    requireTenant,
    createTenantQuery,
    getTenantId
};