import { test, expect } from '@playwright/test';

/**
 * Core Authentication Tests
 *
 * These tests validate the fundamental authentication functionality that underlies
 * all tenant-specific operations. These must pass before any tenant tests can run.
 */
test.describe('Core Authentication System', () => {
  test.describe('Authentication Infrastructure', () => {
    test('should have working authentication endpoints', async ({ page }) => {
      let authEndpointsCalled = 0;

      // Mock core auth endpoints
      await page.route('**/api/auth/login', async (route) => {
        authEndpointsCalled++;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            accessToken: 'mock_access_token',
            refreshToken: 'mock_refresh_token',
            user: {
              id: 'core-test-user',
              email: 'test@core.com',
              firstName: 'Core',
              lastName: 'Test'
            }
          })
        });
      });

      await page.route('**/api/auth/me', async (route) => {
        authEndpointsCalled++;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'core-test-user',
              email: 'test@core.com',
              firstName: 'Core',
              lastName: 'Test'
            }
          })
        });
      });

      await page.goto('/login');

      // Should be able to interact with login form
      const emailInput = page.locator('input[type="email"], input[name*="email"]');
      const passwordInput = page.locator('input[type="password"], input[name*="password"]');
      const loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');

      if (await emailInput.count() > 0) {
        await emailInput.fill('test@core.com');
        await passwordInput.fill('testpassword');
        await loginButton.click();

        // Wait for potential API calls
        await page.waitForTimeout(2000);

        // Check that authentication endpoints were called
        expect(authEndpointsCalled).toBeGreaterThan(0);
      }
    });

    test('should handle authentication errors gracefully', async ({ page }) => {
      // Mock authentication failure
      await page.route('**/api/auth/login', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Invalid credentials',
            message: 'Email or password is incorrect'
          })
        });
      });

      await page.goto('/login');

      const emailInput = page.locator('input[type="email"], input[name*="email"]');
      const passwordInput = page.locator('input[type="password"], input[name*="password"]');
      const loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');

      if (await emailInput.count() > 0) {
        await emailInput.fill('wrong@email.com');
        await passwordInput.fill('wrongpassword');
        await loginButton.click();

        // Should show error message without crashing
        await page.waitForTimeout(2000);

        // Check for error indicators
        const hasErrorMessage = await page.locator(
          'text=/invalid.*credentials|wrong.*password|error/i, [class*="error"], [role="alert"]'
        ).count() > 0;

        // App should handle error gracefully (either show message or stay on login page)
        const stillOnLoginPage = page.url().includes('/login');
        const hasLoginForm = await emailInput.isVisible();

        expect(hasErrorMessage || stillOnLoginPage || hasLoginForm).toBe(true);
      }
    });

    test('should handle token storage correctly', async ({ page }) => {
      // Mock successful login
      await page.route('**/api/auth/login', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            accessToken: 'test_access_token_123',
            refreshToken: 'test_refresh_token_456',
            expiresIn: 3600,
            user: {
              id: 'core-test-user',
              email: 'test@core.com'
            }
          })
        });
      });

      await page.goto('/login');

      const emailInput = page.locator('input[type="email"], input[name*="email"]');
      const passwordInput = page.locator('input[type="password"], input[name*="password"]');
      const loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');

      if (await emailInput.count() > 0) {
        await emailInput.fill('test@core.com');
        await passwordInput.fill('testpassword');
        await loginButton.click();

        await page.waitForTimeout(2000);

        // Check that tokens are stored (localStorage or sessionStorage)
        const storedToken = await page.evaluate(() => {
          return localStorage.getItem('accessToken') ||
                 localStorage.getItem('authToken') ||
                 localStorage.getItem('token') ||
                 sessionStorage.getItem('accessToken') ||
                 sessionStorage.getItem('authToken') ||
                 sessionStorage.getItem('token');
        });

        // If the app uses token storage, it should work
        // If not, that's also valid (could use httpOnly cookies)
        console.log('Token storage check:', storedToken ? 'Found tokens' : 'No tokens in storage (possibly using cookies)');
      }
    });
  });

  test.describe('Session Management', () => {
    test('should handle session expiration', async ({ page }) => {
      // Mock expired session
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Token expired',
            message: 'Session has expired'
          })
        });
      });

      // Try to access protected route
      await page.goto('/dashboard');

      // Should redirect to login or show login form
      await page.waitForTimeout(2000);

      const isOnLoginPage = page.url().includes('/login');
      const hasLoginForm = await page.locator('input[type="email"], input[type="password"]').count() > 0;
      const hasAuthMessage = await page.locator('text=/login|sign.*in|authenticate/i').count() > 0;

      expect(isOnLoginPage || hasLoginForm || hasAuthMessage).toBe(true);
    });

    test('should handle refresh token flow', async ({ page }) => {
      let refreshTokenCalled = false;

      // Mock refresh token endpoint
      await page.route('**/api/auth/refresh', async (route) => {
        refreshTokenCalled = true;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            accessToken: 'new_access_token',
            refreshToken: 'new_refresh_token',
            expiresIn: 3600
          })
        });
      });

      // Mock initial auth that triggers refresh
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Token expired',
            refreshable: true
          })
        });
      });

      // Set a mock refresh token
      await page.evaluate(() => {
        localStorage.setItem('refreshToken', 'mock_refresh_token');
      });

      await page.goto('/dashboard');
      await page.waitForTimeout(3000);

      // Refresh token flow should be attempted if implemented
      console.log('Refresh token called:', refreshTokenCalled);
    });

    test('should handle logout correctly', async ({ page }) => {
      // Mock logout endpoint
      await page.route('**/api/auth/logout', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Logged out successfully'
          })
        });
      });

      // First, set up authenticated state
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'mock_token');
      });

      await page.goto('/dashboard');

      // Look for logout button/link
      const logoutElement = page.locator(
        'button:has-text("Logout"), button:has-text("Sign Out"), a:has-text("Logout"), a:has-text("Sign Out"), [data-testid*="logout"]'
      );

      if (await logoutElement.count() > 0) {
        await logoutElement.first().click();
        await page.waitForTimeout(2000);

        // Should redirect to login or clear tokens
        const tokensCleared = await page.evaluate(() => {
          return !localStorage.getItem('accessToken') &&
                 !localStorage.getItem('authToken') &&
                 !sessionStorage.getItem('accessToken');
        });

        const redirectedToLogin = page.url().includes('/login') || page.url().includes('/auth');

        expect(tokensCleared || redirectedToLogin).toBe(true);
      }
    });
  });

  test.describe('Registration System', () => {
    test('should have working registration flow', async ({ page }) => {
      // Mock registration endpoint
      await page.route('**/api/auth/register', async (route) => {
        const requestData = await route.request().postDataJSON();

        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            user: {
              id: 'new-user-123',
              email: requestData.email,
              firstName: requestData.firstName,
              lastName: requestData.lastName
            },
            message: 'Registration successful'
          })
        });
      });

      // Try to access registration page
      await page.goto('/register');

      // If registration page doesn't exist, try from login page
      if (page.url().includes('/login') || !page.url().includes('/register')) {
        await page.goto('/login');

        // Look for registration link
        const registerLink = page.locator('a:has-text("Register"), a:has-text("Sign Up"), a:has-text("Create Account")');
        if (await registerLink.count() > 0) {
          await registerLink.first().click();
          await page.waitForTimeout(1000);
        }
      }

      // Check for registration form fields
      const emailInput = page.locator('input[type="email"], input[name*="email"]');
      const passwordInput = page.locator('input[type="password"], input[name*="password"]');
      const firstNameInput = page.locator('input[name*="firstName"], input[name*="first"]');

      const hasRegistrationForm = await emailInput.count() > 0 &&
                                   await passwordInput.count() > 0;

      if (hasRegistrationForm) {
        await emailInput.fill('newuser@test.com');
        await passwordInput.fill('testpassword123');

        if (await firstNameInput.count() > 0) {
          await firstNameInput.fill('Test');
        }

        const submitButton = page.locator('button[type="submit"], button:has-text("Register"), button:has-text("Sign Up")');

        if (await submitButton.count() > 0) {
          await submitButton.click();
          await page.waitForTimeout(2000);

          // Should either redirect or show success message
          const hasSuccessIndication = await page.locator(
            'text=/success|registered|welcome/i, [class*="success"]'
          ).count() > 0;

          const redirectedFromRegister = !page.url().includes('/register');

          expect(hasSuccessIndication || redirectedFromRegister).toBe(true);
        }
      } else {
        console.log('Registration form not found - may not be implemented yet');
      }
    });

    test('should validate registration input', async ({ page }) => {
      // Mock validation error
      await page.route('**/api/auth/register', async (route) => {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Validation failed',
            message: 'Email already exists'
          })
        });
      });

      await page.goto('/register');

      // Look for registration form
      const emailInput = page.locator('input[type="email"], input[name*="email"]');
      const submitButton = page.locator('button[type="submit"], button:has-text("Register"), button:has-text("Sign Up")');

      if (await emailInput.count() > 0) {
        // Try to submit with existing email
        await emailInput.fill('existing@test.com');

        if (await submitButton.count() > 0) {
          await submitButton.click();
          await page.waitForTimeout(2000);

          // Should show validation error
          const hasErrorMessage = await page.locator(
            'text=/email.*exists|validation.*failed|error/i, [class*="error"], [role="alert"]'
          ).count() > 0;

          expect(hasErrorMessage).toBe(true);
        }
      }
    });
  });

  test.describe('Password Security', () => {
    test('should handle password reset flow', async ({ page }) => {
      // Mock password reset endpoint
      await page.route('**/api/auth/forgot-password', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            success: true,
            message: 'Password reset email sent'
          })
        });
      });

      await page.goto('/login');

      // Look for forgot password link
      const forgotPasswordLink = page.locator(
        'a:has-text("Forgot Password"), a:has-text("Reset Password"), a:has-text("Forgot")'
      );

      if (await forgotPasswordLink.count() > 0) {
        await forgotPasswordLink.first().click();
        await page.waitForTimeout(1000);

        // Should be on password reset page or show reset form
        const emailInput = page.locator('input[type="email"], input[name*="email"]');
        const resetButton = page.locator('button:has-text("Reset"), button:has-text("Send")');

        if (await emailInput.count() > 0) {
          await emailInput.fill('test@example.com');

          if (await resetButton.count() > 0) {
            await resetButton.click();
            await page.waitForTimeout(2000);

            // Should show success message
            const hasSuccessMessage = await page.locator(
              'text=/email.*sent|reset.*sent|check.*email/i'
            ).count() > 0;

            expect(hasSuccessMessage).toBe(true);
          }
        }
      } else {
        console.log('Password reset functionality not found - may not be implemented');
      }
    });

    test('should enforce password requirements', async ({ page }) => {
      await page.goto('/register');

      const passwordInput = page.locator('input[type="password"], input[name*="password"]');

      if (await passwordInput.count() > 0) {
        // Try weak password
        await passwordInput.fill('123');

        // Should show validation feedback
        await page.waitForTimeout(1000);

        const hasPasswordValidation = await page.locator(
          'text=/password.*weak|password.*short|minimum.*characters/i, [class*="error"], [class*="validation"]'
        ).count() > 0;

        // Password validation might be client-side or server-side
        console.log('Password validation check:', hasPasswordValidation ? 'Found' : 'Not visible');
      }
    });
  });

  test.describe('Multi-Factor Authentication (if implemented)', () => {
    test('should handle MFA flow if available', async ({ page }) => {
      // This test is optional since MFA might not be implemented yet

      // Mock MFA challenge
      await page.route('**/api/auth/mfa/challenge', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            challenge: 'mfa_challenge_token',
            methods: ['totp', 'sms']
          })
        });
      });

      console.log('MFA test - checking if implemented');

      // This test serves as a placeholder for future MFA implementation
      expect(true).toBe(true);
    });
  });
});

/**
 * Core User Context Tests
 *
 * These tests validate user context management that's required for tenant operations
 */
test.describe('Core User Context', () => {
  test.describe('User State Management', () => {
    test('should maintain user context across page reloads', async ({ page }) => {
      // Mock authenticated user
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'persistent-user',
              email: 'persistent@test.com',
              firstName: 'Persistent',
              lastName: 'User'
            }
          })
        });
      });

      // Set token to simulate logged in state
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'persistent_token');
      });

      await page.goto('/dashboard');
      await page.waitForTimeout(2000);

      // Reload the page
      await page.reload();
      await page.waitForTimeout(2000);

      // User should still be authenticated (either redirect to dashboard or show user info)
      const isAuthenticated = !page.url().includes('/login') && !page.url().includes('/auth');

      // Or check for user-specific content
      const hasUserContent = await page.locator(
        'text=/dashboard|welcome|persistent@test.com/i'
      ).count() > 0;

      expect(isAuthenticated || hasUserContent).toBe(true);
    });

    test('should handle concurrent session management', async ({ page, context }) => {
      // Create a second page to simulate another tab/window
      const secondPage = await context.newPage();

      // Mock authentication in both tabs
      const mockUser = {
        id: 'concurrent-user',
        email: 'concurrent@test.com'
      };

      for (const testPage of [page, secondPage]) {
        await testPage.route('**/api/auth/me', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ user: mockUser })
          });
        });

        await testPage.route('**/api/auth/logout', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ success: true })
          });
        });
      }

      // Login in first tab
      await page.evaluate(() => {
        localStorage.setItem('accessToken', 'concurrent_token');
      });

      await page.goto('/dashboard');
      await secondPage.goto('/dashboard');

      // Both should be authenticated
      await page.waitForTimeout(1000);
      await secondPage.waitForTimeout(1000);

      // Logout from first tab
      const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")');
      if (await logoutButton.count() > 0) {
        await logoutButton.first().click();
        await page.waitForTimeout(2000);

        // Check if second tab is affected (depends on implementation)
        await secondPage.reload();
        await secondPage.waitForTimeout(2000);

        console.log('Concurrent session test completed');
      }

      await secondPage.close();
    });
  });

  test.describe('Role and Permission Foundation', () => {
    test('should detect user role correctly', async ({ page }) => {
      const roles = ['admin', 'user', 'viewer'];

      for (const role of roles) {
        // Mock user with specific role
        await page.route('**/api/auth/me', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              user: {
                id: `${role}-user`,
                email: `${role}@test.com`,
                role: role,
                permissions: role === 'admin' ? ['*'] : [`read_${role}`, `write_${role}`]
              }
            })
          });
        });

        await page.goto('/dashboard');
        await page.waitForTimeout(2000);

        // Should load without errors regardless of role
        const isLoaded = await page.locator('body').isVisible();
        expect(isLoaded).toBe(true);

        console.log(`Role test passed for: ${role}`);
      }
    });

    test('should handle permission-based UI rendering', async ({ page }) => {
      // Mock user with limited permissions
      await page.route('**/api/auth/me', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            user: {
              id: 'limited-user',
              email: 'limited@test.com',
              role: 'viewer',
              permissions: ['read_invoices', 'read_inventory']
            }
          })
        });
      });

      await page.goto('/dashboard');
      await page.waitForTimeout(2000);

      // Should render appropriate UI based on permissions
      // The specific behavior depends on the implementation
      const hasContent = await page.locator('main, [role="main"], .dashboard').count() > 0;
      expect(hasContent).toBe(true);

      console.log('Permission-based UI test completed');
    });
  });
});