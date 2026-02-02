# General Invoice API with JWT Authentication

A Node.js invoice API service with JWT authentication designed to integrate with the Facebook-automation platform.

## Features

- 🔐 **JWT Authentication** - Secure token-based authentication
- 🏢 **Multi-tenant Support** - Complete tenant isolation
- 📊 **Export Functionality** - CSV and Excel export with date filtering
- 📄 **PDF Generation** - Invoice PDF generation
- 🛡️ **Security** - Rate limiting, CORS, Helmet protection
- 🔄 **API Compatibility** - Compatible with Facebook-automation platform

## Quick Start

### 1. Installation

```bash
# Clone or copy the example files
cd general-invoice
npm install
```

### 2. Environment Configuration

Create a `.env` file:

```env
# Server Configuration
NODE_ENV=production
PORT=3001

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/invoice_db

# JWT Authentication (REQUIRED)
INVOICE_JWT_SECRET=your_jwt_secret_here
MASTER_SECRET_KEY=fallback_secret_key

# API Key (optional - for backward compatibility)
INVOICE_API_KEY=your_api_key_here

# Frontend URL (for CORS)
FRONTEND_URL=https://facebooktiktokautomation.vercel.app

# Optional: API Gateway URL
API_GATEWAY_URL=https://your-api-gateway.com
```

### 3. Database Setup

Create the required tables:

```sql
-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    company VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Invoices table
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    customer_id UUID REFERENCES customers(id),
    invoice_number VARCHAR(100) NOT NULL,
    items JSONB DEFAULT '[]',
    subtotal DECIMAL(10,2) DEFAULT 0,
    tax_amount DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'draft',
    notes TEXT,
    due_date DATE,
    bank VARCHAR(255),
    expected_account VARCHAR(255),
    recipient_name VARCHAR(255),
    verification_status VARCHAR(50) DEFAULT 'pending',
    verified_at TIMESTAMP,
    verified_by VARCHAR(255),
    verification_note TEXT,
    created_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_customers_tenant ON customers(tenant_id);
CREATE INDEX idx_invoices_tenant ON invoices(tenant_id);
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_created ON invoices(created_at);
```

### 4. Start the Server

```bash
# Development mode
npm run dev

# Production mode
npm start
```

## API Endpoints

### Authentication

All `/api/*` endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Health Check

```bash
GET /health
# No authentication required
```

### Invoice Operations

```bash
# List invoices
GET /api/invoices?limit=50&skip=0&status=pending

# Get single invoice
GET /api/invoices/:id

# Create invoice
POST /api/invoices
{
  "customer_id": "uuid",
  "items": [...],
  "due_date": "2023-12-31",
  "currency": "USD"
}

# Update invoice
PUT /api/invoices/:id

# Delete invoice
DELETE /api/invoices/:id

# Verify payment
POST /api/invoices/:id/verify
{
  "verification_status": "verified",
  "verified_by": "user_id",
  "verification_note": "Payment confirmed"
}

# Generate PDF
GET /api/invoices/:id/pdf
```

### Export

```bash
# Export to CSV
GET /api/invoices/export?format=csv&start_date=2023-01-01&end_date=2023-12-31

# Export to Excel
GET /api/invoices/export?format=xlsx&start_date=2023-01-01&end_date=2023-12-31
```

### Customer Operations

```bash
# List customers
GET /api/customers?limit=50&skip=0&search=company

# Create customer
POST /api/customers
{
  "name": "Customer Name",
  "email": "customer@example.com",
  "company": "Company Name"
}
```

## Integration with Facebook-Automation

### 1. Configure Facebook-Automation

Add to your `.env` file:

```env
INVOICE_API_URL=https://your-invoice-api.com
INVOICE_JWT_SECRET=same_secret_as_invoice_api
```

### 2. Get JWT Token

The Facebook-automation platform will automatically generate JWT tokens for API requests:

```javascript
// Get token from Facebook-automation
const response = await fetch('/api/integrations/invoice/auth/token', {
  headers: { 'Authorization': 'Bearer your_fb_automation_token' }
});

const { token } = await response.json();

// Use token for invoice API calls
const invoices = await fetch('https://your-invoice-api.com/api/invoices', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### 3. Webhook Integration (Optional)

If you want to receive webhooks from the invoice service:

```javascript
// In your Facebook-automation webhook handler
app.post('/api/webhooks/invoice', (req, res) => {
  const { event, invoice_id, tenant_id } = req.body;

  if (event === 'invoice.paid') {
    // Handle paid invoice
    console.log(`Invoice ${invoice_id} paid for tenant ${tenant_id}`);
  }

  res.json({ received: true });
});
```

## Security Features

### JWT Token Structure

Tokens include:
- `tenant_id` - For multi-tenant isolation
- `user_id` - User context (optional)
- `service` - Service identifier
- `exp` - Token expiration
- `jti` - Unique token ID

### Tenant Isolation

All database operations automatically filter by `tenant_id` to prevent cross-tenant data access.

### Rate Limiting

- 1000 requests per 15 minutes per IP
- Configurable limits in middleware

### Input Validation

- All inputs validated using Joi schemas
- SQL injection protection via parameterized queries
- XSS protection via Helmet middleware

## Development

### Project Structure

```
general-invoice/
├── server.js              # Main server file
├── auth.js                # JWT authentication middleware
├── routes/
│   ├── invoices.js        # Invoice CRUD operations
│   └── customers.js       # Customer operations
├── controllers/
│   └── exportController.js # Export functionality
├── db/
│   └── index.js           # Database connection
├── migrations/            # Database migrations
├── tests/                 # Test files
└── package.json
```

### Running Tests

```bash
npm test
```

### Linting

```bash
npm run lint
```

## Deployment

### Railway Deployment

1. Connect your repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on push

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
```

## Troubleshooting

### Common Issues

1. **JWT Secret Not Configured**
   ```
   Error: JWT secret not configured
   ```
   Solution: Set `INVOICE_JWT_SECRET` in environment variables

2. **Database Connection Failed**
   ```
   Error: connect ECONNREFUSED
   ```
   Solution: Check `DATABASE_URL` and ensure PostgreSQL is running

3. **CORS Issues**
   ```
   Error: CORS policy
   ```
   Solution: Set correct `FRONTEND_URL` in environment variables

### Debugging

Enable debug logging:

```env
NODE_ENV=development
DEBUG=invoice:*
```

## Support

For issues related to:
- **JWT Integration**: Check token generation in Facebook-automation
- **Database**: Verify PostgreSQL connection and table structure
- **API Compatibility**: Ensure endpoint URLs match Facebook-automation expectations

## License

MIT License - see LICENSE file for details.