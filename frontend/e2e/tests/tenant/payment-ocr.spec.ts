import { test, expect } from '../../fixtures/auth.fixture';
import invoiceData from '../../fixtures/invoices.json';

test.describe('Payment OCR Verification System', () => {
  const paymentScenarios = invoiceData.payment_verification_scenarios;

  test.beforeEach(async ({ page }) => {
    // Mock authenticated user
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            id: '123e4567-e89b-12d3-a456-426614174000',
            email: 'merchant@test.com',
            firstName: 'Test',
            lastName: 'Merchant',
            telegramLinked: true
          }
        })
      });
    });

    // Mock invoice details
    await page.route('**/api/invoice/invoices/*', async (route) => {
      const invoiceId = route.request().url().split('/').pop();

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: invoiceId,
          invoiceNumber: `INV-${invoiceId}`,
          amount: 2499.99,
          currency: 'USD',
          recipientName: 'Tech Solutions Inc',
          status: 'pending',
          expectedAccount: 'ABA Bank - 001234567',
          bank: 'ABA Bank',
          lineItems: [
            {
              name: 'iPhone 15 Pro',
              quantity: 2,
              unitPrice: 1200.00,
              total: 2400.00
            }
          ]
        })
      });
    });
  });

  test.describe('High Confidence Payment Verification', () => {
    test('should auto-approve payment with high OCR confidence', async ({ page }) => {
      const scenario = paymentScenarios.find(s => s.should_auto_approve);

      // Mock OCR verification API with high confidence
      await page.route('**/api/ocr/verify-payment', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            confidence: scenario!.expected_ocr_confidence,
            extractedData: {
              amount: scenario!.payment_amount,
              currency: scenario!.currency,
              recipientAccount: scenario!.recipient_account,
              bank: scenario!.bank,
              date: new Date().toISOString().split('T')[0]
            },
            verification: {
              amountMatch: true,
              bankMatch: true,
              accountMatch: true,
              autoApproved: true
            },
            message: 'Payment verified and approved automatically'
          })
        });
      });

      // Mock invoice update after verification
      await page.route('**/api/invoice/invoices/*/verify-payment', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: scenario!.invoice_id,
            status: 'paid',
            verifiedAt: new Date().toISOString(),
            verificationMethod: 'ocr_auto'
          })
        });
      });

      await page.goto('/dashboard/verify/INV-001');

      // Upload payment screenshot
      const fileInput = page.locator('input[type="file"]');
      await expect(fileInput).toBeVisible();

      // Simulate successful file upload
      await fileInput.setInputFiles({
        name: scenario!.screenshot_filename,
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      // Submit verification
      const verifyButton = page.getByRole('button', { name: /verify|submit/i });
      await verifyButton.click();

      // Should show auto-approval success
      await expect(
        page.locator('text=/payment.*verified.*approved|auto.*approved/i')
      ).toBeVisible({ timeout: 10000 });

      // Should show confidence score
      await expect(
        page.locator(`text=/${scenario!.expected_ocr_confidence}%/`)
      ).toBeVisible();

      // Should redirect to invoice detail with paid status
      await expect(page).toHaveURL(/\/dashboard\/invoices\/INV-001/);
      await expect(page.locator('text=/paid|verified/i')).toBeVisible();
    });

    test('should update inventory stock after payment verification', async ({ page }) => {
      // Mock stock adjustment API
      let stockUpdated = false;
      await page.route('**/api/inventory/products/*/adjust-stock', async (route) => {
        stockUpdated = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            newStock: 23, // 25 - 2 = 23
            movement: {
              type: 'sale',
              quantity: -2,
              reason: 'Invoice payment verified: INV-001'
            }
          })
        });
      });

      // Mock OCR with auto-approval
      await page.route('**/api/ocr/verify-payment', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            confidence: 90,
            verification: { autoApproved: true },
            extractedData: {
              amount: 2499.99,
              currency: 'USD'
            }
          })
        });
      });

      await page.goto('/dashboard/verify/INV-001');

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: 'payment_success.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.getByRole('button', { name: /verify/i }).click();

      // Wait for success message
      await expect(
        page.locator('text=/payment.*verified/i')
      ).toBeVisible({ timeout: 10000 });

      // Verify stock was updated
      expect(stockUpdated).toBe(true);
    });
  });

  test.describe('Medium Confidence Manual Review', () => {
    test('should require manual review for medium confidence', async ({ page }) => {
      // Mock OCR with medium confidence (manual review required)
      await page.route('**/api/ocr/verify-payment', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            confidence: 75, // Medium confidence
            extractedData: {
              amount: 2499.99,
              currency: 'USD',
              recipientAccount: '001234567',
              bank: 'ABA Bank'
            },
            verification: {
              amountMatch: true,
              bankMatch: true,
              accountMatch: true,
              autoApproved: false,
              requiresManualReview: true
            },
            message: 'Payment details match but confidence is medium. Manual review required.'
          })
        });
      });

      await page.goto('/dashboard/verify/INV-001');

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: 'payment_medium_quality.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.getByRole('button', { name: /verify/i }).click();

      // Should show manual review required message
      await expect(
        page.locator('text=/manual.*review.*required|admin.*approval/i')
      ).toBeVisible({ timeout: 10000 });

      // Should show confidence level
      await expect(page.locator('text=/75%/')).toBeVisible();

      // Should not auto-approve
      await expect(
        page.locator('text=/auto.*approved/i')
      ).not.toBeVisible();
    });

    test('should allow admin to manually approve payment', async ({ page }) => {
      // Mock admin user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: '123e4567-e89b-12d3-a456-426614174000',
              email: 'admin@test.com',
              role: 'admin',
              firstName: 'Admin',
              lastName: 'User'
            }
          })
        });
      });

      // Mock manual approval API
      await page.route('**/api/invoice/invoices/*/manual-approve', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            approvedBy: 'admin@test.com',
            approvedAt: new Date().toISOString(),
            status: 'paid'
          })
        });
      });

      await page.goto('/dashboard/admin/pending-verifications');

      // Should see pending payment
      await expect(
        page.locator('text=/INV-001|pending.*review/i')
      ).toBeVisible();

      // Click approve button
      const approveButton = page.getByRole('button', { name: /approve/i }).first();
      await approveButton.click();

      // Should show approval confirmation
      await expect(
        page.locator('text=/approved.*successfully|manually.*approved/i')
      ).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Low Confidence Rejection', () => {
    test('should reject payment with low OCR confidence', async ({ page }) => {
      // Mock OCR with low confidence
      await page.route('**/api/ocr/verify-payment', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            confidence: 45, // Low confidence
            extractedData: {
              amount: null,
              currency: null,
              recipientAccount: null,
              bank: null
            },
            verification: {
              autoApproved: false,
              rejected: true,
              reason: 'OCR confidence too low - image quality insufficient'
            },
            message: 'Unable to verify payment details. Please upload a clearer image.'
          })
        });
      });

      await page.goto('/dashboard/verify/INV-001');

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: 'payment_blurry.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.getByRole('button', { name: /verify/i }).click();

      // Should show rejection message
      await expect(
        page.locator('text=/unable.*verify|confidence.*low|clearer.*image/i')
      ).toBeVisible({ timeout: 10000 });

      // Should show retry option
      await expect(
        page.getByRole('button', { name: /try.*again|upload.*again/i })
      ).toBeVisible();
    });

    test('should reject payment with wrong bank details', async ({ page }) => {
      const scenario = paymentScenarios.find(s => s.reason?.includes('Wrong bank'));

      // Mock OCR with wrong bank account
      await page.route('**/api/ocr/verify-payment', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            confidence: scenario!.expected_ocr_confidence,
            extractedData: {
              amount: scenario!.payment_amount,
              currency: scenario!.currency,
              recipientAccount: scenario!.recipient_account,
              bank: scenario!.bank
            },
            verification: {
              amountMatch: true,
              bankMatch: false,
              accountMatch: false,
              autoApproved: false,
              rejected: true,
              reason: 'Payment sent to wrong bank account'
            },
            message: 'Payment verification failed: Wrong bank account detected.'
          })
        });
      });

      await page.goto('/dashboard/verify/INV-001');

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: scenario!.screenshot_filename,
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.getByRole('button', { name: /verify/i }).click();

      // Should show wrong bank error
      await expect(
        page.locator('text=/wrong.*bank.*account|verification.*failed/i')
      ).toBeVisible({ timeout: 10000 });

      // Should show expected vs actual bank details
      await expect(page.locator('text=/ABA Bank/i')).toBeVisible(); // Expected
      await expect(page.locator('text=/Wrong Bank/i')).toBeVisible(); // Actual
    });
  });

  test.describe('Partial Payment Handling', () => {
    test('should handle partial payment correctly', async ({ page }) => {
      const scenario = paymentScenarios.find(s => s.reason?.includes('Partial payment'));

      // Mock OCR with partial payment
      await page.route('**/api/ocr/verify-payment', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: false,
            confidence: scenario!.expected_ocr_confidence,
            extractedData: {
              amount: scenario!.payment_amount, // 250.00 vs expected 2499.99
              currency: scenario!.currency,
              recipientAccount: scenario!.recipient_account,
              bank: scenario!.bank
            },
            verification: {
              amountMatch: false,
              bankMatch: true,
              accountMatch: true,
              autoApproved: false,
              rejected: false,
              partialPayment: true,
              expectedAmount: 2499.99,
              receivedAmount: scenario!.payment_amount
            },
            message: `Partial payment detected: Received $${scenario!.payment_amount} of $2499.99`
          })
        });
      });

      await page.goto('/dashboard/verify/INV-001');

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: scenario!.screenshot_filename,
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.getByRole('button', { name: /verify/i }).click();

      // Should show partial payment message
      await expect(
        page.locator('text=/partial.*payment|received.*\$250|expected.*\$2499/i')
      ).toBeVisible({ timeout: 10000 });

      // Should offer options to accept partial or request remainder
      await expect(
        page.getByRole('button', { name: /accept.*partial/i })
      ).toBeVisible();
      await expect(
        page.getByRole('button', { name: /request.*remainder/i })
      ).toBeVisible();
    });
  });

  test.describe('Error Handling and Edge Cases', () => {
    test('should handle OCR API errors gracefully', async ({ page }) => {
      // Mock OCR API error
      await page.route('**/api/ocr/verify-payment', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'OCR service temporarily unavailable',
            message: 'Please try again in a few minutes or contact support.'
          })
        });
      });

      await page.goto('/dashboard/verify/INV-001');

      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: 'payment.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-image-data')
      });

      await page.getByRole('button', { name: /verify/i }).click();

      // Should show error message
      await expect(
        page.locator('text=/ocr.*service.*unavailable|try.*again.*minutes/i')
      ).toBeVisible({ timeout: 10000 });

      // Should offer manual verification option
      await expect(
        page.getByRole('button', { name: /manual.*verification|contact.*support/i })
      ).toBeVisible();
    });

    test('should validate file upload types and sizes', async ({ page }) => {
      await page.goto('/dashboard/verify/INV-001');

      const fileInput = page.locator('input[type="file"]');

      // Test invalid file type
      await fileInput.setInputFiles({
        name: 'document.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('fake-pdf-data')
      });

      // Should show file type error
      await expect(
        page.locator('text=/invalid.*file.*type|only.*images.*accepted/i')
      ).toBeVisible({ timeout: 5000 });

      // Test oversized file (mock)
      await page.route('**/api/ocr/verify-payment', async (route) => {
        await route.fulfill({
          status: 413,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'File too large',
            message: 'Maximum file size is 10MB. Please compress your image.'
          })
        });
      });

      await fileInput.setInputFiles({
        name: 'large_image.png',
        mimeType: 'image/png',
        buffer: Buffer.from('fake-large-image-data')
      });

      await page.getByRole('button', { name: /verify/i }).click();

      // Should show file size error
      await expect(
        page.locator('text=/file.*too.*large|maximum.*size.*10mb/i')
      ).toBeVisible({ timeout: 10000 });
    });
  });

  test.describe('Payment Verification History', () => {
    test('should show verification attempts history', async ({ page }) => {
      // Mock verification history
      await page.route('**/api/invoice/invoices/*/verification-history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            attempts: [
              {
                id: '1',
                timestamp: new Date(Date.now() - 3600000).toISOString(),
                confidence: 45,
                status: 'rejected',
                reason: 'OCR confidence too low'
              },
              {
                id: '2',
                timestamp: new Date(Date.now() - 1800000).toISOString(),
                confidence: 78,
                status: 'pending_review',
                reason: 'Manual review required'
              }
            ]
          })
        });
      });

      await page.goto('/dashboard/invoices/INV-001');

      // Should show verification history section
      await expect(
        page.locator('text=/verification.*history|payment.*attempts/i')
      ).toBeVisible();

      // Should show previous attempts
      await expect(page.locator('text=/rejected.*45%/i')).toBeVisible();
      await expect(page.locator('text=/pending.*review.*78%/i')).toBeVisible();
    });
  });
});