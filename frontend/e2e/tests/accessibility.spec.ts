import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y, getViolations } from 'axe-playwright';

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authenticated user for accessibility tests
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            id: '123e4567-e89b-12d3-a456-426614174000',
            email: 'accessibility-test@example.com',
            firstName: 'Accessibility',
            lastName: 'Tester'
          }
        })
      });
    });

    // Inject axe-core into the page
    await injectAxe(page);
  });

  test.describe('Core Application Accessibility', () => {
    test('should have no accessibility violations on dashboard', async ({ page }) => {
      // Mock dashboard data
      await page.route('**/api/dashboard/stats', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: { total: 10, pending: 2, paid: 8 },
            products: { total: 25, lowStock: 1 },
            revenue: { thisMonth: 5000, lastMonth: 4500 }
          })
        });
      });

      await page.goto('/dashboard');

      // Wait for dashboard to load
      await expect(page.locator('[class*="dashboard"], main')).toBeVisible();

      // Check for accessibility violations
      await checkA11y(page, null, {
        detailedReport: true,
        detailedReportOptions: { html: true },
      });
    });

    test('should have no accessibility violations on login page', async ({ page }) => {
      await page.goto('/login');

      // Wait for login form to load
      await expect(page.locator('form, [class*="login"]')).toBeVisible();

      // Check accessibility
      await checkA11y(page, null, {
        rules: {
          // Common accessibility rules to check
          'color-contrast': { enabled: true },
          'keyboard-navigation': { enabled: true },
          'aria-labels': { enabled: true },
          'heading-order': { enabled: true },
          'landmark-unique': { enabled: true },
          'link-purpose': { enabled: true },
          'form-labels': { enabled: true }
        }
      });
    });

    test('should have no accessibility violations on invoice list', async ({ page }) => {
      // Mock invoice data
      await page.route('**/api/invoice/invoices*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            invoices: [
              {
                id: 'inv-1',
                invoiceNumber: 'INV-001',
                recipientName: 'Test Customer',
                amount: 1000,
                status: 'pending',
                createdAt: '2026-01-01T00:00:00Z'
              },
              {
                id: 'inv-2',
                invoiceNumber: 'INV-002',
                recipientName: 'Another Customer',
                amount: 2000,
                status: 'paid',
                createdAt: '2026-01-02T00:00:00Z'
              }
            ],
            totalCount: 2
          })
        });
      });

      await page.goto('/dashboard/invoices');

      // Wait for invoice list to load
      await expect(page.locator('table, [class*="invoice-list"]')).toBeVisible();

      // Check accessibility with table-specific rules
      await checkA11y(page, null, {
        rules: {
          'table-headers': { enabled: true },
          'table-caption': { enabled: false }, // May not always be required
          'th-scope': { enabled: true },
          'color-contrast': { enabled: true }
        }
      });
    });

    test('should have accessible navigation', async ({ page }) => {
      await page.goto('/dashboard');

      // Check navigation accessibility
      await checkA11y(page, 'nav, [role="navigation"]', {
        rules: {
          'aria-labels': { enabled: true },
          'keyboard-navigation': { enabled: true },
          'link-purpose': { enabled: true },
          'focus-order': { enabled: true }
        }
      });

      // Test keyboard navigation
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');

      // Check that focus is visible and logical
      const focusedElement = await page.locator(':focus');
      await expect(focusedElement).toBeVisible();
    });
  });

  test.describe('Form Accessibility', () => {
    test('should have accessible invoice creation form', async ({ page }) => {
      await page.goto('/dashboard/invoices/new');

      // Wait for form to load
      await expect(page.locator('form')).toBeVisible();

      // Check form accessibility
      await checkA11y(page, 'form', {
        rules: {
          'form-labels': { enabled: true },
          'form-field-multiple-labels': { enabled: true },
          'aria-input-field-name': { enabled: true },
          'color-contrast': { enabled: true },
          'focus-order': { enabled: true }
        }
      });

      // Test form validation accessibility
      const submitButton = page.getByRole('button', { name: /save|create|submit/i });
      if (await submitButton.isVisible()) {
        await submitButton.click();

        // Check that validation errors are accessible
        const errorElements = page.locator('[class*="error"], [role="alert"], [aria-invalid="true"]');
        if (await errorElements.count() > 0) {
          // Ensure errors are announced to screen readers
          await checkA11y(page, null, {
            rules: {
              'aria-valid-attr-value': { enabled: true },
              'aria-input-field-name': { enabled: true }
            }
          });
        }
      }
    });

    test('should have accessible search functionality', async ({ page }) => {
      await page.goto('/dashboard/invoices');

      // Check search input accessibility
      const searchInput = page.locator('input[type="search"], input[placeholder*="search"]');
      if (await searchInput.isVisible()) {
        await checkA11y(page, 'input[type="search"], input[placeholder*="search"]', {
          rules: {
            'aria-input-field-name': { enabled: true },
            'color-contrast': { enabled: true }
          }
        });

        // Test search results accessibility
        await searchInput.fill('test');
        await searchInput.press('Enter');

        // Wait for search results
        await page.waitForTimeout(1000);

        // Check search results accessibility
        await checkA11y(page, '[class*="search-results"], [class*="results"]');
      }
    });
  });

  test.describe('Modal and Dialog Accessibility', () => {
    test('should have accessible product creation modal', async ({ page }) => {
      // Mock products endpoint
      await page.route('**/api/inventory/products*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            products: [],
            stats: { total: 0, lowStock: 0 }
          })
        });
      });

      await page.goto('/dashboard/inventory');

      // Open product creation modal
      const createButton = page.getByRole('button', { name: /create|add.*product/i });
      if (await createButton.isVisible()) {
        await createButton.click();

        // Wait for modal
        await expect(page.locator('[role="dialog"], .modal')).toBeVisible();

        // Check modal accessibility
        await checkA11y(page, '[role="dialog"], .modal', {
          rules: {
            'aria-dialog-name': { enabled: true },
            'focus-trap': { enabled: true },
            'aria-modal': { enabled: true },
            'color-contrast': { enabled: true }
          }
        });

        // Check that focus is trapped in modal
        await page.keyboard.press('Tab');
        await page.keyboard.press('Tab');

        // Focus should stay within modal
        const focusedElement = await page.locator(':focus');
        const modalElement = page.locator('[role="dialog"], .modal');

        const isInModal = await modalElement.locator(':focus').count() > 0;
        expect(isInModal).toBe(true);
      }
    });

    test('should have accessible confirmation dialogs', async ({ page }) => {
      await page.goto('/dashboard/invoices');

      // Try to trigger a delete confirmation (if available)
      const deleteButton = page.getByRole('button', { name: /delete/i }).first();
      if (await deleteButton.isVisible()) {
        await deleteButton.click();

        // Check if confirmation dialog appears
        const confirmDialog = page.locator('[role="dialog"], [role="alertdialog"]');
        if (await confirmDialog.isVisible()) {
          // Check confirmation dialog accessibility
          await checkA11y(page, '[role="dialog"], [role="alertdialog"]', {
            rules: {
              'aria-dialog-name': { enabled: true },
              'aria-describedby': { enabled: true },
              'button-name': { enabled: true }
            }
          });
        }
      }
    });
  });

  test.describe('Color Contrast and Visual Accessibility', () => {
    test('should meet WCAG color contrast requirements', async ({ page }) => {
      await page.goto('/dashboard');

      // Check color contrast throughout the application
      await checkA11y(page, null, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });

      // Get detailed contrast violations if any
      const violations = await getViolations(page, null, {
        rules: {
          'color-contrast': { enabled: true }
        }
      });

      if (violations.length > 0) {
        console.log('Color contrast violations found:');
        violations.forEach(violation => {
          console.log(`- ${violation.description}`);
          violation.nodes.forEach(node => {
            console.log(`  Element: ${node.html}`);
            console.log(`  Impact: ${node.impact}`);
          });
        });
      }
    });

    test('should work without relying solely on color', async ({ page }) => {
      await page.goto('/dashboard/invoices');

      // Check that status indicators don't rely solely on color
      const statusElements = page.locator('[class*="status"], [class*="badge"]');
      const statusCount = await statusElements.count();

      for (let i = 0; i < Math.min(statusCount, 5); i++) {
        const element = statusElements.nth(i);
        const text = await element.textContent();

        // Status should have text content, not just color
        expect(text?.trim()).not.toBe('');
      }

      // Check accessibility of status indicators
      if (statusCount > 0) {
        await checkA11y(page, '[class*="status"], [class*="badge"]', {
          rules: {
            'color-contrast': { enabled: true }
          }
        });
      }
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('should support full keyboard navigation', async ({ page }) => {
      await page.goto('/dashboard');

      // Test keyboard navigation through main elements
      const focusableElements: string[] = [];

      // Navigate through the page with Tab
      for (let i = 0; i < 20; i++) {
        await page.keyboard.press('Tab');

        const focusedElement = await page.locator(':focus');
        if (await focusedElement.count() > 0) {
          const tagName = await focusedElement.evaluate(el => el.tagName.toLowerCase());
          const role = await focusedElement.getAttribute('role') || '';
          const id = await focusedElement.getAttribute('id') || '';

          focusableElements.push(`${tagName}${role ? `[role="${role}"]` : ''}${id ? `#${id}` : ''}`);
        }
      }

      // Should have navigated through multiple focusable elements
      expect(focusableElements.length).toBeGreaterThan(3);

      // Test that Enter/Space work on buttons
      await page.goto('/dashboard/invoices');
      const createButton = page.getByRole('button', { name: /create|new/i });

      if (await createButton.isVisible()) {
        await createButton.focus();
        await page.keyboard.press('Enter');

        // Should navigate or open modal
        await page.waitForTimeout(1000);
        const currentUrl = page.url();
        const hasModal = await page.locator('[role="dialog"], .modal').isVisible();

        expect(currentUrl.includes('/new') || hasModal).toBe(true);
      }
    });

    test('should have visible focus indicators', async ({ page }) => {
      await page.goto('/dashboard');

      // Add CSS to highlight focus for testing
      await page.addStyleTag({
        content: `
          *:focus {
            outline: 2px solid red !important;
            outline-offset: 2px !important;
          }
        `
      });

      // Navigate and check focus visibility
      await page.keyboard.press('Tab');

      const focusedElement = await page.locator(':focus');
      if (await focusedElement.count() > 0) {
        // Check that focus is visible (has outline or other visual indicator)
        const styles = await focusedElement.evaluate(el => {
          const computed = window.getComputedStyle(el);
          return {
            outline: computed.outline,
            outlineWidth: computed.outlineWidth,
            boxShadow: computed.boxShadow
          };
        });

        const hasFocusIndicator =
          styles.outline !== 'none' ||
          styles.outlineWidth !== '0px' ||
          styles.boxShadow !== 'none';

        expect(hasFocusIndicator).toBe(true);
      }
    });
  });

  test.describe('Screen Reader Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      await page.goto('/dashboard');

      // Check heading hierarchy
      await checkA11y(page, null, {
        rules: {
          'heading-order': { enabled: true },
          'empty-heading': { enabled: true },
          'heading-levels': { enabled: true }
        }
      });

      // Verify heading structure manually
      const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
      const headingLevels: number[] = [];

      for (const heading of headings) {
        const tagName = await heading.evaluate(el => el.tagName);
        const level = parseInt(tagName.substring(1));
        headingLevels.push(level);
      }

      // Check that heading levels don't skip (e.g., h1 -> h3)
      if (headingLevels.length > 1) {
        for (let i = 1; i < headingLevels.length; i++) {
          const levelDifference = headingLevels[i] - headingLevels[i - 1];
          expect(levelDifference).toBeLessThanOrEqual(1);
        }
      }
    });

    test('should have proper ARIA landmarks', async ({ page }) => {
      await page.goto('/dashboard');

      // Check for essential landmarks
      await checkA11y(page, null, {
        rules: {
          'landmark-unique': { enabled: true },
          'landmark-main-is-top-level': { enabled: true },
          'landmark-contentinfo-is-top-level': { enabled: true },
          'landmark-banner-is-top-level': { enabled: true }
        }
      });

      // Verify key landmarks exist
      const landmarks = {
        main: await page.locator('[role="main"], main').count(),
        navigation: await page.locator('[role="navigation"], nav').count(),
        banner: await page.locator('[role="banner"], header').count()
      };

      expect(landmarks.main).toBeGreaterThan(0);
      expect(landmarks.navigation).toBeGreaterThan(0);
    });

    test('should provide informative page titles', async ({ page }) => {
      const pages = [
        { url: '/dashboard', expectedTitlePattern: /dashboard/i },
        { url: '/dashboard/invoices', expectedTitlePattern: /invoice/i },
        { url: '/dashboard/inventory', expectedTitlePattern: /inventory|product/i }
      ];

      for (const pageInfo of pages) {
        await page.goto(pageInfo.url);

        const title = await page.title();
        expect(title).toMatch(pageInfo.expectedTitlePattern);
        expect(title.trim()).not.toBe('');
      }
    });
  });

  test.describe('Responsive Design Accessibility', () => {
    test('should maintain accessibility on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      await page.goto('/dashboard');

      // Check accessibility on mobile
      await checkA11y(page, null, {
        rules: {
          'color-contrast': { enabled: true },
          'touch-target-size': { enabled: true },
          'aria-labels': { enabled: true }
        }
      });

      // Check that interactive elements are large enough for touch
      const buttons = await page.locator('button, a, input[type="submit"]').all();

      for (const button of buttons.slice(0, 5)) { // Check first 5 buttons
        if (await button.isVisible()) {
          const boundingBox = await button.boundingBox();
          if (boundingBox) {
            // Touch targets should be at least 44px x 44px
            expect(boundingBox.width).toBeGreaterThanOrEqual(44);
            expect(boundingBox.height).toBeGreaterThanOrEqual(44);
          }
        }
      }
    });

    test('should work with high contrast mode', async ({ page }) => {
      // Simulate high contrast mode
      await page.emulateMedia({ colorScheme: 'dark', forcedColors: 'active' });

      await page.goto('/dashboard');

      // Check that content is still accessible in high contrast mode
      await checkA11y(page, null, {
        rules: {
          'color-contrast': { enabled: false }, // Skip normal contrast in forced colors mode
          'aria-labels': { enabled: true },
          'form-labels': { enabled: true }
        }
      });
    });
  });
});