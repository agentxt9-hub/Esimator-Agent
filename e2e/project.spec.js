// Project creation + isolation tests — uses saved auth session (no login per test)
const { test, expect } = require('@playwright/test');
const { AUTH_STATE_PATH } = require('./helpers/global-setup');

// Reuse the auth session created in global-setup — avoids rate-limit churn
test.use({ storageState: AUTH_STATE_PATH });

test.describe('Project flows', () => {
  test('dashboard loads after login', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard|\/app/);
    await expect(page.locator('body')).not.toContainText('Internal Server Error');
    await expect(page.locator('body')).not.toContainText('500');
  });

  test('new project page loads', async ({ page }) => {
    await page.goto('/project/new');
    await expect(page.getByRole('heading', { name: /create new project/i })).toBeVisible();
    await expect(page.locator('[name="project_name"]')).toBeVisible();
  });

  test('create a project and land on project page', async ({ page }) => {
    await page.goto('/project/new');
    const projectName = `E2E Project ${Date.now()}`;
    await page.fill('[name="project_name"]', projectName);
    await page.fill('[name="project_number"]', 'E2E-001');
    await page.fill('[name="city"]', 'Denver');
    await page.fill('[name="state"]', 'CO');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/project\/\d+/);
    await expect(page.locator('body')).toContainText(projectName);
  });

  test('cross-company project access returns 403 or 404', async ({ page }) => {
    const res = await page.request.get('/project/999999');
    expect([403, 404]).toContain(res.status());
  });
});
