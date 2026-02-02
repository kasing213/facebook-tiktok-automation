import { test as base } from '@playwright/test';
import testUsers from './test-users.json';

/**
 * Tenant-specific test fixture that extends the base auth fixture
 *
 * This fixture sets up tenant context for tests that require specific
 * tenant data and subscription states.
 */

export interface TenantTestContext {
  tenantId: string;
  tenantName: string;
  subscriptionTier: 'free' | 'invoice_plus' | 'marketing_plus' | 'pro' | 'pro_trial';
  features: string[];
  limits: Record<string, any>;
  usage?: Record<string, any>;
}

export interface TenantFixtures {
  freeTierTenant: TenantTestContext;
  invoicePlusTenant: TenantTestContext;
  marketingPlusTenant: TenantTestContext;
  proTierTenant: TenantTestContext;
  trialTenant: TenantTestContext;
  setupTenantAuth: (tenant: TenantTestContext) => Promise<void>;
}

export const test = base.extend<TenantFixtures>({
  freeTierTenant: async ({}, use) => {
    const tenant: TenantTestContext = {
      tenantId: 'tenant-free-tier-uuid-123',
      tenantName: testUsers.users.free_tier.businessName,
      subscriptionTier: 'free',
      features: ['basic_invoicing'],
      limits: testUsers.users.free_tier.expectedLimits,
      usage: {
        invoices: 5,
        products: 20,
        customers: 10,
        storage: '25MB'
      }
    };
    await use(tenant);
  },

  invoicePlusTenant: async ({}, use) => {
    const tenant: TenantTestContext = {
      tenantId: 'tenant-invoice-plus-uuid-456',
      tenantName: testUsers.users.invoice_plus.businessName,
      subscriptionTier: 'invoice_plus',
      features: ['basic_invoicing', 'inventory_management'],
      limits: testUsers.users.invoice_plus.expectedLimits,
      usage: {
        invoices: 85,
        products: 250,
        customers: 120,
        storage: '450MB'
      }
    };
    await use(tenant);
  },

  marketingPlusTenant: async ({}, use) => {
    const tenant: TenantTestContext = {
      tenantId: 'tenant-marketing-plus-uuid-789',
      tenantName: testUsers.users.marketing_plus.businessName,
      subscriptionTier: 'marketing_plus',
      features: ['basic_invoicing', 'marketing_media', 'marketing_chats'],
      limits: testUsers.users.marketing_plus.expectedLimits,
      usage: {
        invoices: 15,
        products: 30,
        customers: 20,
        promotions: 5,
        recipients: 250,
        storage: '300MB'
      }
    };
    await use(tenant);
  },

  proTierTenant: async ({}, use) => {
    const tenant: TenantTestContext = {
      tenantId: 'tenant-pro-tier-uuid-101',
      tenantName: testUsers.users.pro_tier.businessName,
      subscriptionTier: 'pro',
      features: [
        'basic_invoicing',
        'inventory_management',
        'marketing_media',
        'marketing_chats',
        'advanced_analytics',
        'bulk_operations',
        'api_access'
      ],
      limits: testUsers.users.pro_tier.expectedLimits,
      usage: {
        invoices: 150,
        products: 300,
        customers: 500,
        promotions: 12,
        recipients: 800,
        storage: '1.5GB'
      }
    };
    await use(tenant);
  },

  trialTenant: async ({}, use) => {
    const tenant: TenantTestContext = {
      tenantId: 'tenant-trial-uuid-202',
      tenantName: testUsers.users.trial_user.businessName,
      subscriptionTier: 'pro_trial',
      features: [
        'basic_invoicing',
        'inventory_management',
        'marketing_media',
        'marketing_chats'
      ],
      limits: testUsers.users.pro_tier.expectedLimits, // Same as pro during trial
      usage: {
        invoices: 25,
        products: 75,
        customers: 45,
        storage: '200MB'
      }
    };
    await use(tenant);
  },

  setupTenantAuth: async ({ page }, use) => {
    const setupAuth = async (tenant: TenantTestContext) => {
      // Mock authentication for specific tenant
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: `user-${tenant.tenantId}`,
              email: `user@${tenant.tenantName.toLowerCase().replace(/\s+/g, '')}.com`,
              firstName: 'Test',
              lastName: 'User',
              role: 'user',
              tenant: {
                id: tenant.tenantId,
                name: tenant.tenantName,
                subscription: {
                  tier: tenant.subscriptionTier,
                  status: tenant.subscriptionTier === 'pro_trial' ? 'trial' : 'active',
                  features: tenant.features,
                  limits: tenant.limits,
                  usage: tenant.usage,
                  ...(tenant.subscriptionTier === 'pro_trial' && {
                    trialEndsAt: testUsers.users.trial_user.trialEndsAt,
                    trialDaysRemaining: 25
                  })
                }
              }
            }
          })
        });
      });

      // Set up common API mocks based on tenant features
      await setupFeatureBasedMocks(page, tenant);
    };

    await use(setupAuth);
  }
});

/**
 * Set up API mocks based on tenant features and subscription tier
 */
async function setupFeatureBasedMocks(page: any, tenant: TenantTestContext) {
  // Mock dashboard stats based on tenant usage
  await page.route('**/api/dashboard/stats', async (route: any) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        invoices: {
          total: tenant.usage?.invoices || 0,
          pending: Math.floor((tenant.usage?.invoices || 0) * 0.3),
          paid: Math.floor((tenant.usage?.invoices || 0) * 0.6),
          overdue: Math.floor((tenant.usage?.invoices || 0) * 0.1)
        },
        products: {
          total: tenant.usage?.products || 0,
          lowStock: Math.floor((tenant.usage?.products || 0) * 0.1)
        },
        customers: {
          total: tenant.usage?.customers || 0,
          active: Math.floor((tenant.usage?.customers || 0) * 0.8)
        },
        revenue: {
          thisMonth: (tenant.usage?.invoices || 0) * 250,
          lastMonth: (tenant.usage?.invoices || 0) * 200
        }
      })
    });
  });

  // Mock inventory access based on features
  if (tenant.features.includes('inventory_management')) {
    await page.route('**/api/inventory/**', async (route: any) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            products: generateMockProducts(tenant),
            stats: {
              total: tenant.usage?.products || 0,
              lowStock: Math.floor((tenant.usage?.products || 0) * 0.1)
            }
          })
        });
      } else {
        // For POST/PUT/DELETE operations
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            tenantId: tenant.tenantId
          })
        });
      }
    });
  } else {
    // Block inventory access for tenants without the feature
    await page.route('**/api/inventory/**', async (route: any) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Feature not available',
          message: 'Inventory management requires Invoice Plus or Pro subscription',
          requiredFeature: 'inventory_management',
          currentTier: tenant.subscriptionTier
        })
      });
    });
  }

  // Mock marketing features access
  if (tenant.features.includes('marketing_media') || tenant.features.includes('marketing_chats')) {
    await page.route('**/api/ads-alert/**', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          campaigns: generateMockCampaigns(tenant),
          media: generateMockMedia(tenant),
          tenantId: tenant.tenantId
        })
      });
    });
  } else {
    // Block marketing access
    await page.route('**/api/ads-alert/**', async (route: any) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Feature not available',
          message: 'Marketing features require Marketing Plus or Pro subscription',
          requiredFeature: 'marketing_media',
          currentTier: tenant.subscriptionTier
        })
      });
    });
  }

  // Mock analytics based on tier
  if (tenant.features.includes('advanced_analytics')) {
    await page.route('**/api/analytics/**', async (route: any) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tenantId: tenant.tenantId,
          advanced: true,
          metrics: generateAdvancedMetrics(tenant)
        })
      });
    });
  }

  // Mock usage limits checking
  await page.route('**/api/usage/check/**', async (route: any) => {
    const url = route.request().url();
    const resource = url.split('/').pop(); // invoices, products, etc.

    const currentUsage = tenant.usage?.[resource] || 0;
    const limit = tenant.limits[resource];

    await route.fulfill({
      status: currentUsage >= limit ? 402 : 200, // 402 Payment Required if over limit
      contentType: 'application/json',
      body: JSON.stringify({
        resource: resource,
        currentUsage: currentUsage,
        limit: limit,
        remaining: Math.max(0, limit - currentUsage),
        canCreate: currentUsage < limit,
        tenantId: tenant.tenantId
      })
    });
  });
}

/**
 * Generate mock products based on tenant context
 */
function generateMockProducts(tenant: TenantTestContext) {
  const productCount = Math.min(tenant.usage?.products || 0, 10); // Limit to 10 for UI testing
  return Array.from({ length: productCount }, (_, i) => ({
    id: `${tenant.tenantId}-product-${i + 1}`,
    tenantId: tenant.tenantId,
    name: `${tenant.tenantName} Product ${i + 1}`,
    sku: `${tenant.subscriptionTier.toUpperCase()}-${String(i + 1).padStart(3, '0')}`,
    price: Math.floor(Math.random() * 1000) + 50,
    stock: Math.floor(Math.random() * 100) + 10,
    lowStockThreshold: 5
  }));
}

/**
 * Generate mock campaigns for marketing features
 */
function generateMockCampaigns(tenant: TenantTestContext) {
  if (!tenant.features.includes('marketing_media')) return [];

  const campaignCount = Math.min(tenant.usage?.promotions || 0, 5);
  return Array.from({ length: campaignCount }, (_, i) => ({
    id: `${tenant.tenantId}-campaign-${i + 1}`,
    tenantId: tenant.tenantId,
    name: `${tenant.tenantName} Campaign ${i + 1}`,
    status: ['active', 'paused', 'completed'][Math.floor(Math.random() * 3)],
    reach: Math.floor(Math.random() * 1000) + 100,
    engagement: Math.floor(Math.random() * 50) + 10
  }));
}

/**
 * Generate mock media files
 */
function generateMockMedia(tenant: TenantTestContext) {
  const mediaCount = Math.min(5, Math.floor((tenant.usage?.storage || '0MB').replace('MB', '') as any / 10));
  return Array.from({ length: mediaCount }, (_, i) => ({
    id: `${tenant.tenantId}-media-${i + 1}`,
    tenantId: tenant.tenantId,
    filename: `media-${i + 1}.jpg`,
    size: `${Math.floor(Math.random() * 5) + 1}MB`,
    type: 'image/jpeg',
    url: `https://example.com/media-${i + 1}.jpg`
  }));
}

/**
 * Generate advanced metrics for pro tier
 */
function generateAdvancedMetrics(tenant: TenantTestContext) {
  return {
    revenueGrowth: Math.floor(Math.random() * 50) + 10,
    customerRetention: Math.floor(Math.random() * 30) + 70,
    averageInvoiceValue: Math.floor(Math.random() * 2000) + 500,
    conversionRate: Math.floor(Math.random() * 15) + 5,
    monthlyRecurring: (tenant.usage?.invoices || 0) * 0.6 * 250
  };
}

export { expect } from '@playwright/test';