#!/usr/bin/env node
/**
 * LOCAL MOCK SERVER FOR E2E TESTING - NOT FOR PRODUCTION
 * Runs on port 8080 to avoid production conflicts
 * Provides basic API endpoints for E2E test authentication
 */

const http = require('http');
const url = require('url');

const PORT = 8080;

// Mock responses for E2E tests
const mockResponses = {
  // Health check endpoint
  '/health': {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0-local-mock',
    database: 'mock',
    redis: 'mock'
  },

  // Authentication success response
  '/api/auth/login': {
    access_token: 'mock-jwt-token-for-testing',
    refresh_token: 'mock-refresh-token',
    token_type: 'bearer',
    expires_in: 3600,
    user: {
      id: 'mock-user-123',
      email: 'test@example.com',
      role: 'user',
      tenant_id: 'mock-tenant-456'
    }
  },

  // User info endpoint
  '/api/auth/me': {
    id: 'mock-user-123',
    email: 'test@example.com',
    role: 'user',
    tenant_id: 'mock-tenant-456',
    tenant: {
      id: 'mock-tenant-456',
      name: 'Test Tenant',
      subscription_tier: 'pro'
    }
  },

  // Dashboard data
  '/api/dashboard/overview': {
    stats: {
      invoices: { total: 23, pending: 5, paid: 18 },
      revenue: { total: 12450, monthly: 3200 },
      products: { total: 847, low_stock: 3 }
    }
  }
};

// Simple HTTP server
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const path = parsedUrl.pathname;
  const method = req.method;

  // Enable CORS for frontend
  res.setHeader('Access-Control-Allow-Origin', 'http://localhost:5173');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Credentials', 'true');

  // Handle preflight requests
  if (method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // Handle POST requests (login)
  if (method === 'POST') {
    let body = '';
    req.on('data', chunk => {
      body += chunk.toString();
    });

    req.on('end', () => {
      try {
        const data = JSON.parse(body);

        // Mock login validation
        if (path === '/api/auth/login') {
          if (data.email === 'test@example.com' && data.password === 'TestPassword123!') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(mockResponses[path]));
          } else {
            res.writeHead(401, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: 'Invalid credentials' }));
          }
          return;
        }

        // Fallback for unknown POST routes
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'POST endpoint not found', path: path }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
        return;
      }
    });
    return;
  }

  // Handle GET requests
  if (method === 'GET') {
    if (mockResponses[path]) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(mockResponses[path]));
      return;
    }
  }

  // 404 for unknown endpoints
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Endpoint not found', path: path }));
});

server.listen(PORT, 'localhost', () => {
  console.log(`🚀 Local mock server running on http://localhost:${PORT}`);
  console.log(`📋 Available endpoints:`);
  console.log(`   GET  /health - Health check`);
  console.log(`   POST /api/auth/login - Login (test@example.com / TestPassword123!)`);
  console.log(`   GET  /api/auth/me - User info`);
  console.log(`   GET  /api/dashboard/overview - Dashboard data`);
  console.log(`🔒 CORS enabled for http://localhost:5173`);
  console.log(`⚠️  FOR LOCAL TESTING ONLY - NOT FOR PRODUCTION`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('\n📡 Shutting down mock server...');
  server.close(() => {
    console.log('✅ Mock server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\n📡 Shutting down mock server...');
  server.close(() => {
    console.log('✅ Mock server closed');
    process.exit(0);
  });
});
