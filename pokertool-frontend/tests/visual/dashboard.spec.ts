import { test, expect } from '@playwright/test';

/**
 * Visual regression tests for Dashboard page
 * Tests both light and dark themes
 */
test.describe('Dashboard Page - Visual Regression', () => {
  test('should match full dashboard snapshot', async ({ page, colorScheme }) => {
    // Navigate to dashboard
    await page.goto('/dashboard');

    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Wait for any WebSocket connections and initial data load
    await page.waitForTimeout(3000);

    // Take full page screenshot
    await expect(page).toHaveScreenshot(`dashboard-${colorScheme}.png`, {
      fullPage: true,
      // Allow for dynamic content differences
      maxDiffPixels: 150,
    });
  });

  test('should match dashboard header section', async ({ page, colorScheme }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Screenshot the header/title area
    const header = page.locator('main').first();
    await expect(header).toHaveScreenshot(`dashboard-header-${colorScheme}.png`, {
      maxDiffPixels: 50,
    });
  });
});
