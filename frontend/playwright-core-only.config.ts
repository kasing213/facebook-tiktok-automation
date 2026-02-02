import { defineConfig, devices } from '@playwright/test';

/**
 * Core-only Playwright configuration
 * Bypasses authentication setup for core system tests
 */
export default defineConfig({
  testDir: './e2e/tests/core',

  /* Run tests in files in parallel */
  fullyParallel: false,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 1,

  /* Limit workers to prevent issues */
  workers: 1,

  /* Reporter to use */
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report-core' }]
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

    /* Standard timeouts */
    actionTimeout: 10000,
    navigationTimeout: 15000,
  },

  /* Global timeout */
  timeout: 30000,

  /* Configure projects for major browsers */
  projects: [
    /* CORE TESTS ONLY - No authentication dependency */
    {
      name: 'core-chromium',
      testMatch: /.*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
      },
      // NO dependencies - run independently
    },
  ],
});