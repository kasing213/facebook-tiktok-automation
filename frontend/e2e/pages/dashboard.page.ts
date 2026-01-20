import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model for Dashboard
 */
export class DashboardPage {
  readonly page: Page;

  // Sidebar navigation
  readonly overviewLink: Locator;
  readonly invoicesLink: Locator;
  readonly inventoryLink: Locator;
  readonly clientsLink: Locator;
  readonly settingsLink: Locator;
  readonly integrationsLink: Locator;
  readonly billingLink: Locator;

  // User menu
  readonly userMenu: Locator;
  readonly logoutButton: Locator;

  // Overview page elements
  readonly welcomeMessage: Locator;
  readonly statsCards: Locator;

  constructor(page: Page) {
    this.page = page;

    // Sidebar navigation - using text content or aria labels
    this.overviewLink = page.getByRole('link', { name: /overview|dashboard/i }).first();
    this.invoicesLink = page.getByRole('link', { name: /invoices/i });
    this.inventoryLink = page.getByRole('link', { name: /inventory/i });
    this.clientsLink = page.getByRole('link', { name: /clients/i });
    this.settingsLink = page.getByRole('link', { name: /settings/i });
    this.integrationsLink = page.getByRole('link', { name: /integrations/i });
    this.billingLink = page.getByRole('link', { name: /billing/i });

    // User menu
    this.userMenu = page.locator('[data-testid="user-menu"], [class*="user-menu"], [class*="avatar"]').first();
    this.logoutButton = page.getByRole('button', { name: /logout|sign out/i });

    // Overview elements
    this.welcomeMessage = page.locator('h1, h2').filter({ hasText: /welcome|dashboard|overview/i }).first();
    this.statsCards = page.locator('[class*="stat"], [class*="card"]');
  }

  async goto() {
    await this.page.goto('/dashboard');
  }

  async navigateToInvoices() {
    await this.invoicesLink.click();
    await expect(this.page).toHaveURL(/\/dashboard\/invoices/);
  }

  async navigateToInventory() {
    await this.inventoryLink.click();
    await expect(this.page).toHaveURL(/\/dashboard\/inventory/);
  }

  async navigateToSettings() {
    await this.settingsLink.click();
    await expect(this.page).toHaveURL(/\/dashboard\/settings/);
  }

  async navigateToClients() {
    await this.clientsLink.click();
    await expect(this.page).toHaveURL(/\/dashboard\/clients/);
  }

  async navigateToIntegrations() {
    await this.integrationsLink.click();
    await expect(this.page).toHaveURL(/\/dashboard\/integrations/);
  }

  async logout() {
    // Try to find and click user menu first, then logout button
    if (await this.userMenu.isVisible()) {
      await this.userMenu.click();
    }
    await this.logoutButton.click();
    await expect(this.page).toHaveURL(/\/login/);
  }

  async expectToBeOnDashboard() {
    await expect(this.page).toHaveURL(/\/dashboard/);
  }
}
