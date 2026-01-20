import { test, expect, TEST_USER } from '../fixtures/auth.fixture';

test.describe('Authentication', () => {
  // These tests don't use the stored auth state
  test.use({ storageState: { cookies: [], origins: [] } });

  test('should display login page', async ({ loginPage }) => {
    await loginPage.goto();
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login('invalid@email.com', 'wrongpassword');

    // Wait for error message
    await expect(loginPage.errorMessage).toBeVisible({ timeout: 5000 });
  });

  test('should login successfully with valid credentials', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login(TEST_USER.email, TEST_USER.password);
    await loginPage.expectRedirectToDashboard();
  });

  test('should navigate to register page', async ({ loginPage, page }) => {
    await loginPage.goto();
    await loginPage.registerLink.click();
    await expect(page).toHaveURL(/\/register/);
  });

  test('should navigate to forgot password page', async ({ loginPage, page }) => {
    await loginPage.goto();
    await loginPage.forgotPasswordLink.click();
    await expect(page).toHaveURL(/\/forgot-password/);
  });
});

test.describe('Registration', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('should display registration form', async ({ page }) => {
    await page.goto('/register');
    await expect(page.getByPlaceholder(/username/i)).toBeVisible();
    await expect(page.getByPlaceholder(/email/i)).toBeVisible();
    await expect(page.locator('input[type="password"]').first()).toBeVisible();
  });

  test('should show error for existing email', async ({ page }) => {
    await page.goto('/register');

    // Try to register with existing test user email
    await page.getByPlaceholder(/username/i).fill('newuser');
    await page.getByPlaceholder(/email/i).fill(TEST_USER.email);
    await page.locator('input[type="password"]').first().fill('Password123!');

    // If there's a confirm password field
    const confirmPassword = page.locator('input[type="password"]').nth(1);
    if (await confirmPassword.isVisible()) {
      await confirmPassword.fill('Password123!');
    }

    await page.getByRole('button', { name: /sign up|register|create/i }).click();

    // Should show error about existing email
    await expect(page.locator('[class*="error"], [role="alert"]')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Password Reset', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('should display forgot password form', async ({ page }) => {
    await page.goto('/forgot-password');
    await expect(page.getByPlaceholder(/email/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /send|reset|submit/i })).toBeVisible();
  });

  test('should accept email and show success message', async ({ page }) => {
    await page.goto('/forgot-password');
    await page.getByPlaceholder(/email/i).fill(TEST_USER.email);
    await page.getByRole('button', { name: /send|reset|submit/i }).click();

    // Should show success message (even if email doesn't exist - anti-enumeration)
    await expect(page.locator('text=/email|sent|check|inbox/i')).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Authenticated User', () => {
  // These tests use the stored auth state from setup
  test('should be logged in and see dashboard', async ({ dashboardPage }) => {
    await dashboardPage.goto();
    await dashboardPage.expectToBeOnDashboard();
  });

  test('should be able to logout', async ({ dashboardPage, page }) => {
    await dashboardPage.goto();

    // Find and click logout
    const logoutButton = page.getByRole('button', { name: /logout|sign out/i });
    const userMenu = page.locator('[class*="user"], [class*="avatar"], [class*="dropdown"]').first();

    if (await userMenu.isVisible()) {
      await userMenu.click();
      await expect(logoutButton).toBeVisible({ timeout: 3000 });
    }

    if (await logoutButton.isVisible()) {
      await logoutButton.click();
      await expect(page).toHaveURL(/\/login/);
    }
  });
});
