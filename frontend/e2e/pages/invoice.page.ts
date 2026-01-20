import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object Model for Invoice pages
 */
export class InvoicePage {
  readonly page: Page;

  // List page elements
  readonly createInvoiceButton: Locator;
  readonly invoiceTable: Locator;
  readonly invoiceRows: Locator;
  readonly searchInput: Locator;
  readonly statusFilter: Locator;

  // Stats cards
  readonly totalInvoicesCard: Locator;
  readonly pendingCard: Locator;
  readonly paidCard: Locator;
  readonly overdueCard: Locator;

  // Create/Edit form elements
  readonly customerSelect: Locator;
  readonly addLineItemButton: Locator;
  readonly lineItemRows: Locator;
  readonly productPickerButton: Locator;
  readonly dueDateInput: Locator;
  readonly notesInput: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;

  // Line item fields (within a row)
  readonly itemNameInput: Locator;
  readonly itemQuantityInput: Locator;
  readonly itemPriceInput: Locator;

  // Detail page elements
  readonly invoiceNumber: Locator;
  readonly invoiceStatus: Locator;
  readonly sendToTelegramButton: Locator;
  readonly editButton: Locator;
  readonly deleteButton: Locator;
  readonly subtotal: Locator;
  readonly total: Locator;

  constructor(page: Page) {
    this.page = page;

    // List page
    this.createInvoiceButton = page.getByRole('button', { name: /create|new invoice/i });
    this.invoiceTable = page.locator('table, [class*="invoice-table"], [class*="InvoiceTable"]');
    this.invoiceRows = page.locator('tbody tr, [class*="invoice-row"]');
    this.searchInput = page.getByPlaceholder(/search/i);
    this.statusFilter = page.locator('select[name*="status"], [class*="status-filter"]');

    // Stats
    this.totalInvoicesCard = page.locator('[class*="stat"], [class*="card"]').filter({ hasText: /total/i });
    this.pendingCard = page.locator('[class*="stat"], [class*="card"]').filter({ hasText: /pending/i });
    this.paidCard = page.locator('[class*="stat"], [class*="card"]').filter({ hasText: /paid/i });
    this.overdueCard = page.locator('[class*="stat"], [class*="card"]').filter({ hasText: /overdue/i });

    // Create/Edit form
    this.customerSelect = page.locator('select[name*="customer"], [class*="customer-select"]');
    this.addLineItemButton = page.getByRole('button', { name: /add.*item|add line/i });
    this.lineItemRows = page.locator('[class*="line-item"], [class*="LineItem"]');
    this.productPickerButton = page.getByRole('button', { name: /select product|product/i });
    this.dueDateInput = page.locator('input[type="date"], input[name*="due"]');
    this.notesInput = page.locator('textarea[name*="notes"], [class*="notes"] textarea');
    this.saveButton = page.getByRole('button', { name: /save|create|submit/i });
    this.cancelButton = page.getByRole('button', { name: /cancel/i });

    // Line item fields
    this.itemNameInput = page.locator('input[name*="name"], input[placeholder*="item name"]').first();
    this.itemQuantityInput = page.locator('input[name*="quantity"], input[type="number"]').first();
    this.itemPriceInput = page.locator('input[name*="price"], input[placeholder*="price"]').first();

    // Detail page
    this.invoiceNumber = page.locator('[class*="invoice-number"], h1, h2').filter({ hasText: /INV-/i });
    this.invoiceStatus = page.locator('[class*="status"], [class*="badge"]').first();
    this.sendToTelegramButton = page.getByRole('button', { name: /send.*telegram|telegram/i });
    this.editButton = page.getByRole('button', { name: /edit/i });
    this.deleteButton = page.getByRole('button', { name: /delete/i });
    this.subtotal = page.locator('text=/subtotal/i').locator('..').locator('[class*="amount"], span').last();
    this.total = page.locator('text=/total/i').locator('..').locator('[class*="amount"], span').last();
  }

  async gotoList() {
    await this.page.goto('/dashboard/invoices');
  }

  async gotoCreate() {
    await this.page.goto('/dashboard/invoices/new');
  }

  async gotoDetail(invoiceId: string) {
    await this.page.goto(`/dashboard/invoices/${invoiceId}`);
  }

  async createInvoice(data: {
    customer?: string;
    items: Array<{ name: string; quantity: number; price: number }>;
    dueDate?: string;
    notes?: string;
  }) {
    // Select customer if provided
    if (data.customer && await this.customerSelect.isVisible()) {
      await this.customerSelect.selectOption({ label: data.customer });
    }

    // Add line items
    for (const item of data.items) {
      await this.addLineItemButton.click();
      const lastRow = this.lineItemRows.last();
      await lastRow.locator('input[name*="name"], input').first().fill(item.name);
      await lastRow.locator('input[type="number"]').first().fill(String(item.quantity));
      await lastRow.locator('input[name*="price"], input').last().fill(String(item.price));
    }

    // Set due date if provided
    if (data.dueDate && await this.dueDateInput.isVisible()) {
      await this.dueDateInput.fill(data.dueDate);
    }

    // Add notes if provided
    if (data.notes && await this.notesInput.isVisible()) {
      await this.notesInput.fill(data.notes);
    }

    // Save
    await this.saveButton.click();
  }

  async expectInvoiceCreated() {
    // Should redirect to invoice detail or list
    await expect(this.page).toHaveURL(/\/dashboard\/invoices/);
  }

  async clickFirstInvoice() {
    await this.invoiceRows.first().click();
  }

  async searchInvoices(query: string) {
    await this.searchInput.fill(query);
    await this.page.keyboard.press('Enter');
  }

  async filterByStatus(status: string) {
    await this.statusFilter.selectOption(status);
  }

  async getInvoiceCount() {
    return await this.invoiceRows.count();
  }
}
