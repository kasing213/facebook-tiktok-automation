import { test as setup, expect } from '@playwright/test';
import { TEST_USER } from '../fixtures/auth.fixture';
import { withRateLimitRetry, RateLimitManager } from '../helpers/rate-limit';

const authFile = 'e2e/.auth/user.json';

/**
 * This setup runs before all tests to create an authenticated state.
 * The auth state is saved to a file and reused by all tests.
 *
 * Rate-limit aware: Respects backend 60 req/min limit
 */
setup('authenticate', async ({ page }) => {
  console.log('[Auth] Starting authentication with rate limiting...');

  await withRateLimitRetry(async () => {
    // Go to login page
    console.log('[Auth] Navigating to login page');
    await page.goto('/login');

    // Check for any existing error messages and clear them
    const errorElements = page.locator('[class*="error"], [class*="alert"]');
    if (await errorElements.count() > 0) {
      console.log('[Auth] Found existing error messages, clearing them');
    }

    // Fill in credentials
    console.log('[Auth] Filling credentials');
    await page.getByPlaceholder(/email/i).fill(TEST_USER.email);
    await page.getByPlaceholder(/password/i).fill(TEST_USER.password);

    // Add small delay before clicking
    await page.waitForTimeout(500);

    // Click login button with rate limit consideration
    console.log('[Auth] Clicking login button');
    await page.getByRole('button', { name: /log in|login/i }).click();

    // Wait for either success (dashboard) or failure (error message)
    const dashboardLoaded = page.waitForURL(/\/dashboard/, { timeout: 15000 });
    const errorShown = page.locator('text=/login failed|network error|too many requests/i').first().waitFor({ timeout: 15000 });

    const result = await Promise.race([
      dashboardLoaded.then(() => 'success'),
      errorShown.then(() => 'error'),
    ]);

    if (result === 'error') {
      // Check if it's a rate limit error
      const errorText = await page.locator('text=/login failed|network error|too many requests/i').first().textContent();
      console.log(`[Auth] Login failed: ${errorText}`);

      if (errorText?.toLowerCase().includes('network error')) {
        // This might be a rate limit issue masquerading as network error
        throw new Error('429: Login failed - possible rate limit');
      }

      throw new Error(`Login failed: ${errorText}`);
    }

    console.log('[Auth] Successfully reached dashboard');

    // Verify we're logged in by checking for dashboard elements
    await expect(page.locator('text=/dashboard|overview|welcome/i').first()).toBeVisible({ timeout: 5000 });

    return 'authenticated';

  }, 5, 'authentication');

  console.log('[Auth] Saving authentication state');

  // Save the authentication state
  await page.context().storageState({ path: authFile });

  console.log(`[Auth] Authentication completed. Used ${RateLimitManager.getRequestCount()} requests this window.`);
});
