// Smoke tests — public pages, health endpoint, brand assertions
const { test, expect } = require('@playwright/test');

test.describe('Public smoke', () => {
  test('landing page loads', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Zenbid/i);
  });

  test('landing page has correct CTA — no $29/mo', async ({ page }) => {
    await page.goto('/');
    const body = await page.content();
    expect(body).not.toContain('$29/mo');
    expect(body).not.toContain('Join Waitlist');
    // Reserve beta access CTA must be present
    await expect(page.getByText(/reserve beta access/i).first()).toBeVisible();
  });

  test('landing H1 has estimator-native copy', async ({ page }) => {
    await page.goto('/');
    const h1 = await page.locator('h1').first().textContent();
    expect(h1).not.toMatch(/build smarter/i);
    expect(h1).not.toMatch(/ai-powered/i);
  });

  test('health endpoint returns ok', async ({ request }) => {
    const res = await request.get('/_health');
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('ok');
  });

  test('login page loads', async ({ page }) => {
    await page.goto('/login');
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('signup page loads', async ({ page }) => {
    await page.goto('/signup');
    await expect(page.locator('#company_name')).toBeVisible();
    await expect(page.locator('#email')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();
  });

  test('unauthenticated dashboard redirects to login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('unauthenticated project route redirects to login', async ({ page }) => {
    await page.goto('/project/1');
    await expect(page).toHaveURL(/\/login/);
  });
});
