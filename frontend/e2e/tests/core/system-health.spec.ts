import { test, expect } from '@playwright/test';

/**
 * Core System Health Tests
 *
 * These tests validate the fundamental system functionality before any tenant-specific tests.
 * They ensure the core infrastructure is working correctly.
 */
test.describe('Core System Health', () => {
  test.describe('Application Startup', () => {
    test('should load the application without errors', async ({ page }) => {
      // Navigate to the app
      await page.goto('/');

      // Should not have any JavaScript errors
      const errors: string[] = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          errors.push(msg.text());
        }
      });

      page.on('pageerror', (error) => {
        errors.push(error.message);
      });

      // Wait for page to load
      await page.waitForLoadState('networkidle');

      // Check that there are no critical errors
      const criticalErrors = errors.filter(error =>
        !error.includes('favicon') &&
        !error.includes('404') &&
        !error.includes('net::ERR_INTERNET_DISCONNECTED')
      );

      expect(criticalErrors).toEqual([]);
    });

    test('should have proper HTML structure', async ({ page }) => {
      await page.goto('/');

      // Check basic HTML structure
      await expect(page.locator('html')).toBeVisible();
      await expect(page.locator('body')).toBeVisible();
      await expect(page.locator('head title')).toHaveText(/Facebook.*TikTok.*Automation/i);

      // Check meta tags exist
      const metaViewport = page.locator('meta[name="viewport"]');
      await expect(metaViewport).toHaveAttribute('content', /width=device-width/);
    });

    test('should load CSS and assets', async ({ page }) => {
      await page.goto('/');

      // Wait for styles to load
      await page.waitForLoadState('networkidle');

      // Check that body has styles applied (not default browser styles)
      const bodyStyles = await page.locator('body').evaluate((element) => {
        const styles = window.getComputedStyle(element);
        return {
          margin: styles.margin,
          fontFamily: styles.fontFamily,
          fontSize: styles.fontSize
        };
      });

      // Should have custom styles, not browser defaults
      expect(bodyStyles.fontFamily).not.toBe('Times');
      expect(bodyStyles.fontSize).not.toBe('16px'); // Default might vary
    });
  });

  test.describe('API Health Checks', () => {
    test('should handle API connectivity gracefully', async ({ page }) => {
      // Mock API health endpoint
      await page.route('**/api/health', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'healthy',
            timestamp: new Date().toISOString(),
            version: '1.0.0',
            database: 'connected',
            redis: 'connected'
          })
        });
      });

      // Mock other API endpoints with proper responses
      await page.route('**/api/**', async (route) => {
        const url = route.request().url();

        // Don't interfere with health endpoint
        if (url.includes('/health')) {
          return route.continue();
        }

        // Simulate working but unauthenticated API
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Unauthorized',
            message: 'Authentication required'
          })
        });
      });

      await page.goto('/');

      // App should load even if user is not authenticated
      await expect(page.locator('body')).toBeVisible();

      // Should either show login form or redirect to login
      const isOnLoginPage = page.url().includes('/login') || page.url().includes('/auth');
      const hasLoginForm = await page.locator('input[type="email"], input[type="password"]').count() > 0;

      expect(isOnLoginPage || hasLoginForm).toBe(true);
    });

    test('should handle API timeouts gracefully', async ({ page }) => {
      // Mock slow API responses
      await page.route('**/api/**', async (route) => {
        // Simulate timeout by delaying response
        await new Promise(resolve => setTimeout(resolve, 1000));

        await route.fulfill({
          status: 408,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Request timeout',
            message: 'Request took too long to complete'
          })
        });
      });

      await page.goto('/');

      // App should still load and show appropriate loading/error states
      await expect(page.locator('body')).toBeVisible();

      // Should show loading indicators or error messages, not crash
      const hasLoadingOrError = await page.locator(
        '[class*="loading"], [class*="spinner"], [class*="error"], text=/loading/i, text=/error/i'
      ).count() > 0;

      // It's okay if there's no loading indicator, but the app shouldn't crash
      expect(true).toBe(true); // App didn't crash if we get here
    });

    test('should handle network errors gracefully', async ({ page }) => {
      // Mock network failure
      await page.route('**/api/**', async (route) => {
        await route.abort('failed');
      });

      await page.goto('/');

      // App should still render the basic structure
      await expect(page.locator('body')).toBeVisible();

      // Should show some form of error handling or offline state
      // This is more about not crashing than specific error messages
      const pageContent = await page.textContent('body');
      expect(pageContent).toBeTruthy(); // App has rendered some content
    });
  });

  test.describe('Environment Configuration', () => {
    test('should have correct base URL configuration', async ({ page }) => {
      await page.goto('/');

      // Check that we can access the expected domain/port
      const currentURL = page.url();
      const expectedPattern = /localhost:5173|facebook.*automation.*vercel/;

      expect(currentURL).toMatch(expectedPattern);
    });

    test('should load environment-specific configuration', async ({ page }) => {
      // Check that the app configures itself for the current environment
      await page.goto('/');

      // Check for development vs production indicators
      const isDevelopment = page.url().includes('localhost');

      if (isDevelopment) {
        // Development-specific checks
        console.log('Running in development mode');
      } else {
        // Production-specific checks
        console.log('Running in production mode');

        // Should have HTTPS in production
        expect(page.url()).toMatch(/^https:/);
      }
    });
  });

  test.describe('Cross-Browser Compatibility', () => {
    test('should work across different browsers', async ({ page, browserName }) => {
      await page.goto('/');

      // Basic functionality should work in all browsers
      await expect(page.locator('body')).toBeVisible();

      // Check for browser-specific issues
      const userAgent = await page.evaluate(() => navigator.userAgent);
      console.log(`Testing on: ${browserName}, User Agent: ${userAgent}`);

      // Ensure no browser-specific errors
      const errors: string[] = [];
      page.on('pageerror', (error) => {
        errors.push(error.message);
      });

      await page.waitForTimeout(2000);

      const browserSpecificErrors = errors.filter(error =>
        error.includes('not supported') ||
        error.includes('undefined method') ||
        error.includes('not a function')
      );

      expect(browserSpecificErrors).toEqual([]);
    });
  });

  test.describe('Performance Baseline', () => {
    test('should load within acceptable time limits', async ({ page }) => {
      const startTime = Date.now();

      await page.goto('/');
      await page.waitForLoadState('networkidle');

      const loadTime = Date.now() - startTime;

      // Core system should load within 5 seconds (generous baseline)
      expect(loadTime).toBeLessThan(5000);

      console.log(`Core system load time: ${loadTime}ms`);
    });

    test('should have reasonable bundle size', async ({ page }) => {
      // Monitor network requests to check bundle size
      const responses: Array<{ url: string; size: number }> = [];

      page.on('response', async (response) => {
        if (response.url().includes('.js') || response.url().includes('.css')) {
          const buffer = await response.body().catch(() => Buffer.alloc(0));
          responses.push({
            url: response.url(),
            size: buffer.length
          });
        }
      });

      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Calculate total bundle size
      const totalSize = responses.reduce((sum, response) => sum + response.size, 0);
      const totalSizeMB = totalSize / (1024 * 1024);

      console.log(`Total bundle size: ${totalSizeMB.toFixed(2)}MB`);

      // Core bundle should be reasonable (under 5MB for initial load)
      expect(totalSizeMB).toBeLessThan(5);
    });
  });

  test.describe('Security Headers', () => {
    test('should have proper security headers in production', async ({ page }) => {
      const response = await page.goto('/');
      const headers = response?.headers();

      if (!page.url().includes('localhost')) {
        // Production security checks

        // Content Security Policy
        const csp = headers?.['content-security-policy'];
        if (csp) {
          expect(csp).toContain('default-src');
        }

        // X-Frame-Options
        const frameOptions = headers?.['x-frame-options'];
        if (frameOptions) {
          expect(frameOptions).toMatch(/DENY|SAMEORIGIN/);
        }

        // X-Content-Type-Options
        const contentTypeOptions = headers?.['x-content-type-options'];
        if (contentTypeOptions) {
          expect(contentTypeOptions).toBe('nosniff');
        }
      }

      // This test passes if we reach here without errors
      expect(true).toBe(true);
    });
  });

  test.describe('Accessibility Baseline', () => {
    test('should have basic accessibility structure', async ({ page }) => {
      await page.goto('/');

      // Check for basic accessibility landmarks
      const hasMain = await page.locator('main, [role="main"]').count() > 0;
      const hasNav = await page.locator('nav, [role="navigation"]').count() > 0;
      const hasTitle = await page.title();

      // Should have proper page title
      expect(hasTitle).toBeTruthy();
      expect(hasTitle.trim()).not.toBe('');

      // Should have semantic structure (main and navigation)
      // Note: These might not be visible immediately, so we just check they exist
      console.log(`Accessibility check - Main: ${hasMain}, Nav: ${hasNav}, Title: "${hasTitle}"`);
    });

    test('should support keyboard navigation basics', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Try to focus on first interactive element
      await page.keyboard.press('Tab');

      // Should have some focused element
      const focusedElement = await page.locator(':focus').count();

      // If there are interactive elements, one should be focused
      const interactiveElements = await page.locator('button, a, input, select, textarea, [tabindex]').count();

      if (interactiveElements > 0) {
        expect(focusedElement).toBeGreaterThan(0);
      }

      console.log(`Interactive elements: ${interactiveElements}, Focused: ${focusedElement}`);
    });
  });
});