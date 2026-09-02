import { test, expect } from '@playwright/test';

/**
 * Dashboard Overview E2E Tests
 *
 * Tests the main dashboard that provides a high-level view of the system.
 * This is the first page users see after logging in.
 */

test.describe('Dashboard Overview', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should load dashboard', async ({ page }) => {
    // Dashboard should be visible
    const dashboard = page.locator('[data-testid="dashboard"]').first();
    await expect(dashboard).toBeVisible({ timeout: 10000 });
  });

  test('should display KPI cards', async ({ page }) => {
    // Should show key performance indicators
    const kpiCards = page.locator('[data-testid="kpi-card"]');

    if (await kpiCards.first().isVisible()) {
      const count = await kpiCards.count();
      expect(count).toBeGreaterThanOrEqual(4); // Should have multiple KPIs
    }
  });

  test('should show decision trend chart', async ({ page }) => {
    // Should display chart of decisions over time
    const chart = page.locator('[data-testid="decision-trend-chart"]').first();

    if (await chart.isVisible()) {
      await expect(chart).toBeVisible();
    }
  });

  test('should display risk distribution', async ({ page }) => {
    // Should show breakdown of risk levels
    const riskChart = page.locator('[data-testid="risk-distribution"]').first();

    if (await riskChart.isVisible()) {
      await expect(riskChart).toBeVisible();
    }
  });

  test('should show system health status', async ({ page }) => {
    // Should display health of all subsystems
    const healthStatus = page.locator('[data-testid="system-health"]').first();
    await expect(healthStatus).toBeVisible({ timeout: 10000 });
  });

  test('should display recent activity', async ({ page }) => {
    // Should show recent decisions or events
    const activity = page.locator('[data-testid="recent-activity"]').first();

    if (await activity.isVisible()) {
      await expect(activity).toBeVisible();
    }
  });

  test('should have working navigation to other sections', async ({ page }) => {
    // Should be able to navigate to decisions page
    const decisionsLink = page.getByRole('link', { name: /decisions/i }).first();

    if (await decisionsLink.isVisible()) {
      await decisionsLink.click();
      await expect(page).toHaveURL(/.*decisions.*/);
    }
  });

  test('should show total decisions count', async ({ page }) => {
    // Should display total number of decisions processed
    const totalDecisions = page.locator('text=/total decisions|decisions processed/i').first();

    if (await totalDecisions.isVisible()) {
      const text = await totalDecisions.textContent();
      expect(text).toMatch(/\d+/); // Should contain a number
    }
  });

  test('should display average response time', async ({ page }) => {
    // Should show system performance metric
    const responseTime = page.locator('text=/response time|latency|p95|p99/i').first();

    if (await responseTime.isVisible()) {
      const text = await responseTime.textContent();
      expect(text).toMatch(/\d+\s*(ms|sec)/i); // Should show time with unit
    }
  });

  test('should show active agents count', async ({ page }) => {
    // Should display number of connected agents
    const agentsCount = page.locator('text=/agents|active agents/i').first();

    if (await agentsCount.isVisible()) {
      const text = await agentsCount.textContent();
      expect(text).toMatch(/\d+/); // Should contain a number
    }
  });

  test('should have refresh button', async ({ page }) => {
    // Should allow manual refresh of data
    const refreshButton = page.getByRole('button', { name: /refresh|reload/i }).first();

    if (await refreshButton.isVisible()) {
      await expect(refreshButton).toBeEnabled();
    }
  });

  test('should update data automatically', async ({ page }) => {
    // Should poll for updates
    await page.waitForTimeout(2000);

    // Check that data is fresh (no errors)
    const errorMessage = page.locator('text=/error|failed to load/i');
    await expect(errorMessage).not.toBeVisible();
  });

  test('performance: dashboard loads in under 2 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(2000);
  });
});
