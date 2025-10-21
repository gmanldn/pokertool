import { test, expect } from '@playwright/test';

/**
 * Visual regression tests for SystemStatus page
 * Tests both light and dark themes
 */
test.describe('SystemStatus Page - Visual Regression', () => {
  test('should match snapshot in light/dark theme', async ({ page, colorScheme }) => {
    // Navigate to System Status page
    await page.goto('/system-status');

    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle');

    // Wait for any health checks to complete
    await page.waitForTimeout(2000);

    // Take screenshot and compare
    await expect(page).toHaveScreenshot(`system-status-${colorScheme}.png`, {
      fullPage: true,
      // Allow small differences due to timing/animation
      maxDiffPixels: 100,
    });
  });

  test('should match navigation bar snapshot', async ({ page, colorScheme }) => {
    await page.goto('/system-status');
    await page.waitForLoadState('networkidle');

    // Screenshot just the navigation bar
    const nav = page.locator('header');
    await expect(nav).toHaveScreenshot(`navigation-${colorScheme}.png`, {
      maxDiffPixels: 50,
    });
  });

  test('should match health status cards', async ({ page, colorScheme }) => {
    await page.goto('/system-status');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Find the main content area with health cards
    const mainContent = page.locator('main');
    await expect(mainContent).toHaveScreenshot(`health-cards-${colorScheme}.png`, {
      fullPage: false,
      maxDiffPixels: 100,
    });
  });
});
