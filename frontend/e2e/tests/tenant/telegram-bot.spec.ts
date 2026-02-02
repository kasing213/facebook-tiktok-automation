import { test, expect } from '../../fixtures/auth.fixture';
import telegramData from '../../fixtures/telegram-responses.json';
import testUsers from '../../fixtures/test-users.json';

test.describe('Telegram Bot Integration', () => {
  const telegramMocks = telegramData.telegram_api_mocks;
  const botCommands = telegramData.bot_commands;

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
            telegramLinked: false // Initially not linked
          }
        })
      });
    });

    // Mock Telegram Bot API calls
    await page.route('**/api/telegram/**', async (route) => {
      const url = route.request().url();
      const method = route.request().method();

      // Bot info endpoint
      if (url.includes('/getMe')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(telegramMocks.bot_info)
        });
      }
      // Send message endpoint
      else if (url.includes('/sendMessage')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(telegramMocks.send_message_success)
        });
      }
      // Send document endpoint
      else if (url.includes('/sendDocument')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(telegramMocks.send_document_success)
        });
      }
      else {
        await route.continue();
      }
    });
  });

  test.describe('Account Linking', () => {
    test('should generate Telegram linking code', async ({ page }) => {
      // Mock linking code generation
      await page.route('**/api/integrations/telegram/generate-link-code', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            linkingCode: 'AUTH123456',
            botUsername: 'KS_automations_bot',
            linkUrl: 'https://t.me/KS_automations_bot?start=AUTH123456',
            expiresAt: new Date(Date.now() + 900000).toISOString(), // 15 minutes
            instructions: 'Click the link below or send /start AUTH123456 to @KS_automations_bot'
          })
        });
      });

      await page.goto('/dashboard/integrations');

      // Click link Telegram button
      const linkButton = page.getByRole('button', { name: /link.*telegram|connect.*telegram/i });
      await linkButton.click();

      // Should show linking instructions
      await expect(page.locator('text=/AUTH123456/')).toBeVisible();
      await expect(page.locator('text=/@KS_automations_bot/i')).toBeVisible();
      await expect(
        page.getByRole('link', { name: /open.*telegram|start.*bot/i })
      ).toBeVisible();
    });

    test('should verify successful account linking', async ({ page }) => {
      // Mock linking verification
      await page.route('**/api/integrations/telegram/verify-linking', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            linkedAt: new Date().toISOString(),
            telegramUser: {
              id: 12345678,
              username: 'testuser',
              firstName: 'Test',
              lastName: 'User'
            },
            message: 'Telegram account linked successfully!'
          })
        });
      });

      // Mock updated user state
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: '123e4567-e89b-12d3-a456-426614174000',
              email: 'merchant@test.com',
              telegramLinked: true,
              telegramUsername: 'testuser'
            }
          })
        });
      });

      await page.goto('/dashboard/integrations');

      // Should show linked status
      await expect(
        page.locator('text=/linked.*successfully|connected.*telegram/i')
      ).toBeVisible();

      // Should show Telegram username
      await expect(page.locator('text=/@testuser/i')).toBeVisible();

      // Should have unlink option
      await expect(
        page.getByRole('button', { name: /unlink|disconnect/i })
      ).toBeVisible();
    });

    test('should handle linking timeout', async ({ page }) => {
      // Mock expired linking code
      await page.route('**/api/integrations/telegram/verify-linking', async (route) => {
        await route.fulfill({
          status: 408,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Linking timeout',
            message: 'Linking code expired. Please generate a new code.',
            expired: true
          })
        });
      });

      await page.goto('/dashboard/integrations');

      // Simulate checking link status after timeout
      await page.getByRole('button', { name: /check.*status|refresh/i }).click();

      // Should show timeout message
      await expect(
        page.locator('text=/linking.*expired|generate.*new.*code/i')
      ).toBeVisible();

      // Should offer to generate new code
      await expect(
        page.getByRole('button', { name: /generate.*new|try.*again/i })
      ).toBeVisible();
    });
  });

  test.describe('Invoice Notifications', () => {
    test('should send invoice via Telegram successfully', async ({ page }) => {
      // Mock successful Telegram send
      await page.route('**/api/integrations/telegram/send-invoice', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            messageId: 789,
            sentAt: new Date().toISOString(),
            recipientCount: 1,
            message: 'Invoice sent successfully via Telegram'
          })
        });
      });

      await page.goto('/dashboard/invoices/INV-001');

      // Click send to Telegram button
      const telegramButton = page.getByRole('button', { name: /send.*telegram|telegram/i });
      await telegramButton.click();

      // Should show success notification
      await expect(
        page.locator('text=/sent.*successfully|telegram.*sent/i')
      ).toBeVisible({ timeout: 5000 });

      // Should show message details
      await expect(page.locator('text=/message.*id.*789/i')).toBeVisible();
    });

    test('should handle Telegram API errors gracefully', async ({ page }) => {
      // Mock Telegram API error
      await page.route('**/api/integrations/telegram/send-invoice', async (route) => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Telegram API error',
            message: 'Chat not found. Please ensure your Telegram account is linked.',
            telegramError: telegramMocks.error_responses.chat_not_found
          })
        });
      });

      await page.goto('/dashboard/invoices/INV-001');

      const telegramButton = page.getByRole('button', { name: /send.*telegram/i });
      await telegramButton.click();

      // Should show error message
      await expect(
        page.locator('text=/telegram.*error|chat.*not.*found/i')
      ).toBeVisible({ timeout: 5000 });

      // Should suggest relinking account
      await expect(
        page.locator('text=/ensure.*account.*linked|relink.*telegram/i')
      ).toBeVisible();
    });

    test('should show invoice delivery confirmation', async ({ page }) => {
      // Mock delivery tracking
      await page.route('**/api/integrations/telegram/delivery-status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            messageId: 789,
            status: 'delivered',
            deliveredAt: new Date().toISOString(),
            readAt: new Date(Date.now() + 60000).toISOString(),
            recipient: {
              telegramId: 12345678,
              username: 'customer_user',
              firstName: 'Customer'
            }
          })
        });
      });

      await page.goto('/dashboard/invoices/INV-001');

      // Should show delivery status
      await expect(page.locator('text=/delivered|sent.*successfully/i')).toBeVisible();
      await expect(page.locator('text=/read.*at/i')).toBeVisible();
    });
  });

  test.describe('Bot Commands Testing', () => {
    test('should respond to /start command correctly', async ({ page }) => {
      // Mock webhook simulation endpoint
      await page.route('**/api/telegram/webhook-test', async (route) => {
        const requestData = await route.request().postDataJSON();

        if (requestData.command === '/start AUTH123456') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              response: botCommands['/start'].expected_response,
              success: true,
              linked: true
            })
          });
        }
      });

      await page.goto('/dashboard/integrations/telegram-test');

      // Simulate sending /start command
      const commandInput = page.locator('input[placeholder*="command"]');
      await commandInput.fill('/start AUTH123456');

      const sendButton = page.getByRole('button', { name: /send.*command/i });
      await sendButton.click();

      // Should show expected response
      await expect(
        page.locator('text=/Account.*linked.*successfully/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should respond to /status command', async ({ page }) => {
      await page.route('**/api/telegram/webhook-test', async (route) => {
        const requestData = await route.request().postDataJSON();

        if (requestData.command === '/status') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              response: botCommands['/status'].expected_response.replace('{{timestamp}}', new Date().toLocaleString()),
              success: true
            })
          });
        }
      });

      await page.goto('/dashboard/integrations/telegram-test');

      const commandInput = page.locator('input[placeholder*="command"]');
      await commandInput.fill('/status');

      await page.getByRole('button', { name: /send.*command/i }).click();

      // Should show status information
      await expect(page.locator('text=/System.*Status.*Online/i')).toBeVisible();
      await expect(page.locator('text=/Invoices.*4.*total/i')).toBeVisible();
      await expect(page.locator('text=/Subscription.*Free.*Tier/i')).toBeVisible();
    });

    test('should respond to /inventory command', async ({ page }) => {
      await page.route('**/api/telegram/webhook-test', async (route) => {
        const requestData = await route.request().postDataJSON();

        if (requestData.command === '/inventory') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              response: botCommands['/inventory'].expected_response,
              success: true
            })
          });
        }
      });

      await page.goto('/dashboard/integrations/telegram-test');

      const commandInput = page.locator('input[placeholder*="command"]');
      await commandInput.fill('/inventory');

      await page.getByRole('button', { name: /send.*command/i }).click();

      // Should show inventory status
      await expect(page.locator('text=/Inventory.*Status/i')).toBeVisible();
      await expect(page.locator('text=/Total.*Products.*10/i')).toBeVisible();
      await expect(page.locator('text=/Low.*Stock.*Items.*2/i')).toBeVisible();
    });

    test('should handle unknown commands gracefully', async ({ page }) => {
      await page.route('**/api/telegram/webhook-test', async (route) => {
        const requestData = await route.request().postDataJSON();

        if (requestData.command === '/unknown') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              response: "❓ Unknown command. Type /help to see available commands.",
              success: true
            })
          });
        }
      });

      await page.goto('/dashboard/integrations/telegram-test');

      const commandInput = page.locator('input[placeholder*="command"]');
      await commandInput.fill('/unknown');

      await page.getByRole('button', { name: /send.*command/i }).click();

      // Should show unknown command response
      await expect(page.locator('text=/Unknown.*command/i')).toBeVisible();
      await expect(page.locator('text=/Type.*\/help/i')).toBeVisible();
    });
  });

  test.describe('Payment Verification via Telegram', () => {
    test('should receive payment screenshot via Telegram', async ({ page }) => {
      // Mock incoming webhook with photo
      await page.route('**/api/telegram/webhook', async (route) => {
        if (route.request().method() === 'POST') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              processed: true,
              message: 'Payment screenshot received',
              verification: {
                initiated: true,
                invoiceId: 'INV-001',
                confidence: 85,
                autoApproved: true
              }
            })
          });
        }
      });

      // Simulate webhook delivery
      await page.goto('/dashboard/admin/telegram-webhooks');

      // Should show recent webhook activity
      await expect(
        page.locator('text=/payment.*screenshot.*received/i')
      ).toBeVisible();

      // Should show verification result
      await expect(page.locator('text=/confidence.*85%/i')).toBeVisible();
      await expect(page.locator('text=/auto.*approved/i')).toBeVisible();
    });

    test('should notify customer of verification status', async ({ page }) => {
      // Mock verification notification
      await page.route('**/api/telegram/notify-verification', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            messageId: 791,
            notificationType: 'verification_approved',
            message: '✅ Payment verified and approved! Your invoice INV-001 is now marked as paid.'
          })
        });
      });

      await page.goto('/dashboard/invoices/INV-001');

      // Trigger verification notification
      const notifyButton = page.getByRole('button', { name: /notify.*customer/i });
      if (await notifyButton.isVisible()) {
        await notifyButton.click();

        // Should show notification sent confirmation
        await expect(
          page.locator('text=/notification.*sent|customer.*notified/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });

    test('should handle verification failure notification', async ({ page }) => {
      // Mock verification failure notification
      await page.route('**/api/telegram/notify-verification', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            messageId: 792,
            notificationType: 'verification_failed',
            message: '❌ Payment verification failed for invoice INV-001. Please upload a clearer image or contact support.'
          })
        });
      });

      await page.goto('/dashboard/invoices/INV-001');

      // Should handle verification failure
      const failureButton = page.getByRole('button', { name: /send.*failure.*notification/i });
      if (await failureButton.isVisible()) {
        await failureButton.click();

        await expect(
          page.locator('text=/verification.*failed.*notification.*sent/i')
        ).toBeVisible();
      }
    });
  });

  test.describe('Low Stock Alerts', () => {
    test('should send low stock notifications via Telegram', async ({ page }) => {
      // Mock low stock alert
      await page.route('**/api/inventory/check-low-stock', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            lowStockProducts: [
              {
                id: 'LOW-001',
                name: 'Low Stock Item 1',
                currentStock: 2,
                threshold: 5,
                price: 49.99
              }
            ],
            alertsSent: true,
            telegramMessageId: 793
          })
        });
      });

      await page.goto('/dashboard/inventory');

      // Trigger low stock check
      const checkStockButton = page.getByRole('button', { name: /check.*stock|run.*alert/i });
      if (await checkStockButton.isVisible()) {
        await checkStockButton.click();

        // Should show alert sent confirmation
        await expect(
          page.locator('text=/low.*stock.*alert.*sent/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });

    test('should show low stock via /lowstock command', async ({ page }) => {
      await page.route('**/api/telegram/webhook-test', async (route) => {
        const requestData = await route.request().postDataJSON();

        if (requestData.command === '/lowstock') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              response: botCommands['/lowstock'].expected_response,
              success: true
            })
          });
        }
      });

      await page.goto('/dashboard/integrations/telegram-test');

      const commandInput = page.locator('input[placeholder*="command"]');
      await commandInput.fill('/lowstock');

      await page.getByRole('button', { name: /send.*command/i }).click();

      // Should show low stock details
      await expect(page.locator('text=/Low.*Stock.*Alert/i')).toBeVisible();
      await expect(page.locator('text=/LOW-001.*Low.*Stock.*Item.*1/i')).toBeVisible();
      await expect(page.locator('text=/Stock.*2.*Threshold.*5/i')).toBeVisible();
    });
  });

  test.describe('Bot Configuration and Health', () => {
    test('should check bot health status', async ({ page }) => {
      // Mock bot health check
      await page.route('**/api/telegram/bot/health', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            botInfo: telegramMocks.bot_info.result,
            webhookStatus: {
              url: 'https://facebook-automation.railway.app/api/telegram/webhook',
              hasCustomCertificate: false,
              pendingUpdateCount: 0,
              lastErrorDate: null,
              maxConnections: 40,
              allowedUpdates: ['message', 'photo']
            },
            lastMessageAt: new Date(Date.now() - 60000).toISOString(),
            status: 'healthy'
          })
        });
      });

      await page.goto('/dashboard/integrations/telegram-health');

      // Should show bot status
      await expect(page.locator('text=/Bot.*Status.*Healthy/i')).toBeVisible();
      await expect(page.locator('text=/@KS_automations_bot/i')).toBeVisible();
      await expect(page.locator('text=/webhook.*configured/i')).toBeVisible();
    });

    test('should detect bot configuration issues', async ({ page }) => {
      // Mock bot health issues
      await page.route('**/api/telegram/bot/health', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Bot configuration error',
            issues: [
              'Invalid bot token',
              'Webhook not set',
              'No recent activity'
            ],
            status: 'unhealthy',
            lastError: 'Unauthorized: Invalid bot token'
          })
        });
      });

      await page.goto('/dashboard/integrations/telegram-health');

      // Should show configuration issues
      await expect(page.locator('text=/Bot.*Status.*Unhealthy/i')).toBeVisible();
      await expect(page.locator('text=/Invalid.*bot.*token/i')).toBeVisible();
      await expect(page.locator('text=/Webhook.*not.*set/i')).toBeVisible();

      // Should offer troubleshooting options
      await expect(
        page.getByRole('button', { name: /fix.*configuration|reconfigure/i })
      ).toBeVisible();
    });
  });
});