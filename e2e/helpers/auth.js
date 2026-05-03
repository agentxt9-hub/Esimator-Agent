// Shared auth helper — creates or reuses a test session
const { expect } = require('@playwright/test');

const TEST_COMPANY = 'E2E Test Co';
const TEST_EMAIL   = process.env.E2E_EMAIL    || 'e2e-test@zenbid-test.local';
const TEST_PASS    = process.env.E2E_PASSWORD  || 'E2eTestPass!1';

/**
 * Log in with test credentials. Assumes the account already exists.
 * Use signupAndLogin() on first run to create the account.
 */
async function login(page) {
  await page.goto('/login');
  await page.fill('#email', TEST_EMAIL);
  await page.fill('#password', TEST_PASS);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/\/dashboard|\/app/, { timeout: 10_000 });
}

/**
 * Sign up for a new account (only if it doesn't exist yet) and land on dashboard.
 * Idempotent: if signup fails with "already registered" we fall back to login.
 */
async function signupOrLogin(page) {
  await page.goto('/signup');
  await page.fill('#company_name', TEST_COMPANY);
  await page.fill('#full_name', 'E2E Runner');
  await page.fill('#email', TEST_EMAIL);
  await page.fill('#password', TEST_PASS);
  // check terms if present
  const terms = page.locator('#terms');
  if (await terms.count()) await terms.check();
  await page.click('button[type="submit"]');

  // Either lands on dashboard or shows "already registered" error
  const url = page.url();
  if (url.includes('/signup')) {
    // account exists — fall back to login
    await login(page);
  } else {
    await expect(page).toHaveURL(/\/dashboard|\/app/, { timeout: 10_000 });
  }
}

async function logout(page) {
  await page.goto('/logout');
  await expect(page).toHaveURL('/login');
}

module.exports = { login, signupOrLogin, logout, TEST_EMAIL, TEST_PASS, TEST_COMPANY };
