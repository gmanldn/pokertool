import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for visual regression testing
 * Tests key UI components in both light and dark themes
 */
export default defineConfig({
  testDir: './tests/visual',

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use
  reporter: [
    ['html'],
    ['list'],
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'http://localhost:3000',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',
  },

  // Configure projects for major browsers
  projects: [
    // Chrome
    {
      name: 'chromium-light',
      use: {
        ...devices['Desktop Chrome'],
        colorScheme: 'light',
      },
    },
    {
      name: 'chromium-dark',
      use: {
        ...devices['Desktop Chrome'],
        colorScheme: 'dark',
      },
    },

    // Firefox
    {
      name: 'firefox-light',
      use: {
        ...devices['Desktop Firefox'],
        colorScheme: 'light',
      },
    },
    {
      name: 'firefox-dark',
      use: {
        ...devices['Desktop Firefox'],
        colorScheme: 'dark',
      },
    },

    // Safari (WebKit)
    {
      name: 'webkit-light',
      use: {
        ...devices['Desktop Safari'],
        colorScheme: 'light',
      },
    },
    {
      name: 'webkit-dark',
      use: {
        ...devices['Desktop Safari'],
        colorScheme: 'dark',
      },
    },

    // Edge
    {
      name: 'edge-light',
      use: {
        ...devices['Desktop Edge'],
        colorScheme: 'light',
      },
    },
    {
      name: 'edge-dark',
      use: {
        ...devices['Desktop Edge'],
        colorScheme: 'dark',
      },
    },
  ],

  // Run your local dev server before starting the tests
  // Comment out webServer since server is managed by start.py
  // webServer: {
  //   command: 'npm start',
  //   url: 'http://localhost:3000',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120000,
  // },
});
