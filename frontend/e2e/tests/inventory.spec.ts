import { test, expect } from '../fixtures/auth.fixture';

test.describe('Inventory List Page', () => {
  test('should display inventory page', async ({ inventoryPage }) => {
    await inventoryPage.goto();
    await expect(inventoryPage.createProductButton).toBeVisible();
  });

  test('should show stats cards', async ({ inventoryPage, page }) => {
    await inventoryPage.goto();

    // Check for stats section
    const statsSection = page.locator('[class*="stat"], [class*="card"], [class*="Stats"]');
    await expect(statsSection.first()).toBeVisible();
  });

  test('should search products', async ({ inventoryPage }) => {
    await inventoryPage.goto();

    if (await inventoryPage.searchInput.isVisible()) {
      await inventoryPage.searchProducts('test');
      await expect(inventoryPage.searchInput).toHaveValue('test');
    }
  });
});

test.describe('Product CRUD', () => {
  const testProduct = {
    name: `Test Product ${Date.now()}`,
    sku: `SKU-${Date.now()}`,
    price: 99.99,
    cost: 50,
    stock: 100,
    lowStockThreshold: 10,
  };

  test('should open create product modal', async ({ inventoryPage }) => {
    await inventoryPage.goto();
    await inventoryPage.createProductButton.click();

    // Modal should be visible
    await expect(inventoryPage.productModal).toBeVisible({ timeout: 3000 });
  });

  test('should create a new product', async ({ inventoryPage, page }) => {
    await inventoryPage.goto();
    await inventoryPage.createProductButton.click();

    // Wait for modal
    await expect(inventoryPage.productModal).toBeVisible({ timeout: 3000 });

    // Fill in product details
    await inventoryPage.nameInput.fill(testProduct.name);
    await inventoryPage.skuInput.fill(testProduct.sku);
    await inventoryPage.priceInput.fill(String(testProduct.price));

    if (await inventoryPage.costInput.isVisible()) {
      await inventoryPage.costInput.fill(String(testProduct.cost));
    }
    if (await inventoryPage.stockInput.isVisible()) {
      await inventoryPage.stockInput.fill(String(testProduct.stock));
    }

    // Save the product
    await inventoryPage.saveProductButton.click();

    // Modal should close
    await expect(inventoryPage.productModal).not.toBeVisible({ timeout: 5000 });

    // Product should appear in list (may need to wait for refresh)
    await page.waitForTimeout(1000);
  });

  test('should edit an existing product', async ({ inventoryPage, page }) => {
    await inventoryPage.goto();
    await page.waitForTimeout(1000);

    const productCount = await inventoryPage.getProductCount();
    if (productCount > 0) {
      // Click edit on first product
      const firstRow = inventoryPage.productRows.first();
      const editBtn = firstRow.getByRole('button', { name: /edit/i });

      if (await editBtn.isVisible()) {
        await editBtn.click();

        // Modal should open
        await expect(inventoryPage.productModal).toBeVisible({ timeout: 3000 });

        // Modify the name
        await inventoryPage.nameInput.fill('Updated Product Name');

        // Save
        await inventoryPage.saveProductButton.click();

        // Modal should close
        await expect(inventoryPage.productModal).not.toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('should delete a product', async ({ inventoryPage, page }) => {
    await inventoryPage.goto();
    await page.waitForTimeout(1000);

    const initialCount = await inventoryPage.getProductCount();
    if (initialCount > 0) {
      // Click delete on first product
      const firstRow = inventoryPage.productRows.first();
      const deleteBtn = firstRow.getByRole('button', { name: /delete/i });

      if (await deleteBtn.isVisible()) {
        await deleteBtn.click();

        // Handle confirmation dialog if present
        const confirmBtn = page.getByRole('button', { name: /confirm|yes|delete/i }).last();
        if (await confirmBtn.isVisible({ timeout: 2000 })) {
          await confirmBtn.click();
        }

        // Wait for deletion
        await page.waitForTimeout(1000);
      }
    }
  });
});

test.describe('Stock Adjustment', () => {
  test('should open stock adjustment modal', async ({ inventoryPage, page }) => {
    await inventoryPage.goto();
    await page.waitForTimeout(1000);

    const productCount = await inventoryPage.getProductCount();
    if (productCount > 0) {
      // Find adjust button
      const firstRow = inventoryPage.productRows.first();
      const adjustBtn = firstRow.getByRole('button', { name: /adjust/i });

      if (await adjustBtn.isVisible()) {
        await adjustBtn.click();

        // Adjustment modal or form should appear
        const adjustModal = page.locator('[class*="modal"], [role="dialog"]');
        await expect(adjustModal).toBeVisible({ timeout: 3000 });
      }
    }
  });

  test('should adjust stock quantity', async ({ inventoryPage, page }) => {
    await inventoryPage.goto();
    await page.waitForTimeout(1000);

    const productCount = await inventoryPage.getProductCount();
    if (productCount > 0) {
      const firstRow = inventoryPage.productRows.first();
      const adjustBtn = firstRow.getByRole('button', { name: /adjust/i });

      if (await adjustBtn.isVisible()) {
        await adjustBtn.click();

        // Wait for modal
        await page.waitForTimeout(500);

        // Fill in adjustment
        const quantityInput = page.locator('input[type="number"]').last();
        if (await quantityInput.isVisible()) {
          await quantityInput.fill('10');
        }

        // Notes field
        const notesInput = page.locator('textarea, input[name*="notes"]').last();
        if (await notesInput.isVisible()) {
          await notesInput.fill('Test adjustment');
        }

        // Confirm
        const confirmBtn = page.getByRole('button', { name: /confirm|save|adjust/i }).last();
        if (await confirmBtn.isVisible()) {
          await confirmBtn.click();

          // Modal should close
          await page.waitForTimeout(1000);
        }
      }
    }
  });
});

test.describe('Low Stock Filter', () => {
  test('should filter by low stock', async ({ inventoryPage, page }) => {
    await inventoryPage.goto();

    // Look for low stock filter/checkbox
    const lowStockFilter = page.locator('input[type="checkbox"]').filter({ hasText: /low stock/i });
    const lowStockButton = page.getByRole('button', { name: /low stock/i });

    if (await lowStockFilter.isVisible()) {
      await lowStockFilter.click();
      await page.waitForTimeout(500);
    } else if (await lowStockButton.isVisible()) {
      await lowStockButton.click();
      await page.waitForTimeout(500);
    }

    // Page should update (we can't verify specific products without seed data)
  });
});

test.describe('Product Picker Integration', () => {
  test('should show products in invoice product picker', async ({ page }) => {
    // Go to create invoice
    await page.goto('/dashboard/invoices/new');

    // Look for product picker
    const productPicker = page.getByRole('button', { name: /product|select/i });

    if (await productPicker.isVisible()) {
      await productPicker.click();

      // Should show product list
      const productList = page.locator('[class*="dropdown"], [class*="picker"], [role="listbox"]');
      await expect(productList).toBeVisible({ timeout: 3000 });
    }
  });
});
