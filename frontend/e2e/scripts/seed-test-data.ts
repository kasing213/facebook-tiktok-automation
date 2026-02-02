/**
 * Test Data Seeding Script for Multi-Tenant Scenarios
 *
 * This script sets up realistic test data across multiple tenants
 * to support comprehensive beta testing scenarios.
 */

import { APIRequestContext, request } from '@playwright/test';
import testUsers from '../fixtures/test-users.json';
import products from '../fixtures/products.json';
import invoices from '../fixtures/invoices.json';

interface TenantSeedData {
  tenantId: string;
  users: any[];
  products: any[];
  invoices: any[];
  campaigns?: any[];
}

/**
 * Main seeding function - creates test data for all tenant types
 */
export async function seedMultiTenantData(baseURL: string = 'http://localhost:8000') {
  console.log('🌱 Starting multi-tenant test data seeding...');

  const apiContext = await request.newContext({
    baseURL: baseURL,
    extraHTTPHeaders: {
      'Content-Type': 'application/json',
      'X-Test-Data-Seed': 'true' // Flag to identify test data
    }
  });

  try {
    // Create tenant data for each subscription tier
    const tenantData: TenantSeedData[] = [
      await createFreeTierTenant(),
      await createInvoicePlusTenant(),
      await createMarketingPlusTenant(),
      await createProTierTenant(),
      await createTrialTenant()
    ];

    // Seed each tenant's data
    for (const tenant of tenantData) {
      await seedTenantData(apiContext, tenant);
    }

    console.log('✅ Multi-tenant test data seeding completed successfully!');

    // Generate summary report
    await generateSeedingSummary(tenantData);

  } catch (error) {
    console.error('❌ Error during test data seeding:', error);
    throw error;
  } finally {
    await apiContext.dispose();
  }
}

/**
 * Create Free Tier tenant data
 */
async function createFreeTierTenant(): Promise<TenantSeedData> {
  const user = testUsers.users.free_tier;

  return {
    tenantId: 'tenant-free-tier-seed-123',
    users: [
      {
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        businessName: user.businessName,
        password: user.password,
        role: 'owner',
        subscription: {
          tier: 'free',
          status: 'active',
          features: ['basic_invoicing'],
          limits: user.expectedLimits
        }
      }
    ],
    products: products.products.slice(0, 10), // Limited for free tier
    invoices: invoices.invoices.slice(0, 3)
  };
}

/**
 * Create Invoice Plus tier tenant data
 */
async function createInvoicePlusTenant(): Promise<TenantSeedData> {
  const user = testUsers.users.invoice_plus;

  return {
    tenantId: 'tenant-invoice-plus-seed-456',
    users: [
      {
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        businessName: user.businessName,
        password: user.password,
        role: 'owner',
        subscription: {
          tier: 'invoice_plus',
          status: 'active',
          features: ['basic_invoicing', 'inventory_management'],
          limits: user.expectedLimits
        }
      },
      // Add additional team member
      {
        email: 'manager@techwholesale.com',
        firstName: 'Inventory',
        lastName: 'Manager',
        role: 'user',
        password: 'manager123'
      }
    ],
    products: products.products, // Full product catalog
    invoices: invoices.invoices
  };
}

/**
 * Create Marketing Plus tier tenant data
 */
async function createMarketingPlusTenant(): Promise<TenantSeedData> {
  const user = testUsers.users.marketing_plus;

  return {
    tenantId: 'tenant-marketing-plus-seed-789',
    users: [
      {
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        businessName: user.businessName,
        password: user.password,
        role: 'owner',
        subscription: {
          tier: 'marketing_plus',
          status: 'active',
          features: ['basic_invoicing', 'marketing_media', 'marketing_chats'],
          limits: user.expectedLimits
        }
      }
    ],
    products: products.products.slice(0, 15),
    invoices: invoices.invoices.slice(0, 2),
    campaigns: [
      {
        name: 'Summer Sale Campaign',
        status: 'active',
        platform: 'facebook',
        budget: 500,
        reach: 2500,
        engagement: 125,
        startDate: new Date().toISOString(),
        endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
      },
      {
        name: 'Product Launch TikTok',
        status: 'draft',
        platform: 'tiktok',
        budget: 300,
        targetAudience: 'young adults'
      }
    ]
  };
}

/**
 * Create Pro tier tenant data
 */
async function createProTierTenant(): Promise<TenantSeedData> {
  const user = testUsers.users.pro_tier;

  return {
    tenantId: 'tenant-pro-tier-seed-101',
    users: [
      {
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        businessName: user.businessName,
        password: user.password,
        role: 'owner',
        subscription: {
          tier: 'pro',
          status: 'active',
          features: [
            'basic_invoicing',
            'inventory_management',
            'marketing_media',
            'marketing_chats',
            'advanced_analytics',
            'bulk_operations'
          ],
          limits: user.expectedLimits
        }
      },
      // Add multiple team members for Pro tier
      {
        email: 'manager@goldendragon.com',
        firstName: 'Operations',
        lastName: 'Manager',
        role: 'user',
        password: 'manager123'
      },
      {
        email: 'analyst@goldendragon.com',
        firstName: 'Data',
        lastName: 'Analyst',
        role: 'user',
        password: 'analyst123'
      }
    ],
    products: [
      ...products.products,
      ...generateBulkProducts(50) // Additional products for bulk testing
    ],
    invoices: [
      ...invoices.invoices,
      ...generateBulkInvoices(20) // Additional invoices for analytics
    ],
    campaigns: [
      {
        name: 'Multi-Location Marketing',
        status: 'active',
        platform: 'facebook',
        budget: 2000,
        reach: 15000,
        engagement: 750,
        locations: ['Phnom Penh', 'Siem Reap', 'Battambang']
      },
      {
        name: 'TikTok Restaurant Series',
        status: 'active',
        platform: 'tiktok',
        budget: 1500,
        videoViews: 50000,
        followers: 1200
      }
    ]
  };
}

/**
 * Create Trial tenant data
 */
async function createTrialTenant(): Promise<TenantSeedData> {
  const user = testUsers.users.trial_user;

  return {
    tenantId: 'tenant-trial-seed-202',
    users: [
      {
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        businessName: user.businessName,
        password: user.password,
        role: 'owner',
        subscription: {
          tier: 'pro_trial',
          status: 'trial',
          features: [
            'basic_invoicing',
            'inventory_management',
            'marketing_media'
          ],
          trialEndsAt: user.trialEndsAt,
          trialDaysRemaining: 25
        }
      }
    ],
    products: products.products.slice(0, 25),
    invoices: invoices.invoices.slice(0, 5)
  };
}

/**
 * Seed individual tenant data via API calls
 */
async function seedTenantData(apiContext: APIRequestContext, tenant: TenantSeedData) {
  console.log(`📡 Seeding data for tenant: ${tenant.tenantId}`);

  try {
    // 1. Create tenant and owner user
    const tenantResponse = await apiContext.post('/api/test/seed/tenant', {
      data: {
        tenantId: tenant.tenantId,
        owner: tenant.users[0],
        subscription: tenant.users[0].subscription
      }
    });

    if (!tenantResponse.ok()) {
      throw new Error(`Failed to create tenant: ${await tenantResponse.text()}`);
    }

    // 2. Create additional users
    for (const user of tenant.users.slice(1)) {
      await apiContext.post('/api/test/seed/user', {
        data: {
          tenantId: tenant.tenantId,
          user: user
        }
      });
    }

    // 3. Seed products (if tenant has inventory feature)
    const hasInventory = tenant.users[0].subscription.features.includes('inventory_management');
    if (hasInventory && tenant.products.length > 0) {
      await apiContext.post('/api/test/seed/products', {
        data: {
          tenantId: tenant.tenantId,
          products: tenant.products.map(product => ({
            ...product,
            tenantId: tenant.tenantId
          }))
        }
      });
    }

    // 4. Seed invoices
    if (tenant.invoices.length > 0) {
      await apiContext.post('/api/test/seed/invoices', {
        data: {
          tenantId: tenant.tenantId,
          invoices: tenant.invoices.map(invoice => ({
            ...invoice,
            tenantId: tenant.tenantId
          }))
        }
      });
    }

    // 5. Seed marketing campaigns (if applicable)
    const hasMarketing = tenant.users[0].subscription.features.includes('marketing_media');
    if (hasMarketing && tenant.campaigns?.length > 0) {
      await apiContext.post('/api/test/seed/campaigns', {
        data: {
          tenantId: tenant.tenantId,
          campaigns: tenant.campaigns.map(campaign => ({
            ...campaign,
            tenantId: tenant.tenantId
          }))
        }
      });
    }

    console.log(`✅ Successfully seeded tenant: ${tenant.tenantId}`);

  } catch (error) {
    console.error(`❌ Failed to seed tenant ${tenant.tenantId}:`, error);
    throw error;
  }
}

/**
 * Generate bulk products for load testing
 */
function generateBulkProducts(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    name: `Bulk Product ${i + 1}`,
    sku: `BULK-${String(i + 1).padStart(4, '0')}`,
    description: `Generated product for load testing - Item ${i + 1}`,
    price: Math.floor(Math.random() * 500) + 50,
    cost: Math.floor(Math.random() * 300) + 25,
    stock: Math.floor(Math.random() * 200) + 50,
    lowStockThreshold: 10,
    category: 'Bulk Test Items'
  }));
}

/**
 * Generate bulk invoices for analytics testing
 */
function generateBulkInvoices(count: number) {
  const customers = [
    'Tech Solutions Ltd',
    'Creative Agency Inc',
    'Startup Ventures',
    'Business Corp',
    'Innovation Hub'
  ];

  return Array.from({ length: count }, (_, i) => {
    const amount = Math.floor(Math.random() * 5000) + 500;
    const daysAgo = Math.floor(Math.random() * 90);

    return {
      invoiceNumber: `BULK-${String(i + 1).padStart(4, '0')}`,
      recipientName: customers[i % customers.length],
      recipientEmail: `contact${i + 1}@${customers[i % customers.length].toLowerCase().replace(/\s+/g, '')}.com`,
      amount: amount,
      currency: 'USD',
      status: ['paid', 'pending', 'overdue'][Math.floor(Math.random() * 3)],
      createdAt: new Date(Date.now() - daysAgo * 24 * 60 * 60 * 1000).toISOString(),
      dueDate: new Date(Date.now() + (30 - daysAgo) * 24 * 60 * 60 * 1000).toISOString(),
      lineItems: [
        {
          name: 'Bulk Service Item',
          quantity: Math.floor(Math.random() * 5) + 1,
          unitPrice: amount / (Math.floor(Math.random() * 5) + 1),
          total: amount
        }
      ]
    };
  });
}

/**
 * Generate seeding summary report
 */
async function generateSeedingSummary(tenantData: TenantSeedData[]) {
  const summary = {
    timestamp: new Date().toISOString(),
    totalTenants: tenantData.length,
    tenants: tenantData.map(tenant => ({
      tenantId: tenant.tenantId,
      subscriptionTier: tenant.users[0].subscription.tier,
      userCount: tenant.users.length,
      productCount: tenant.products.length,
      invoiceCount: tenant.invoices.length,
      campaignCount: tenant.campaigns?.length || 0
    })),
    totalUsers: tenantData.reduce((sum, t) => sum + t.users.length, 0),
    totalProducts: tenantData.reduce((sum, t) => sum + t.products.length, 0),
    totalInvoices: tenantData.reduce((sum, t) => sum + t.invoices.length, 0),
    totalCampaigns: tenantData.reduce((sum, t) => sum + (t.campaigns?.length || 0), 0)
  };

  console.log('\n📊 SEEDING SUMMARY:');
  console.log('===================');
  console.log(`🏢 Total Tenants: ${summary.totalTenants}`);
  console.log(`👥 Total Users: ${summary.totalUsers}`);
  console.log(`📦 Total Products: ${summary.totalProducts}`);
  console.log(`🧾 Total Invoices: ${summary.totalInvoices}`);
  console.log(`📱 Total Campaigns: ${summary.totalCampaigns}`);
  console.log('\n📋 Per Tenant Breakdown:');

  summary.tenants.forEach(tenant => {
    console.log(`  • ${tenant.tenantId} (${tenant.subscriptionTier}): ${tenant.userCount} users, ${tenant.productCount} products, ${tenant.invoiceCount} invoices`);
  });

  // Write summary to file
  const fs = require('fs');
  fs.writeFileSync('test-data-seeding-summary.json', JSON.stringify(summary, null, 2));
  console.log('\n📄 Summary saved to: test-data-seeding-summary.json');
}

/**
 * Clean up test data (for teardown)
 */
export async function cleanupTestData(baseURL: string = 'http://localhost:8000') {
  console.log('🧹 Cleaning up test data...');

  const apiContext = await request.newContext({
    baseURL: baseURL,
    extraHTTPHeaders: {
      'X-Test-Data-Cleanup': 'true'
    }
  });

  try {
    const response = await apiContext.delete('/api/test/cleanup');

    if (response.ok()) {
      console.log('✅ Test data cleanup completed');
    } else {
      console.error('❌ Failed to cleanup test data:', await response.text());
    }
  } finally {
    await apiContext.dispose();
  }
}

// CLI execution
if (require.main === module) {
  const baseURL = process.argv[2] || 'http://localhost:8000';
  seedMultiTenantData(baseURL).catch(console.error);
}