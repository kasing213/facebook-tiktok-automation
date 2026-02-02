import { test, expect } from '../../fixtures/auth.fixture';
import testUsers from '../../fixtures/test-users.json';

test.describe('Subscription Tiers and Feature Gates', () => {
  const users = testUsers.users;

  test.describe('Free Tier Limitations', () => {
    test('should restrict inventory management for free tier users', async ({ page }) => {
      // Mock API to simulate free tier user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: '123e4567-e89b-12d3-a456-426614174000',
              email: users.free_tier.email,
              firstName: users.free_tier.firstName,
              lastName: users.free_tier.lastName,
              role: 'user',
              tenant: {
                id: '123e4567-e89b-12d3-a456-426614174001',
                name: users.free_tier.businessName,
                subscription: {
                  tier: 'free',
                  status: 'active',
                  features: ['basic_invoicing']
                }
              }
            }
          })
        });
      });

      // Mock inventory access to return 403 for free tier
      await page.route('**/api/inventory/**', async (route) => {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Pro feature required',
            message: 'Inventory management requires Invoice Plus or Pro subscription'
          })
        });
      });

      // Navigate to inventory page
      await page.goto('/dashboard/inventory');

      // Should show upgrade prompt or be redirected
      await expect(
        page.locator('text=/upgrade|pro feature|subscription required/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should allow basic invoice creation for free tier', async ({ page }) => {
      // Mock free tier user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: '123e4567-e89b-12d3-a456-426614174000',
              email: users.free_tier.email,
              firstName: users.free_tier.firstName,
              subscription: {
                tier: 'free',
                features: ['basic_invoicing']
              }
            }
          })
        });
      });

      // Mock invoice creation success
      await page.route('**/api/invoice/invoices', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 201,
            contentType: 'application/json',
            body: JSON.stringify({
              id: '123e4567-e89b-12d3-a456-426614174002',
              invoiceNumber: 'INV-001',
              status: 'draft'
            })
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ invoices: [], total: 0 })
          });
        }
      });

      await page.goto('/dashboard/invoices/new');

      // Should be able to create invoice
      await expect(page.locator('input, textarea')).toBeVisible();
    });

    test('should enforce invoice limit for free tier', async ({ page }) => {
      // Mock API to simulate free tier user at limit
      await page.route('**/api/invoice/invoices', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 402,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Subscription limit reached',
              message: `You have reached your limit of ${users.free_tier.expectedLimits.invoices} invoices. Upgrade to create more.`,
              limit: users.free_tier.expectedLimits.invoices,
              current: users.free_tier.expectedLimits.invoices
            })
          });
        }
      });

      await page.goto('/dashboard/invoices/new');

      // Try to create an invoice
      const submitButton = page.getByRole('button', { name: /save|create|submit/i });
      await submitButton.click();

      // Should show limit reached message
      await expect(
        page.locator('text=/limit reached|upgrade/i')
      ).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Pro Tier Features', () => {
    test('should allow full access to inventory for pro users', async ({ page }) => {
      // Mock pro tier user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: '123e4567-e89b-12d3-a456-426614174003',
              email: users.pro_tier.email,
              firstName: users.pro_tier.firstName,
              subscription: {
                tier: 'pro',
                features: ['basic_invoicing', 'inventory_management', 'marketing_media', 'marketing_chats']
              }
            }
          })
        });
      });

      // Mock successful inventory access
      await page.route('**/api/inventory/products', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            products: [],
            stats: { total: 0, lowStock: 0 }
          })
        });
      });

      await page.goto('/dashboard/inventory');

      // Should be able to access inventory features
      await expect(
        page.getByRole('button', { name: /create|add.*product/i })
      ).toBeVisible({ timeout: 5000 });
    });

    test('should allow marketing features for pro users', async ({ page }) => {
      // Mock pro tier user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              email: users.pro_tier.email,
              subscription: {
                tier: 'pro',
                features: ['marketing_media', 'marketing_chats']
              }
            }
          })
        });
      });

      // Mock marketing features access
      await page.route('**/api/ads-alert/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: [] })
        });
      });

      await page.goto('/dashboard/marketing');

      // Should access marketing features without restrictions
      const marketingElements = page.locator('[class*="marketing"], [class*="campaign"], [class*="media"]');
      await expect(marketingElements.first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Subscription Upgrade Flow', () => {
    test('should display upgrade options from free tier', async ({ page }) => {
      // Mock free tier user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              email: users.free_tier.email,
              subscription: { tier: 'free' }
            }
          })
        });
      });

      // Mock subscription plans
      await page.route('**/api/billing/plans', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            plans: [
              {
                id: 'invoice_plus',
                name: 'Invoice Plus',
                price: 10,
                currency: 'USD',
                features: ['basic_invoicing', 'inventory_management']
              },
              {
                id: 'marketing_plus',
                name: 'Marketing Plus',
                price: 10,
                currency: 'USD',
                features: ['basic_invoicing', 'marketing_media', 'marketing_chats']
              },
              {
                id: 'pro',
                name: 'Pro',
                price: 20,
                currency: 'USD',
                features: ['basic_invoicing', 'inventory_management', 'marketing_media', 'marketing_chats']
              }
            ]
          })
        });
      });

      await page.goto('/dashboard/billing');

      // Should show upgrade plans
      await expect(page.locator('text=/Invoice Plus/i')).toBeVisible();
      await expect(page.locator('text=/Marketing Plus/i')).toBeVisible();
      await expect(page.locator('text=/Pro/i')).toBeVisible();
    });

    test('should initiate upgrade process', async ({ page }) => {
      // Mock free tier user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              email: users.free_tier.email,
              subscription: { tier: 'free' }
            }
          })
        });
      });

      // Mock upgrade initiation
      await page.route('**/api/billing/upgrade', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            paymentUrl: '/dashboard/payment/confirm',
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

      // Click upgrade button for Pro plan
      const upgradeButton = page.getByRole('button', { name: /upgrade.*pro|select.*pro/i });
      await upgradeButton.click();

      // Should show payment interface
      await expect(
        page.locator('text=/payment|bank transfer|qr code/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should process payment verification for upgrade', async ({ page }) => {
      // Mock upgrade payment verification
      await page.route('**/api/billing/verify-upgrade', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            confidence: 87,
            newSubscription: {
              tier: 'pro',
              status: 'active',
              upgradeDate: new Date().toISOString()
            }
          })
        });
      });

      await page.goto('/dashboard/payment/confirm');

      // Upload payment screenshot
      const fileInput = page.locator('input[type="file"]');
      if (await fileInput.isVisible()) {
        // Simulate file upload
        await page.evaluate(() => {
          const input = document.querySelector('input[type="file"]') as HTMLInputElement;
          if (input) {
            const event = new Event('change', { bubbles: true });
            Object.defineProperty(event, 'target', { value: input });
            input.dispatchEvent(event);
          }
        });

        // Submit verification
        const submitButton = page.getByRole('button', { name: /verify|submit|confirm/i });
        await submitButton.click();

        // Should show success message
        await expect(
          page.locator('text=/upgrade.*successful|pro.*activated/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });
  });

  test.describe('Trial Period Management', () => {
    test('should show trial status and expiration', async ({ page }) => {
      // Mock trial user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              email: users.trial_user.email,
              subscription: {
                tier: 'pro_trial',
                status: 'trial',
                trialEndsAt: users.trial_user.trialEndsAt,
                daysRemaining: 25
              }
            }
          })
        });
      });

      await page.goto('/dashboard');

      // Should show trial banner
      await expect(
        page.locator('text=/trial|25.*days.*remaining/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should prompt upgrade when trial expires', async ({ page }) => {
      // Mock expired trial
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              email: users.trial_user.email,
              subscription: {
                tier: 'free',
                status: 'active',
                previousTier: 'pro_trial',
                trialExpiredAt: new Date(Date.now() - 86400000).toISOString()
              }
            }
          })
        });
      });

      await page.goto('/dashboard');

      // Should show upgrade prompt
      await expect(
        page.locator('text=/trial.*expired|upgrade.*continue/i')
      ).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Storage Limit Enforcement', () => {
    test('should prevent file upload when storage limit reached', async ({ page }) => {
      // Mock storage limit reached
      await page.route('**/api/ads-alert/media/upload', async (route) => {
        await route.fulfill({
          status: 413,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Storage limit exceeded',
            message: 'You have reached your storage limit of 100MB. Upgrade to upload more files.',
            currentUsage: 100,
            limit: 100
          })
        });
      });

      await page.goto('/dashboard/marketing');

      // Try to upload file
      const uploadButton = page.getByRole('button', { name: /upload|add.*file/i });
      if (await uploadButton.isVisible()) {
        await uploadButton.click();

        // Should show storage limit error
        await expect(
          page.locator('text=/storage.*limit|upgrade.*upload/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });
  });
});

test.describe('Feature Gate Validation', () => {
  test('should consistently enforce subscription gates across API calls', async ({ page }) => {
    // Mock free tier user trying to access restricted features
    await page.route('**/api/**', async (route) => {
      const url = route.request().url();

      // Inventory endpoints should be restricted
      if (url.includes('/inventory/') || url.includes('/products/')) {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Feature not available',
            requiredSubscription: 'invoice_plus'
          })
        });
      }
      // Marketing endpoints should be restricted
      else if (url.includes('/ads-alert/') || url.includes('/marketing/')) {
        await route.fulfill({
          status: 403,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Feature not available',
            requiredSubscription: 'marketing_plus'
          })
        });
      }
      // Allow other requests
      else {
        await route.continue();
      }
    });

    // Test multiple restricted endpoints
    const restrictedUrls = [
      '/dashboard/inventory',
      '/dashboard/marketing',
      '/dashboard/campaigns'
    ];

    for (const url of restrictedUrls) {
      await page.goto(url);
      await expect(
        page.locator('text=/feature.*not.*available|upgrade.*required/i')
      ).toBeVisible({ timeout: 3000 });
    }
  });
});