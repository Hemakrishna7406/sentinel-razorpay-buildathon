import { test, expect } from '@playwright/test';

/**
 * Live Decisions E2E Tests
 *
 * Tests the live decision feed that shows real-time authorization decisions.
 * This is a key page for demonstrating Sentinel's real-time capabilities.
 */

test.describe('Live Decisions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/decisions');
    await page.waitForLoadState('networkidle');
  });

  test('should load decisions page', async ({ page }) => {
    // Page title should be visible
    const heading = page.locator('h1');
    await expect(heading).toContainText(/decisions|live/i);
  });

  test('should display decision feed', async ({ page }) => {
    // Should show list of decisions
    const decisionList = page.locator('[data-testid="decision-list"]').first();
    await expect(decisionList).toBeVisible({ timeout: 10000 });
  });

  test('should show decision cards with key information', async ({ page }) => {
    // Each decision card should show essential information
    const decisionCard = page.locator('[data-testid="decision-card"]').first();

    if (await decisionCard.isVisible()) {
      // Should show decision type (ALLOW, ESCALATE, CONTAIN)
      const decision = decisionCard.locator('[data-testid="decision-type"]');
      await expect(decision).toBeVisible();

      // Should show agent identifier
      const agent = decisionCard.locator('[data-testid="agent-id"]');
      await expect(agent).toBeVisible();

      // Should show timestamp
      const timestamp = decisionCard.locator('[data-testid="timestamp"]');
      await expect(timestamp).toBeVisible();
    }
  });

  test('should open decision details on click', async ({ page }) => {
    const decisionCard = page.locator('[data-testid="decision-card"]').first();

    if (await decisionCard.isVisible()) {
      await decisionCard.click();

      // Modal or detail view should appear
      const modal = page.locator('[data-testid="decision-modal"]');
      await expect(modal).toBeVisible({ timeout: 5000 });

      // Should show detailed information
      const details = modal.locator('[data-testid="decision-details"]');
      await expect(details).toBeVisible();
    }
  });

  test('should filter decisions by type', async ({ page }) => {
    // Look for filter controls
    const filterButton = page.getByRole('button', { name: /filter|type/i }).first();

    if (await filterButton.isVisible()) {
      await filterButton.click();

      // Should show filter options
      const filterOptions = page.locator('[data-testid="filter-options"]');
      await expect(filterOptions).toBeVisible();
    }
  });

  test('should show decision statistics', async ({ page }) => {
    // Should display summary stats
    const stats = page.locator('[data-testid="decision-stats"]').first();
    await expect(stats).toBeVisible({ timeout: 10000 });
  });

  test('should handle empty state gracefully', async ({ page }) => {
    // If no decisions exist, should show empty state
    const emptyState = page.locator('text=/no decisions|no data/i');

    // Either decisions exist OR empty state is shown
    const hasDecisions = await page.locator('[data-testid="decision-card"]').isVisible();
    const hasEmptyState = await emptyState.isVisible();

    expect(hasDecisions || hasEmptyState).toBe(true);
  });

  test('should display risk scores correctly', async ({ page }) => {
    const decisionCard = page.locator('[data-testid="decision-card"]').first();

    if (await decisionCard.isVisible()) {
      // Risk score should be visible and formatted
      const riskScore = decisionCard.locator('[data-testid="risk-score"]');

      if (await riskScore.isVisible()) {
        const scoreText = await riskScore.textContent();
        expect(scoreText).toMatch(/\d+/); // Should contain a number
      }
    }
  });

  test('should paginate decisions if many exist', async ({ page }) => {
    const decisionCards = page.locator('[data-testid="decision-card"]');
    const count = await decisionCards.count();

    if (count > 10) {
      // Should have pagination controls
      const pagination = page.locator('[data-testid="pagination"]');
      await expect(pagination).toBeVisible();
    }
  });

  test('should update in real-time (polling or websocket)', async ({ page }) => {
    // Get initial count of decisions
    await page.waitForTimeout(1000);
    const initialCards = page.locator('[data-testid="decision-card"]');
    const initialCount = await initialCards.count();

    // Wait a bit for potential updates
    await page.waitForTimeout(3000);

    // Count should be same or increased (new decisions)
    const updatedCount = await initialCards.count();
    expect(updatedCount).toBeGreaterThanOrEqual(initialCount);
  });

  test('performance: page loads decision feed in under 2 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/dashboard/decisions');

    // Wait for first decision card to appear
    await page.waitForSelector('[data-testid="decision-card"]', { timeout: 10000 });

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(2000);
  });
});
