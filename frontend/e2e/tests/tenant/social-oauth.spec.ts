import { test, expect } from '../../fixtures/auth.fixture';

test.describe('Social Media OAuth Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authenticated user
    await page.route('**/api/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            id: '123e4567-e89b-12d3-a456-426614174000',
            email: 'oauth-test@example.com',
            firstName: 'OAuth',
            lastName: 'Tester',
            socialConnections: []
          }
        })
      });
    });
  });

  test.describe('Facebook OAuth Integration', () => {
    test('should initiate Facebook OAuth flow', async ({ page }) => {
      // Mock Facebook OAuth initiation
      await page.route('**/api/oauth/facebook/authorize', async (route) => {
        const fbAuthUrl = new URL('https://www.facebook.com/v18.0/dialog/oauth');
        fbAuthUrl.searchParams.set('client_id', 'test_fb_app_id');
        fbAuthUrl.searchParams.set('redirect_uri', 'https://facebook-automation.vercel.app/auth/facebook/callback');
        fbAuthUrl.searchParams.set('scope', 'pages_manage_posts,pages_read_engagement,pages_manage_metadata');
        fbAuthUrl.searchParams.set('state', 'test-state-token-123');

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            authUrl: fbAuthUrl.toString(),
            state: 'test-state-token-123',
            scopes: ['pages_manage_posts', 'pages_read_engagement', 'pages_manage_metadata']
          })
        });
      });

      await page.goto('/dashboard/integrations');

      // Click connect Facebook button
      const fbConnectButton = page.getByRole('button', { name: /connect.*facebook|link.*facebook/i });
      await fbConnectButton.click();

      // Should open Facebook OAuth popup or redirect
      await expect(
        page.locator('text=/connecting.*facebook|facebook.*authorization/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should handle Facebook OAuth callback success', async ({ page }) => {
      // Mock successful OAuth callback
      await page.route('**/api/oauth/facebook/callback**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            connection: {
              id: 'fb-connection-123',
              provider: 'facebook',
              providerUserId: 'fb_user_12345',
              accessToken: 'fb_access_token_encrypted',
              refreshToken: 'fb_refresh_token_encrypted',
              expiresAt: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(), // 60 days
              scopes: ['pages_manage_posts', 'pages_read_engagement'],
              profile: {
                id: 'fb_user_12345',
                name: 'Test Facebook User',
                email: 'fbuser@example.com'
              },
              pages: [
                {
                  id: 'fb_page_123',
                  name: 'Test Business Page',
                  category: 'Business',
                  accessToken: 'page_access_token_encrypted'
                }
              ]
            }
          })
        });
      });

      // Simulate OAuth callback URL
      await page.goto('/auth/facebook/callback?code=test_auth_code&state=test-state-token-123');

      // Should show success message
      await expect(
        page.locator('text=/facebook.*connected|connection.*successful/i')
      ).toBeVisible({ timeout: 5000 });

      // Should redirect to integrations page
      await expect(page).toHaveURL(/\/dashboard\/integrations/);

      // Should show connected Facebook account
      await expect(page.locator('text=/Test Business Page/i')).toBeVisible();
    });

    test('should handle Facebook OAuth errors', async ({ page }) => {
      // Mock OAuth error scenarios
      const errorScenarios = [
        {
          error: 'access_denied',
          description: 'User cancelled the authorization',
          expectedMessage: 'Facebook authorization was cancelled'
        },
        {
          error: 'invalid_request',
          description: 'Invalid OAuth parameters',
          expectedMessage: 'Facebook authorization failed due to invalid request'
        }
      ];

      for (const scenario of errorScenarios) {
        await page.route('**/api/oauth/facebook/callback**', async (route) => {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              success: false,
              error: scenario.error,
              error_description: scenario.description,
              message: scenario.expectedMessage
            })
          });
        });

        await page.goto(`/auth/facebook/callback?error=${scenario.error}&error_description=${encodeURIComponent(scenario.description)}`);

        // Should show appropriate error message
        await expect(
          page.locator(`text=/${scenario.expectedMessage}/i`)
        ).toBeVisible({ timeout: 5000 });
      }
    });

    test('should manage Facebook page permissions', async ({ page }) => {
      // Mock Facebook connection with pages
      await page.route('**/api/oauth/facebook/pages', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            pages: [
              {
                id: 'fb_page_123',
                name: 'Main Business Page',
                category: 'Local Business',
                accessToken: 'page_token_1',
                permissions: ['MANAGE', 'CREATE_CONTENT', 'MODERATE', 'ADVERTISE'],
                connected: true
              },
              {
                id: 'fb_page_456',
                name: 'Secondary Page',
                category: 'Brand',
                accessToken: 'page_token_2',
                permissions: ['MANAGE', 'CREATE_CONTENT'],
                connected: false
              }
            ]
          })
        });
      });

      await page.goto('/dashboard/integrations/facebook');

      // Should display available pages
      await expect(page.locator('text=/Main Business Page/i')).toBeVisible();
      await expect(page.locator('text=/Secondary Page/i')).toBeVisible();

      // Should show page permissions
      await expect(page.locator('text=/MANAGE|CREATE_CONTENT|MODERATE/i')).toBeVisible();

      // Should allow connecting/disconnecting pages
      const connectButton = page.getByRole('button', { name: /connect.*secondary/i });
      if (await connectButton.isVisible()) {
        await connectButton.click();

        await expect(
          page.locator('text=/secondary.*page.*connected/i')
        ).toBeVisible({ timeout: 3000 });
      }
    });
  });

  test.describe('TikTok OAuth Integration', () => {
    test('should initiate TikTok OAuth flow', async ({ page }) => {
      // Mock TikTok OAuth initiation
      await page.route('**/api/oauth/tiktok/authorize', async (route) => {
        const tiktokAuthUrl = new URL('https://www.tiktok.com/v2/auth/authorize/');
        tiktokAuthUrl.searchParams.set('client_key', 'test_tiktok_client_key');
        tiktokAuthUrl.searchParams.set('redirect_uri', 'https://facebook-automation.vercel.app/auth/tiktok/callback');
        tiktokAuthUrl.searchParams.set('scope', 'user.info.basic,video.upload,video.publish');
        tiktokAuthUrl.searchParams.set('state', 'test-tiktok-state-456');

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            authUrl: tiktokAuthUrl.toString(),
            state: 'test-tiktok-state-456',
            scopes: ['user.info.basic', 'video.upload', 'video.publish']
          })
        });
      });

      await page.goto('/dashboard/integrations');

      // Click connect TikTok button
      const tiktokConnectButton = page.getByRole('button', { name: /connect.*tiktok|link.*tiktok/i });
      await tiktokConnectButton.click();

      // Should show TikTok authorization flow
      await expect(
        page.locator('text=/connecting.*tiktok|tiktok.*authorization/i')
      ).toBeVisible({ timeout: 5000 });
    });

    test('should handle TikTok OAuth callback success', async ({ page }) => {
      // Mock successful TikTok OAuth callback
      await page.route('**/api/oauth/tiktok/callback**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            connection: {
              id: 'tiktok-connection-456',
              provider: 'tiktok',
              providerUserId: 'tiktok_user_67890',
              accessToken: 'tiktok_access_token_encrypted',
              refreshToken: 'tiktok_refresh_token_encrypted',
              expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days
              scopes: ['user.info.basic', 'video.upload', 'video.publish'],
              profile: {
                openId: 'tiktok_user_67890',
                unionId: 'tiktok_union_123',
                displayName: 'TikTok Creator',
                avatar: 'https://tiktok-avatar-url.com/avatar.jpg'
              }
            }
          })
        });
      });

      await page.goto('/auth/tiktok/callback?code=test_tiktok_code&state=test-tiktok-state-456&scopes=user.info.basic,video.upload');

      // Should show TikTok connection success
      await expect(
        page.locator('text=/tiktok.*connected|connection.*successful/i')
      ).toBeVisible({ timeout: 5000 });

      // Should redirect to integrations page
      await expect(page).toHaveURL(/\/dashboard\/integrations/);

      // Should show connected TikTok account
      await expect(page.locator('text=/TikTok Creator/i')).toBeVisible();
    });

    test('should handle TikTok API limitations', async ({ page }) => {
      // Mock TikTok API with rate limiting
      await page.route('**/api/oauth/tiktok/user-info', async (route) => {
        await route.fulfill({
          status: 429,
          contentType: 'application/json',
          headers: {
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': String(Math.floor(Date.now() / 1000) + 3600)
          },
          body: JSON.stringify({
            error: 'Rate limit exceeded',
            message: 'TikTok API rate limit reached. Please try again later.',
            retryAfter: 3600
          })
        });
      });

      await page.goto('/dashboard/integrations/tiktok');

      // Try to refresh user info
      const refreshButton = page.getByRole('button', { name: /refresh.*info|update.*profile/i });
      if (await refreshButton.isVisible()) {
        await refreshButton.click();

        // Should show rate limit message
        await expect(
          page.locator('text=/rate.*limit.*exceeded|try.*again.*later/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });
  });

  test.describe('OAuth Token Management', () => {
    test('should handle token refresh automatically', async ({ page }) => {
      let refreshCalled = false;

      // Mock token refresh for Facebook
      await page.route('**/api/oauth/facebook/refresh', async (route) => {
        refreshCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            accessToken: 'new_fb_access_token',
            expiresAt: new Date(Date.now() + 60 * 24 * 60 * 60 * 1000).toISOString(),
            refreshedAt: new Date().toISOString()
          })
        });
      });

      // Mock Facebook connection with expiring token
      await page.route('**/api/oauth/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            connected: true,
            tokenExpiresAt: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(), // Expires in 2 days
            needsRefresh: true,
            profile: {
              name: 'Test User',
              id: 'fb_user_123'
            }
          })
        });
      });

      await page.goto('/dashboard/integrations/facebook');

      // Should show token expiration warning
      await expect(
        page.locator('text=/token.*expiring|expires.*in.*2.*days/i')
      ).toBeVisible();

      // Should offer manual refresh option
      const refreshTokenButton = page.getByRole('button', { name: /refresh.*token|renew.*connection/i });
      if (await refreshTokenButton.isVisible()) {
        await refreshTokenButton.click();

        // Should show refresh success
        await expect(
          page.locator('text=/token.*refreshed|connection.*renewed/i')
        ).toBeVisible({ timeout: 5000 });

        expect(refreshCalled).toBe(true);
      }
    });

    test('should handle expired tokens gracefully', async ({ page }) => {
      // Mock expired token response
      await page.route('**/api/oauth/facebook/pages', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Token expired',
            message: 'Facebook access token has expired. Please reconnect your account.',
            expired: true,
            reconnectRequired: true
          })
        });
      });

      await page.goto('/dashboard/integrations/facebook');

      // Should show reconnection prompt
      await expect(
        page.locator('text=/token.*expired|reconnect.*required/i')
      ).toBeVisible({ timeout: 5000 });

      // Should offer reconnection option
      await expect(
        page.getByRole('button', { name: /reconnect.*facebook|connect.*again/i })
      ).toBeVisible();
    });

    test('should validate OAuth scope permissions', async ({ page }) => {
      // Mock insufficient permissions
      await page.route('**/api/oauth/facebook/validate-scopes', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            valid: false,
            currentScopes: ['pages_show_list', 'pages_read_engagement'],
            requiredScopes: ['pages_manage_posts', 'pages_manage_metadata'],
            missingScopes: ['pages_manage_posts', 'pages_manage_metadata'],
            message: 'Additional permissions required for full functionality'
          })
        });
      });

      await page.goto('/dashboard/integrations/facebook');

      // Should show scope validation warning
      await expect(
        page.locator('text=/additional.*permissions.*required|missing.*scopes/i')
      ).toBeVisible();

      // Should show what permissions are missing
      await expect(page.locator('text=/pages_manage_posts/i')).toBeVisible();
      await expect(page.locator('text=/pages_manage_metadata/i')).toBeVisible();

      // Should offer to request additional permissions
      await expect(
        page.getByRole('button', { name: /request.*permissions|upgrade.*access/i })
      ).toBeVisible();
    });
  });

  test.describe('Social Media Content Publishing', () => {
    test('should publish content to Facebook', async ({ page }) => {
      // Mock Facebook publishing
      await page.route('**/api/social/facebook/publish', async (route) => {
        const requestData = await route.request().postDataJSON();

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            postId: 'fb_post_12345',
            publishedAt: new Date().toISOString(),
            postUrl: `https://facebook.com/testpage/posts/fb_post_12345`,
            content: requestData.message,
            pageId: requestData.pageId,
            metrics: {
              reach: 0,
              engagement: 0,
              shares: 0
            }
          })
        });
      });

      await page.goto('/dashboard/marketing/publish');

      // Fill in post content
      const contentTextarea = page.locator('textarea[placeholder*="content"], textarea[name*="message"]');
      if (await contentTextarea.isVisible()) {
        await contentTextarea.fill('Test post content for Facebook automation');

        // Select Facebook platform
        const facebookOption = page.locator('input[value="facebook"], input[type="checkbox"][name*="facebook"]');
        if (await facebookOption.isVisible()) {
          await facebookOption.check();
        }

        // Publish the post
        const publishButton = page.getByRole('button', { name: /publish|post.*now/i });
        await publishButton.click();

        // Should show publishing success
        await expect(
          page.locator('text=/published.*successfully|posted.*to.*facebook/i')
        ).toBeVisible({ timeout: 10000 });

        // Should show post URL or ID
        await expect(page.locator('text=/fb_post_12345/i')).toBeVisible();
      }
    });

    test('should schedule content for later publishing', async ({ page }) => {
      // Mock scheduled post creation
      await page.route('**/api/social/schedule', async (route) => {
        const requestData = await route.request().postDataJSON();

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            scheduleId: 'schedule_789',
            scheduledFor: requestData.scheduledAt,
            platforms: requestData.platforms,
            content: requestData.message,
            status: 'scheduled',
            estimatedPublishTime: requestData.scheduledAt
          })
        });
      });

      await page.goto('/dashboard/marketing/schedule');

      const contentInput = page.locator('textarea[placeholder*="content"], input[name*="message"]');
      if (await contentInput.isVisible()) {
        await contentInput.fill('Scheduled post content');

        // Set schedule time (tomorrow at 9 AM)
        const scheduleInput = page.locator('input[type="datetime-local"], input[name*="schedule"]');
        if (await scheduleInput.isVisible()) {
          const tomorrow9am = new Date();
          tomorrow9am.setDate(tomorrow9am.getDate() + 1);
          tomorrow9am.setHours(9, 0, 0, 0);

          await scheduleInput.fill(tomorrow9am.toISOString().slice(0, 16));
        }

        // Schedule the post
        const scheduleButton = page.getByRole('button', { name: /schedule|save.*draft/i });
        await scheduleButton.click();

        // Should show scheduling success
        await expect(
          page.locator('text=/scheduled.*successfully|post.*scheduled/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });

    test('should handle publishing failures gracefully', async ({ page }) => {
      // Mock publishing failure scenarios
      const failureScenarios = [
        {
          error: 'INSUFFICIENT_PERMISSIONS',
          message: 'Insufficient permissions to post on this page',
          action: 'Request additional permissions'
        },
        {
          error: 'CONTENT_VIOLATION',
          message: 'Content violates platform community guidelines',
          action: 'Review and edit content'
        },
        {
          error: 'RATE_LIMIT_EXCEEDED',
          message: 'Publishing rate limit exceeded. Try again later',
          action: 'Schedule for later'
        }
      ];

      for (const scenario of failureScenarios) {
        await page.route('**/api/social/facebook/publish', async (route) => {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              success: false,
              error: scenario.error,
              message: scenario.message,
              recommendedAction: scenario.action
            })
          });
        });

        await page.goto('/dashboard/marketing/publish');

        const contentTextarea = page.locator('textarea');
        if (await contentTextarea.isVisible()) {
          await contentTextarea.fill('Test content that will fail');

          const publishButton = page.getByRole('button', { name: /publish/i });
          await publishButton.click();

          // Should show specific error message
          await expect(
            page.locator(`text=/${scenario.message}/i`)
          ).toBeVisible({ timeout: 5000 });

          // Should show recommended action
          await expect(
            page.locator(`text=/${scenario.action}/i`)
          ).toBeVisible();
        }
      }
    });
  });

  test.describe('OAuth Security Validation', () => {
    test('should validate OAuth state parameter', async ({ page }) => {
      // Mock invalid state parameter
      await page.route('**/api/oauth/facebook/callback**', async (route) => {
        const url = new URL(route.request().url());
        const state = url.searchParams.get('state');

        if (state !== 'expected-state-token') {
          await route.fulfill({
            status: 400,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'Invalid state parameter',
              message: 'OAuth state validation failed. Possible CSRF attack.',
              securityIssue: true
            })
          });
        }
      });

      // Simulate OAuth callback with wrong state
      await page.goto('/auth/facebook/callback?code=test_code&state=wrong-state-token');

      // Should show security error
      await expect(
        page.locator('text=/state.*validation.*failed|security.*issue/i')
      ).toBeVisible({ timeout: 5000 });

      // Should redirect to safe page
      await expect(page).toHaveURL(/\/dashboard|\/login/);
    });

    test('should handle OAuth CSRF protection', async ({ page }) => {
      // Mock CSRF token validation
      await page.route('**/api/oauth/*/authorize', async (route) => {
        const headers = route.request().headers();
        const csrfToken = headers['x-csrf-token'];

        if (!csrfToken || csrfToken !== 'valid-csrf-token') {
          await route.fulfill({
            status: 403,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'CSRF token invalid',
              message: 'Missing or invalid CSRF protection token'
            })
          });
        }
      });

      await page.goto('/dashboard/integrations');

      // Should include CSRF token in OAuth requests
      const connectButton = page.getByRole('button', { name: /connect.*facebook/i });
      if (await connectButton.isVisible()) {
        await connectButton.click();

        // Should handle missing CSRF token appropriately
        await expect(
          page.locator('text=/security.*error|csrf.*token|try.*again/i')
        ).toBeVisible({ timeout: 5000 });
      }
    });
  });
});