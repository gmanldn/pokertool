import { test, expect } from '@playwright/test';

/**
 * Visual regression tests for Navigation component
 * Tests both light and dark themes
 */
test.describe('Navigation Component - Visual Regression', () => {
  test('should match navigation bar in light/dark theme', async ({ page, colorScheme }) => {
    // Navigate to any page to see navigation
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Screenshot the AppBar (navigation)
    const appBar = page.locator('header[class*="MuiAppBar"]');
    await expect(appBar).toHaveScreenshot(`appbar-${colorScheme}.png`, {
      maxDiffPixels: 50,
    });
  });

  test('should match mobile drawer menu', async ({ page, colorScheme }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Open the mobile drawer
    const menuButton = page.locator('button[aria-label*="menu"], button:has(svg[data-testid="MenuIcon"])').first();
    if (await menuButton.isVisible()) {
      await menuButton.click();

      // Wait for drawer animation
      await page.waitForTimeout(500);

      // Screenshot the drawer
      const drawer = page.locator('[class*="MuiDrawer"]');
      await expect(drawer).toHaveScreenshot(`drawer-${colorScheme}.png`, {
        maxDiffPixels: 50,
      });
    }
  });

  test('should match backend status indicator', async ({ page, colorScheme }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Find and screenshot the backend status chip
    const statusChip = page.locator('header [class*="MuiChip"]').first();
    if (await statusChip.isVisible()) {
      await expect(statusChip).toHaveScreenshot(`backend-status-${colorScheme}.png`, {
        maxDiffPixels: 30,
      });
    }
  });
});
