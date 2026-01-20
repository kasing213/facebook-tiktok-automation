import { test as setup, expect } from '@playwright/test';
import { TEST_USER } from '../fixtures/auth.fixture';

const authFile = 'e2e/.auth/user.json';

/**
 * This setup runs before all tests to create an authenticated state.
 * The auth state is saved to a file and reused by all tests.
 */
setup('authenticate', async ({ page }) => {
  // Go to login page
  await page.goto('/login');

  // Fill in credentials
  await page.getByPlaceholder(/email/i).fill(TEST_USER.email);
  await page.getByPlaceholder(/password/i).fill(TEST_USER.password);

  // Click login button
  await page.getByRole('button', { name: /sign in|login/i }).click();

  // Wait for redirect to dashboard
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 });

  // Verify we're logged in by checking for dashboard elements
  await expect(page.locator('text=/dashboard|overview|welcome/i').first()).toBeVisible({ timeout: 5000 });

  // Save the authentication state
  await page.context().storageState({ path: authFile });
});
