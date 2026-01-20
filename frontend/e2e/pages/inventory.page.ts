import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model for Inventory pages
 */
export class InventoryPage {
  readonly page: Page;

  // List page elements
  readonly createProductButton: Locator;
  readonly productTable: Locator;
  readonly productRows: Locator;
  readonly searchInput: Locator;
  readonly lowStockFilter: Locator;

  // Stats cards
  readonly totalProductsCard: Locator;
  readonly activeProductsCard: Locator;
  readonly lowStockCard: Locator;
  readonly stockValueCard: Locator;

  // Create/Edit modal elements
  readonly productModal: Locator;
  readonly nameInput: Locator;
  readonly skuInput: Locator;
  readonly priceInput: Locator;
  readonly costInput: Locator;
  readonly stockInput: Locator;
  readonly lowStockThresholdInput: Locator;
  readonly trackStockCheckbox: Locator;
  readonly saveProductButton: Locator;
  readonly cancelButton: Locator;

  // Adjust stock modal
  readonly adjustStockModal: Locator;
  readonly adjustmentTypeSelect: Locator;
  readonly adjustmentQuantityInput: Locator;
  readonly adjustmentNotesInput: Locator;
  readonly confirmAdjustButton: Locator;

  // Row actions
  readonly editButton: Locator;
  readonly deleteButton: Locator;
  readonly adjustStockButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // List page
    this.createProductButton = page.getByRole('button', { name: /create|add|new.*product/i });
    this.productTable = page.locator('table, [class*="product-table"], [class*="ProductTable"]');
    this.productRows = page.locator('tbody tr, [class*="product-row"]');
    this.searchInput = page.getByPlaceholder(/search/i);
    this.lowStockFilter = page.locator('[class*="low-stock-filter"], input[type="checkbox"]').filter({ hasText: /low stock/i });

    // Stats
    this.totalProductsCard = page.locator('[class*="stat"], [class*="card"]').filter({ hasText: /total.*product/i });
    this.activeProductsCard = page.locator('[class*="stat"], [class*="card"]').filter({ hasText: /active/i });
    this.lowStockCard = page.locator('[class*="stat"], [class*="card"]').filter({ hasText: /low stock/i });
    this.stockValueCard = page.locator('[class*="stat"], [class*="card"]').filter({ hasText: /value/i });

    // Create/Edit modal
    this.productModal = page.locator('[class*="modal"], [role="dialog"]');
    this.nameInput = page.locator('input[name="name"], input[placeholder*="name"]');
    this.skuInput = page.locator('input[name="sku"], input[placeholder*="sku"]');
    this.priceInput = page.locator('input[name="unit_price"], input[name="price"], input[placeholder*="price"]');
    this.costInput = page.locator('input[name="cost_price"], input[name="cost"]');
    this.stockInput = page.locator('input[name="current_stock"], input[name="stock"]');
    this.lowStockThresholdInput = page.locator('input[name="low_stock_threshold"], input[name*="threshold"]');
    this.trackStockCheckbox = page.locator('input[name="track_stock"], input[type="checkbox"]');
    this.saveProductButton = page.getByRole('button', { name: /save|create|add/i }).last();
    this.cancelButton = page.getByRole('button', { name: /cancel/i });

    // Adjust stock modal
    this.adjustStockModal = page.locator('[class*="modal"], [role="dialog"]').filter({ hasText: /adjust.*stock/i });
    this.adjustmentTypeSelect = page.locator('select[name*="type"], [class*="adjustment-type"]');
    this.adjustmentQuantityInput = page.locator('input[name*="quantity"]').last();
    this.adjustmentNotesInput = page.locator('textarea[name*="notes"], input[name*="notes"]');
    this.confirmAdjustButton = page.getByRole('button', { name: /confirm|adjust|save/i }).last();

    // Row actions
    this.editButton = page.getByRole('button', { name: /edit/i });
    this.deleteButton = page.getByRole('button', { name: /delete/i });
    this.adjustStockButton = page.getByRole('button', { name: /adjust/i });
  }

  async goto() {
    await this.page.goto('/dashboard/inventory');
  }

  async createProduct(data: {
    name: string;
    sku: string;
    price: number;
    cost?: number;
    stock?: number;
    lowStockThreshold?: number;
  }) {
    await this.createProductButton.click();
    await expect(this.productModal).toBeVisible();

    await this.nameInput.fill(data.name);
    await this.skuInput.fill(data.sku);
    await this.priceInput.fill(String(data.price));

    if (data.cost !== undefined) {
      await this.costInput.fill(String(data.cost));
    }
    if (data.stock !== undefined) {
      await this.stockInput.fill(String(data.stock));
    }
    if (data.lowStockThreshold !== undefined) {
      await this.lowStockThresholdInput.fill(String(data.lowStockThreshold));
    }

    await this.saveProductButton.click();
  }

  async adjustStock(productName: string, adjustment: {
    type: 'in' | 'out' | 'adjustment';
    quantity: number;
    notes?: string;
  }) {
    // Find the product row and click adjust
    const row = this.productRows.filter({ hasText: productName });
    await row.locator('button').filter({ hasText: /adjust/i }).click();

    await expect(this.adjustStockModal).toBeVisible();

    if (await this.adjustmentTypeSelect.isVisible()) {
      await this.adjustmentTypeSelect.selectOption(adjustment.type);
    }
    await this.adjustmentQuantityInput.fill(String(adjustment.quantity));

    if (adjustment.notes && await this.adjustmentNotesInput.isVisible()) {
      await this.adjustmentNotesInput.fill(adjustment.notes);
    }

    await this.confirmAdjustButton.click();
  }

  async searchProducts(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
  }

  async editProduct(productName: string) {
    const row = this.productRows.filter({ hasText: productName });
    await row.locator('button').filter({ hasText: /edit/i }).click();
  }

  async deleteProduct(productName: string) {
    const row = this.productRows.filter({ hasText: productName });
    await row.locator('button').filter({ hasText: /delete/i }).click();

    // Confirm deletion if there's a confirmation dialog
    const confirmButton = this.page.getByRole('button', { name: /confirm|yes|delete/i });
    if (await confirmButton.isVisible()) {
      await confirmButton.click();
    }
  }

  async getProductCount() {
    return await this.productRows.count();
  }

  async expectProductInList(productName: string) {
    await expect(this.productRows.filter({ hasText: productName })).toBeVisible();
  }

  async expectProductNotInList(productName: string) {
    await expect(this.productRows.filter({ hasText: productName })).not.toBeVisible();
  }
}
