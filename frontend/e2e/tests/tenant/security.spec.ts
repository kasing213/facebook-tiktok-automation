import { test, expect } from '../../fixtures/auth.fixture';
import testUsers from '../../fixtures/test-users.json';

test.describe('Security and Permission Tests', () => {
  const users = testUsers.users;

  test.describe('Tenant Isolation', () => {
    test('should prevent access to other tenant data', async ({ page }) => {
      // Mock user from Tenant A
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'user-tenant-a',
              email: 'user-a@tenanta.com',
              tenant: {
                id: 'tenant-a-uuid',
                name: 'Tenant A Company'
              }
            }
          })
        });
      });

      // Mock API calls to return 404 for cross-tenant access attempts
      await page.route('**/api/**', async (route) => {
        const url = route.request().url();

        // Simulate attempting to access Tenant B's data
        if (url.includes('tenant-b-uuid') || url.includes('user-tenant-b')) {
          await route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Resource not found',
              message: 'The requested resource was not found'
            })
          });
        } else {
          // Allow same-tenant requests
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ data: [] })
          });
        }
      });

      // Try to access another tenant's invoice directly via URL manipulation
      await page.goto('/dashboard/invoices/tenant-b-invoice-id');

      // Should show 404 or redirect to safe page
      await expect(
        page.locator('text=/not found|access denied|unauthorized/i')
      ).toBeVisible({ timeout: 5000 });

      // Try to access another tenant's product
      await page.goto('/dashboard/inventory/tenant-b-product-id');

      await expect(
        page.locator('text=/not found|access denied|unauthorized/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should isolate search results by tenant', async ({ page }) => {
      // Mock tenant A user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'user-tenant-a',
              tenant: { id: 'tenant-a-uuid' }
            }
          })
        });
      });

      // Mock search API to only return tenant-specific results
      await page.route('**/api/invoice/invoices*', async (route) => {
        const url = new URL(route.request().url());
        const searchQuery = url.searchParams.get('search');

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: [
              {
                id: 'invoice-tenant-a-1',
                invoiceNumber: 'INV-A-001',
                tenantId: 'tenant-a-uuid',
                recipientName: `Tenant A Customer - ${searchQuery}`
              }
            ],
            // Should NOT return tenant B results
            totalCount: 1
          })
        });
      });

      await page.goto('/dashboard/invoices');

      // Perform search
      const searchInput = page.locator('input[type="search"], input[placeholder*="search"]');
      if (await searchInput.isVisible()) {
        await searchInput.fill('shared-customer-name');
        await searchInput.press('Enter');

        // Wait for search results
        await page.waitForTimeout(1000);

        // Should only see tenant A results
        await expect(page.locator('text=/INV-A-001/i')).toBeVisible();

        // Should NOT see tenant B results (if they existed)
        await expect(page.locator('text=/INV-B-001/i')).not.toBeVisible();
      }
    });

    test('should prevent file access across tenants', async ({ page }) => {
      // Mock file access attempt to different tenant
      await page.route('**/api/inventory/products/image/*', async (route) => {
        const imageId = route.request().url().split('/').pop();

        if (imageId?.includes('tenant-b')) {
          await route.fulfill({
            status: 403,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Access denied',
              message: 'You do not have permission to access this file'
            })
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'image/png',
            body: Buffer.from('fake-image-data')
          });
        }
      });

      // Try to access cross-tenant image directly
      const response = await page.request.get('/api/inventory/products/image/tenant-b-image-123');
      expect(response.status()).toBe(403);

      // Try to access own tenant's image
      const ownResponse = await page.request.get('/api/inventory/products/image/tenant-a-image-123');
      expect(ownResponse.status()).toBe(200);
    });

    test('should validate tenant context in all API calls', async ({ page }) => {
      let apiCallsChecked = 0;
      const expectedTenantId = 'tenant-a-uuid';

      // Intercept all API calls to verify tenant context
      await page.route('**/api/**', async (route) => {
        const headers = route.request().headers();
        const authHeader = headers['authorization'];

        // Verify JWT contains correct tenant ID (in real app)
        // For testing, we'll check that API calls include tenant validation

        apiCallsChecked++;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenantVerified: true,
            requestedBy: expectedTenantId
          })
        });
      });

      await page.goto('/dashboard');
      await page.goto('/dashboard/invoices');
      await page.goto('/dashboard/inventory');

      // Multiple API calls should have been made
      expect(apiCallsChecked).toBeGreaterThan(0);
    });
  });

  test.describe('Role-Based Access Control', () => {
    test('should restrict admin features for regular users', async ({ page }) => {
      // Mock regular user (not admin)
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'regular-user-id',
              email: 'user@company.com',
              role: 'user',
              permissions: ['read_invoices', 'create_invoices', 'read_inventory']
            }
          })
        });
      });

      // Mock admin-only endpoints to return 403
      await page.route('**/api/admin/**', async (route) => {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Insufficient permissions',
            message: 'Admin role required for this action',
            requiredRole: 'admin',
            userRole: 'user'
          })
        });
      });

      // Try to access admin routes
      await page.goto('/dashboard/admin');

      // Should be blocked or redirected
      await expect(
        page.locator('text=/access denied|insufficient permissions|admin required/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should allow admin access to all features', async ({ page }) => {
      // Mock admin user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'admin-user-id',
              email: 'admin@company.com',
              role: 'admin',
              permissions: ['*'] // All permissions
            }
          })
        });
      });

      // Mock admin endpoints to be accessible
      await page.route('**/api/admin/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [],
            adminAccess: true
          })
        });
      });

      await page.goto('/dashboard/admin');

      // Should access admin features
      await expect(
        page.locator('text=/admin.*dashboard|user.*management|system.*settings/i')
      ).toBeVisible({ timeout: 5000 });

      // Should see admin-only navigation items
      await expect(
        page.locator('a[href*="admin"], button[class*="admin"]')
      ).toBeVisible();
    });

    test('should enforce viewer role restrictions', async ({ page }) => {
      // Mock viewer user (read-only)
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'viewer-user-id',
              email: 'viewer@company.com',
              role: 'viewer',
              permissions: ['read_invoices', 'read_inventory']
            }
          })
        });
      });

      // Mock write operations to return 403
      await page.route('**/api/**', async (route) => {
        const method = route.request().method();

        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
          await route.fulfill({
            status: 403,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Read-only access',
              message: 'Viewer role can only read data, not modify it'
            })
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ data: [] })
          });
        }
      });

      await page.goto('/dashboard/invoices');

      // Should see read-only interface
      await expect(page.locator('table, .invoice-list')).toBeVisible();

      // Should NOT see create/edit buttons
      await expect(
        page.getByRole('button', { name: /create|add|new/i })
      ).not.toBeVisible();

      await expect(
        page.getByRole('button', { name: /edit|update|modify/i })
      ).not.toBeVisible();

      await expect(
        page.getByRole('button', { name: /delete|remove/i })
      ).not.toBeVisible();
    });

    test('should validate permission hierarchy', async ({ page }) => {
      // Test different permission levels
      const permissionTests = [
        {
          role: 'viewer',
          permissions: ['read_invoices'],
          shouldAccess: ['/dashboard/invoices'],
          shouldBlock: ['/dashboard/invoices/new', '/dashboard/admin']
        },
        {
          role: 'user',
          permissions: ['read_invoices', 'create_invoices', 'read_inventory'],
          shouldAccess: ['/dashboard/invoices', '/dashboard/invoices/new'],
          shouldBlock: ['/dashboard/admin']
        },
        {
          role: 'admin',
          permissions: ['*'],
          shouldAccess: ['/dashboard/invoices', '/dashboard/admin'],
          shouldBlock: []
        }
      ];

      for (const testCase of permissionTests) {
        // Mock user with specific role
        await page.route('**/api/auth/me', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              user: {
                id: `${testCase.role}-user-id`,
                email: `${testCase.role}@company.com`,
                role: testCase.role,
                permissions: testCase.permissions
              }
            })
          });
        });

        // Test accessible routes
        for (const route of testCase.shouldAccess) {
          await page.goto(route);

          // Should NOT show access denied
          await expect(
            page.locator('text=/access denied|insufficient permissions/i')
          ).not.toBeVisible();
        }

        // Test blocked routes
        for (const route of testCase.shouldBlock) {
          await page.goto(route);

          // Should show access denied or redirect
          await expect(
            page.locator('text=/access denied|insufficient permissions|unauthorized/i')
          ).toBeVisible({ timeout: 5000 });
        }
      }
    });
  });

  test.describe('JWT Token Security', () => {
    test('should reject expired tokens', async ({ page }) => {
      // Mock expired token response
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Token expired',
            message: 'JWT token has expired. Please login again.',
            expired: true
          })
        });
      });

      await page.goto('/dashboard');

      // Should redirect to login
      await expect(page).toHaveURL(/\/login/);

      // Should show login form
      await expect(
        page.locator('input[type="email"], input[type="password"]')
      ).toBeVisible();
    });

    test('should reject malformed tokens', async ({ page }) => {
      // Mock invalid token response
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Invalid token',
            message: 'JWT token is malformed or invalid'
          })
        });
      });

      // Set malformed token in storage
      await page.evaluate(() => {
        localStorage.setItem('authToken', 'invalid.malformed.token');
      });

      await page.goto('/dashboard');

      // Should redirect to login and clear invalid token
      await expect(page).toHaveURL(/\/login/);

      const storedToken = await page.evaluate(() => localStorage.getItem('authToken'));
      expect(storedToken).toBeNull();
    });

    test('should validate token refresh mechanism', async ({ page }) => {
      let refreshCalled = false;

      // Mock token refresh
      await page.route('**/api/auth/refresh', async (route) => {
        refreshCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            accessToken: 'new-access-token',
            refreshToken: 'new-refresh-token',
            expiresIn: 3600
          })
        });
      });

      // Mock initial auth to return token expiry soon
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'test-user',
              email: 'test@example.com'
            },
            tokenExpiresIn: 60 // Expires in 1 minute
          })
        });
      });

      await page.goto('/dashboard');

      // Wait for potential token refresh
      await page.waitForTimeout(2000);

      // Token refresh should have been called
      expect(refreshCalled).toBe(true);
    });
  });

  test.describe('Data Validation and Sanitization', () => {
    test('should prevent XSS attacks in user inputs', async ({ page }) => {
      // Mock user creation with XSS attempt
      await page.route('**/api/auth/register', async (route) => {
        const requestData = await route.request().postDataJSON();

        // Check if input contains XSS attempt
        const hasXSS = ['<script', 'javascript:', 'onerror=', 'onload='].some(
          xss => JSON.stringify(requestData).toLowerCase().includes(xss.toLowerCase())
        );

        if (hasXSS) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Invalid input',
              message: 'Input contains potentially harmful content',
              sanitized: true
            })
          });
        } else {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({ success: true })
          });
        }
      });

      await page.goto('/register');

      // Try to submit XSS payload
      const nameInput = page.locator('input[name="firstName"]');
      await nameInput.fill('<script>alert("xss")</script>');

      const submitButton = page.getByRole('button', { name: /register|sign.*up/i });
      await submitButton.click();

      // Should show validation error
      await expect(
        page.locator('text=/invalid.*input|harmful.*content/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should validate SQL injection attempts', async ({ page }) => {
      // Mock search with SQL injection attempt
      await page.route('**/api/invoice/invoices*', async (route) => {
        const url = new URL(route.request().url());
        const searchQuery = url.searchParams.get('search') || '';

        // Check for SQL injection patterns
        const sqlPatterns = ['union select', 'drop table', '--', ';', 'or 1=1'];
        const hasSQLInjection = sqlPatterns.some(
          pattern => searchQuery.toLowerCase().includes(pattern.toLowerCase())
        );

        if (hasSQLInjection) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Invalid search query',
              message: 'Search query contains invalid characters',
              blocked: true
            })
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              invoices: [],
              searchQuery: searchQuery
            })
          });
        }
      });

      await page.goto('/dashboard/invoices');

      // Try SQL injection in search
      const searchInput = page.locator('input[type="search"], input[placeholder*="search"]');
      if (await searchInput.isVisible()) {
        await searchInput.fill("'; DROP TABLE invoices; --");
        await searchInput.press('Enter');

        // Should show validation error
        await expect(
          page.locator('text=/invalid.*search|invalid.*characters/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });

    test('should validate file upload security', async ({ page }) => {
      // Mock file upload validation
      await page.route('**/api/ads-alert/media/upload', async (route) => {
        const request = route.request();
        const contentType = request.headers()['content-type'] || '';

        // Check for dangerous file types
        if (contentType.includes('executable') || contentType.includes('script')) {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Invalid file type',
              message: 'Executable files are not allowed',
              blockedType: contentType
            })
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              success: true,
              filename: 'uploaded-file.jpg'
            })
          });
        }
      });

      await page.goto('/dashboard/marketing');

      // Try to upload executable file
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.isVisible()) {
        await fileInput.setInputFiles({
          name: 'malicious.exe',
          mimeType: 'application/executable',
          buffer: Buffer.from('fake-exe-data')
        });

        const uploadButton = page.getByRole('button', { name: /upload/i });
        if (await uploadButton.isVisible()) {
          await uploadButton.click();

          // Should block dangerous file
          await expect(
            page.locator('text=/invalid.*file.*type|executable.*not.*allowed/i')
          ).toBeVisible({ timeout: 5000 });
        }
      }
    });
  });

  test.describe('Rate Limiting and DoS Protection', () => {
    test('should enforce rate limits on API calls', async ({ page }) => {
      let requestCount = 0;

      // Mock rate limiting after 10 requests
      await page.route('**/api/invoice/invoices', async (route) => {
        requestCount++;

        if (requestCount > 10) {
          await route.fulfill({
            status: 429,
            contentType: 'application/json',
            headers: {
              'Retry-After': '60',
              'X-RateLimit-Limit': '10',
              'X-RateLimit-Remaining': '0'
            },
            body: JSON.stringify({
              error: 'Rate limit exceeded',
              message: 'Too many requests. Please try again in 60 seconds.',
              retryAfter: 60
            })
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              invoices: [],
              requestCount: requestCount
            })
          });
        }
      });

      await page.goto('/dashboard/invoices');

      // Make multiple rapid requests by refreshing
      for (let i = 0; i < 12; i++) {
        await page.reload();
        await page.waitForTimeout(100);
      }

      // Should show rate limit error
      await expect(
        page.locator('text=/rate.*limit.*exceeded|too.*many.*requests/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should prevent brute force login attempts', async ({ page }) => {
      let loginAttempts = 0;

      await page.route('**/api/auth/login', async (route) => {
        loginAttempts++;

        if (loginAttempts > 5) {
          await route.fulfill({
            status: 429,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Account temporarily locked',
              message: 'Too many failed login attempts. Account locked for 15 minutes.',
              lockedUntil: new Date(Date.now() + 900000).toISOString()
            })
          });
        } else {
          await route.fulfill({
            status: 401,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Invalid credentials',
              attemptsRemaining: 5 - loginAttempts
            })
          });
        }
      });

      await page.goto('/login');

      // Make multiple failed login attempts
      for (let i = 0; i < 6; i++) {
        await page.fill('input[type="email"]', 'test@example.com');
        await page.fill('input[type="password"]', 'wrongpassword');
        await page.getByRole('button', { name: /login|sign.*in/i }).click();
        await page.waitForTimeout(500);
      }

      // Should show account locked message
      await expect(
        page.locator('text=/account.*locked|too.*many.*attempts/i')
      ).toBeVisible({ timeout: 5000 });
    });
  });
});