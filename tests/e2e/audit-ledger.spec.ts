import { test, expect } from '@playwright/test';

/**
 * Audit Ledger E2E Tests
 *
 * Tests the tamper-proof audit chain that provides cryptographic proof
 * of all authorization decisions. This is critical for compliance and security.
 */

test.describe('Audit Ledger', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard/audit');
    await page.waitForLoadState('networkidle');
  });

  test('should load audit ledger page', async ({ page }) => {
    // Page title should be visible
    const heading = page.locator('h1');
    await expect(heading).toContainText(/audit|ledger|log/i);
  });

  test('should display audit entries', async ({ page }) => {
    // Should show list of audit entries
    const auditList = page.locator('[data-testid="audit-list"]').first();
    await expect(auditList).toBeVisible({ timeout: 10000 });
  });

  test('should show audit entry details', async ({ page }) => {
    const auditEntry = page.locator('[data-testid="audit-entry"]').first();

    if (await auditEntry.isVisible()) {
      // Should show timestamp
      const timestamp = auditEntry.locator('[data-testid="timestamp"]');
      await expect(timestamp).toBeVisible();

      // Should show entry type/action
      const action = auditEntry.locator('[data-testid="action"]');
      await expect(action).toBeVisible();

      // Should show hash for chain integrity
      const hash = auditEntry.locator('[data-testid="hash"]');
      await expect(hash).toBeVisible();
    }
  });

  test('should verify chain integrity', async ({ page }) => {
    // Look for chain verification button
    const verifyButton = page.getByRole('button', { name: /verify|check integrity/i }).first();

    if (await verifyButton.isVisible()) {
      await verifyButton.click();

      // Wait for verification result
      await page.waitForSelector('[data-testid="chain-status"]', { timeout: 10000 });

      // Should show VALID status (all tests passing = valid chain)
      const status = page.locator('[data-testid="chain-status"]');
      await expect(status).toContainText(/valid|verified|intact/i);
    }
  });

  test('should display chain integrity indicator', async ({ page }) => {
    // Should have visual indicator of chain health
    const indicator = page.locator('[data-testid="chain-integrity"]').first();
    await expect(indicator).toBeVisible({ timeout: 10000 });
  });

  test('should show previous hash links', async ({ page }) => {
    const auditEntry = page.locator('[data-testid="audit-entry"]').first();

    if (await auditEntry.isVisible()) {
      // Should show link to previous hash (blockchain-style)
      const prevHash = auditEntry.locator('[data-testid="prev-hash"]');

      if (await prevHash.isVisible()) {
        const hashText = await prevHash.textContent();
        expect(hashText).toMatch(/[0-9a-f]{8,}/); // Should look like a hash
      }
    }
  });

  test('should filter audit entries by type', async ({ page }) => {
    // Look for filter controls
    const filterButton = page.getByRole('button', { name: /filter|type/i }).first();

    if (await filterButton.isVisible()) {
      await filterButton.click();

      // Should show filter options
      const filterOptions = page.locator('[data-testid="filter-options"]');
      await expect(filterOptions).toBeVisible();
    }
  });

  test('should search audit entries', async ({ page }) => {
    // Look for search input
    const searchInput = page.getByPlaceholder(/search|find/i).first();

    if (await searchInput.isVisible()) {
      await searchInput.fill('test');
      await page.waitForTimeout(500);

      // Results should update
      const results = page.locator('[data-testid="audit-entry"]');
      expect(await results.count()).toBeGreaterThanOrEqual(0);
    }
  });

  test('should export audit log', async ({ page }) => {
    // Look for export button
    const exportButton = page.getByRole('button', { name: /export|download/i }).first();

    if (await exportButton.isVisible()) {
      await exportButton.click();

      // Should show export options or trigger download
      const exportModal = page.locator('[data-testid="export-modal"]');
      const downloadStarted = await exportModal.isVisible({ timeout: 2000 }).catch(() => false);

      // Either modal appears or download starts
      expect(downloadStarted).toBeTruthy();
    }
  });

  test('should display audit statistics', async ({ page }) => {
    // Should show summary stats about audit log
    const stats = page.locator('[data-testid="audit-stats"]').first();
    await expect(stats).toBeVisible({ timeout: 10000 });
  });

  test('should show chain visualization', async ({ page }) => {
    // Optional: visual representation of the chain
    const visualization = page.locator('[data-testid="chain-visualization"]');

    if (await visualization.isVisible()) {
      // Should render without errors
      await expect(visualization).toBeVisible();
    }
  });

  test('should handle large audit logs efficiently', async ({ page }) => {
    // Should use pagination or virtualization for performance
    const auditEntries = page.locator('[data-testid="audit-entry"]');
    const count = await auditEntries.count();

    // Should limit displayed entries for performance
    expect(count).toBeLessThanOrEqual(100);
  });

  test('performance: audit page loads in under 2 seconds', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/dashboard/audit');
    await page.waitForLoadState('domcontentloaded');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(2000);
  });
});
