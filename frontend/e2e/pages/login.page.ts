import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model for Login page
 */
export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly registerLink: Locator;
  readonly forgotPasswordLink: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByPlaceholder(/email/i);
    this.passwordInput = page.getByPlaceholder(/password/i);
    this.loginButton = page.getByRole('button', { name: /log in|sign in|login/i });
    this.registerLink = page.locator('a').filter({ hasText: /sign up|register/i });
    this.forgotPasswordLink = page.getByRole('link', { name: /forgot password/i });
    this.errorMessage = page.locator('[role="alert"]');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async expectError(message: string | RegExp) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectRedirectToDashboard() {
    await expect(this.page).toHaveURL(/\/dashboard/);
  }
}
