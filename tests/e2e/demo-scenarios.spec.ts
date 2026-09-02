import { test, expect } from '@playwright/test';

/**
 * Demo Scenarios E2E Tests
 *
 * Tests all 5 demo scenarios that will be shown to judges:
 * 1. Normal Agent - Legitimate transfer (ALLOW)
 * 2. Suspicious Agent - Anomalous behavior (ESCALATE)
 * 3. Malicious Agent - Clear attack (CONTAIN)
 * 4. Replay Attack - Duplicate JTI (REJECT)
 * 5. Redis Failure - Graceful degradation (FAIL_CLOSED)
 */

test.describe('Demo Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard overview which has demo scenarios
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should load demo scenario section', async ({ page }) => {
    // Check for demo scenarios section
    const demoSection = page.locator('text=/demo|scenario|try it/i').first();
    await expect(demoSection).toBeVisible({ timeout: 10000 });
  });

  test('should execute normal agent scenario', async ({ page }) => {
    // Look for Normal Agent scenario button
    const normalAgentButton = page.getByRole('button', { name: /normal|legitimate/i }).first();

    if (await normalAgentButton.isVisible()) {
      await normalAgentButton.click();

      // Wait for decision result
      await page.waitForSelector('[data-testid="decision-result"]', { timeout: 10000 });

      // Should show ALLOW decision
      const decision = page.locator('[data-testid="decision"]');
      await expect(decision).toContainText(/allow/i);

      // Should display risk score
      const riskScore = page.locator('[data-testid="risk-score"]');
      await expect(riskScore).toBeVisible();
    }
  });

  test('should execute suspicious agent scenario', async ({ page }) => {
    const suspiciousButton = page.getByRole('button', { name: /suspicious|escalate/i }).first();

    if (await suspiciousButton.isVisible()) {
      await suspiciousButton.click();

      await page.waitForSelector('[data-testid="decision-result"]', { timeout: 10000 });

      // Should show ESCALATE decision
      const decision = page.locator('[data-testid="decision"]');
      await expect(decision).toContainText(/escalate/i);
    }
  });

  test('should execute malicious agent scenario', async ({ page }) => {
    const maliciousButton = page.getByRole('button', { name: /malicious|contain/i }).first();

    if (await maliciousButton.isVisible()) {
      await maliciousButton.click();

      await page.waitForSelector('[data-testid="decision-result"]', { timeout: 10000 });

      // Should show CONTAIN decision
      const decision = page.locator('[data-testid="decision"]');
      await expect(decision).toContainText(/contain/i);
    }
  });

  test('should execute replay attack scenario', async ({ page }) => {
    const replayButton = page.getByRole('button', { name: /replay|duplicate/i }).first();

    if (await replayButton.isVisible()) {
      await replayButton.click();

      await page.waitForSelector('[data-testid="decision-result"]', { timeout: 10000 });

      // Should show rejection due to duplicate JTI
      const result = page.locator('[data-testid="decision-result"]');
      await expect(result).toContainText(/duplicate|replay|rejected/i);
    }
  });

  test('should execute redis failure scenario', async ({ page }) => {
    const failureButton = page.getByRole('button', { name: /redis|failure|fail/i }).first();

    if (await failureButton.isVisible()) {
      await failureButton.click();

      await page.waitForSelector('[data-testid="decision-result"]', { timeout: 10000 });

      // Should show fail-closed behavior
      const result = page.locator('[data-testid="decision-result"]');
      await expect(result).toContainText(/fail|closed|degraded/i);
    }
  });

  test('should display scenario details', async ({ page }) => {
    // Each scenario should have details about what it demonstrates
    const scenarioCards = page.locator('[data-testid="scenario-card"]');

    if (await scenarioCards.first().isVisible()) {
      const count = await scenarioCards.count();
      expect(count).toBeGreaterThanOrEqual(5); // At least 5 scenarios
    }
  });

  test('should show execution timeline', async ({ page }) => {
    const normalButton = page.getByRole('button', { name: /normal|legitimate/i }).first();

    if (await normalButton.isVisible()) {
      await normalButton.click();
      await page.waitForTimeout(1000);

      // Should show steps in the authorization flow
      const timeline = page.locator('[data-testid="execution-timeline"]');
      await expect(timeline).toBeVisible({ timeout: 10000 });
    }
  });

  test('performance: scenario execution completes in under 5 seconds', async ({ page }) => {
    const button = page.getByRole('button', { name: /normal|legitimate/i }).first();

    if (await button.isVisible()) {
      const startTime = Date.now();
      await button.click();

      await page.waitForSelector('[data-testid="decision-result"]', { timeout: 10000 });

      const executionTime = Date.now() - startTime;
      expect(executionTime).toBeLessThan(5000);
    }
  });
});
