// Auth flow tests — signup, login, logout, failed login
const { test, expect } = require('@playwright/test');
const { signupOrLogin, login, logout, TEST_EMAIL, TEST_PASS } = require('./helpers/auth');

test.describe('Auth flows', () => {
  test('signup creates account and lands on dashboard', async ({ page }) => {
    await signupOrLogin(page);
    await expect(page).toHaveURL(/\/dashboard|\/app/);
    // Logged-in nav should not show login link
    await expect(page.getByRole('link', { name: /log in/i })).not.toBeVisible();
  });

  test('login with valid credentials succeeds', async ({ page }) => {
    await signupOrLogin(page);   // ensure account exists
    await logout(page);
    await login(page);
    await expect(page).toHaveURL(/\/dashboard|\/app/);
  });

  test('login with bad password shows error, stays on login page', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#email', TEST_EMAIL);
    await page.fill('#password', 'WrongPassword!99');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/login');
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
  });

  test('login with unknown email shows error', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#email', 'nobody@nowhere.invalid');
    await page.fill('#password', 'Whatever123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/login');
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();
  });

  test('logout redirects to login page', async ({ page }) => {
    await signupOrLogin(page);
    await logout(page);
    await expect(page).toHaveURL('/login');
  });

  test('after logout, accessing dashboard redirects to login', async ({ page }) => {
    await signupOrLogin(page);
    await logout(page);
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });
});
