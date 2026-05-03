// Runs once before the test suite — creates the E2E test account and saves auth session.
// project.spec.js and api.spec.js (authenticated) use this saved state instead of logging in per-test.
const { chromium } = require('@playwright/test');
const { signupOrLogin } = require('./auth');
const path = require('path');

const AUTH_STATE_PATH = path.join(__dirname, '..', '.auth-state.json');

async function globalSetup(config) {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    baseURL: config.use?.baseURL || 'http://127.0.0.1:5000',
  });
  await signupOrLogin(page);
  await page.context().storageState({ path: AUTH_STATE_PATH });
  await browser.close();
}

module.exports = globalSetup;
module.exports.AUTH_STATE_PATH = AUTH_STATE_PATH;
