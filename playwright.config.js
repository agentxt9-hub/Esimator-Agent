// @ts-check
const { defineConfig, devices } = require('@playwright/test');
const { AUTH_STATE_PATH } = require('./e2e/helpers/global-setup');

// When BASE_URL is set (CI against staging), skip spinning up a local server.
// When running locally, Playwright starts run_server.py automatically.
const baseURL = process.env.BASE_URL || 'http://127.0.0.1:5000';
const isRemote = !!process.env.BASE_URL;

module.exports = defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/helpers/global-setup',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,      // sequential — single test DB instance
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'e2e/reports/html', open: 'never' }],
  ],

  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    headless: true,
  },

  // Spin up Flask automatically for local runs; skip for remote (staging/prod)
  webServer: isRemote ? undefined : {
    command: 'python run_server.py',
    url: 'http://127.0.0.1:5000/_health',
    reuseExistingServer: true,
    timeout: 30_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
