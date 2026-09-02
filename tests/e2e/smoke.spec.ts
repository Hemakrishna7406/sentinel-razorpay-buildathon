import { test, expect } from '@playwright/test';

/**
 * Smoke Tests
 *
 * Quick sanity checks to ensure the system is basically functional.
 * Run these first to catch major issues before running full test suite.
 */

test.describe('Smoke Tests', () => {
  test('landing page loads', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Page should load without errors
    const title = await page.title();
    expect(title).toBeTruthy();
  });

  test('dashboard is accessible', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');

    // Should load without 404
    const url = page.url();
    expect(url).toContain('dashboard');
  });

  test('no console errors on landing page', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should have no console errors
    expect(errors.length).toBe(0);
  });

  test('no console errors on dashboard', async ({ page }) => {
    const errors: string[] = [];

    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Should have no console errors
    expect(errors.length).toBe(0);
  });

  test('API is reachable', async ({ page }) => {
    const response = await page.request.get('http://localhost:8000/health');
    expect(response.ok()).toBeTruthy();
  });

  test('frontend assets load', async ({ page }) => {
    const resources: string[] = [];

    page.on('response', (response) => {
      if (response.status() >= 400) {
        resources.push(`${response.status()} ${response.url()}`);
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // No 404s or 500s for assets
    expect(resources.length).toBe(0);
  });

  test('navigation works', async ({ page }) => {
    await page.goto('/');

    // Try navigating to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');

    const url = page.url();
    expect(url).toContain('dashboard');
  });

  test('responsive design works', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Page should still be functional
    const content = await page.textContent('body');
    expect(content).toBeTruthy();
  });
});
