import { test, expect } from '@playwright/test';

/**
 * Landing Page E2E Tests
 *
 * Tests the public-facing landing page that judges will see first.
 * Validates hero messaging, animations, and navigation to app.
 */

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load and display hero section', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for key hero elements
    await expect(page.locator('h1')).toBeVisible();

    // Verify the main value proposition is present
    const heading = page.locator('h1');
    await expect(heading).toContainText('AI');
  });

  test('should display animated architecture diagram', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Check for architecture visualization elements
    // Note: Update these selectors once frontend team implements the animations
    const architectureSection = page.locator('[data-testid="architecture-section"]').first();
    await expect(architectureSection).toBeVisible({ timeout: 10000 });
  });

  test('should have working CTA button', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Look for primary CTA (Get Started, View Demo, etc.)
    const ctaButton = page.getByRole('button', { name: /get started|view demo|try it/i }).first();

    if (await ctaButton.isVisible()) {
      await ctaButton.click();

      // Should navigate to dashboard or demo
      await expect(page).toHaveURL(/.*dashboard.*/);
    }
  });

  test('should display key features or benefits', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Check for feature section
    const features = page.locator('text=/zero-trust|authorization|security/i').first();
    await expect(features).toBeVisible();
  });

  test('should have responsive navigation', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Navigation should be present
    const nav = page.locator('nav').first();
    await expect(nav).toBeVisible();
  });

  test('performance: page loads in under 3 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(3000);
  });
});
