import { Page, expect } from '@playwright/test';

/**
 * E2E Test Utilities
 *
 * Common helper functions for Sentinel E2E tests.
 */

/**
 * Wait for page to be fully loaded with network idle
 */
export async function waitForPageLoad(page: Page, timeout: number = 10000) {
  await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Check for console errors on the page
 */
export async function checkNoConsoleErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  return errors;
}

/**
 * Wait for element with test ID
 */
export async function waitForTestId(page: Page, testId: string, timeout: number = 10000) {
  return await page.waitForSelector(`[data-testid="${testId}"]`, { timeout });
}

/**
 * Get element by test ID
 */
export function getByTestId(page: Page, testId: string) {
  return page.locator(`[data-testid="${testId}"]`);
}

/**
 * Click element by test ID
 */
export async function clickByTestId(page: Page, testId: string) {
  const element = getByTestId(page, testId);
  await element.click();
}

/**
 * Check if element with test ID is visible
 */
export async function isTestIdVisible(page: Page, testId: string): Promise<boolean> {
  const element = getByTestId(page, testId);
  return await element.isVisible();
}

/**
 * Wait for API call to complete
 */
export async function waitForApiCall(page: Page, urlPattern: string | RegExp, timeout: number = 10000) {
  return await page.waitForResponse(
    (response) => {
      const url = response.url();
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern);
      }
      return urlPattern.test(url);
    },
    { timeout }
  );
}

/**
 * Navigate and wait for load
 */
export async function navigateAndWait(page: Page, path: string) {
  await page.goto(path);
  await waitForPageLoad(page);
}

/**
 * Take a screenshot with a descriptive name
 */
export async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({ path: `test-results/screenshots/${name}.png`, fullPage: true });
}

/**
 * Measure page load time
 */
export async function measureLoadTime(page: Page, url: string): Promise<number> {
  const startTime = Date.now();
  await page.goto(url);
  await page.waitForLoadState('domcontentloaded');
  return Date.now() - startTime;
}

/**
 * Check if text exists on page
 */
export async function hasText(page: Page, text: string | RegExp): Promise<boolean> {
  const locator = typeof text === 'string'
    ? page.locator(`text=${text}`)
    : page.locator(`:has-text("${text}")`);

  return await locator.isVisible().catch(() => false);
}

/**
 * Fill form field by test ID
 */
export async function fillByTestId(page: Page, testId: string, value: string) {
  const element = getByTestId(page, testId);
  await element.fill(value);
}

/**
 * Select option by test ID
 */
export async function selectByTestId(page: Page, testId: string, value: string) {
  const element = getByTestId(page, testId);
  await element.selectOption(value);
}

/**
 * Wait for element to contain specific text
 */
export async function waitForText(page: Page, testId: string, text: string | RegExp, timeout: number = 10000) {
  const element = getByTestId(page, testId);
  await expect(element).toContainText(text, { timeout });
}

/**
 * Get all elements by test ID
 */
export function getAllByTestId(page: Page, testId: string) {
  return page.locator(`[data-testid="${testId}"]`);
}

/**
 * Count elements by test ID
 */
export async function countByTestId(page: Page, testId: string): Promise<number> {
  const elements = getAllByTestId(page, testId);
  return await elements.count();
}

/**
 * Wait for specific count of elements
 */
export async function waitForCount(page: Page, testId: string, expectedCount: number, timeout: number = 10000) {
  await page.waitForFunction(
    ({ testId, expectedCount }) => {
      const elements = document.querySelectorAll(`[data-testid="${testId}"]`);
      return elements.length === expectedCount;
    },
    { testId, expectedCount },
    { timeout }
  );
}

/**
 * Check if page has no loading spinners
 */
export async function waitForNoLoadingSpinners(page: Page, timeout: number = 10000) {
  await page.waitForSelector('[data-testid="loading"], .loading, .spinner', {
    state: 'detached',
    timeout,
  }).catch(() => {
    // Spinner may not exist at all, which is fine
  });
}

/**
 * Scroll element into view by test ID
 */
export async function scrollIntoView(page: Page, testId: string) {
  const element = getByTestId(page, testId);
  await element.scrollIntoViewIfNeeded();
}

/**
 * Check for HTTP errors on page load
 */
export async function checkNoHttpErrors(page: Page): Promise<string[]> {
  const errors: string[] = [];

  page.on('response', (response) => {
    if (response.status() >= 400) {
      errors.push(`${response.status()} ${response.url()}`);
    }
  });

  return errors;
}

/**
 * Wait for backend to be ready
 */
export async function waitForBackend(baseUrl: string = 'http://localhost:8000', timeout: number = 30000): Promise<boolean> {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      const response = await fetch(`${baseUrl}/health`);
      if (response.ok) {
        return true;
      }
    } catch {
      // Backend not ready yet
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  return false;
}

/**
 * Get text content by test ID
 */
export async function getTextByTestId(page: Page, testId: string): Promise<string | null> {
  const element = getByTestId(page, testId);
  return await element.textContent();
}

/**
 * Check if element is enabled by test ID
 */
export async function isEnabledByTestId(page: Page, testId: string): Promise<boolean> {
  const element = getByTestId(page, testId);
  return await element.isEnabled();
}

/**
 * Double click element by test ID
 */
export async function doubleClickByTestId(page: Page, testId: string) {
  const element = getByTestId(page, testId);
  await element.dblclick();
}

/**
 * Hover over element by test ID
 */
export async function hoverByTestId(page: Page, testId: string) {
  const element = getByTestId(page, testId);
  await element.hover();
}
