import { test as base, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';
import { InvoicePage } from '../pages/invoice.page';
import { InventoryPage } from '../pages/inventory.page';

// Test user credentials - should match seed data
export const TEST_USER = {
  email: 'test@gmail.com',
  password: 'test1234',
  username: 'testuser',
};

// Extend the base test with page objects
export const test = base.extend<{
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  invoicePage: InvoicePage;
  inventoryPage: InventoryPage;
}>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
  invoicePage: async ({ page }, use) => {
    await use(new InvoicePage(page));
  },
  inventoryPage: async ({ page }, use) => {
    await use(new InventoryPage(page));
  },
});

export { expect };
