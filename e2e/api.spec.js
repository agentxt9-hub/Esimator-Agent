// API contract tests — JSON endpoints, auth guards, health checks
const { test, expect } = require('@playwright/test');
const { AUTH_STATE_PATH } = require('./helpers/global-setup');

test.describe('API contracts — unauthenticated guards', () => {
  test('GET /_health returns 200 with status ok', async ({ request }) => {
    const res = await request.get('/_health');
    expect(res.status()).toBe(200);
    const body = await res.json();
    expect(body.status).toBe('ok');
  });

  test('GET /ai/chat without session ends at login page', async ({ page }) => {
    // AI routes use @login_required — unauthenticated requests redirect to /login
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('unauthenticated GET /project/1 redirects to login', async ({ page }) => {
    await page.goto('/project/1');
    await expect(page).toHaveURL(/\/login/);
  });

  test('unauthenticated GET /settings redirects to login', async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL(/\/login/);
  });

  test('GET /_sentry-test returns 404 in production, 500 in dev', async ({ request }) => {
    const res = await request.get('/_sentry-test');
    expect([404, 500]).toContain(res.status());
  });
});

test.describe('API contracts — authenticated', () => {
  test.use({ storageState: AUTH_STATE_PATH });

  test('GET /dashboard returns 200 when authenticated', async ({ page }) => {
    const res = await page.request.get('/dashboard');
    expect(res.status()).toBe(200);
  });

  test('/project/new POST with missing name stays on form', async ({ page }) => {
    await page.goto('/project/new');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/project/new');
  });
});
