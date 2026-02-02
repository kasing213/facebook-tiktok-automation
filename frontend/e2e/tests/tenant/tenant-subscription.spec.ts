import { test, expect } from '../../fixtures/auth.fixture';
import testUsers from '../../fixtures/test-users.json';

/**
 * Tenant-Specific Subscription Tests
 *
 * These tests validate subscription functionality within specific tenant contexts.
 * They assume core authentication is working (tested in core/auth-core.spec.ts).
 */
test.describe('Tenant Subscription Management', () => {
  const users = testUsers.users;

  test.describe('Free Tier Tenant Limitations', () => {
    test('should enforce free tier limits for tenant operations', async ({ page }) => {
      // Mock free tier tenant user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'free-tenant-user-123',
              email: users.free_tier.email,
              firstName: users.free_tier.firstName,
              lastName: users.free_tier.lastName,
              role: 'user',
              tenant: {
                id: 'tenant-free-tier-uuid',
                name: users.free_tier.businessName,
                subscription: {
                  tier: 'free',
                  status: 'active',
                  features: ['basic_invoicing'],
                  limits: users.free_tier.expectedLimits
                }
              }
            }
          })
        });
      });

      // Mock inventory access restriction for free tier
      await page.route('**/api/inventory/**', async (route) => {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Feature not available',
            message: 'Inventory management requires Invoice Plus or Pro subscription',
            requiredTier: 'invoice_plus',
            currentTier: 'free'
          })
        });
      });

      await page.goto('/dashboard/inventory');

      // Should show upgrade prompt for free tier tenant
      await expect(
        page.locator('text=/upgrade.*required|feature.*not.*available|invoice.*plus.*required/i')
      ).toBeVisible({ timeout: 5000 });

      // Should show current tier information
      await expect(
        page.locator('text=/free.*tier|current.*plan.*free/i')
      ).toBeVisible();
    });

    test('should track usage limits for free tier tenant', async ({ page }) => {
      // Mock free tier user approaching limits
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'free-tenant-user-123',
              tenant: {
                id: 'tenant-free-tier-uuid',
                subscription: {
                  tier: 'free',
                  limits: users.free_tier.expectedLimits,
                  usage: {
                    invoices: 18, // Close to 20 limit
                    products: 45, // Close to 50 limit
                    customers: 20  // Close to 25 limit
                  }
                }
              }
            }
          })
        });
      });

      // Mock invoice creation near limit
      await page.route('**/api/invoice/invoices', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 402, // Payment Required
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Limit approaching',
              message: 'You have 2 invoices remaining on your free plan. Upgrade to create more.',
              currentUsage: 18,
              limit: 20,
              remaining: 2
            })
          });
        }
      });

      await page.goto('/dashboard/invoices/new');

      // Try to create invoice near limit
      const submitButton = page.getByRole('button', { name: /save|create|submit/i });
      if (await submitButton.isVisible()) {
        await submitButton.click();

        // Should show limit warning with upgrade option
        await expect(
          page.locator('text=/2.*invoices.*remaining|limit.*approaching|upgrade.*create.*more/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });

    test('should allow basic invoicing features for free tier', async ({ page }) => {
      // Mock successful basic invoice operations for free tier
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'free-tenant-user-123',
              tenant: {
                id: 'tenant-free-tier-uuid',
                subscription: {
                  tier: 'free',
                  features: ['basic_invoicing']
                }
              }
            }
          })
        });
      });

      await page.route('**/api/invoice/invoices', async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              invoices: [
                {
                  id: 'free-tier-invoice-1',
                  invoiceNumber: 'INV-FREE-001',
                  tenantId: 'tenant-free-tier-uuid',
                  recipientName: 'Free Tier Customer',
                  amount: 500.00,
                  status: 'pending'
                }
              ],
              totalCount: 1
            })
          });
        }
      });

      await page.goto('/dashboard/invoices');

      // Should display invoices for free tier tenant
      await expect(page.locator('text=/INV-FREE-001/i')).toBeVisible({ timeout: 5000 });
      await expect(page.locator('text=/Free Tier Customer/i')).toBeVisible();

      // Should be able to view invoice details
      const invoiceRow = page.locator('text=/INV-FREE-001/i');
      await invoiceRow.click();

      // Should navigate to invoice detail without restrictions
      await expect(page).toHaveURL(/\/invoices\/free-tier-invoice-1/);
    });
  });

  test.describe('Pro Tier Tenant Features', () => {
    test('should enable all features for pro tier tenant', async ({ page }) => {
      // Mock pro tier tenant user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'pro-tenant-user-456',
              email: users.pro_tier.email,
              tenant: {
                id: 'tenant-pro-tier-uuid',
                name: users.pro_tier.businessName,
                subscription: {
                  tier: 'pro',
                  status: 'active',
                  features: [
                    'basic_invoicing',
                    'inventory_management',
                    'marketing_media',
                    'marketing_chats',
                    'advanced_analytics'
                  ],
                  limits: users.pro_tier.expectedLimits
                }
              }
            }
          })
        });
      });

      // Mock successful inventory access for pro tier
      await page.route('**/api/inventory/products', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            products: [
              {
                id: 'pro-product-1',
                tenantId: 'tenant-pro-tier-uuid',
                name: 'Pro Product',
                sku: 'PRO-001',
                price: 299.99,
                stock: 100
              }
            ],
            stats: { total: 150, lowStock: 2 }
          })
        });
      });

      await page.goto('/dashboard/inventory');

      // Should access inventory without restrictions
      await expect(
        page.getByRole('button', { name: /create.*product|add.*product/i })
      ).toBeVisible({ timeout: 5000 });

      await expect(page.locator('text=/Pro Product/i')).toBeVisible();
      await expect(page.locator('text=/PRO-001/i')).toBeVisible();
    });

    test('should support advanced pro tier features', async ({ page }) => {
      // Mock pro tier with advanced features
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              tenant: {
                id: 'tenant-pro-tier-uuid',
                subscription: {
                  tier: 'pro',
                  features: ['advanced_analytics', 'bulk_operations', 'api_access']
                }
              }
            }
          })
        });
      });

      // Mock advanced analytics endpoint
      await page.route('**/api/analytics/advanced', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenantId: 'tenant-pro-tier-uuid',
            metrics: {
              revenueGrowth: 25.5,
              customerRetention: 85.2,
              averageInvoiceValue: 1250.00
            },
            charts: {
              monthlyRevenue: [1000, 1200, 1500, 1800, 2000],
              customerGrowth: [10, 15, 22, 35, 42]
            }
          })
        });
      });

      await page.goto('/dashboard/analytics');

      // Should display advanced analytics for pro tier
      await expect(page.locator('text=/25.5%|revenue.*growth/i')).toBeVisible();
      await expect(page.locator('text=/85.2%|customer.*retention/i')).toBeVisible();
      await expect(page.locator('text=/1.*250|average.*invoice/i')).toBeVisible();
    });

    test('should handle bulk operations for pro tier', async ({ page }) => {
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              tenant: {
                id: 'tenant-pro-tier-uuid',
                subscription: {
                  tier: 'pro',
                  features: ['bulk_operations']
                }
              }
            }
          })
        });
      });

      // Mock bulk export endpoint
      await page.route('**/api/invoice/export/bulk', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
          headers: {
            'Content-Disposition': 'attachment; filename="invoices-bulk-export.xlsx"'
          },
          body: Buffer.from('fake-excel-data')
        });
      });

      await page.goto('/dashboard/invoices');

      // Should show bulk operation buttons for pro tier
      const bulkExportButton = page.getByRole('button', { name: /bulk.*export|export.*all/i });

      if (await bulkExportButton.isVisible()) {
        const downloadPromise = page.waitForEvent('download');
        await bulkExportButton.click();

        const download = await downloadPromise;
        expect(download.suggestedFilename()).toContain('bulk-export');
      }
    });
  });

  test.describe('Tenant-Specific Upgrade Flow', () => {
    test('should handle tenant upgrade from free to pro', async ({ page }) => {
      // Mock free tier tenant
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              tenant: {
                id: 'tenant-upgrade-test-uuid',
                name: 'Upgrade Test Company',
                subscription: {
                  tier: 'free',
                  canUpgrade: true
                }
              }
            }
          })
        });
      });

      // Mock upgrade initiation
      await page.route('**/api/billing/upgrade', async (route) => {
        const requestData = await route.request().postDataJSON();

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenantId: 'tenant-upgrade-test-uuid',
            upgradeTo: requestData.plan,
            paymentDetails: {
              amount: requestData.plan === 'pro' ? 20.00 : 10.00,
              currency: 'USD',
              method: 'bank_transfer'
            },
            qrCode: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==',
            bankDetails: {
              bank: 'ABA Bank',
              account: '001234567',
              accountName: 'Facebook Automation Ltd'
            }
          })
        });
      });

      await page.goto('/dashboard/billing');

      // Should show upgrade options
      const upgradeButton = page.getByRole('button', { name: /upgrade.*pro|select.*pro/i });
      await upgradeButton.click();

      // Should show payment interface with tenant context
      await expect(
        page.locator('text=/upgrade.*test.*company|tenant.*upgrade/i')
      ).toBeVisible({ timeout: 5000 });

      await expect(
        page.locator('text=/aba.*bank|001234567/i')
      ).toBeVisible();

      await expect(page.locator('img[src*="data:image/png"]')).toBeVisible(); // QR code
    });

    test('should process tenant upgrade payment verification', async ({ page }) => {
      // Mock upgrade payment verification
      await page.route('**/api/billing/verify-upgrade', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenantId: 'tenant-upgrade-test-uuid',
            verificationResult: {
              success: true,
              confidence: 88,
              paymentAmount: 20.00,
              expectedAmount: 20.00,
              bank: 'ABA Bank',
              autoApproved: true
            },
            newSubscription: {
              tier: 'pro',
              status: 'active',
              activatedAt: new Date().toISOString(),
              features: ['basic_invoicing', 'inventory_management', 'marketing_media']
            }
          })
        });
      });

      await page.goto('/dashboard/payment/verify-upgrade');

      // Upload payment screenshot for tenant upgrade
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.isVisible()) {
        await fileInput.setInputFiles({
          name: 'tenant-upgrade-payment.png',
          mimeType: 'image/png',
          buffer: Buffer.from('fake-image-data')
        });

        const verifyButton = page.getByRole('button', { name: /verify|submit|confirm/i });
        await verifyButton.click();

        // Should show tenant upgrade success
        await expect(
          page.locator('text=/upgrade.*successful|pro.*activated.*company/i')
        ).toBeVisible({ timeout: 10000 });

        await expect(
          page.locator('text=/confidence.*88%|auto.*approved/i')
        ).toBeVisible();
      }
    });
  });

  test.describe('Trial Management for Tenants', () => {
    test('should handle tenant trial period', async ({ page }) => {
      // Mock trial tenant
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              tenant: {
                id: 'tenant-trial-uuid',
                name: 'Trial Company',
                subscription: {
                  tier: 'pro_trial',
                  status: 'trial',
                  trialEndsAt: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(), // 20 days
                  trialDaysRemaining: 20,
                  features: ['basic_invoicing', 'inventory_management', 'marketing_media']
                }
              }
            }
          })
        });
      });

      await page.goto('/dashboard');

      // Should show trial status for tenant
      await expect(
        page.locator('text=/trial.*company|20.*days.*remaining|trial.*period/i')
      ).toBeVisible({ timeout: 5000 });

      // Should show trial banner with tenant context
      await expect(
        page.locator('text=/trial.*expires|upgrade.*before.*trial.*ends/i')
      ).toBeVisible();
    });

    test('should handle expired trial for tenant', async ({ page }) => {
      // Mock expired trial tenant
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              tenant: {
                id: 'tenant-expired-trial-uuid',
                name: 'Expired Trial Company',
                subscription: {
                  tier: 'free',
                  status: 'active',
                  previousTier: 'pro_trial',
                  trialExpiredAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // Yesterday
                  features: ['basic_invoicing']
                }
              }
            }
          })
        });
      });

      await page.goto('/dashboard');

      // Should show trial expiration notice
      await expect(
        page.locator('text=/trial.*expired.*company|downgraded.*free/i')
      ).toBeVisible({ timeout: 5000 });

      // Should prompt for upgrade with tenant context
      await expect(
        page.getByRole('button', { name: /upgrade.*now|renew.*subscription/i })
      ).toBeVisible();
    });

    test('should extend trial period for tenant', async ({ page }) => {
      // Mock trial extension
      await page.route('**/api/billing/extend-trial', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenantId: 'tenant-trial-uuid',
            extendedBy: 14, // days
            newTrialEndDate: new Date(Date.now() + 34 * 24 * 60 * 60 * 1000).toISOString(),
            reason: 'customer_request'
          })
        });
      });

      await page.goto('/dashboard/billing');

      // Look for trial extension option
      const extendTrialButton = page.getByRole('button', { name: /extend.*trial|add.*days/i });

      if (await extendTrialButton.isVisible()) {
        await extendTrialButton.click();

        // Should show extension confirmation
        await expect(
          page.locator('text=/trial.*extended|14.*days.*added/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });
  });

  test.describe('Tenant Subscription Analytics', () => {
    test('should track tenant usage metrics', async ({ page }) => {
      // Mock tenant usage analytics
      await page.route('**/api/analytics/tenant/usage', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenantId: 'tenant-analytics-uuid',
            currentPeriod: {
              invoicesCreated: 45,
              productsManaged: 120,
              storageUsed: '1.2GB',
              apiCallsMade: 2500,
              telegramNotifications: 150
            },
            limits: {
              invoices: 200,
              products: 500,
              storage: '2GB',
              apiCalls: 10000,
              telegramNotifications: 1000
            },
            utilizationPercentages: {
              invoices: 22.5,
              products: 24.0,
              storage: 60.0,
              apiCalls: 25.0,
              telegramNotifications: 15.0
            }
          })
        });
      });

      await page.goto('/dashboard/analytics/usage');

      // Should show tenant-specific usage metrics
      await expect(page.locator('text=/45.*invoices.*created/i')).toBeVisible();
      await expect(page.locator('text=/120.*products.*managed/i')).toBeVisible();
      await expect(page.locator('text=/1\.2gb.*storage.*used/i')).toBeVisible();

      // Should show utilization percentages
      await expect(page.locator('text=/22\.5%|24\.0%|60\.0%/i')).toBeVisible();
    });

    test('should show tenant billing history', async ({ page }) => {
      // Mock tenant billing history
      await page.route('**/api/billing/tenant/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenantId: 'tenant-billing-uuid',
            billingHistory: [
              {
                id: 'bill-1',
                date: '2026-01-01T00:00:00Z',
                amount: 20.00,
                currency: 'USD',
                plan: 'pro',
                status: 'paid',
                method: 'bank_transfer'
              },
              {
                id: 'bill-2',
                date: '2025-12-01T00:00:00Z',
                amount: 20.00,
                currency: 'USD',
                plan: 'pro',
                status: 'paid',
                method: 'bank_transfer'
              }
            ],
            totalSpent: 140.00,
            averageMonthlySpend: 20.00
          })
        });
      });

      await page.goto('/dashboard/billing/history');

      // Should show tenant billing history
      await expect(page.locator('text=/\$20\.00/i')).toBeVisible();
      await expect(page.locator('text=/pro.*plan/i')).toBeVisible();
      await expect(page.locator('text=/total.*spent.*140/i')).toBeVisible();
    });
  });
});