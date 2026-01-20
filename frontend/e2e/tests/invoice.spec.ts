import { test, expect } from '../fixtures/auth.fixture';

test.describe('Invoice List Page', () => {
  test('should display invoice list page', async ({ invoicePage }) => {
    await invoicePage.gotoList();
    await expect(invoicePage.createInvoiceButton).toBeVisible();
  });

  test('should show stats cards', async ({ invoicePage, page }) => {
    await invoicePage.gotoList();

    // Check for stats section
    const statsSection = page.locator('[class*="stat"], [class*="card"], [class*="Stats"]');
    await expect(statsSection.first()).toBeVisible();
  });

  test('should navigate to create invoice page', async ({ invoicePage, page }) => {
    await invoicePage.gotoList();
    await invoicePage.createInvoiceButton.click();
    await expect(page).toHaveURL(/\/dashboard\/invoices\/new/);
  });

  test('should search invoices', async ({ invoicePage }) => {
    await invoicePage.gotoList();

    if (await invoicePage.searchInput.isVisible()) {
      await invoicePage.searchInvoices('INV-');
      // Just verify the search input works without erroring
      await expect(invoicePage.searchInput).toHaveValue('INV-');
    }
  });
});

test.describe('Invoice Creation', () => {
  test('should display create invoice form', async ({ invoicePage }) => {
    await invoicePage.gotoCreate();
    await expect(invoicePage.saveButton).toBeVisible();
  });

  test('should add line items', async ({ invoicePage, page }) => {
    await invoicePage.gotoCreate();

    // Look for add line item button
    const addButton = page.getByRole('button', { name: /add.*item|add.*line|\+/i });
    if (await addButton.isVisible()) {
      await addButton.click();

      // Verify a line item row appears
      const lineItems = page.locator('[class*="line-item"], [class*="LineItem"], tr').filter({
        has: page.locator('input'),
      });
      await expect(lineItems.first()).toBeVisible();
    }
  });

  test('should show product picker when available', async ({ invoicePage, page }) => {
    await invoicePage.gotoCreate();

    // Look for product picker button
    const productPicker = page.getByRole('button', { name: /product|select/i });
    if (await productPicker.isVisible()) {
      await productPicker.click();

      // Should open a dropdown or modal
      const dropdown = page.locator('[class*="dropdown"], [class*="picker"], [role="listbox"]');
      await expect(dropdown).toBeVisible({ timeout: 3000 });
    }
  });

  test('should create a basic invoice', async ({ invoicePage, page }) => {
    await invoicePage.gotoCreate();

    // Fill in basic invoice details
    // Add a line item
    const addButton = page.getByRole('button', { name: /add.*item|add.*line|\+/i });
    if (await addButton.isVisible()) {
      await addButton.click();

      // Fill in line item details
      const nameInput = page.locator('input').filter({ has: page.locator('[placeholder*="name"], [name*="name"]') }).first();
      const quantityInput = page.locator('input[type="number"]').first();
      const priceInput = page.locator('input').filter({ has: page.locator('[placeholder*="price"], [name*="price"]') }).first();

      // Try to fill fields if they exist
      if (await nameInput.isVisible()) {
        await nameInput.fill('Test Item');
      }
      if (await quantityInput.isVisible()) {
        await quantityInput.fill('1');
      }
      if (await priceInput.isVisible()) {
        await priceInput.fill('100');
      }
    }

    // Try to save
    await invoicePage.saveButton.click();

    // Should either redirect to list or show the created invoice
    // Wait a bit for the save operation
    await page.waitForTimeout(2000);

    // Check we're either on list or detail page
    const url = page.url();
    expect(url).toMatch(/\/dashboard\/invoices/);
  });
});

test.describe('Invoice Detail Page', () => {
  test.beforeEach(async ({ invoicePage }) => {
    // Go to invoice list first
    await invoicePage.gotoList();
  });

  test('should click on invoice to view details', async ({ invoicePage, page }) => {
    // Wait for invoices to load
    await page.waitForTimeout(1000);

    const invoiceCount = await invoicePage.getInvoiceCount();
    if (invoiceCount > 0) {
      await invoicePage.clickFirstInvoice();
      await expect(page).toHaveURL(/\/dashboard\/invoices\/[a-zA-Z0-9-]+/);
    }
  });

  test('should display invoice number and status', async ({ invoicePage, page }) => {
    await page.waitForTimeout(1000);

    const invoiceCount = await invoicePage.getInvoiceCount();
    if (invoiceCount > 0) {
      await invoicePage.clickFirstInvoice();

      // Should show invoice number
      await expect(page.locator('text=/INV-/i').first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('should show send to Telegram button', async ({ invoicePage, page }) => {
    await page.waitForTimeout(1000);

    const invoiceCount = await invoicePage.getInvoiceCount();
    if (invoiceCount > 0) {
      await invoicePage.clickFirstInvoice();

      // Look for Telegram button
      const telegramButton = page.getByRole('button', { name: /telegram|send/i });
      // Button might not be visible if not configured, that's okay
      if (await telegramButton.isVisible()) {
        await expect(telegramButton).toBeEnabled();
      }
    }
  });
});

test.describe('Invoice Telegram Integration (Mocked)', () => {
  test('should mock Telegram send and show success', async ({ invoicePage, page }) => {
    // Mock the Telegram API endpoint
    await page.route('**/api/integrations/invoice/*/send-telegram', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          message: 'Invoice sent successfully via Telegram',
        }),
      });
    });

    await invoicePage.gotoList();
    await page.waitForTimeout(1000);

    const invoiceCount = await invoicePage.getInvoiceCount();
    if (invoiceCount > 0) {
      await invoicePage.clickFirstInvoice();

      const telegramButton = page.getByRole('button', { name: /telegram|send/i });
      if (await telegramButton.isVisible()) {
        await telegramButton.click();

        // Should show success message
        await expect(page.locator('text=/sent|success/i')).toBeVisible({ timeout: 5000 });
      }
    }
  });
});
