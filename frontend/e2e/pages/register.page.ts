import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model for Register page
 */
export class RegisterPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly registerButton: Locator;
  readonly loginLink: Locator;
  readonly errorMessage: Locator;
  readonly successMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.getByPlaceholder(/username/i);
    this.emailInput = page.getByPlaceholder(/email/i);
    this.passwordInput = page.locator('input[type="password"]').first();
    this.confirmPasswordInput = page.locator('input[type="password"]').nth(1);
    this.registerButton = page.getByRole('button', { name: /sign up|register|create account/i });
    this.loginLink = page.getByRole('link', { name: /sign in|login/i });
    this.errorMessage = page.locator('[class*="error"], [role="alert"]');
    this.successMessage = page.locator('[class*="success"]');
  }

  async goto() {
    await this.page.goto('/register');
  }

  async register(username: string, email: string, password: string, confirmPassword?: string) {
    await this.usernameInput.fill(username);
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    if (this.confirmPasswordInput) {
      await this.confirmPasswordInput.fill(confirmPassword || password);
    }
    await this.registerButton.click();
  }

  async expectError(message: string | RegExp) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectRedirectToVerification() {
    await expect(this.page).toHaveURL(/\/verification-pending/);
  }
}
