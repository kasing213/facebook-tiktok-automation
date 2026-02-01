import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Facebook-automation E2E tests
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './e2e/tests',

  /* Run tests in files in parallel - reduced to respect rate limits */
  fullyParallel: false,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only - increased for rate limit handling */
  retries: process.env.CI ? 3 : 1,

  /* Limit workers to prevent rate limit violations */
  workers: 1,

  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
    ['json', { outputFile: 'test-results.json' }]
  ],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: 'http://localhost:5173',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Take screenshot on failure */
    screenshot: 'only-on-failure',

    /* Record video on failure */
    video: 'on-first-retry',

    /* Increased timeouts for rate limiting */
    actionTimeout: 15000,
    navigationTimeout: 20000,
  },

  /* Global timeout increased for rate limiting delays */
  timeout: 60000,

  /* Configure projects for major browsers */
  projects: [
    /* Setup project - runs before all tests to create auth state */
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    /* CORE TESTS - Run first to validate system foundation */
    {
      name: 'core-chromium',
      testMatch: /e2e\/tests\/core\/.*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
      },
      dependencies: ['setup'],
    },

    /* TENANT TESTS - Run after core tests pass */
    {
      name: 'tenant-chromium',
      testMatch: /e2e\/tests\/tenant\/.*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        /* Use prepared auth state */
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['core-chromium'],
    },

    /* EXISTING TESTS - Integration and user flows */
    {
      name: 'integration-chromium',
      testMatch: /e2e\/tests\/(?!core|tenant).*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        /* Use prepared auth state */
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['core-chromium'],
    },

    /* PERFORMANCE TESTS - Run separately */
    {
      name: 'performance-chromium',
      testMatch: /e2e\/tests\/performance\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        /* Use prepared auth state */
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['core-chromium'],
    },

    /* Multi-browser testing - Firefox (after core validation) */
    {
      name: 'core-firefox',
      testMatch: /e2e\/tests\/core\/.*\.spec\.ts/,
      use: {
        ...devices['Desktop Firefox'],
      },
      dependencies: ['core-chromium'], // Run only after Chrome core tests pass
    },

    {
      name: 'tenant-firefox',
      testMatch: /e2e\/tests\/tenant\/.*\.spec\.ts/,
      use: {
        ...devices['Desktop Firefox'],
        storageState: 'e2e/.auth/user.json',
      },
      dependencies: ['core-firefox'],
    },

    /* Webkit/Safari testing - Critical paths only */
    {
      name: 'core-webkit',
      testMatch: /e2e\/tests\/core\/system-health\.spec\.ts/,
      use: {
        ...devices['Desktop Safari'],
      },
      dependencies: ['core-firefox'],
    },
  ],

  /*
   * Before running tests, start servers manually:
   * Terminal 1: cd /mnt/d/Facebook-Automation && uvicorn app.main:app --reload --port 8000
   * Terminal 2: cd /mnt/d/Facebook-Automation/frontend && npm run dev
   *
   * Test execution order:
   * 1. Core system tests (foundation)
   * 2. Tenant-specific tests (business logic)
   * 3. Integration tests (user flows)
   * 4. Performance tests (optimization)
   */
});
